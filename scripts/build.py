#!/usr/bin/env python3
"""
Copa Revoada — build do site.

Lê dados/COPA_REVOADA_planilha.xlsx, junta com as fotos de fotos/ e o logo de
assets/, e escreve index.html a partir de src/app.template.html.

    python3 scripts/build.py

Nada aqui depende de internet. As únicas dependências são openpyxl e Pillow.
"""

import base64
import io
import json
import os
import sys
import unicodedata
import re

try:
    import openpyxl
    from PIL import Image, ImageEnhance, ImageOps
except ImportError:
    sys.exit("Faltam dependências. Rode:  pip install openpyxl pillow")

# opencv é opcional: com ele o recorte do retrato acha o rosto; sem ele, cai no
# enquadramento por proporção. O build funciona dos dois jeitos.
try:
    import cv2
    import numpy as np
    TEM_ROSTO = os.path.isfile(
        os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
except ImportError:
    TEM_ROSTO = False

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANILHA = os.path.join(RAIZ, "dados", "COPA_REVOADA_planilha.xlsx")
LEGADO = os.path.join(RAIZ, "dados", "ranking-legado.json")
TEMPLATE = os.path.join(RAIZ, "src", "app.template.html")
LOGO = os.path.join(RAIZ, "assets", "logo.png")
FOTOS = os.path.join(RAIZ, "fotos")
ASSETS = os.path.join(RAIZ, "assets")
IMG = os.path.join(RAIZ, "img")
SAIDA = os.path.join(RAIZ, "index.html")

PLAYLIST = "PLSnrz0oA5cB49hSu2rMMCCtbXZOK6l9hq"

# Nos três primeiros jogos ninguém anotou gol nem assistência por jogador, só
# quem foi campeão. Decisão do grupo: esses jogos contam título e nada mais.
# É o que faz cada um ter 10 jogos válidos e 13 presenças.
# Esvaziar este conjunto devolve a contagem antiga de 13.
SO_TITULO = {"2020-12", "2021-07", "2021-12"}

EXTS = (".jpg", ".jpeg", ".png", ".webp")
AVISOS = []

# Arquivos de assets/ cujo nome não bate com o id da planilha. Só entram aqui
# os casos em que a correspondência é evidente (erro de digitação ou apelido do
# time). Nome duvidoso não é chutado: vira aviso no fim do build.
APELIDO_JOGADOR = {
    "danilin": "danilim",
    "leobittencour": "leobittencourt",
    "be": "correa",          # Be / Be Correa / Bernardo C
    "bemarucco": "marucco",  # Be Marucco / Bernardo M
    "dede": "andre",         # Dedé é o André
    "vitim": "kretzer",      # Vitim e Kretzer são a mesma pessoa
}
ESCUDO_TIME = {
    "borussetalogo": "borussia22",
    "dentrofclogo": "dentro26",
    "ferroviagralogo": "ferroviagra26",
    "jumentuslogo": "jumentus25",
    "liverpoollogo": "liverpool22",
    "milanblogo": "milanbe25",
}
FOTO_TIME = {
    "borusseta": "borussia22",
    "citifodo": "city23",
    "dentofc2026": "dentro26",
    "ferroviagra2026": "ferroviagra26",
    "jumentos": "jumentus25",
    "liverpool": "liverpool22",
    "milanb": "milanbe25",
}
# Não são foto de jogador nem de time; ficam de fora do site até alguém dizer
# o que são. Listados aqui só para não aparecerem como "arquivo sem uso".
IGNORAR_ASSET = {"logo", "logo-azul", "logo-branco"}


def aviso(msg):
    AVISOS.append(msg)


def slug(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def linhas(ws, cabecalho_em):
    """Devolve dicts a partir da linha de cabeçalho informada (1-based)."""
    hdr = [str(c.value).strip() if c.value else "" for c in ws[cabecalho_em]]
    for row in ws.iter_rows(min_row=cabecalho_em + 1, values_only=True):
        if not any(v not in (None, "") for v in row):
            continue
        yield {hdr[i]: row[i] for i in range(len(hdr)) if hdr[i]}


def acha_cabecalho(ws, primeira_coluna):
    """A planilha tem uma nota na linha 1; o cabeçalho pode estar na 1 ou na 3."""
    for r in (1, 2, 3, 4):
        v = ws.cell(r, 1).value
        if v and str(v).strip() == primeira_coluna:
            return r
    raise SystemExit(f"Não achei o cabeçalho '{primeira_coluna}' na aba {ws.title}")


def num(v, padrao=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return padrao


def sim(v):
    return str(v).strip().upper() in ("SIM", "S", "1", "TRUE", "X")


USADOS = set()


def acha_origem(base, pastas=(FOTOS, ASSETS)):
    """Procura <base>.<ext> nas pastas dadas, na ordem."""
    for pasta in pastas:
        for ext in EXTS:
            caminho = os.path.join(pasta, base + ext)
            if os.path.exists(caminho):
                USADOS.add(base.lower())
                return caminho
    return ""


def _destino(sub):
    caminho = os.path.join(IMG, sub)
    os.makedirs(caminho, exist_ok=True)
    return caminho


ROSTOS_ACHADOS = []
ROSTOS_PERDIDOS = []


def acha_rosto(im):
    """(centro_x, centro_y, largura, altura) do maior rosto, ou None."""
    if not TEM_ROSTO:
        return None
    cinza = np.array(im.convert("L"))
    # equalizar ajuda bastante em foto de jogo, com sol estourado ou sombra
    cinza = cv2.equalizeHist(cinza)
    alt, larg = cinza.shape
    lado_menor = min(alt, larg)

    def plausivel(f):
        """Rosto de retrato fica na metade de cima e tem tamanho de rosto.
        Sem isso, a passada mais frouxa acha 'rosto' em grama e alambrado."""
        x, y, w, h = f
        cy = y + h / 2
        return (cy < alt * .72                      # não fica lá embaixo
                and .05 < w / larg < .75            # nem minúsculo nem a foto toda
                and .5 < w / h < 1.6)               # rosto é quase quadrado

    # afrouxa aos poucos; a foto de corpo inteiro só cai nas últimas
    for minimo, vizinhos in ((max(40, lado_menor // 8), 6),
                             (max(28, lado_menor // 16), 5),
                             (max(20, lado_menor // 22), 4)):
        for arquivo in ("haarcascade_frontalface_default.xml",
                        "haarcascade_frontalface_alt2.xml",
                        "haarcascade_profileface.xml"):
            cascata = cv2.CascadeClassifier(cv2.data.haarcascades + arquivo)
            achados = [f for f in cascata.detectMultiScale(
                cinza, scaleFactor=1.06, minNeighbors=vizinhos,
                minSize=(minimo, minimo))if plausivel(f)]
            if achados:
                x, y, w, h = max(achados, key=lambda f: f[2] * f[3])
                return x + w / 2, y + h / 2, w, h
    return None


def deriva_retrato(origem, nome):
    """Recorta quadrado em cima do rosto e grava JPEG leve e tratado."""
    saida = os.path.join(_destino("jogadores"), nome + ".jpg")
    im = Image.open(origem).convert("RGB")

    achado = acha_rosto(im)
    if achado:
        cx, cy, _, fh = achado
        # o rosto fica ocupando ~46% da altura do quadro, com ar em cima
        lado = int(min(min(im.size), fh * 2.2))
        x, y = int(cx - lado / 2), int(cy - lado * .42)
        ROSTOS_ACHADOS.append(nome)
    else:
        lado = min(im.size)
        x, y = (im.width - lado) // 2, int((im.height - lado) * .18)
        ROSTOS_PERDIDOS.append(nome)

    x = max(0, min(x, im.width - lado))
    y = max(0, min(y, im.height - lado))
    im = im.crop((x, y, x + lado, y + lado))
    im = im.resize((420, 420), Image.LANCZOS)

    # tratamento: nivela exposição, dá contraste e um pouco de nitidez
    im = ImageOps.autocontrast(im, cutoff=(1, 2))
    im = ImageEnhance.Color(im).enhance(1.08)
    im = ImageEnhance.Sharpness(im).enhance(1.4)

    im.save(saida, "JPEG", quality=86, optimize=True, progressive=True)
    return "img/jogadores/%s.jpg" % nome


def deriva_escudo(origem, nome):
    """Escudo mantém transparência; PNG pequeno."""
    saida = os.path.join(_destino("times"), nome + "-escudo.png")
    im = Image.open(origem).convert("RGBA")
    caixa = im.getbbox()
    if caixa:
        im = im.crop(caixa)
    im.thumbnail((320, 320), Image.LANCZOS)
    im.save(saida, "PNG", optimize=True)
    return "img/times/%s-escudo.png" % nome


def deriva_foto_time(origem, nome):
    saida = os.path.join(_destino("times"), nome + "-foto.jpg")
    im = Image.open(origem).convert("RGB")
    im.thumbnail((1100, 1100), Image.LANCZOS)
    im.save(saida, "JPEG", quality=80, optimize=True, progressive=True)
    return "img/times/%s-foto.jpg" % nome


def foto_de(pid):
    origem = acha_origem(pid)
    if not origem:
        for arquivo, alvo in APELIDO_JOGADOR.items():
            if alvo == pid:
                origem = acha_origem(arquivo)
                break
    return deriva_retrato(origem, pid) if origem else ""


def imagens_do_time(tid):
    """Devolve (escudo, foto) já otimizados, ou strings vazias."""
    escudo = foto = ""
    for arquivo, alvo in ESCUDO_TIME.items():
        if alvo == tid:
            o = acha_origem(arquivo, (ASSETS,))
            if o:
                escudo = deriva_escudo(o, tid)
            break
    for arquivo, alvo in FOTO_TIME.items():
        if alvo == tid:
            o = acha_origem(arquivo, (ASSETS,))
            if o:
                foto = deriva_foto_time(o, tid)
            break
    return escudo, foto


def assets_sem_uso():
    """Arquivo de imagem em assets/ que o build não soube onde encaixar."""
    sobra = []
    for f in sorted(os.listdir(ASSETS)):
        base, ext = os.path.splitext(f)
        if ext.lower() not in EXTS or base.lower() in IGNORAR_ASSET:
            continue
        if base.lower() not in USADOS:
            sobra.append(f)
    return sobra


def logo_b64(px=300):
    im = Image.open(LOGO)
    im = im.crop(im.getbbox())
    im.thumbnail((px, px), Image.LANCZOS)
    alpha = im.split()[3] if im.mode == "RGBA" else None
    rgb = im.convert("RGB").quantize(colors=4).convert("RGB")
    if alpha:
        rgb.putalpha(alpha)
    buf = io.BytesIO()
    rgb.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def main():
    wb = openpyxl.load_workbook(PLANILHA, data_only=True)

    # ---------------- jogadores ----------------
    ws = wb["JOGADORES"]
    jogadores = []
    for r in linhas(ws, acha_cabecalho(ws, "id")):
        pid = str(r.get("id") or "").strip()
        if not pid:
            continue
        jogadores.append({
            "id": pid,
            "apelido": str(r.get("apelido") or pid).strip(),
            "nome": str(r.get("nome_completo") or "").strip(),
            "pos": str(r.get("posicao") or "").strip().upper(),
            "numero": num(r.get("numero_camisa"), 0),
            "foto": foto_de(pid),
            "jogos": 0, "gols": 0, "assist": 0, "titulos": 0, "contra": 0,
            "presencas": 0,
        })
    porId = {p["id"]: p for p in jogadores}

    # ---------------- times ----------------
    ws = wb["TIMES"]
    times = []
    for r in linhas(ws, acha_cabecalho(ws, "id")):
        tid = str(r.get("id") or "").strip()
        if not tid:
            continue
        escudo, foto = imagens_do_time(tid)
        # a planilha pode apontar um arquivo à mão; quando aponta, ela manda
        manual = str(r.get("escudo_arquivo") or "").strip()
        if manual:
            o = acha_origem(os.path.splitext(manual)[0], (ASSETS,))
            if o:
                escudo = deriva_escudo(o, tid)
            else:
                aviso(f"TIMES {tid}: escudo_arquivo '{manual}' não existe em assets/")
        times.append({
            "id": tid,
            "nome": str(r.get("nome") or tid).strip(),
            "temporada": num(r.get("temporada")),
            "sigla": str(r.get("sigla") or tid[:3]).strip().upper(),
            "c1": str(r.get("cor_1") or "#12A150").strip(),
            "c2": str(r.get("cor_2") or "#F2B01E").strip(),
            "escudo": escudo,
            "foto": foto,
        })
    times.sort(key=lambda t: (t["temporada"], t["id"]))
    timeIds = {t["id"] for t in times}

    # ---------------- jogos ----------------
    ws = wb["JOGOS"]
    jogos = []
    for r in linhas(ws, acha_cabecalho(ws, "id")):
        gid = str(r.get("id") or "").strip()
        if not gid:
            continue
        jogos.append({
            "id": gid,
            "temporada": num(r.get("temporada")),
            "mes": str(r.get("mes") or "").strip(),
            "dia": str(r.get("dia") or "").strip(),
            "casa": str(r.get("time_casa") or "").strip(),
            "gc": num(r.get("gols_casa")),
            "fora": str(r.get("time_fora") or "").strip(),
            "gf": num(r.get("gols_fora")),
            "estadio": str(r.get("estadio") or "").strip(),
            "campeao": str(r.get("campeao_time_id") or "").strip(),
            "video": str(r.get("video_youtube") or "").strip(),
        })
    jogos.sort(key=lambda g: g["id"])
    jogoIds = {g["id"] for g in jogos}

    for g in jogos:
        for campo in ("casa", "fora"):
            if g[campo] and g[campo] not in timeIds:
                aviso(f"JOGOS {g['id']}: time '{g[campo]}' não existe na aba TIMES")

    # ---------------- escalações ----------------
    escalacoes = []
    if "ESCALACOES" in wb.sheetnames:
        ws = wb["ESCALACOES"]
        for r in linhas(ws, acha_cabecalho(ws, "jogo_id")):
            jid = str(r.get("jogo_id") or "").strip()
            pid = str(r.get("jogador_id") or "").strip()
            if not jid or not pid:
                continue
            if jid.upper().startswith("EXEMPLO") or pid.upper().startswith("EXEMPLO"):
                continue
            if jid not in jogoIds:
                aviso(f"ESCALACOES: jogo '{jid}' não existe na aba JOGOS")
                continue
            if pid not in porId:
                aviso(f"ESCALACOES: jogador '{pid}' não existe na aba JOGADORES")
                continue
            escalacoes.append({
                "jogo": jid, "jogador": pid,
                "time": str(r.get("time_id") or "").strip(),
                "gols": num(r.get("gols")),
                "assist": num(r.get("assistencias")),
                "gols_lancados": r.get("gols") is not None and str(r.get("gols")).strip() != "",
                "campeao": sim(r.get("campeao")),
                "nota": num(r.get("nota_1a5"), 0) or None,
                "numero": num(r.get("numero"), 0) or None,
                # gol contra: conta pro adversário, nunca pro total do jogador
                "contra": num(r.get("gols_contra")),
                # gol anulado (VAR): vale pro jogador, não vale pro placar
                "no_placar": str(r.get("conta_no_placar") or "SIM").strip().upper() != "NAO",
            })

    # ---------------- desempenho por time ----------------
    # o rostinho da página do time sai daqui: é o julgamento de como a pessoa
    # foi naquele time, não em cada jogo isolado
    desempenho = []
    if "DESEMPENHO" in wb.sheetnames:
        ws = wb["DESEMPENHO"]
        for r in linhas(ws, acha_cabecalho(ws, "time_id")):
            tid = str(r.get("time_id") or "").strip()
            pid = str(r.get("jogador_id") or "").strip()
            nota = num(r.get("nota_1a5"), 0)
            if not tid or not pid or not nota:
                continue
            if tid not in timeIds:
                aviso(f"DESEMPENHO: time '{tid}' não existe na aba TIMES")
                continue
            if pid not in porId:
                aviso(f"DESEMPENHO: jogador '{pid}' não existe na aba JOGADORES")
                continue
            desempenho.append({
                "time": tid, "jogador": pid,
                "nota": max(1, min(5, nota)),
                "obs": str(r.get("observacao") or "").strip(),
            })

    # ---------------- estatísticas ----------------
    cobertos = {e["jogo"] for e in escalacoes}
    faltando = [g["id"] for g in jogos if g["id"] not in cobertos]
    # os totais só passam a sair das escalações quando TODOS os jogos estiverem
    # lançados; parcial contaria menos jogo do que a pessoa realmente fez
    completo = bool(jogos) and not faltando

    jogos_sem_gol = sorted({e["jogo"] for e in escalacoes if not e["gols_lancados"]})

    # ---------------- placar x gols lançados ----------------
    # é a conferência que a aba CONFERE fazia à mão. Gol contra vai pro outro
    # lado; gol anulado pelo VAR não entra. Sobrou diferença, o build reclama.
    # só pula o jogo em que NINGUÉM teve gol lançado. Jogo com uma ou outra
    # célula vazia continua conferível — 2022-04 e 2022-10 são desses.
    sem_nenhum = {g["id"] for g in jogos
                  if not any(e["gols_lancados"] for e in escalacoes if e["jogo"] == g["id"])}
    for g in jogos:
        if g["id"] in sem_nenhum or not g["casa"] or not g["fora"]:
            continue
        marcou = {g["casa"]: 0, g["fora"]: 0}
        for e in escalacoes:
            if e["jogo"] != g["id"] or e["time"] not in marcou:
                continue
            if e["no_placar"]:
                marcou[e["time"]] += e["gols"]
            if e["contra"]:
                outro = g["fora"] if e["time"] == g["casa"] else g["casa"]
                marcou[outro] += e["contra"]
        if marcou[g["casa"]] != g["gc"] or marcou[g["fora"]] != g["gf"]:
            aviso(f"{g['id']}: as escalações somam {marcou[g['casa']]}x{marcou[g['fora']]} "
                  f"mas o placar da aba JOGOS é {g['gc']}x{g['gf']}")

    if completo:
        for e in escalacoes:
            p = porId[e["jogador"]]
            # presença é toda escalação; jogo válido exclui os três primeiros,
            # em que só o título conta
            p["presencas"] += 1
            if e["jogo"] not in SO_TITULO:
                p["jogos"] += 1
                p["gols"] += e["gols"]
                p["assist"] += e["assist"]
                p["contra"] += e["contra"]
            if e["campeao"]:
                p["titulos"] += 1

        validos = [g["id"] for g in jogos if g["id"] not in SO_TITULO]
        print(f"  totais de {len(escalacoes)} escalacoes — {len(validos)} jogos valem "
              f"estatistica, {len(SO_TITULO)} valem so titulo")
        # depois da regra dos três primeiros, o ranking antigo deixa de ser
        # necessário como fonte: os gols saem inteiros das escalações
        ainda_sem = sorted(set(jogos_sem_gol) - SO_TITULO - set(sem_nenhum))
        if ainda_sem:
            aviso("Jogos que valem estatística e ainda têm célula de gol em branco: "
                  + ", ".join(ainda_sem) + ". O placar bate, então provavelmente a "
                  "célula vazia quer dizer zero — mas confirme.")
        leg = {slug(x["id"]): x for x in json.load(open(LEGADO, encoding="utf-8"))}
        difs = []
        for p in jogadores:
            l = leg.get(slug(p["id"]))
            if l and l["jogos"] and abs(l["jogos"] - p["jogos"]) > 2:
                difs.append(f"{p['apelido']} {p['jogos']}x{l['jogos']}")
        if difs:
            aviso("Contagem de jogos ainda diverge do ranking antigo mesmo depois da "
                  "regra dos três primeiros (site x ranking): " + ", ".join(difs) + ".")
    else:
        legado = {slug(x["id"]): x for x in json.load(open(LEGADO, encoding="utf-8"))}
        achou = 0
        for p in jogadores:
            l = legado.get(slug(p["id"]))
            if l:
                p.update(jogos=l["jogos"], gols=l["gols"], presencas=l["jogos"],
                         assist=l["assist"], titulos=l["titulos"])
                achou += 1
        print(f"  totais vindos do ranking antigo ({achou} jogadores) — "
              f"ESCALACOES cobre {len(cobertos)}/{len(jogos)} jogos")
        if faltando:
            aviso("Sem escalação lançada em: " + ", ".join(faltando) +
                  ". Enquanto faltar algum jogo, os totais de cada jogador vêm do ranking "
                  "antigo (as telas de elenco e time já usam as escalações que existem).")

    # ---------------- troféus e premiações ----------------
    # todos são de ouro: é assim que os troféus da copa existem de verdade.
    # o "modelo" diz qual arte o site desenha.
    trofeus = [
        {"id": "campeao", "nome": "Campeão do dia", "tier": "ouro", "modelo": "lutador"},
        {"id": "artilheiro", "nome": "Artilheiro", "tier": "ouro", "modelo": "chuteira"},
        {"id": "garcom", "nome": "Garçom", "tier": "ouro", "modelo": "bandeja"},
        {"id": "craque", "nome": "Craque da copa", "tier": "ouro", "modelo": "bola"},
        {"id": "paredao", "nome": "Paredão", "tier": "ouro", "modelo": "goleiro"},
        {"id": "piroquinha", "nome": "Piroquinha", "tier": "ouro", "modelo": "piroquinha"},
    ]
    premiacoes = []
    if "TROFEUS" in wb.sheetnames:
        ws = wb["TROFEUS"]
        for r in linhas(ws, acha_cabecalho(ws, "temporada")):
            pid = str(r.get("jogador_id") or "").strip()
            if not pid or str(r.get("jogo_id") or "").upper().startswith("EXEMPLO"):
                continue
            if pid not in porId:
                aviso(f"TROFEUS: jogador '{pid}' não existe na aba JOGADORES")
                continue
            premiacoes.append({
                "temporada": num(r.get("temporada")),
                "jogo": str(r.get("jogo_id") or "").strip(),
                "trofeu": str(r.get("trofeu_id") or "").strip(),
                "jogador": pid,
                "obs": str(r.get("observacao") or "").strip(),
            })

    # ---------------- clipes ----------------
    clipes = []
    if "CLIPES" in wb.sheetnames:
        ws = wb["CLIPES"]
        for r in linhas(ws, acha_cabecalho(ws, "jogador_id")):
            pid = str(r.get("jogador_id") or "").strip()
            video = str(r.get("video_youtube") or "").strip()
            if not pid or not video or pid.upper().startswith("EXEMPLO"):
                continue
            if pid not in porId:
                aviso(f"CLIPES: jogador '{pid}' não existe na aba JOGADORES")
                continue
            clipes.append({
                "jogador": pid,
                "titulo": str(r.get("titulo") or "Melhor momento").strip(),
                "video": video,
                "inicio": num(r.get("inicio_seg")),
                "fim": num(r.get("fim_seg")) or None,
                "temporada": num(r.get("temporada")) or None,
            })

    jogadores.sort(key=lambda p: (-p["jogos"], -p["gols"], p["apelido"]))

    dados = {
        "copa": {"nome": "Copa Revoada", "antigo": "Milior Fut", "playlist": PLAYLIST},
        "jogadores": jogadores, "times": times, "jogos": jogos,
        "trofeus": trofeus, "escalacoes": escalacoes, "desempenho": desempenho,
        "premiacoes": premiacoes, "clipes": clipes,
    }

    js = "const LOGO='data:image/png;base64,%s';\nconst DADOS=%s;\n" % (
        logo_b64(), json.dumps(dados, ensure_ascii=False, separators=(",", ":")))

    tpl = open(TEMPLATE, encoding="utf-8").read()
    if "// __DADOS__" not in tpl:
        sys.exit("src/app.template.html perdeu o marcador // __DADOS__")
    open(SAIDA, "w", encoding="utf-8").write(tpl.replace("// __DADOS__", js))

    com_foto = sum(1 for p in jogadores if p["foto"])
    com_video = sum(1 for g in jogos if g["video"])
    com_escudo = sum(1 for t in times if t["escudo"])
    com_ft = sum(1 for t in times if t["foto"])
    print(f"\nindex.html gerado — {os.path.getsize(SAIDA)//1024} KB")
    print(f"  {len(jogadores)} jogadores ({com_foto} com foto)")
    print(f"  {len(times)} times ({com_escudo} com escudo, {com_ft} com foto) · "
          f"{len(jogos)} jogos ({com_video} com vídeo)")
    print(f"  {len(escalacoes)} escalações · {len(premiacoes)} troféus · {len(clipes)} clipes")
    print(f"  {len(desempenho)} notas de desempenho por time")

    if not TEM_ROSTO:
        aviso("opencv não está instalado — o recorte do retrato caiu no "
              "enquadramento por proporção. Instale com: pip install "
              "'opencv-python-headless<5'")
    elif ROSTOS_PERDIDOS:
        aviso(f"rosto detectado em {len(ROSTOS_ACHADOS)} fotos; nestas o "
              f"detector não achou e o corte foi por proporção: "
              + ", ".join(ROSTOS_PERDIDOS))
    else:
        print(f"  rosto detectado e centralizado em {len(ROSTOS_ACHADOS)} fotos")

    sem_num = [p["id"] for p in jogadores if not p["numero"]]
    if sem_num:
        aviso(f"{len(sem_num)} de {len(jogadores)} jogadores sem número de camisa "
              "na coluna numero_camisa da aba JOGADORES. Sem ele, o Estúdio usa a "
              "ordem da lista no lugar do número.")

    sem_foto = [p["id"] for p in jogadores if not p["foto"]]
    if sem_foto:
        aviso(f"{len(sem_foto)} jogadores ainda sem foto: " + ", ".join(sem_foto))
    sobra = assets_sem_uso()
    if sobra:
        aviso("Imagens em assets/ que o build não soube onde encaixar: "
              + ", ".join(sobra) + ". Diga de quem/de que time é cada uma e eu ligo.")

    if AVISOS:
        print("\nAvisos:")
        for a in dict.fromkeys(AVISOS):
            print("  ! " + a)


if __name__ == "__main__":
    main()
