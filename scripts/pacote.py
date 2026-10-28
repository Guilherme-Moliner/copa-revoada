#!/usr/bin/env python3
"""
Copa Revoada — pacote de mídias.

Lê o arquivo de lances baixado do Registro ("Baixar lances") e gera, numa
pasta só daquele jogo, todas as peças com transparência de verdade (ProRes
4444 em .mov, e PNG para o placar parado) e o manifesto.tsv que o script do
DaVinci lê para posicionar cada uma na timeline.

    .venv\\Scripts\\python.exe scripts\\pacote.py gerar caminho\\lances-<jogo>.json
    .venv\\Scripts\\python.exe scripts\\pacote.py teste

Opções do gerar:
    --inicio SEG   onde o placar fixo começa, em segundos do vídeo (padrão 0)
    --fim SEG      onde termina (padrão: a duração do vídeo, se o arquivo
                   trouxer; senão, 30 s depois do último lance)

O desenho é o mesmo do site: a página index.html é aberta de verdade num
Chromium sem janela e quem pinta é o próprio código do Estúdio. Aqui só se
escolhe o quadro e se recolhe a imagem — sem MediaRecorder, sem relógio,
sem fundo verde.

Precisa de ferramentas/ffmpeg e do Chromium do Playwright em
ferramentas/ms-playwright (ver docs/pacote-de-midias.md).
"""

import base64
import functools
import glob
import http.server
import json
import os
import subprocess
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTAS = os.path.join(RAIZ, "ferramentas")
FFMPEG = os.path.join(FERRAMENTAS, "ffmpeg", "ffmpeg.exe")
MIDIAS = os.path.join(RAIZ, "midias")

# O Playwright baixaria o navegador para a pasta do usuário; com esta variável
# ele procura dentro do projeto, onde foi instalado.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(FERRAMENTAS, "ms-playwright"))

# A timeline do DaVinci é 24 fps, e a peça tem que ter o mesmo fps: quadro de
# arte e quadro de vídeo andam juntos, sem o Resolve reamostrar nada.
FPS = 24

# ---------------------------------------------------------------------------
# GUIA DE TEMPO DE CADA PEÇA — é aqui que se ajusta.
#
# Cada peça entra, segura e sai dentro da duração. Peça mais densa precisa de
# mais tempo para dar para ler: a regra é 1 s a mais do que parece bastar.
#
#   chave: (trilha, começa N s depois do gol, duração em s, o que é)
#
# O placar fixo fica na mesma trilha do placar animado: ele some enquanto o
# gol anima e volta com o placar novo.
PECAS_GOL = {
    "placar": (2, 0.0, 5.0, "placar de transmissão com a animação do gol"),
    "golaco": (3, 0.0, 4.0, "GOL em tela cheia com o nome de quem fez"),
    "barra":  (4, 4.0, 6.0, "barra inferior com foto, nome, time e minuto"),
}
TRILHA_PLACAR_FIXO = 2
# ---------------------------------------------------------------------------


def servidor():
    """Serve a pasta do projeto numa porta livre, só nesta máquina.
    O index.html precisa de http (as fotos em img/ não abrem por file://)."""
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quieto, directory=RAIZ)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def abre_estudio(navegador, porta):
    pg = navegador.new_page(viewport={"width": 1600, "height": 1000})
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"http://127.0.0.1:{porta}/index.html", wait_until="networkidle")
    # sem as fontes carregadas, o primeiro quadro sai com a fonte de reserva
    pg.evaluate("""async () => {
        await document.fonts.ready;
        await Promise.all([
          document.fonts.load('400 300px "Archivo Black"'),
          document.fonts.load('800 32px "Barlow Condensed"'),
          document.fonts.load('800 96px "Barlow Condensed"')]);
        go('estudio');
    }""")
    if erros:
        sys.exit("a página do site deu erro ao abrir: " + erros[0])
    return pg


