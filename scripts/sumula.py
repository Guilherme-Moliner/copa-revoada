#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copa Revoada — lê as súmulas minuto a minuto e devolve os lances já ligados
aos ids da planilha.

Uma súmula é um par de CSVs em `dados/sumulas/`:

    <jogo>-lances.csv     um lance por linha, com timestamp
    <jogo>-jogadores.csv  de que lado cada nome estava, e quem era goleiro

O build chama `carrega()` e joga o resultado dentro do index.html. O site
recebe a lista crua de eventos e faz as contas no navegador — é isso que
deixa o controle de tempo deslizar sem recarregar nada.

As regras de classificação são as mesmas do `analise_jogo.py` que veio junto
com os dados, de propósito: os números daqui têm que bater com o PDF e com o
explorador que já circularam no grupo.

    bloqueado  "bloq" aparece no texto do lance
    gol        o texto começa com "gol " (e "gol anulado" NÃO conta)
    no gol     gerou defesa, ou foi gol
    defesa     a coluna Defesas diz o TIME DO GOLEIRO que defendeu,
               então o chute foi do adversário
"""

import csv
import io
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "dados", "sumulas")

# Como o nome aparece escrito no meio da súmula x como está no elenco. Vieram
# do analise_jogo.py que acompanhava os dados — quem anota no calor do jogo
# abrevia, e "Garopa" e "Garopaba" são a mesma pessoa.
ALIASES = {"garopa": "Garopaba", "meme": "Merizi"}

AVISOS = []


def _av(t):
    AVISOS.append(t)


def sem_acento(t):
    t = unicodedata.normalize("NFKD", str(t or ""))
    return "".join(c for c in t if not unicodedata.combining(c)).strip().lower()


def segundos(linha):
    try:
        return (int(linha["Hora"]) * 3600 + int(linha["Minuto"]) * 60
                + int(linha["Segundo"]))
    except (TypeError, ValueError, KeyError):
        return None


def _le(caminho):
    with io.open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _elenco(caminho, por_nome):
    """Nome da súmula -> {lado, posicao, pid}. `pid` é o id da planilha."""
    fora = {}
    for r in _le(caminho):
        nome = (r.get("jogador") or "").strip()
        if not nome:
            continue
        apelido = (r.get("apelido") or "").strip()
        pid = por_nome.get(sem_acento(nome)) or por_nome.get(sem_acento(apelido))
        fora[nome] = {
            "lado": (r.get("time") or "").strip(),
            # opcional, e manda quando existe: o id do time na planilha
            "time_id": (r.get("time_id") or "").strip(),
            "posicao": (r.get("posicao") or "").strip(),
            "pid": pid or "",
            "nome": nome,
        }
    return fora


def _lados_para_times(elenco, escalacoes, jogo):
    """Descobre qual lado da súmula é qual time da planilha.

    A súmula chama os times de "Branco" e "Preto", que é como o pessoal se
    referia na hora.

    Se o CSV do elenco trouxer a coluna `time_id`, ela manda e o assunto acaba
    aí. Sem ela, conto quantos jogadores de cada lado aparecem em cada time na
    aba ESCALACOES e fico com o mais votado.

    A coluna existe porque a votação é boa para adivinhar uma vez e péssima
    como fonte permanente: ela depende de uma aba que muda por outros motivos,
    e uma edição na escalação pode inverter os dois times de um jogo inteiro
    sem ninguém encostar na súmula. Quando a resposta já é conhecida, ela fica
    escrita.
    """
    fixo = {}
    for info in elenco.values():
        if info.get("time_id"):
            fixo.setdefault(info["lado"], set()).add(info["time_id"])
    if fixo and all(len(v) == 1 for v in fixo.values()):
        return {lado: list(v)[0] for lado, v in fixo.items()}
    if fixo:
        _av("SUMULA %s: a coluna time_id diz coisas diferentes para o mesmo "
            "lado (%s); voltei a deduzir pela aba ESCALACOES"
            % (jogo, ", ".join("%s=%s" % (k, "/".join(sorted(v)))
                               for k, v in sorted(fixo.items()))))
    do_jogo = [e for e in escalacoes if e.get("jogo") == jogo]
    time_de = {}
    for e in do_jogo:
        if e.get("jogador"):
            time_de[e["jogador"]] = e.get("time")

    votos = {}
    for info in elenco.values():
        tid = time_de.get(info["pid"])
        if not tid:
            continue
        votos.setdefault(info["lado"], {}).setdefault(tid, 0)
        votos[info["lado"]][tid] += 1

    fora = {}
    for lado, contagem in votos.items():
        tid, n = max(contagem.items(), key=lambda kv: kv[1])
        fora[lado] = tid
        _av("SUMULA %s: o lado '%s' virou %s por dedução da aba ESCALACOES. "
            "Para travar, ponha a coluna time_id no %s-jogadores.csv"
            % (jogo, lado, tid, jogo))
        if len(contagem) > 1:
            _av("SUMULA %s: o lado '%s' tem gente de mais de um time na "
                "escalação (%s); fiquei com %s, que tem %d"
                % (jogo, lado, ", ".join(contagem), tid, n))
    if len(set(fora.values())) < len(fora):
        _av("SUMULA %s: os dois lados caíram no mesmo time — confira a "
            "escalação desse jogo" % jogo)
    return fora


def _classifica(texto, tem_defesa):
    """Devolve (subtipo, ehGol) a partir do texto do lance."""
    t = sem_acento(texto)
    # "gol anulado" começa com "gol " mas não é gol. O script original contava
    # como gol; só não estourava porque aquela linha não tem chutador.
    anulado = "anulad" in t
    gol = t.startswith("gol ") and not anulado
    if gol:
        return "gol", True
    if "bloq" in t:
        return "bloqueado", False
    if tem_defesa:
        return "defendido", False
    if "fora" in t:
        return "fora", False
    return "outro", False


def carrega(jogadores, escalacoes):
    """Lê todas as súmulas de dados/sumulas/. Devolve {jogo: {...}}."""
    if not os.path.isdir(PASTA):
        return {}

    por_nome = {}
    for p in jogadores:
        por_nome[sem_acento(p.get("apelido"))] = p["id"]
        por_nome[sem_acento(p["id"])] = p["id"]

    fora = {}
    for arquivo in sorted(os.listdir(PASTA)):
        m = re.match(r"^(.+)-lances\.csv$", arquivo)
        if not m:
            continue
        jogo = m.group(1)
        cam_elenco = os.path.join(PASTA, "%s-jogadores.csv" % jogo)
        if not os.path.exists(cam_elenco):
            _av("SUMULA %s: falta o arquivo %s-jogadores.csv, que diz de que "
                "lado cada um estava" % (jogo, jogo))
            continue

        elenco = _elenco(cam_elenco, por_nome)
        sem_id = sorted(n for n, i in elenco.items() if not i["pid"])
        if sem_id:
            _av("SUMULA %s: %s não bate com ninguém da aba JOGADORES. O lance "
                "continua no gráfico do time, mas fora da conta individual — "
                "digam quem é e eu ligo." % (jogo, ", ".join(sem_id)))

        lado_time = _lados_para_times(elenco, escalacoes, jogo)
        goleiro = {}
        for nome, i in elenco.items():
            if sem_acento(i["posicao"]).startswith("gol"):
                goleiro[i["lado"]] = nome

        eventos = []
        fim = 0
        inicio2t = None
        for linha in _le(os.path.join(PASTA, arquivo)):
            s = segundos(linha)
            if s is None:
                continue
            fim = max(fim, s)
            texto = (linha.get("lance") or "").strip()
            if "2t" in sem_acento(texto):
                inicio2t = s
                eventos.append({"t": s, "tipo": "marco", "txt": "Início do 2º tempo"})
                continue

            obs = (linha.get("obs") or "").strip()
            chutador = (linha.get("Chutes") or "").strip()
            defesa = (linha.get("Defesas") or "").strip()
            escanteio = (linha.get("Escanteios") or "").strip()
            falta = (linha.get("Faltas") or "").strip()
            cagada = (linha.get("Cagadas") or "").strip()

            def acha(nome):
                """Aceita o nome do elenco, o apelido, ou a abreviação usada
                no meio da súmula."""
                i = elenco.get(nome)
                if i:
                    return i
                chave = sem_acento(nome)
                alvo = sem_acento(ALIASES.get(chave, ""))
                for n, info in elenco.items():
                    if sem_acento(n) in (chave, alvo):
                        return info
                return {}

            def quem(nome):
                i = acha(nome)
                return i.get("pid", ""), lado_time.get(i.get("lado"), "")

            if chutador:
                sub, eh_gol = _classifica(texto, bool(defesa))
                pid, tid = quem(chutador)
                if not tid:
                    _av("SUMULA %s: não sei de que time foi o chute de '%s'"
                        % (jogo, chutador))
                gk = goleiro.get(sem_acento(defesa).capitalize()) if defesa else None
                if not gk and defesa:
                    for lado, tnome in lado_time.items():
                        if sem_acento(lado) == sem_acento(defesa):
                            gk = goleiro.get(lado)
                eventos.append({
                    "t": s, "tipo": "chute", "sub": sub, "gol": eh_gol,
                    "j": pid, "nome": chutador, "time": tid,
                    "gk": (elenco.get(gk or "") or {}).get("pid", ""),
                    "txt": texto,
                })
            elif eh_gol_solto(texto):
                eventos.append({"t": s, "tipo": "nota", "txt": texto})

            if defesa:
                tid = lado_time.get(sem_acento(defesa).capitalize()) \
                      or lado_time.get(defesa.capitalize()) or ""
                gk = goleiro.get(defesa.capitalize()) or goleiro.get(
                    sem_acento(defesa).capitalize())
                eventos.append({"t": s, "tipo": "defesa", "time": tid,
                                "j": (elenco.get(gk or "") or {}).get("pid", ""),
                                "nome": gk or "", "txt": texto})

            if escanteio or sem_acento(obs) == "escanteio":
                lado = escanteio or ""
                tid = lado_time.get(lado.capitalize()) or ""
                eventos.append({"t": s, "tipo": "escanteio", "time": tid, "txt": texto})

            if falta:
                pid, tid = quem(falta)
                eventos.append({"t": s, "tipo": "falta", "j": pid, "nome": falta,
                                "time": tid, "txt": texto})

            if cagada:
                pid, tid = quem(cagada)
                eventos.append({"t": s, "tipo": "cagada", "j": pid, "nome": cagada,
                                "time": tid, "txt": texto})

        eventos.sort(key=lambda e: e["t"])
        lados = sorted(lado_time.items())
        # quem era goleiro sai daqui, e não da contagem de defesas: goleiro
        # que passou o jogo sem trabalho continua sendo goleiro, e a ficha
        # dele tem que mostrar "0 defesas", não virar ficha de jogador de linha
        fora[jogo] = {
            "fim": fim,
            "inicio2t": inicio2t,
            "lados": {lado: tid for lado, tid in lados},
            "goleiros": {lado_time.get(lado, lado): (elenco.get(nome) or {}).get("pid", "")
                         for lado, nome in goleiro.items()},
            # O elenco inteiro, e não só quem apareceu num lance: a arte do
            # time precisa mostrar todo mundo que entrou em campo, inclusive
            # quem passou o jogo sem finalizar. Zero é informação também.
            "elenco": [
                {"pid": i["pid"], "nome": nome,
                 "time": lado_time.get(i["lado"], ""),
                 "gk": sem_acento(i["posicao"]).startswith("gol")}
                for nome, i in elenco.items()
            ],
            "eventos": eventos,
        }
    return fora


def eh_gol_solto(texto):
    """Gol registrado sem chutador na coluna Chutes — some da conta se ignorar."""
    t = sem_acento(texto)
    return t.startswith("gol ") and "anulad" not in t
