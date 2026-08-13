# Pendências — Copa Revoada

Gerado a partir de `COPA_REVOADA.xlsx` (versão de agosto/2026).
A mesma lista está na aba **PENDENCIAS** da planilha, com coluna pra marcar quem pegou.

O que já entrou sozinho: **13 jogos**, **45 jogadores**, **233 escalações** e
**14 times** em 7 temporadas. As escalações estavam espalhadas pela aba Dados da
planilha antiga e foram extraídas jogo a jogo. Oito jogos fecharam certinho com o
placar; o resto está aqui embaixo.

---

## Prioridade 1 — gols que não batem com o placar

| Jogo | Situação |
|---|---|
| Dez/2020 · Chelsea 6×7 PSG | a planilha guardou só quem jogou, sem gol por jogador |
| Jul/2021 · Chelsea 10×10 PSG | idem |
| Dez/2021 · Chelsea 6×9 PSG | idem |
| Dez/2024 · Branco 5×3 Preto | lançados 7 gols, o placar soma 8 — falta 1 |
| Ago/2026 · Dentro FC 1×1 Ferroviagra | lançados 3 gols, o placar soma 2 — sobra 1 |

Enquanto os três primeiros não tiverem gol por jogador, o total individual de gols
e assistências continua vindo do ranking antigo em vez de sair das escalações.
Não quebra nada, mas são duas fontes de verdade convivendo.

A aba **CONFERE** da planilha mostra isso jogo a jogo e atualiza sozinha conforme
vocês preenchem.

## Prioridade 2 — de que lado cada time estava

Em dois jogos o placar empatou, então não dá pra deduzir automaticamente qual
escalação era de qual time. Chutei uma ordem; confirmem na aba ESCALACOES:

- **Ago/2022 · Liverpool 1×1 Borussia**
- **Jun/2023 · Boca 0×0 City**

## Prioridade 3 — nomes que podem ser a mesma pessoa

Cada linha virou um jogador diferente no site. Se for a mesma pessoa, digam qual
`id` fica e eu unifico:

| Variantes | Observação |
|---|---|
| `derek` · `dereck` · `dereka` · `minidereck` | quatro grafias, aparecem em anos diferentes |
| `bernardoc` · `bernardom` · `berna` | Bernardo C, Bernardo M e Berna |
| `vitim` · `vitor` | Vitim só aparece em 2020–2021; Vitor só no ranking |
| `robson` · `pairobson` | Robson e Pai Robson, ambos em Ago/2026 |

Já unifiquei sozinho, por serem claramente a mesma pessoa:
`Garopa`→`Garopaba`, `Felps`→`Phelps`, `Andre`/`André`, e todos os `GK` no fim do
apelido (`Arthur gk`→`arthur`, `Merizi GK`→`merizi`).

## Prioridade 4 — gente que joga mas não está no ranking

Aparecem nas escalações e não constam no RANKING Atual. Precisam de apelido
oficial e confirmação de que existem mesmo:

`Berna` · `Bernardo C` · `Bernardo M` · `Dereck` · `Derek` · `Dereka` ·
`Gordo` · `Mito` · `Pai Robson` · `Robson` · `Vitim`

## Prioridade 5 — a contagem de jogos não fecha

As escalações dão mais jogos por pessoa do que o RANKING Atual. Provavelmente o
ranking não foi atualizado com todos os jogos, mas vale conferir se algum nome não
foi lançado a mais em alguma partida:

| Jogador | Escalações | Ranking |
|---|---|---|
| Fanta | 13 | 10 |
| Letti | 13 | 10 |
| Nathan | 13 | 10 |
| Leo | 13 | 8 |
| André | 11 | 8 |
| Borba | 11 | 7 |
| Hanon | 11 | 7 |
| Zaga | 8 | 5 |
| Danilim | 8 | 5 |
| Phelps | 8 | 4 |
| Pietro | 7 | 4 |
| Vitor | 0 | 3 |

O site hoje usa a contagem das escalações, que é a mais detalhada.

---

## O que continua faltando (não é erro, é material que ninguém mandou ainda)

| O quê | Onde entra | Quem |
|---|---|---|
| Nome completo e posição de cada um dos 45 | aba JOGADORES | |
| Time campeão de cada jogo | aba JOGOS, `campeao_time_id` | |
| ID do YouTube de cada partida | aba JOGOS, `video_youtube` | |
| Troféus entregues por ano, inclusive a piroquinha | aba TROFEUS | |
| Melhores momentos: jogador + vídeo + minuto | aba CLIPES | |
| Foto de cada jogador | pasta `fotos/`, arquivo com o nome do id | |
| Nota 1 a 5 de cada um por jogo (o rostinho) | aba ESCALACOES, `nota_1a5` | |
| Cores e escudos oficiais dos times | aba TIMES | |

## Coisas que eu chutei e você precisa confirmar

- **Nomes dos times por temporada.** Usei o que estava na planilha: Chelsea×PSG
  (2020 e 2021), Liverpool×Borussia (2022), Boca×City (2023), Branco×Preto (2024),
  Milan Be×Jumentus (2025), Dentro FC×Ferroviagra (2026).
- **Cores de cada time.** Deduzidas do nome. São elas que desenham o escudo no site.
- **Estádio.** Onde faltava, coloquei Paula Ramos.
- **Quem é goleiro.** Marquei GOL em quem tinha "GK" no apelido.

---

## Como aplicar as correções

Edite `dados/COPA_REVOADA_planilha.xlsx` e rode:

```bash
python3 scripts/build.py
```

O script reclama do que ainda estiver inconsistente. Quando o `git push` acontecer,
o site republica sozinho.