def prepara(pg, prepara_js, segundos):
    """Deixa o Estúdio com os campos que a peça pede e espera as fotos."""
    erro = pg.evaluate(f"""async () => {{
        const erro = ({prepara_js})(F);
        if(erro) return erro;
        syncFields();
        F.dur.value = {segundos};
        // fotos chegam depois do primeiro desenho; espera todas
        await Promise.all([...document.images].filter(i=>!i.complete)
          .map(i=>new Promise(r=>{{ i.onload=i.onerror=r; }})));
        await new Promise(r=>setTimeout(r,200));
        return '';
    }}""")
    return erro


def quadro_png(pg, u):
    """Um quadro do canvas em PNG. u=None é a peça assentada, parada."""
    js = "null" if u is None else repr(u)
    url = pg.evaluate(f"""() => {{
        const u = {js};
        animandoLance = u !== null;
        draw(u === null ? 1 : curva(u));
        animandoLance = false;
        return cv.toDataURL('image/png');
    }}""")
    return base64.b64decode(url.split(",", 1)[1])


def grava_mov(pg, segundos, saida):
    """Desenha a peça quadro a quadro e entrega ao ffmpeg. Cada quadro é
    desenhado no seu instante exato da animação (i/(total-1))."""
    total = max(2, round(segundos * FPS))
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
           # ProRes 4444 com alfa: abre no Resolve gratuito no Windows
           "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
           "-alpha_bits", "16", "-vendor", "apl0", "-r", str(FPS), saida]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(total):
            ff.stdin.write(quadro_png(pg, i / (total - 1)))
    finally:
        ff.stdin.close()
        ff.wait()
    if ff.returncode:
        sys.exit(f"o ffmpeg falhou ao gravar {saida}")
    return total


def timecode(quadro, inicio_h=1):
    """Timecode de conferência, contando a timeline a partir de 01:00:00:00."""
    q = quadro + inicio_h * 3600 * FPS
    h, q = divmod(q, 3600 * FPS)
    m, q = divmod(q, 60 * FPS)
    s, f = divmod(q, FPS)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def mmss(seg):
    seg = int(round(seg))
    return f"{seg // 60}:{seg % 60:02d}"


# --------------------------------------------------------------------------
# o que gerar


def planeja(dados, inicio, fim):
    """Transforma os lances em peças: cada uma com arquivo, trilha, quadro de
    entrada e duração em quadros. O placar é calculado gol a gol, na ordem do
    tempo do vídeo."""
    gols = [e for e in dados["eventos"] if e.get("tipo") == "gol"]
    sem_tempo = [e for e in gols if e.get("seg") is None]
    if sem_tempo:
        sys.exit(f"{len(sem_tempo)} gol(s) sem o tempo do vídeo. Sem ele não há onde pôr a "
                 "peça: marque de novo com o vídeo carregado no Registro.")
    gols.sort(key=lambda e: float(e["seg"]))

    pecas = []
    gc = gf = 0
    q_cursor = round(inicio * FPS)
    q_fim = round(fim * FPS)
    for n, g in enumerate(gols, 1):
        seg = float(g["seg"])
        if g["t"] == "A":
            gc += 1
        else:
            gf += 1
        g["placar_depois"] = (gc, gf)
        lance = f"gol-{n:02d}"

        trilha, desloc, dur, _ = PECAS_GOL["placar"]
        q_anim = round((seg + desloc) * FPS)
        if q_anim < q_cursor:
            print(f"  ! {lance} aos {mmss(seg)} veio colado no anterior: a animação do placar "
                  f"começa {(q_cursor - q_anim) / FPS:.1f} s depois")
            q_anim = q_cursor
        antes = (gc - (g["t"] == "A"), gf - (g["t"] != "A"))
        if q_anim > q_cursor:
            pecas.append(dict(lance=f"placar-{antes[0]}x{antes[1]}", peca="placar-fixo",
                              arquivo=f"placar-fixo-{antes[0]}x{antes[1]}.png", tipo="imagem",
                              quadro=q_cursor, duracao=q_anim - q_cursor,
                              trilha=TRILHA_PLACAR_FIXO, gc=antes[0], gf=antes[1]))
        q_dur = round(dur * FPS)
        pecas.append(dict(lance=lance, peca="placar", arquivo=f"{lance}-placar.mov", tipo="video",
                          quadro=q_anim, duracao=q_dur, trilha=trilha, gc=gc, gf=gf,
                          evento="golCasa" if g["t"] == "A" else "golFora", seg=seg))
        q_cursor = q_anim + q_dur

        for peca in ("golaco", "barra"):
            trilha, desloc, dur, _ = PECAS_GOL[peca]
            pecas.append(dict(lance=lance, peca=peca, arquivo=f"{lance}-{peca}.mov", tipo="video",
                              quadro=round((seg + desloc) * FPS), duracao=round(dur * FPS),
                              trilha=trilha, jogador=g.get("j") or "", lado=g["t"],
                              minuto=g.get("min"), seg=seg))

    if q_fim > q_cursor:
        pecas.append(dict(lance=f"placar-{gc}x{gf}", peca="placar-fixo",
                          arquivo=f"placar-fixo-{gc}x{gf}.png", tipo="imagem",
                          quadro=q_cursor, duracao=q_fim - q_cursor,
                          trilha=TRILHA_PLACAR_FIXO, gc=gc, gf=gf))
    return gols, pecas


