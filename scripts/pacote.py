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

Manutenção:

    .venv\\Scripts\\python.exe scripts\\pacote.py mede-artes
        mede a área que cada arte do Estúdio ocupa (dados/areas-artes.json)

Opções do gerar:
    --video ARQ    lê a duração do vídeo do próprio arquivo (vale como --fim)
    --inicio SEG   onde o placar fixo começa, em segundos do vídeo (padrão 0)
    --fim SEG      onde termina (padrão: a duração do vídeo, se o arquivo
                   trouxer; senão, 30 s depois do último lance)

QUEM DECIDE O QUÊ: o plano da edição (que peça entra, quando, quanto dura, em
que camada, quem espera na fila e quem fica de fora) é calculado pelo próprio
site, em PACOTE.planeja — a mesma função que desenha o plano no Registro. Este
script só abre o site num Chromium sem janela, pede o plano, e desenha cada
peça com o código do Estúdio, quadro a quadro. Assim o que se vê no Registro é
exatamente o que sai no DaVinci.

Precisa de ferramentas/ffmpeg e do Chromium do Playwright em
ferramentas/ms-playwright (ver docs/pacote-de-midias.md).
"""

import base64
import functools
import glob
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTAS = os.path.join(RAIZ, "ferramentas")
FFMPEG = os.path.join(FERRAMENTAS, "ffmpeg", "ffmpeg.exe")
MIDIAS = os.path.join(RAIZ, "midias")
REGRAS = os.path.join(RAIZ, "dados", "regras-pacote.json")
AREAS = os.path.join(RAIZ, "dados", "areas-artes.json")

# O Playwright baixaria o navegador para a pasta do usuário; com esta variável
# ele procura dentro do projeto, onde foi instalado.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(FERRAMENTAS, "ms-playwright"))

# A timeline do DaVinci é 24 fps, e a peça tem que ter o mesmo fps: quadro de
# arte e quadro de vídeo andam juntos, sem o Resolve reamostrar nada.
FPS = 24

# Abaixo disto ficam as câmeras: nenhuma peça pode cair ali, mesmo que o
# arquivo de regras diga outra coisa. O script do DaVinci confere de novo.
MENOR_TRILHA_GRAFICA = 4

FORMATOS = ("copa-revoada-lances/1", "copa-revoada-lances/2")


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


def prepara(pg, peca, lances):
    """Deixa o Estúdio pronto para desenhar a peça (PACOTE.prepara, no site) e
    espera as fotos. Devolve '' ou o motivo de não dar."""
    return pg.evaluate("""async a => {
        const erro = PACOTE.prepara(a.p, a.L);
        if(erro) return erro;
        syncFields();
        F.dur.value = a.p.dura;
        // fotos chegam depois do primeiro desenho; espera todas
        await Promise.all([...document.images].filter(i=>!i.complete)
          .map(i=>new Promise(r=>{ i.onload=i.onerror=r; })));
        await new Promise(r=>setTimeout(r,150));
        return '';
    }""", {"p": peca, "L": lances})


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


def grava_mov(pg, quadros, saida):
    """Desenha a peça quadro a quadro e entrega ao ffmpeg. Cada quadro é
    desenhado no seu instante exato da animação (i/(total-1))."""
    total = max(2, int(quadros))
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
    seg = int(round(float(seg)))
    h, m, s = seg // 3600, seg % 3600 // 60, seg % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def mais_recente_nos_downloads():
    pasta = os.path.join(os.path.expanduser("~"), "Downloads")
    achados = glob.glob(os.path.join(pasta, "lances-*.json"))
    if not achados:
        sys.exit(f"Não achei nenhum lances-*.json em {pasta}.\n"
                 "No Registro, clique em Baixar lances — ou arraste o arquivo para cima do "
                 "\"Gerar pacote de midias.bat\".")
    return max(achados, key=os.path.getmtime)


def garante_site():
    """As peças e o plano saem do index.html. Se o template, as regras, as
    áreas ou o build mudaram depois dele, refaz — lendo a planilha, quando o
    gh deixa."""
    site = os.path.join(RAIZ, "index.html")
    fontes = [os.path.join(RAIZ, "src", "app.template.html"), REGRAS, AREAS,
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


# --------------------------------------------------------------------------
# gerar


def gerar(arquivo=None, inicio=0.0, fim=None):
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(FFMPEG):
        sys.exit("falta o ffmpeg em ferramentas/ffmpeg — ver docs/pacote-de-midias.md")
    if not arquivo:
        arquivo = mais_recente_nos_downloads()
    print(f"lances: {arquivo}")
    lances = json.load(open(arquivo, encoding="utf-8"))
    if lances.get("formato") not in FORMATOS:
        sys.exit(f"{arquivo} não é um arquivo de lances do Registro")
    garante_site()
    comeco = time.time()

    srv = servidor()
    try:
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = abre_estudio(nav, srv.server_address[1])
            plano = pg.evaluate("a => PACOTE.planeja(a.L, a.op)",
                                {"L": lances, "op": {"inicio": inicio, "fim": fim}})
            if plano["camadas"]["primeira"] < MENOR_TRILHA_GRAFICA:
                sys.exit(f"regras-pacote.json: primeira_trilha = {plano['camadas']['primeira']}, mas as "
                         f"trilhas abaixo da V{MENOR_TRILHA_GRAFICA} são das câmeras")
            mostra_cabecalho(lances, plano)

            pasta = os.path.join(MIDIAS, lances["jogo"])
            os.makedirs(pasta, exist_ok=True)
            # pasta gerada: o que sobrou de uma rodada anterior sairia no manifesto errado
            for velho in glob.glob(os.path.join(pasta, "*.mov")) + glob.glob(os.path.join(pasta, "*.png")):
                os.remove(velho)

            vivas = [p for p in plano["pecas"] if p["status"] != "fora"]
            feitas, falhas = [], []
            for n, p in enumerate(vivas, 1):
                destino = os.path.join(pasta, p["arquivo"])
                if p["peca"] == "placar-fixo" and os.path.exists(destino):
                    feitas.append(p)          # mesmo placar parado, já desenhado
                    continue
                erro = prepara(pg, p, lances)
                if erro:
                    falhas.append((p, erro))
                    continue
                if p["peca"] == "placar-fixo":
                    open(destino, "wb").write(quadro_png(pg, None))
                else:
                    grava_mov(pg, p["duracao"], destino)
                feitas.append(p)
                print(f"  {n:3d}/{len(vivas)}  {p['arquivo']}")
            nav.close()
    finally:
        srv.shutdown()

    escreve_manifesto(pasta, feitas)
    # é por aqui que o script do DaVinci acha o pacote mais recente
    open(os.path.join(MIDIAS, "ultimo-pacote.txt"), "w", encoding="utf-8").write(pasta)
    mostra_resumo(pasta, plano, feitas, falhas, time.time() - comeco)
    return pasta


def mostra_cabecalho(lances, plano):
    casa, fora = lances["casa"]["nome"], lances["fora"]["nome"]
    print(f"{lances.get('nome') or lances['jogo']}: {casa} × {fora} · até {mmss(plano['fim'])}")
    gc = gf = 0
    for n, g in enumerate(plano["gols"], 1):
        if g["t"] == "A":
            gc += 1
        else:
            gf += 1
        lado = casa if g["t"] == "A" else fora
        assist = f" (assist. {g['a']})" if g.get("a") else ""
        print(f"  gol {n:2d}  {mmss(g['seg']):>7}  {lado:<14} {(g['j'] or '(sem jogador)') + assist:<26}"
              f"  {gc} × {gf}")


def escreve_manifesto(pasta, feitas):
    with open(os.path.join(pasta, "manifesto.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("lance\tpeca\tarquivo\ttipo\tquadro\tduracao\ttrilha\tcamada\tcamada_nome"
                "\ttimecode\tseg_video\torigem\tesperou\n")
        for p in sorted(feitas, key=lambda x: (x["trilha"], x["quadro"])):
            tipo = "imagem" if p["peca"] == "placar-fixo" else "video"
            f.write(f"{p.get('lance') or p.get('momento') or p['id']}\t{p['peca']}\t{p['arquivo']}\t{tipo}\t"
                    f"{p['quadro']}\t{p['duracao']}\t{p['trilha']}\t{p['camada']}\t{p['nomeCamada']}\t"
                    f"{timecode(p['quadro'])}\t{p['quadro'] / FPS:.2f}\t{p['origem']}\t"
                    f"{p.get('esperou', 0):.1f}\n")


def mostra_resumo(pasta, plano, feitas, falhas, segundos):
    """O que o briefing pede no fim: geradas, as que esperaram, as de fora e o
    motivo, e o tempo."""
    por_camada = {}
    for p in feitas:
        por_camada.setdefault((p["camada"], p["nomeCamada"], p["trilha"]), []).append(p)
    print(f"\n{pasta}\n  {len(feitas)} peças no manifesto, em {segundos / 60:.1f} min")
    for (c, nome, t), ps in sorted(por_camada.items()):
        print(f"    camada {c:2d} ({nome}) = V{t}: {len(ps)}")
    esperaram = [p for p in feitas if p["status"] == "espera"]
    if esperaram:
        print(f"\n  esperaram na fila ({len(esperaram)}):")
        for p in esperaram:
            print(f"    {p['nome']} ({mmss(p['pedido'])} → {mmss(p['seg'])}): {p['motivo']}")
    de_fora = [p for p in plano["pecas"] if p["status"] == "fora"]
    if de_fora or falhas:
        print(f"\n  de fora ({len(de_fora) + len(falhas)}):")
        for p in de_fora:
            print(f"    {p['nome']} ({mmss(p['pedido'])}): {p['motivo']}")
        for p, erro in falhas:
            print(f"    {p['nome']} ({mmss(p['seg'])}): não deu para desenhar — {erro}")
    for a in plano["avisos"]:
        print(f"  ! {a}")
    print("\nNo DaVinci: Workspace > Scripts > Copa Revoada - importar pacote")


def teste():
    """Clipe de 2 s da barra de gol, para conferir a transparência no DaVinci."""
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(FFMPEG):
        sys.exit("falta o ffmpeg em ferramentas/ffmpeg — ver docs/pacote-de-midias.md")
    saida = os.path.join(MIDIAS, "teste", "teste-gol-barra.mov")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    srv = servidor()
    try:
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = abre_estudio(nav, srv.server_address[1])
            pg.evaluate("() => { F.tipo.value = 'gol'; F.min.value = \"11'\"; syncFields(); }")
            n = grava_mov(pg, 2 * FPS, saida)
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


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t or ""))
    return "".join(c for c in t if not unicodedata.combining(c)).strip().lower()


def da_sumula(jogo):
    """Converte a súmula minuto a minuto (dados/sumulas/) num arquivo de lances
    igual ao que o Registro baixa. Nada é inventado: cada lance sai de uma
    linha da súmula, com o tempo dela.

    - Defesa comum de goleiro NÃO vira "defesaça": a súmula não diz qual
      defesa foi difícil, e isso é escolha de quem edita.
    - Assistência sai do texto do lance ("Gol Zaga + Assistência Letti").
    - O fim do 1º tempo é o marco "2T" da súmula: no vídeo de tempos jogados,
      o 1º tempo acaba onde o 2º começa."""
    D = dados_do_site()
    sumula = D.get("sumulas", {}).get(jogo)
    if not sumula:
        sys.exit(f"não há súmula do jogo {jogo} em dados/sumulas/")
    g = next((x for x in D["jogos"] + D.get("amistosos", []) if x["id"] == jogo), None)
    if not g:
        sys.exit(f"o jogo {jogo} não está na aba JOGOS")
    apelido = {x["id"]: x["apelido"] for x in D["jogadores"]}
    por_nome = {}
    for x in D["jogadores"]:
        por_nome[sem_acento(x["apelido"])] = x["apelido"]
    for x in sumula.get("elenco", []):
        if x.get("pid") in apelido:
            por_nome[sem_acento(x["nome"])] = apelido[x["pid"]]
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
        ev = {"seg": e["t"], "min": e["t"] // 60, "t": t, "tipo": tipo,
              "j": apelido.get(e.get("j"), "") if e.get("j") else "", "xg": 0, "origem": e.get("txt", "")}
        if tipo == "gol":
            m = re.search(r"assist[eê]ncia\s+(?:de\s+|do\s+)?([^\s,+]+)", e.get("txt", ""), re.I)
            if m and por_nome.get(sem_acento(m.group(1))):
                ev["a"] = por_nome[sem_acento(m.group(1))]
        eventos.append(ev)
    if sumula.get("inicio2t") is not None:
        s = sumula["inicio2t"]
        eventos.append({"seg": s, "min": s // 60, "t": "J", "tipo": "intervalo", "j": "", "xg": 0,
                        "origem": "marco 2T da súmula"})
    eventos.sort(key=lambda e: e["seg"])
    gols = [e for e in eventos if e["tipo"] == "gol"]
    gc = sum(1 for e in gols if e["t"] == "A")
    gf = len(gols) - gc
    if (gc, gf) != (g.get("gc"), g.get("gf")):
        print(f"  ! os gols da súmula somam {gc} × {gf}, e a aba JOGOS diz {g.get('gc')} × {g.get('gf')}")

    destino = _salva_lances(f"lances-{jogo}-sumula.json", {
        "formato": "copa-revoada-lances/2", "jogo": jogo,
        "nome": f"{g.get('mes', '')} {g.get('temporada', '')}".strip() or jogo,
        "conta_na_copa": True, "sumula": jogo,
        "casa": _time(D, g["casa"]), "fora": _time(D, g["fora"]),
        "video": f"https://youtu.be/{g['video']}" if g.get("video") else "",
        "duracao_video": None,
        "exportado_em": f"convertido da súmula dados/sumulas/{jogo}-lances.csv",
        "eventos": eventos,
        "plano": {"ajustes": {}, "manuais": []},
    })
    por_tipo = {}
    for e in eventos:
        por_tipo[e["tipo"]] = por_tipo.get(e["tipo"], 0) + 1
    print(f"{destino}\n  {len(eventos)} lances: "
          + ", ".join(f"{n} {k}" for k, n in sorted(por_tipo.items())))
    for e in gols:
        print(f"  gol {mmss(e['seg']):>7}  {e['j'] or '(sem jogador)':<12}"
              f"{' assist. ' + e['a'] if e.get('a') else '':<18} {e['origem']}")
    if sumula.get("inicio2t") is not None:
        print(f"  fim do 1º tempo: {mmss(sumula['inicio2t'])} (marco 2T da súmula)")
    if fora_da_conta:
        print("  fora do arquivo: " + ", ".join(f"{n} {k}" for k, n in fora_da_conta.items())
              + " (defesa comum não vira defesaça)")
    return destino


def bateria(jogo, fim):
    """Lances DE TESTE, para ver todas as peças no DaVinci de uma vez, cada uma
    no seu contexto: abertura, lances, replay, intervalo com estatísticas, fim
    com estatísticas, artilheiro e fim de jogo. Três blocos (começo, meio e
    fim), com lances colados para forçar a fila e sobreposições propositais
    entre camadas: um gol durante a abertura, um bloco encostado no intervalo
    e um gol no meio das estatísticas do fim.

    Não é o que aconteceu no jogo: o placar diz BATERIA DE TESTE. As
    estatísticas (comparativo, corrida, quem mais apareceu) vêm da súmula
    verdadeira do jogo, porque não há como inventar súmula."""
    D = dados_do_site()
    sumula = D.get("sumulas", {}).get(jogo) or {}
    g = next((x for x in D["jogos"] + D.get("amistosos", []) if x["id"] == jogo), None)
    if not g:
        sys.exit(f"o jogo {jogo} não está na aba JOGOS")
    apelido = {x["id"]: x["apelido"] for x in D["jogadores"]}
    goleiros = set((sumula.get("goleiros") or {}).values())
    linha, goleiro = {"A": [], "B": []}, {}
    for x in sumula.get("elenco", []):
        lado = "A" if x.get("time") == g["casa"] else "B" if x.get("time") == g["fora"] else None
        if not lado or x.get("pid") not in apelido:
            continue
        if x["pid"] in goleiros:
            goleiro[lado] = apelido[x["pid"]]
        else:
            linha[lado].append(apelido[x["pid"]])
    if len(linha["A"]) < 3 or len(linha["B"]) < 3 or len(goleiro) < 2:
        sys.exit(f"o elenco da súmula de {jogo} não tem gente suficiente para a bateria")
    A, B = linha["A"], linha["B"]
    E = lambda s, t, tipo, j="", **x: dict({"seg": round(s, 1), "min": int(s // 60), "t": t,
                                           "tipo": tipo, "j": j, "xg": 0}, **x)

    def bloco(t0, k):
        """Um bloco de ~95 s. Lances espaçados para cada arte aparecer, com
        duas colisões de propósito: o cartão 3 s depois da cagada (as duas no
        rodapé: o cartão espera) e dois gols colados (a fila do placar)."""
        b1, b2, b3 = B[k % len(B)], B[(k + 1) % len(B)], B[(k + 2) % len(B)]
        return [
            E(t0, "A", "gol", A[0], a=A[1]),                    # o artilheiro: 2 por bloco
            E(t0 + 20, "B", "cagada", b1),
            E(t0 + 23, "A", "cartao", A[1], cor="amarelo"),     # colado na cagada
            E(t0 + 34, "B", "defesa", goleiro["B"]),
            E(t0 + 44, "A", "falta", A[2]),                     # desligada no jogo; a bateria liga
            E(t0 + 54, "B", "sub", b3, sai=b2),
            E(t0 + 64, "J", "replay", fim=t0 + 76),
            E(t0 + 70, "B", "gol", b1),
            E(t0 + 72, "A", "gol", A[0]),                       # colado: fila do placar
            E(t0 + 96, "B", "cartao", b2, cor="vermelho"),
        ]

    meio = fim / 2
    eventos = (bloco(5, 0)                     # gol aos 5 s: em cima da abertura
               + bloco(meio - 125, 1)          # o fim do bloco encosta no intervalo
               + [E(meio, "J", "intervalo")]
               + bloco(fim - 230, 2)
               + [E(fim - 40, "B", "gol", B[0])])  # no meio das estatísticas do fim
    eventos.sort(key=lambda e: e["seg"])
    manuais = [
        {"id": "manual-ficha-jogador", "peca": "stat", "seg": 150, "dura": 8, "jogador": A[0]},
        {"id": "manual-desempenho", "peca": "estjogador", "seg": 400, "dura": 9, "jogador": B[0]},
        {"id": "manual-historico", "peca": "historico", "seg": 600, "dura": 7, "jogador": A[0]},
        {"id": "manual-cagadas", "peca": "cagadas", "seg": meio + 120, "dura": 8},
        {"id": "manual-analise", "peca": "ficha", "seg": meio + 200, "dura": 8},
    ]
    destino = _salva_lances(f"lances-{jogo}-bateria.json", {
        "formato": "copa-revoada-lances/2", "jogo": f"{jogo}-bateria",
        "nome": "Bateria de teste", "competicao": "BATERIA DE TESTE",
        "conta_na_copa": True, "sumula": jogo, "perfil": "bateria",
        "casa": _time(D, g["casa"]), "fora": _time(D, g["fora"]),
        "video": f"https://youtu.be/{g['video']}" if g.get("video") else "",
        "duracao_video": fim,
        "exportado_em": "lances de teste gerados por scripts/pacote.py bateria — não são do jogo",
        "eventos": eventos,
        "plano": {"ajustes": {}, "manuais": manuais},
    })
    print(f"{destino}\n  {len(eventos)} lances de teste e {len(manuais)} peças à mão; blocos em "
          f"{mmss(5)}, {mmss(meio - 125)} e {mmss(fim - 230)}; fim do 1º tempo em {mmss(meio)}")
    return destino


# --------------------------------------------------------------------------
# manutenção


def mede_artes():
    """Desenha cada arte do Estúdio e lê do canvas a área que ela ocupa de
    verdade. O plano usa essas áreas para a fila. Rode de novo quando uma arte
    mudar de tamanho ou de lugar."""
    from playwright.sync_api import sync_playwright
    garante_site()
    srv = servidor()
    try:
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = abre_estudio(nav, srv.server_address[1])
            res = pg.evaluate("""async () => {
              // o ranking de cagadas cresce com a lista: mede no tamanho máximo
              const antes = LANCES.estado.analise.eventos;
              LANCES.estado.analise.eventos = jog.slice(0,6).map((p,i)=>({tipo:'cagada', j:p.apelido, t:'A', seg:i}));
              const out = {};
              for(const o of [...F.tipo.querySelectorAll('option')]){
                F.tipo.value = o.value; syncFields();
                await new Promise(r=>setTimeout(r,120));
                animandoLance = false; draw(1);
                const d = ctx.getImageData(0,0,1920,1080).data;
                let x0=1920,y0=1080,x1=0,y1=0;
                for(let y=0;y<1080;y+=4) for(let x=0;x<1920;x+=4){
                  if(d[(y*1920+x)*4+3]>6){ if(x<x0)x0=x; if(x>x1)x1=x; if(y<y0)y0=y; if(y>y1)y1=y; }
                }
                if(x1>x0) out[o.value] = [x0,y0,x1,y1];
              }
              LANCES.estado.analise.eventos = antes;
              return out;
            }""")
            nav.close()
    finally:
        srv.shutdown()
    dados = json.load(open(AREAS, encoding="utf-8"))
    dados["areas"] = res
    dados["medido_em"] = time.strftime("%Y-%m-%d")
    json.dump(dados, open(AREAS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{AREAS}\n  {len(res)} artes medidas")


def opcao(nome, padrao=None):
    if nome in sys.argv:
        return float(sys.argv[sys.argv.index(nome) + 1])
    return padrao


def fim_das_opcoes():
    if "--video" in sys.argv:
        fim = duracao_do_video(sys.argv[sys.argv.index("--video") + 1])
        print(f"duração do vídeo: {mmss(fim)}")
        return fim
    return opcao("--fim")


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "teste":
        teste()
    elif acao == "gerar":
        arq = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        gerar(arq, inicio=opcao("--inicio", 0.0), fim=fim_das_opcoes())
    elif acao == "da-sumula" and len(sys.argv) > 2:
        da_sumula(sys.argv[2])
    elif acao == "bateria" and len(sys.argv) > 2:
        fim = fim_das_opcoes()
        if not fim:
            sys.exit("diga a duração: --video arquivo.mp4  ou  --fim segundos")
        bateria(sys.argv[2], fim)
    elif acao == "mede-artes":
        mede_artes()
    else:
        sys.exit(__doc__)
