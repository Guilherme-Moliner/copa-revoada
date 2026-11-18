#!/usr/bin/env python3
"""
Copa Revoada — pacote de mídias.

Lê o arquivo de lances baixado do Registro ("Baixar lances") e gera, numa
pasta só daquele jogo, todas as peças com transparência de verdade (ProRes
4444 em .mov, e PNG para o placar parado) e o manifesto.tsv que o script do
DaVinci lê para posicionar cada uma na timeline.

    .venv\\Scripts\\python.exe scripts\\pacote.py gerar caminho\\lances-<jogo>.json
    .venv\\Scripts\\python.exe scripts\\pacote.py gerar        (pega o mais novo em Downloads)
    .venv\\Scripts\\python.exe scripts\\pacote.py teste

Lances que não vieram do Registro:

    .venv\\Scripts\\python.exe scripts\\pacote.py da-sumula 2026-08
        converte a súmula minuto a minuto em arquivo de lances
    .venv\\Scripts\\python.exe scripts\\pacote.py bateria 2026-08 --video jogo.mp4
        lances DE TESTE com todas as peças, no começo, meio e fim do vídeo

Opções do gerar:
    --video ARQ    lê a duração do vídeo do próprio arquivo (vale como --fim)
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

# O que cada lance vira, em que trilha, quando entra e quanto dura: tudo em
# dados/regras-pacote.json. É o mesmo arquivo que o Registro mostra ao lado de
# cada lance, para o que se vê na marcação ser o que sai no vídeo.
REGRAS = os.path.join(RAIZ, "dados", "regras-pacote.json")

# Abaixo disto ficam as câmeras: nenhuma peça pode cair ali, mesmo que o
# arquivo de regras diga outra coisa. O script do DaVinci confere de novo.
MENOR_TRILHA_GRAFICA = 4


def carrega_regras():
    """Lê as regras e traduz camada gráfica em trilha do DaVinci.

    Quem edita as regras pensa em camadas (1 = placar, 2 = GOL tela cheia…);
    a trilha é conta: camada 1 = primeira_trilha. Essa conta mora só aqui, e
    o resto do gerador trabalha com a trilha já calculada."""
    regras = json.load(open(REGRAS, encoding="utf-8"))
    cam = regras.get("camadas", {})
    primeira = int(cam.get("primeira_trilha", MENOR_TRILHA_GRAFICA))
    if primeira < MENOR_TRILHA_GRAFICA:
        sys.exit(f"regras-pacote.json: primeira_trilha = {primeira}, mas as trilhas abaixo da "
                 f"V{MENOR_TRILHA_GRAFICA} são das câmeras")
    nomes = {int(k): v for k, v in cam.get("nomes", {}).items()}
    todas = [r for lista in regras["lances"].values() for r in lista] + regras.get("jogo", [])
    for r in todas:
        if "camada" not in r:
            sys.exit(f"regras-pacote.json: a peça {r.get('peca')} está sem camada")
        r["trilha"] = primeira + int(r["camada"]) - 1
    regras["_primeira_trilha"] = primeira
    regras["_nomes"] = nomes
    return regras


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


# Peça que chega com a trilha ocupada espera a anterior sair. Esperar mais do
# que isto já não faz sentido: o lance passou, e a peça fica de fora.
ESPERA_MAXIMA = 8.0


class Trilhas:
    """Quem ocupa cada trilha. Peças da mesma trilha aparecem no mesmo lugar
    da tela, então duas ao mesmo tempo ficariam uma por cima da outra — subir
    a segunda para outra trilha não resolve isso. Ela entra em fila: começa
    quando a anterior termina."""

    def __init__(self):
        self.ocupado = {}

    def reserva(self, trilha, quadro, dur):
        self.ocupado.setdefault(trilha, []).append((quadro, quadro + dur))

    def encaixa(self, trilha, quadro, dur):
        """Devolve o quadro em que a peça entra, ou None se a espera passar
        do limite."""
        pedido = quadro
        mexeu = True
        while mexeu:
            mexeu = False
            for i, f in self.ocupado.get(trilha, []):
                if quadro < f and quadro + dur > i:
                    quadro, mexeu = f, True
        if quadro - pedido > ESPERA_MAXIMA * FPS:
            return None
        self.reserva(trilha, quadro, dur)
        return quadro


def planeja(dados, regras, inicio, fim):
    """Transforma os lances em peças: cada uma com arquivo, trilha, quadro de
    entrada e duração em quadros. O placar é calculado gol a gol, na ordem do
    tempo do vídeo."""
    avisos = []
    lances = [e for e in dados["eventos"] if regras["lances"].get(e.get("tipo"))]
    sem_tempo = [e for e in lances if e.get("seg") is None]
    if any(e["tipo"] == "gol" for e in sem_tempo):
        sys.exit("Há gol sem o tempo do vídeo. Sem ele não há onde pôr a peça, e o placar "
                 "sairia errado: marque de novo com o vídeo carregado no Registro.")
    if sem_tempo:
        avisos.append(f"{len(sem_tempo)} lance(s) sem o tempo do vídeo ficaram de fora")
    lances = sorted((e for e in lances if e.get("seg") is not None), key=lambda e: float(e["seg"]))

    do_jogo = {r["peca"]: r for r in regras.get("jogo", [])}
    fixo = do_jogo.get("placar-fixo")
    trilhas = Trilhas()
    if fixo:      # a trilha do placar é dele o jogo inteiro
        trilhas.reserva(fixo["trilha"], round(inicio * FPS), round((fim - inicio) * FPS))

    pecas, gols = [], []
    gc = gf = 0
    q_cursor = round(inicio * FPS)
    q_fim = round(fim * FPS)

    # abertura, artilheiro e fim têm hora marcada: reservam o lugar antes, e os
    # lances é que esperam por eles
    lugar = {}
    for nome in ("abertura", "artilheiro", "fim"):
        r = do_jogo.get(nome)
        if not r:
            continue
        dur = round(r["dura"] * FPS)
        if "antes_do_fim" in r:
            quadro = round((fim - r["antes_do_fim"]) * FPS)
        else:
            quadro = round((inicio + r.get("entra", 0)) * FPS)
        if quadro < round(inicio * FPS) or quadro + dur > q_fim:
            avisos.append(f"sem {nome}: não cabe entre {mmss(inicio)} e {mmss(fim)}")
            continue
        trilhas.reserva(r["trilha"], quadro, dur)
        lugar[nome] = (r["trilha"], quadro, dur)
    conta = {}
    for e in lances:
        seg = float(e["seg"])
        conta[e["tipo"]] = conta.get(e["tipo"], 0) + 1
        lance = f"{e['tipo'].lower()}-{conta[e['tipo']]:02d}"
        eh_gol = e["tipo"] == "gol"
        if eh_gol:
            if e["t"] == "A":
                gc += 1
            else:
                gf += 1
            e["placar_depois"] = (gc, gf)
            gols.append(e)
        for r in regras["lances"][e["tipo"]]:
            dur = round(r["dura"] * FPS)
            quadro = round((seg + r.get("entra", 0)) * FPS)
            if r["peca"] == "placar":
                if not eh_gol:
                    continue
                if quadro < q_cursor:
                    avisos.append(f"{lance} aos {mmss(seg)} veio colado no gol anterior: a animação "
                                  f"do placar começa {(q_cursor - quadro) / FPS:.1f} s depois")
                    quadro = q_cursor
                antes = (gc - (e["t"] == "A"), gf - (e["t"] != "A"))
                if fixo and quadro > q_cursor:
                    pecas.append(dict(lance=f"placar-{antes[0]}x{antes[1]}", peca="placar-fixo",
                                      arquivo=f"placar-fixo-{antes[0]}x{antes[1]}.png", tipo="imagem",
                                      quadro=q_cursor, duracao=quadro - q_cursor,
                                      trilha=fixo["trilha"], gc=antes[0], gf=antes[1]))
                pecas.append(dict(lance=lance, peca="placar", arquivo=f"{lance}-placar.mov",
                                  tipo="video", quadro=quadro, duracao=dur,
                                  trilha=fixo["trilha"] if fixo else r["trilha"],
                                  gc=gc, gf=gf, seg=seg,
                                  evento="golCasa" if e["t"] == "A" else "golFora"))
                q_cursor = quadro + dur
                continue
            titulo = r.get("titulo", "")
            if dados.get("conta_na_copa", True) and r.get("titulo_copa"):
                titulo = r["titulo_copa"]
            if not e.get("j"):
                avisos.append(f"sem {r['peca']} no {lance} ({mmss(seg)}): o lance foi marcado sem jogador")
                continue
            entra = trilhas.encaixa(r["trilha"], quadro, dur)
            if entra is None:
                avisos.append(f"sem {r['peca']} no {lance} ({mmss(seg)}): a tela ainda estava ocupada "
                              f"por outra peça {ESPERA_MAXIMA:.0f} s depois")
                continue
            if entra != quadro:
                avisos.append(f"{r['peca']} do {lance} ({mmss(seg)}) entra {(entra - quadro) / FPS:.1f} s "
                              "depois, esperando a peça anterior sair")
            pecas.append(dict(lance=lance, peca=r["peca"], arquivo=f"{lance}-{r['peca']}.mov",
                              tipo="video", quadro=entra, duracao=dur, trilha=r["trilha"],
                              jogador=e["j"], lado=e["t"], minuto=e.get("min"),
                              seg=seg, titulo=titulo))

    if fixo and q_fim > q_cursor:
        pecas.append(dict(lance=f"placar-{gc}x{gf}", peca="placar-fixo",
                          arquivo=f"placar-fixo-{gc}x{gf}.png", tipo="imagem",
                          quadro=q_cursor, duracao=q_fim - q_cursor,
                          trilha=fixo["trilha"], gc=gc, gf=gf))

    # ---- peças do jogo, nos lugares reservados lá em cima
    if "abertura" in lugar:
        t, q, dur = lugar["abertura"]
        pecas.append(dict(lance="jogo", peca="abertura", arquivo="jogo-abertura.mov", tipo="video",
                          quadro=q, duracao=dur, trilha=t))
    if "fim" in lugar:
        t, q, dur = lugar["fim"]
        pecas.append(dict(lance="jogo", peca="fim", arquivo="jogo-fim.mov", tipo="video",
                          quadro=q, duracao=dur, trilha=t, gc=gc, gf=gf))
    if "artilheiro" in lugar and gols:
        # Artilheiro só sai quando é fato: todo gol com jogador, e um só na frente.
        # Empate ou gol sem dono não se decide aqui.
        if any(not g.get("j") for g in gols):
            avisos.append("sem artilheiro do dia: há gol marcado sem jogador")
        else:
            soma = {}
            for g in gols:
                soma[(g["j"], g["t"])] = soma.get((g["j"], g["t"]), 0) + 1
            topo = max(soma.values())
            lideres = [k for k, v in soma.items() if v == topo]
            if len(lideres) > 1:
                avisos.append("sem artilheiro do dia: empate entre "
                              + ", ".join(k[0] for k in lideres) + f" ({topo} cada)")
            else:
                t, q, dur = lugar["artilheiro"]
                pecas.append(dict(lance="jogo", peca="artilheiro", arquivo="jogo-artilheiro.mov",
                                  tipo="video", quadro=q, duracao=dur, trilha=t,
                                  jogador=lideres[0][0], lado=lideres[0][1], gols=topo))
    return gols, pecas, avisos


def competicao(dados):
    if dados.get("conta_na_copa", True):
        return "COPA REVOADA"
    return (dados.get("nome") or dados["jogo"]).upper()


def time_de(dados, lado):
    return dados["casa"]["id"] if lado == "A" else dados["fora"]["id"]


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


def js_jogador(dados, p, arte):
    """Peças com um jogador: barra, GOL em tela cheia, artilheiro do dia."""
    time = time_de(dados, p["lado"])
    minuto = "" if p.get("minuto") is None else f"{p['minuto']}'"
    return f"""F => {{
        const quem = jog.find(x=>x.apelido === {json.dumps(p['jogador'])});
        if(!quem) return 'jogador ' + {json.dumps(p['jogador'])} + ' não está no site';
        if(!tById[{json.dumps(time)}]) return 'time desconhecido no site: ' + {json.dumps(time)};
        F.tipo.value = {json.dumps(arte)};
        F.p1.value = quem.id;
        F.time.value = {json.dumps(time)};
        F.min.value = {json.dumps(minuto)};
        TITULO_GOL = {json.dumps(p.get('titulo') or 'GOL')};
        GOLS_DO_DIA = {json.dumps(p.get('gols'))};
        return '';
    }}"""


def js_cartao_do_jogo(dados, p):
    """Abertura (os dois escudos) e fim de jogo (com o placar final)."""
    return f"""F => {{
        const casa = {json.dumps(dados['casa']['id'])}, fora = {json.dumps(dados['fora']['id'])};
        if(!tById[casa] || !tById[fora]) return 'time desconhecido no site: '+casa+' ou '+fora;
        F.tipo.value = {json.dumps('fim' if p['peca'] == 'fim' else 'placar')};
        F.time.value = casa; F.time2.value = fora;
        F.ga.value = {p.get('gc', 0)}; F.gb.value = {p.get('gf', 0)};
        F.min.value = '';
        TITULO_PLACAR = {json.dumps(competicao(dados))};
        return '';
    }}"""


ARTE_DA_PECA = {"barra": "gol", "golaco": "golaco", "artilheiro": "artilheiro"}


def mais_recente_nos_downloads():
    pasta = os.path.join(os.path.expanduser("~"), "Downloads")
    achados = glob.glob(os.path.join(pasta, "lances-*.json"))
    if not achados:
        sys.exit(f"Não achei nenhum lances-*.json em {pasta}.\n"
                 "No Registro, clique em Baixar lances — ou arraste o arquivo para cima do "
                 "\"Gerar pacote de midias.bat\".")
    return max(achados, key=os.path.getmtime)


def garante_site():
    """As peças são desenhadas pelo index.html. Se o template, as regras ou o
    build mudaram depois dele, refaz — lendo a planilha, quando o gh deixa."""
    site = os.path.join(RAIZ, "index.html")
    fontes = [os.path.join(RAIZ, "src", "app.template.html"), REGRAS,
              os.path.join(RAIZ, "scripts", "build.py")]
    if os.path.isfile(site) and all(os.path.getmtime(site) >= os.path.getmtime(f) for f in fontes):
        return
    print("o site local está desatualizado: refazendo…")
    amb = dict(os.environ, PYTHONIOENCODING="utf-8")
    for var in ("PLANILHA_URL", "LANCES_URL"):
        if amb.get(var):
            continue
        for gh in ("gh", r"C:\Program Files\GitHub CLI\gh.exe"):
            try:
                r = subprocess.run([gh, "variable", "get", var, "-R", "Guilherme-Moliner/copa-revoada"],
                                   capture_output=True, text=True, timeout=30)
                if r.returncode == 0 and r.stdout.strip():
                    amb[var] = r.stdout.strip()
                    break
            except (OSError, subprocess.TimeoutExpired):
                pass
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "build.py")],
                       env=amb, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit("o build do site falhou:\n" + (r.stdout + r.stderr)[-1500:])
    origem = [l.strip() for l in r.stdout.splitlines() if "planilha" in l.lower()]
    print("  " + (origem[0] if origem else "site refeito"))
    if not amb.get("PLANILHA_URL"):
        print("  ! sem acesso à planilha online (gh): usei a cópia do repositório, que pode "
              "estar sem jogador novo")


def duracao_do_video(caminho):
    """Duração em segundos, lida pelo ffprobe que veio com o ffmpeg."""
    probe = os.path.join(os.path.dirname(FFMPEG), "ffprobe.exe")
    r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", caminho], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit(f"não consegui ler a duração de {caminho}: {r.stderr.strip()[:200]}")


def gerar(arquivo=None, inicio=0.0, fim=None):
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(FFMPEG):
        sys.exit("falta o ffmpeg em ferramentas/ffmpeg — ver docs/pacote-de-midias.md")
    if not arquivo:
        arquivo = mais_recente_nos_downloads()
    print(f"lances: {arquivo}")
    dados = json.load(open(arquivo, encoding="utf-8"))
    if dados.get("formato") != "copa-revoada-lances/1":
        sys.exit(f"{arquivo} não é um arquivo de lances do Registro")
    regras = carrega_regras()
    garante_site()
    if fim is None:
        if dados.get("duracao_video"):
            fim = float(dados["duracao_video"])
        else:
            segs = [float(e["seg"]) for e in dados["eventos"] if e.get("seg") is not None]
            fim = (max(segs) if segs else 0) + 30
            print(f"  ! o arquivo não traz a duração do vídeo: o jogo vai até {mmss(fim)}"
                  " (30 s depois do último lance). Use --fim para mudar.")

    gols, pecas, avisos = planeja(dados, regras, inicio, fim)
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
            for n, peca in enumerate(pecas, 1):
                destino = os.path.join(pasta, peca["arquivo"])
                seg_dur = peca["duracao"] / FPS
                if peca["peca"] == "placar-fixo":
                    if not os.path.exists(destino):     # mesmo placar já desenhado
                        erro = prepara(pg, js_placar(dados, peca, 1), 1)
                        if erro:
                            sys.exit(erro)
                        open(destino, "wb").write(quadro_png(pg, None))
                    feitas.append(peca)
                    continue
                if peca["peca"] == "placar":
                    js = js_placar(dados, peca, seg_dur)
                elif peca["peca"] in ("abertura", "fim"):
                    js = js_cartao_do_jogo(dados, peca)
                else:
                    js = js_jogador(dados, peca, ARTE_DA_PECA[peca["peca"]])
                erro = prepara(pg, js, seg_dur)
                if erro:
                    if peca["peca"] in ("placar", "abertura", "fim"):
                        sys.exit(erro)
                    puladas.append((peca, erro))
                    continue
                grava_mov(pg, seg_dur, destino)
                feitas.append(peca)
                print(f"  {n:3d}/{len(pecas)}  {peca['arquivo']}")
            nav.close()
    finally:
        srv.shutdown()

    manifesto = os.path.join(pasta, "manifesto.tsv")
    primeira, nomes = regras["_primeira_trilha"], regras["_nomes"]
    with open(manifesto, "w", encoding="utf-8", newline="\n") as f:
        f.write("lance\tpeca\tarquivo\ttipo\tquadro\tduracao\ttrilha\tcamada\tcamada_nome"
                "\ttimecode\tseg_video\n")
        for p in sorted(feitas, key=lambda x: (x["trilha"], x["quadro"])):
            camada = p["trilha"] - primeira + 1
            f.write(f"{p['lance']}\t{p['peca']}\t{p['arquivo']}\t{p['tipo']}\t{p['quadro']}\t"
                    f"{p['duracao']}\t{p['trilha']}\t{camada}\t{nomes.get(camada, '')}\t"
                    f"{timecode(p['quadro'])}\t{p['quadro'] / FPS:.2f}\n")
    # é por aqui que o script do DaVinci acha o pacote mais recente
    open(os.path.join(MIDIAS, "ultimo-pacote.txt"), "w", encoding="utf-8").write(pasta)

    por_trilha = {}
    for p in feitas:
        por_trilha[p["trilha"]] = por_trilha.get(p["trilha"], 0) + 1
    print(f"\n{pasta}\n  {len(feitas)} peças no manifesto")
    for t, n in sorted(por_trilha.items()):
        c = t - primeira + 1
        print(f"    camada {c} ({nomes.get(c, '?')}) = V{t}: {n} peça(s)")
    for peca, motivo in puladas:
        quando = f" ({mmss(peca['seg'])})" if peca.get("seg") is not None else ""
        print(f"  ! sem {peca['peca']} no {peca['lance']}{quando}: {motivo}")
    for a in avisos:
        print(f"  ! {a}")
    print("\nNo DaVinci: Workspace > Scripts > Copa Revoada - importar pacote")
    return pasta


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


# --------------------------------------------------------------------------
# lances que não vieram do Registro


def dados_do_site():
    """O DADOS que o build gravou dentro do index.html: jogadores, times,
    jogos e as súmulas já ligadas aos ids da planilha."""
    garante_site()
    for linha in open(os.path.join(RAIZ, "index.html"), encoding="utf-8"):
        if linha.startswith("const DADOS="):
            return json.loads(linha[len("const DADOS="):].rstrip().rstrip(";"))
    sys.exit("o index.html não tem o bloco de dados: rode o build")


def _time(dados_site, tid):
    t = next((x for x in dados_site["times"] + dados_site.get("mistos", []) if x["id"] == tid), None)
    if not t:
        sys.exit(f"o time {tid} não existe no site")
    return {"id": tid, "nome": t["nome"], "sigla": t.get("sigla", ""),
            "c1": t.get("c1", ""), "c2": t.get("c2", "")}


def _salva_lances(nome_arquivo, pacote):
    destino = os.path.join(MIDIAS, "lances", nome_arquivo)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    json.dump(pacote, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return destino


def da_sumula(jogo):
    """Converte a súmula minuto a minuto (dados/sumulas/) num arquivo de lances
    igual ao que o Registro baixa. Nada é inventado: cada lance sai de uma
    linha da súmula, com o tempo dela. Defesa comum de goleiro NÃO vira
    "defesaça" — a súmula não diz qual defesa foi difícil, e isso é escolha
    de quem edita."""
    D = dados_do_site()
    sumula = D.get("sumulas", {}).get(jogo)
    if not sumula:
        sys.exit(f"não há súmula do jogo {jogo} em dados/sumulas/")
    g = next((x for x in D["jogos"] + D.get("amistosos", []) if x["id"] == jogo), None)
    if not g:
        sys.exit(f"o jogo {jogo} não está na aba JOGOS")
    apelido = {x["id"]: x["apelido"] for x in D["jogadores"]}
    lado = {g["casa"]: "A", g["fora"]: "B"}

    eventos, fora_da_conta = [], {}
    for e in sumula["eventos"]:
        tipo = None
        if e["tipo"] == "chute":
            tipo = "gol" if e.get("gol") else ("noGol" if e.get("sub") == "defendido" else "fora")
        elif e["tipo"] in ("falta", "cagada"):
            tipo = e["tipo"]
        elif e["tipo"] == "escanteio":
            tipo = "escant"
        if not tipo:
            fora_da_conta[e["tipo"]] = fora_da_conta.get(e["tipo"], 0) + 1
            continue
        t = lado.get(e.get("time"))
        if not t:
            fora_da_conta["sem time"] = fora_da_conta.get("sem time", 0) + 1
            continue
        j = apelido.get(e.get("j"), "") if e.get("j") else ""
        eventos.append({"seg": e["t"], "min": e["t"] // 60, "t": t, "tipo": tipo, "j": j, "xg": 0,
                        "origem": e.get("txt", "")})
    gols = [e for e in eventos if e["tipo"] == "gol"]
    gc = sum(1 for e in gols if e["t"] == "A")
    gf = len(gols) - gc
    if (gc, gf) != (g.get("gc"), g.get("gf")):
        print(f"  ! os gols da súmula somam {gc} × {gf}, e a aba JOGOS diz {g.get('gc')} × {g.get('gf')}")

    destino = _salva_lances(f"lances-{jogo}-sumula.json", {
        "formato": "copa-revoada-lances/1", "jogo": jogo,
        "nome": f"{g.get('mes', '')} {g.get('temporada', '')}".strip() or jogo,
        "conta_na_copa": True,
        "casa": _time(D, g["casa"]), "fora": _time(D, g["fora"]),
        "video": f"https://youtu.be/{g['video']}" if g.get("video") else "",
        "duracao_video": None,
        "exportado_em": f"convertido da súmula dados/sumulas/{jogo}-lances.csv",
        "eventos": eventos,
    })
    por_tipo = {}
    for e in eventos:
        por_tipo[e["tipo"]] = por_tipo.get(e["tipo"], 0) + 1
    print(f"{destino}\n  {len(eventos)} lances: "
          + ", ".join(f"{n} {k}" for k, n in sorted(por_tipo.items())))
    for e in gols:
        print(f"  gol {mmss(e['seg']):>6}  {e['j'] or '(sem jogador)':<12} {e['origem']}")
    if fora_da_conta:
        print("  fora do arquivo: " + ", ".join(f"{n} {k}" for k, n in fora_da_conta.items())
              + " (defesa comum não vira defesaça)")
    return destino


def bateria(jogo, fim):
    """Lances DE TESTE, para ver todas as peças no DaVinci de uma vez: o mesmo
    bloco no começo, no meio e no fim do vídeo, com lances colados para
    exercitar a fila. Não é o que aconteceu no jogo — o arquivo e o placar
    dizem BATERIA DE TESTE, e ele não conta para a copa."""
    D = dados_do_site()
    sumula = D.get("sumulas", {}).get(jogo) or {}
    g = next((x for x in D["jogos"] + D.get("amistosos", []) if x["id"] == jogo), None)
    if not g:
        sys.exit(f"o jogo {jogo} não está na aba JOGOS")
    apelido = {x["id"]: x["apelido"] for x in D["jogadores"]}
    goleiros = set((sumula.get("goleiros") or {}).values())
    elenco = {"A": [], "B": []}
    for x in sumula.get("elenco", []):
        lado = "A" if x.get("time") == g["casa"] else "B" if x.get("time") == g["fora"] else None
        if lado and x.get("pid") in apelido:
            elenco[lado].append((apelido[x["pid"]], x["pid"] in goleiros))
    if not elenco["A"] or not elenco["B"]:
        sys.exit(f"não achei o elenco dos dois times na súmula de {jogo}")
    linha = lambda l, i: [n for n, gk in elenco[l] if not gk][i % max(1, len([1 for _, gk in elenco[l] if not gk]))]
    goleiro = lambda l: next((n for n, gk in elenco[l] if gk), elenco[l][0][0])

    def bloco(t0, k):
        E = lambda dt, t, tipo, j: {"seg": t0 + dt, "min": int((t0 + dt) // 60), "t": t,
                                    "tipo": tipo, "j": j, "xg": 0}
        return [E(0, "A", "gol", linha("A", k)),
                E(2, "B", "cagada", linha("B", k)),
                E(3, "A", "cartao", linha("A", k + 1)),
                E(6, "B", "defesa", goleiro("B")),
                E(25, "B", "gol", linha("B", k + 1)),
                E(27, "A", "gol", linha("A", k))]          # colado: testa a fila do placar

    eventos = bloco(60, 0) + bloco(fim / 2, 1) + bloco(fim - 75, 2)
    destino = _salva_lances(f"lances-{jogo}-bateria.json", {
        "formato": "copa-revoada-lances/1", "jogo": f"{jogo}-bateria",
        "nome": "Bateria de teste", "conta_na_copa": False,
        "casa": _time(D, g["casa"]), "fora": _time(D, g["fora"]),
        "video": f"https://youtu.be/{g['video']}" if g.get("video") else "",
        "duracao_video": fim,
        "exportado_em": "lances de teste gerados por scripts/pacote.py bateria — não são do jogo",
        "eventos": eventos,
    })
    print(f"{destino}\n  {len(eventos)} lances de teste em 3 blocos: "
          f"{mmss(60)}, {mmss(fim / 2)} e {mmss(fim - 75)}")
    return destino


def opcao(nome, padrao=None):
    if nome in sys.argv:
        return float(sys.argv[sys.argv.index(nome) + 1])
    return padrao


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "teste":
        teste()
    elif acao == "gerar":
        arq = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        fim = opcao("--fim")
        if "--video" in sys.argv:
            fim = duracao_do_video(sys.argv[sys.argv.index("--video") + 1])
            print(f"duração do vídeo: {mmss(fim)}")
        gerar(arq, inicio=opcao("--inicio", 0.0), fim=fim)
    elif acao == "da-sumula" and len(sys.argv) > 2:
        da_sumula(sys.argv[2])
    elif acao == "bateria" and len(sys.argv) > 2:
        if "--video" in sys.argv:
            fim = duracao_do_video(sys.argv[sys.argv.index("--video") + 1])
        else:
            fim = opcao("--fim")
        if not fim:
            sys.exit("diga a duração: --video arquivo.mp4  ou  --fim segundos")
        bateria(sys.argv[2], fim)
    else:
        sys.exit(__doc__)