def js_placar(dados, p, segundos):
    """Campos do placar de transmissão. Sem relógio: o placar parado fica no
    ar o jogo inteiro, e um relógio congelado ali seria mentira."""
    return f"""F => {{
        const P = LANCES.estado.placar;
        const casa = {json.dumps(dados['casa']['id'])}, fora = {json.dumps(dados['fora']['id'])};
        if(!tById[casa] || !tById[fora]) return 'time desconhecido no site: '+casa+' ou '+fora;
        Object.assign(P, {{modo:'jogo', casa, fora, gc:{p['gc']}, gf:{p['gf']},
          relogio:'', acrescimo:0, competicao:{json.dumps(competicao(dados))}, fase:'',
          pos:'topo-esq', escala:1, evento:{json.dumps(p.get('evento', 'nenhum'))},
          dur:{segundos}}});
        F.tipo.value = 'placar2';
        return '';
    }}"""


def js_gol(dados, p):
    """Campos da barra de gol e do GOL em tela cheia."""
    time = dados["casa"]["id"] if p["lado"] == "A" else dados["fora"]["id"]
    titulo = "GOL NA COPA REVOADA" if dados.get("conta_na_copa", True) else "GOL"
    minuto = "" if p.get("minuto") is None else f"{p['minuto']}'"
    return f"""F => {{
        const quem = jog.find(x=>x.apelido === {json.dumps(p['jogador'])});
        if(!quem) return 'jogador {p['jogador']} não está no site';
        if(!tById[{json.dumps(time)}]) return 'time desconhecido no site: {time}';
        F.tipo.value = {json.dumps('gol' if p['peca'] == 'barra' else 'golaco')};
        F.p1.value = quem.id;
        F.time.value = {json.dumps(time)};
        F.min.value = {json.dumps(minuto)};
        TITULO_GOL = {json.dumps(titulo)};
        return '';
    }}"""


def competicao(dados):
    if dados.get("conta_na_copa", True):
        return "COPA REVOADA"
    return (dados.get("nome") or dados["jogo"]).upper()


