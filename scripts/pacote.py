#!/usr/bin/env python3
"""
Copa Revoada — pacote de mídias.

Desenha as artes do Estúdio quadro a quadro, num Chromium sem janela, e grava
cada peça em ProRes 4444 (.mov) com transparência de verdade, para o DaVinci.

    .venv\\Scripts\\python.exe scripts\\pacote.py teste

O desenho é o mesmo do site: a página index.html é aberta de verdade e quem
pinta é o próprio código do Estúdio. Aqui só se escolhe o quadro e se recolhe
a imagem — sem MediaRecorder, sem relógio, sem fundo verde.

Precisa de ferramentas/ffmpeg e do Chromium do Playwright em
ferramentas/ms-playwright (ver docs/pacote-de-midias.md).
"""

import base64
import functools
import http.server
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


def grava(pg, prepara_js, segundos, saida):
    """Desenha a peça quadro a quadro e entrega ao ffmpeg.

    prepara_js recebe o F do Estúdio e deixa os campos como a peça pede.
    Cada quadro é desenhado no seu instante exato da animação (i/(total-1)),
    o mesmo cálculo da sequência PNG do Estúdio."""
    total = max(2, round(segundos * FPS))
    pg.evaluate(f"""async () => {{
        ({prepara_js})(F);
        F.dur.value = {segundos};
        syncFields();
        // fotos chegam depois do primeiro desenho; espera todas
        await Promise.all([...document.images].filter(i=>!i.complete)
          .map(i=>new Promise(r=>{{ i.onload=i.onerror=r; }})));
        await new Promise(r=>setTimeout(r,300));
    }}""")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
           # ProRes 4444 com alfa: abre no Resolve gratuito no Windows
           "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
           "-alpha_bits", "16", "-vendor", "apl0", "-r", str(FPS), saida]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(total):
            url = pg.evaluate(f"""() => {{
                animandoLance = true;
                draw(curva({i}/{total - 1}));
                animandoLance = false;
                return cv.toDataURL('image/png');
            }}""")
            ff.stdin.write(base64.b64decode(url.split(",", 1)[1]))
    finally:
        ff.stdin.close()
        ff.wait()
    if ff.returncode:
        sys.exit(f"o ffmpeg falhou ao gravar {saida}")
    return total


def teste():
    """Clipe de 2 s da barra de gol, para conferir a transparência no DaVinci
    antes de gerar o pacote inteiro."""
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(FFMPEG):
        sys.exit("falta o ffmpeg em ferramentas/ffmpeg — ver docs/pacote-de-midias.md")
    saida = os.path.join(MIDIAS, "teste", "teste-gol-barra.mov")
    srv = servidor()
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = abre_estudio(nav, srv.server_address[1])
            n = grava(pg, """F => {
                F.tipo.value = 'gol';
                F.min.value = "11'";
            }""", 2, saida)
            nav.close()
    finally:
        srv.shutdown()
    print(f"{saida}\n  {n} quadros a {FPS} fps · ProRes 4444 com transparência")


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "teste":
        teste()
    else:
        sys.exit(__doc__)
