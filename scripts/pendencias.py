#!/usr/bin/env python3
"""
Copa Revoada — gera o conteúdo da aba PENDENCIAS a partir da planilha viva.

    python scripts/pendencias.py

Lê a planilha pelo mesmo endpoint que o build usa (PLANILHA_URL) e escreve
`dados/PENDENCIAS.tsv`. É só abrir esse arquivo, copiar tudo e colar na célula
**A3** da aba PENDENCIAS — o Google Sheets separa as colunas sozinho.

Por que não grava direto: o Apps Script só aceita escrita nas abas `LANCES
<jogo>`, e mesmo assim exigindo a chave que mora na CONFIG. Nenhuma outra aba
é gravável de fora, de propósito. Então o caminho é gerar e colar.

Nada aqui é inventado: cada linha sai de uma contagem de célula vazia na
planilha. Se um item sumir da lista, é porque alguém preencheu.
"""

import io
import json
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "dados", "PENDENCIAS.tsv")
URL = os.environ.get("PLANILHA_URL", "").strip()

CABECALHO = ["prio", "tipo", "o que resolver", "quem", "resolvido em"]

# Lançamento errado na planilha antiga: fica lá para conferência, mas não entra
# no site. Contar essa gente inflaria a lista de pendências com trabalho que
# ninguém precisa fazer. Tem que bater com o EXCLUIR_DO_SITE do build.py.
FORA_DO_SITE = {"derek", "davi", "dereck", "matheus", "luigi", "dereka",
                "joao", "miniderek"}


def baixa():
    if not URL:
        sys.exit("Defina PLANILHA_URL — a mesma que está no repositório.\n"
                 "  export PLANILHA_URL='https://script.google.com/.../exec?acao=planilha'")
    req = urllib.request.Request(URL, headers={"User-Agent": "copa-revoada"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    if not d.get("ok"):
        sys.exit("A planilha respondeu com erro: %s" % d.get("erro"))
    return d["abas"]


def registros(abas, nome, cabecalho_em=3):
    """A linha 1 é nota de uso e a 3 é o cabeçalho; dado começa na 4."""
    linhas = abas.get(nome) or []
    if len(linhas) < cabecalho_em:
        return []
    hdr = [str(c).strip() if c is not None else "" for c in linhas[cabecalho_em - 1]]
    fora = []
    for l in linhas[cabecalho_em:]:
        if not l or l[0] in (None, ""):
            continue
        fora.append({hdr[i]: l[i] for i in range(min(len(hdr), len(l))) if hdr[i]})
    return fora


def vazios(regs, coluna):
    return [r for r in regs if r.get(coluna) in (None, "")]


def main():
    abas = baixa()
    J = [r for r in registros(abas, "JOGADORES")
         if str(r.get("id") or "").strip().lower() not in FORA_DO_SITE]
    G = registros(abas, "JOGOS")
    E = registros(abas, "ESCALACOES")
    D = registros(abas, "DESEMPENHO")
    R = registros(abas, "TROFEUS")
    C = registros(abas, "CLIPES")
    T = registros(abas, "TIMES")

    linhas = []

    def item(prio, tipo, texto):
        linhas.append([str(prio), tipo, texto, "", ""])

    # ── 1: o que trava número no site ────────────────────────────────
    sem_campeao = [r["id"] for r in vazios(G, "campeao_time_id")]
    nome_time = {r["id"]: r.get("nome") or r["id"] for r in T}
    for jid in sem_campeao:
        g = next(x for x in G if x["id"] == jid)
        casa, fora = g.get("gols_casa"), g.get("gols_fora")
        placar = "%s x %s" % (casa, fora)
        try:
            venceu = (g["time_casa"] if int(casa) > int(fora)
                      else g["time_fora"] if int(fora) > int(casa) else None)
        except (TypeError, ValueError):
            venceu = None
        # o placar é dado; quem venceu sai dele. Só não preencho a célula por
        # vocês — a decisão de gravar é de quem estava lá.
        pista = ("empate: se foi empate mesmo, deixe vazio que o site entende"
                 if venceu is None else
                 "pelo placar quem venceu foi %s — confirmem e preencham"
                 % nome_time.get(venceu, venceu))
        item(1, "campeao", "%s (%s): %s" % (jid, placar, pista))

    # ── 2: muito resultado por pouco trabalho ────────────────────────
    n = len(vazios(D, "nota_1a5"))
    if n:
        item(2, "nota", "aba DESEMPENHO: %d notas de 1 a 5 em branco. É o rostinho "
                        "que aparece na página do time — a linha já está montada, "
                        "falta só o número" % n)

    n = len(vazios(J, "numero_camisa"))
    if n:
        item(2, "camisa", "aba JOGADORES: %d números de camisa em branco. Sem eles "
                          "o Estúdio usa a ordem da lista no lugar do número" % n)

    n = len(vazios(J, "posicao"))
    if n:
        item(2, "posicao", "aba JOGADORES: %d posições em branco. É o que põe cada "
                           "um na faixa certa do mapa de formação (GOL, ZAG, MEI, ATA)" % n)

    sem_video = [r["id"] for r in G
                 if not str(r.get("video_youtube") or "").strip()]
    if sem_video:
        item(2, "video", "aba JOGOS, coluna do link: falta o vídeo de %s. Pode colar "
                         "a URL inteira, o site extrai o id" % ", ".join(sem_video))

    simulados = [r for r in R if "simula" in str(r.get("observacao") or "").lower()]
    if simulados:
        item(2, "trofeu", "aba TROFEUS: %d troféus estão marcados SIMULADO, todos no "
                          "nome do mesmo jogador. São enfeite para a tela não ficar "
                          "vazia — troque por premiação de verdade ou apague a linha"
                          % len(simulados))

    # ── 3: acabamento ────────────────────────────────────────────────
    n = len(vazios(J, "nome_completo"))
    if n:
        item(3, "nome", "aba JOGADORES: %d nomes completos em branco. Aparece embaixo "
                        "do apelido no perfil" % n)

    apelido2 = "Apelido Perfil"
    n = len(vazios(J, apelido2)) if any(apelido2 in r for r in J) else 0
    if n:
        item(3, "apelido", "aba JOGADORES, coluna %s: %d em branco. É o apelido de "
                           "zoeira que vira etiqueta dourada no perfil" % (apelido2, n))

    if all("EXEMPLO" in str(r.get("jogador_id") or "").upper() for r in C) and C:
        item(3, "clipe", "aba CLIPES: só tem linha de exemplo. Cada clipe é um recorte "
                         "de melhor momento (jogador, título, segundo de início e fim)")

    n = len(vazios(G, "dia"))
    if n:
        item(3, "data", "aba JOGOS: %d jogos sem o dia do mês. Hoje o site mostra só "
                        "mês e ano" % n)

    item(3, "imagem", "assets/jogo1-2026.jpg e assets/vencedorjogo12026.jpg estão na "
                      "pasta sem ninguém saber de quem são. Digam e eu ligo no site")

    txt = io.StringIO()
    txt.write("\t".join(CABECALHO) + "\n")
    for l in linhas:
        txt.write("\t".join(x.replace("\t", " ") for x in l) + "\n")

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(txt.getvalue())

    print("dados/PENDENCIAS.tsv — %d itens" % len(linhas))
    print("Cole na célula A3 da aba PENDENCIAS (apague o que estiver lá antes).\n")
    for l in linhas:
        print("  [%s] %-9s %s" % (l[0], l[1], l[2]))


if __name__ == "__main__":
    main()
