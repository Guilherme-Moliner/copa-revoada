#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copa Revoada — diagnóstico dos WebM exportados pelo Estúdio.

    python scripts/checa-webm.py <pasta ou arquivo> [...]

Lê a estrutura Matroska/WebM byte a byte e diz o que um editor de vídeo vai
encontrar: codec, se existe duração declarada, se existe índice de busca
(Cues), e se a taxa de quadros é constante ou variável.

Não precisa de ffmpeg. Não altera nenhum arquivo.

Por que isso existe: o WebM que sai do navegador é gravado como transmissão ao
vivo, não como arquivo finalizado. O MediaRecorder não sabe de antemão quanto
o vídeo vai durar, então escreve o Segment com tamanho desconhecido, sem
duração e sem índice — e monta os quadros no ritmo em que a tela desenhou, que
não é constante. O navegador lê isso numa boa; editor de vídeo, não.
"""

import io
import os
import struct
import sys

# ── EBML: o mínimo para andar pela árvore ────────────────────────────
CABECALHO = 0x1A45DFA3
SEGMENT = 0x18538067
SEEKHEAD = 0x114D9B74
INFO = 0x1549A966
TIMECODESCALE = 0x2AD7B1
DURACAO = 0x4489
MUXINGAPP = 0x4D80
WRITINGAPP = 0x5741
TRACKS = 0x1654AE6B
TRACKENTRY = 0xAE
TRACKTYPE = 0x83
CODECID = 0x86
VIDEO = 0xE0
LARGURA = 0xB0
ALTURA = 0xBA
DEFAULTDURATION = 0x23E383
CLUSTER = 0x1F43B675
TIMECODE = 0xE7
SIMPLEBLOCK = 0xA3
BLOCKGROUP = 0xA0
BLOCK = 0xA1
CUES = 0x1C53BB6B

# elementos que a gente precisa entrar; o resto é pulado inteiro
CONTEINERES = {SEGMENT, INFO, TRACKS, TRACKENTRY, VIDEO, CLUSTER, BLOCKGROUP}

DESCONHECIDO = -1


def _vint(f, manter_marca):
    """Lê um inteiro de tamanho variável. IDs guardam a marca; tamanhos não."""
    b = f.read(1)
    if not b:
        return None, 0
    primeiro = b[0]
    if primeiro == 0:
        return None, 1
    comprimento = 1
    mascara = 0x80
    while not (primeiro & mascara):
        mascara >>= 1
        comprimento += 1
    resto = f.read(comprimento - 1)
    if len(resto) != comprimento - 1:
        return None, comprimento
    bruto = bytes([primeiro]) + resto
    valor = int.from_bytes(bruto, "big")
    if manter_marca:
        return valor, comprimento
    # tamanho com todos os bits em 1 = "não sei quanto vai durar"
    sem_marca = valor & ~(mascara << (8 * (comprimento - 1)))
    limite = (1 << (7 * comprimento)) - 1
    if sem_marca == limite:
        return DESCONHECIDO, comprimento
    return sem_marca, comprimento


def _uint(dados):
    return int.from_bytes(dados, "big") if dados else 0


def _float(dados):
    if len(dados) == 4:
        return struct.unpack(">f", dados)[0]
    if len(dados) == 8:
        return struct.unpack(">d", dados)[0]
    return 0.0


def analisa(caminho):
    tam = os.path.getsize(caminho)
    r = {"arquivo": caminho, "bytes": tam, "codec": "?", "largura": 0, "altura": 0,
         "duracao_ms": None, "escala": 1000000, "tem_cues": False,
         "tem_seekhead": False, "segment_desconhecido": False,
         "cluster_desconhecido": 0, "quadros": [], "chaves": 0,
         "muxer": "", "defaultduration": None, "erro": ""}

    with io.open(caminho, "rb") as f:
        def percorre(fim, dentro_de_cluster_tc=None):
            while fim is None or f.tell() < fim:
                inicio = f.tell()
                eid, _ = _vint(f, True)
                if eid is None:
                    return
                tamanho, _ = _vint(f, False)
                if tamanho is None:
                    return
                dados_em = f.tell()

                if eid == SEGMENT and tamanho == DESCONHECIDO:
                    r["segment_desconhecido"] = True
                if eid == CLUSTER and tamanho == DESCONHECIDO:
                    r["cluster_desconhecido"] += 1
                if eid == SEEKHEAD:
                    r["tem_seekhead"] = True
                if eid == CUES:
                    r["tem_cues"] = True

                if eid in CONTEINERES:
                    novo_fim = None if tamanho == DESCONHECIDO else dados_em + tamanho
                    if eid == CLUSTER:
                        percorre(novo_fim, [0])
                    else:
                        percorre(novo_fim, dentro_de_cluster_tc)
                    if novo_fim is not None:
                        f.seek(novo_fim)
                    continue

                if tamanho == DESCONHECIDO:
                    return
                dados = f.read(tamanho)
                if len(dados) != tamanho:
                    r["erro"] = "arquivo termina no meio de um elemento"
                    return

                if eid == TIMECODESCALE:
                    r["escala"] = _uint(dados) or 1000000
                elif eid == DURACAO:
                    r["duracao_ms"] = _float(dados)
                elif eid == CODECID:
                    v = dados.decode("ascii", "ignore").strip("\x00")
                    if v.startswith("V_"):
                        r["codec"] = v
                elif eid == LARGURA:
                    r["largura"] = _uint(dados)
                elif eid == ALTURA:
                    r["altura"] = _uint(dados)
                elif eid == DEFAULTDURATION:
                    r["defaultduration"] = _uint(dados)
                elif eid == MUXINGAPP or eid == WRITINGAPP:
                    v = dados.decode("utf-8", "ignore").strip("\x00")
                    if v and v not in r["muxer"]:
                        r["muxer"] = (r["muxer"] + " / " + v).strip(" /")
                elif eid == TIMECODE and dentro_de_cluster_tc is not None:
                    dentro_de_cluster_tc[0] = _uint(dados)
                elif eid in (SIMPLEBLOCK, BLOCK) and dentro_de_cluster_tc is not None:
                    b = io.BytesIO(dados)
                    _vint(b, False)                    # número da faixa
                    rel = b.read(2)
                    if len(rel) == 2:
                        desloc = struct.unpack(">h", rel)[0]
                        t = dentro_de_cluster_tc[0] + desloc
                        chave = True
                        if eid == SIMPLEBLOCK:
                            flags = b.read(1)
                            chave = bool(flags and (flags[0] & 0x80))
                        r["quadros"].append(t)
                        if chave:
                            r["chaves"] += 1
                if inicio == f.tell():
                    return

        percorre(None)

    q = sorted(r["quadros"])
    r["n_quadros"] = len(q)
    if len(q) > 2:
        ms = r["escala"] / 1e6
        gaps = [round((q[i + 1] - q[i]) * ms, 3) for i in range(len(q) - 1)]
        gaps = [g for g in gaps if g > 0]
        r["intervalos"] = gaps
        if gaps:
            r["gap_min"] = min(gaps)
            r["gap_max"] = max(gaps)
            r["gap_medio"] = sum(gaps) / len(gaps)
            r["distintos"] = len(set(gaps))
            r["fps_medio"] = 1000.0 / r["gap_medio"] if r["gap_medio"] else 0
            r["span_ms"] = (q[-1] - q[0]) * ms
    return r


def veredito(r):
    """O que impede um editor de abrir isso, em ordem de gravidade."""
    p = []
    if r["codec"] in ("V_VP8", "V_VP9", "V_AV1"):
        p.append("codec %s — o DaVinci Resolve no Windows não decodifica VP8/VP9 "
                 "de forma confiável; é a causa raiz do \"could not be decoded\""
                 % r["codec"][2:])
    if r["duracao_ms"] is None:
        p.append("SEM duração declarada no cabeçalho — o editor não sabe onde o "
                 "clipe termina antes de ler o arquivo inteiro")
    if not r["tem_cues"]:
        p.append("SEM índice de busca (Cues) — cada salto na timeline vira uma "
                 "varredura do arquivo; é o que produz \"Media Offline\" que some "
                 "quando você dá play de novo")
    if r["segment_desconhecido"]:
        p.append("Segment gravado com tamanho DESCONHECIDO — assinatura de "
                 "arquivo de transmissão ao vivo, não de arquivo finalizado")
    if r.get("distintos", 0) > 3:
        p.append("taxa de quadros VARIÁVEL — %d intervalos diferentes, de %.1f ms "
                 "a %.1f ms (%.1f a %.1f fps)"
                 % (r["distintos"], r["gap_min"], r["gap_max"],
                    1000/r["gap_max"] if r["gap_max"] else 0,
                    1000/r["gap_min"] if r["gap_min"] else 0))
    return p


def main():
    alvos = sys.argv[1:]
    if not alvos:
        sys.exit(__doc__.strip())

    arquivos = []
    for a in alvos:
        if os.path.isdir(a):
            for n in sorted(os.listdir(a)):
                if n.lower().endswith(".webm"):
                    arquivos.append(os.path.join(a, n))
        elif os.path.isfile(a):
            arquivos.append(a)

    if not arquivos:
        sys.exit("nenhum .webm encontrado")

    for caminho in arquivos:
        r = analisa(caminho)
        print("=" * 72)
        print(os.path.basename(caminho), " · %.1f KB" % (r["bytes"] / 1024))
        if r["erro"]:
            print("  !! " + r["erro"])
        print("  codec ............ %s  %dx%d" % (r["codec"], r["largura"], r["altura"]))
        print("  gravado por ...... %s" % (r["muxer"] or "(não declarado)"))
        print("  duração no header  %s" % ("%.0f ms" % r["duracao_ms"]
                                           if r["duracao_ms"] is not None else "AUSENTE"))
        print("  índice (Cues) .... %s" % ("sim" if r["tem_cues"] else "AUSENTE"))
        print("  SeekHead ......... %s" % ("sim" if r["tem_seekhead"] else "ausente"))
        print("  Segment ---------- %s" % ("tamanho DESCONHECIDO (live)"
                                           if r["segment_desconhecido"] else "tamanho fixo"))
        print("  quadros .......... %d  (%d keyframes)" % (r["n_quadros"], r["chaves"]))
        if r.get("gap_medio"):
            print("  tempo real ....... %.0f ms" % r["span_ms"])
            print("  fps médio ........ %.2f" % r["fps_medio"])
            print("  intervalo ........ %.1f a %.1f ms, %d valores distintos"
                  % (r["gap_min"], r["gap_max"], r["distintos"]))
        pontos = veredito(r)
        if pontos:
            print("  --- por que o editor reclama ---")
            for x in pontos:
                print("   * " + x)
        else:
            print("  nada de anormal")
    print("=" * 72)


if __name__ == "__main__":
    main()