def gerar(arquivo, inicio=0.0, fim=None):
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(FFMPEG):
        sys.exit("falta o ffmpeg em ferramentas/ffmpeg — ver docs/pacote-de-midias.md")
    dados = json.load(open(arquivo, encoding="utf-8"))
    if dados.get("formato") != "copa-revoada-lances/1":
        sys.exit(f"{arquivo} não é um arquivo de lances do Registro")
    if fim is None:
        if dados.get("duracao_video"):
            fim = float(dados["duracao_video"])
        else:
            segs = [float(e["seg"]) for e in dados["eventos"] if e.get("seg") is not None]
            fim = (max(segs) if segs else 0) + 30
            print(f"  ! o arquivo não traz a duração do vídeo: o placar fixo vai até {mmss(fim)}"
                  " (30 s depois do último lance). Use --fim para mudar.")

    gols, pecas = planeja(dados, inicio, fim)
    print(f"{dados.get('nome') or dados['jogo']}: {dados['casa']['nome']} × {dados['fora']['nome']}")
    for n, g in enumerate(gols, 1):
        lado = dados["casa"]["nome"] if g["t"] == "A" else dados["fora"]["nome"]
        print(f"  gol {n:2d}  {mmss(float(g['seg'])):>6}  {lado:<14} {g.get('j') or '(sem jogador)':<14}"
              f"  {g['placar_depois'][0]} × {g['placar_depois'][1]}")

    pasta = os.path.join(MIDIAS, dados["jogo"])
    os.makedirs(pasta, exist_ok=True)
    # pasta gerada: o que sobrou de uma rodada anterior sairia no manifesto errado
    for velho in glob.glob(os.path.join(pasta, "*.mov")) + glob.glob(os.path.join(pasta, "*.png")):
        os.remove(velho)

    feitas, puladas = [], []
    srv = servidor()
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = abre_estudio(nav, srv.server_address[1])
            for peca in pecas:
                destino = os.path.join(pasta, peca["arquivo"])
                if peca["peca"] == "placar-fixo":
                    if os.path.exists(destino):         # mesmo placar já desenhado
                        feitas.append(peca)
                        continue
                    erro = prepara(pg, js_placar(dados, peca, 1), 1)
                    if erro:
                        sys.exit(erro)
                    open(destino, "wb").write(quadro_png(pg, None))
                elif peca["peca"] == "placar":
                    erro = prepara(pg, js_placar(dados, peca, peca["duracao"] / FPS), peca["duracao"] / FPS)
                    if erro:
                        sys.exit(erro)
                    grava_mov(pg, peca["duracao"] / FPS, destino)
                else:
                    if not peca["jogador"]:
                        puladas.append((peca, "o gol foi marcado sem jogador"))
                        continue
                    erro = prepara(pg, js_gol(dados, peca), peca["duracao"] / FPS)
                    if erro:
                        puladas.append((peca, erro))
                        continue
                    grava_mov(pg, peca["duracao"] / FPS, destino)
                feitas.append(peca)
                print(f"  ok  {peca['arquivo']}")
            nav.close()
    finally:
        srv.shutdown()

    manifesto = os.path.join(pasta, "manifesto.tsv")
    with open(manifesto, "w", encoding="utf-8", newline="\n") as f:
        f.write("lance\tpeca\tarquivo\ttipo\tquadro\tduracao\ttrilha\ttimecode\tseg_video\n")
        for p in sorted(feitas, key=lambda x: (x["trilha"], x["quadro"])):
            f.write(f"{p['lance']}\t{p['peca']}\t{p['arquivo']}\t{p['tipo']}\t{p['quadro']}\t"
                    f"{p['duracao']}\t{p['trilha']}\t{timecode(p['quadro'])}\t"
                    f"{p['quadro'] / FPS:.2f}\n")
    # é por aqui que o script do DaVinci acha o pacote mais recente
    open(os.path.join(MIDIAS, "ultimo-pacote.txt"), "w", encoding="utf-8").write(pasta)

    print(f"\n{pasta}\n  {len(feitas)} peças no manifesto")
    for peca, motivo in puladas:
        print(f"  ! sem {peca['peca']} no {peca['lance']} ({mmss(peca['seg'])}): {motivo}")


def teste():
    """Clipe de 2 s da barra de gol, para conferir a transparência no DaVinci."""
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(FFMPEG):
        sys.exit("falta o ffmpeg em ferramentas/ffmpeg — ver docs/pacote-de-midias.md")
    saida = os.path.join(MIDIAS, "teste", "teste-gol-barra.mov")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    srv = servidor()
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = abre_estudio(nav, srv.server_address[1])
            prepara(pg, "F => { F.tipo.value = 'gol'; F.min.value = \"11'\"; return ''; }", 2)
            n = grava_mov(pg, 2, saida)
            nav.close()
    finally:
        srv.shutdown()
    print(f"{saida}\n  {n} quadros a {FPS} fps · ProRes 4444 com transparência")


def opcao(nome, padrao=None):
    if nome in sys.argv:
        return float(sys.argv[sys.argv.index(nome) + 1])
    return padrao


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "teste":
        teste()
    elif acao == "gerar" and len(sys.argv) > 2:
        gerar(sys.argv[2], inicio=opcao("--inicio", 0.0), fim=opcao("--fim"))
    else:
        sys.exit(__doc__)
