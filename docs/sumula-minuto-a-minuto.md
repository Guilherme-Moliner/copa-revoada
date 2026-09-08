# Súmula minuto a minuto — a tela de Estatísticas

A aba **Estatísticas** mostra um jogo lance a lance: chutes, defesas,
escanteios, faltas e cagadas, cada um com o segundo em que aconteceu. Dá para
arrastar o controle e ver como estava o jogo **até qualquer minuto**, ou olhar
só um dos tempos.

Hoje só **Ago/2026 (Dentro FC × Ferroviagra)** tem súmula. Qualquer outro jogo
entra na tela no dia em que alguém anotar os lances.

## Como adicionar um jogo

Dois arquivos em `dados/sumulas/`, com o id do jogo no nome:

```
dados/sumulas/2026-08-lances.csv
dados/sumulas/2026-08-jogadores.csv
```

### `<jogo>-jogadores.csv`

Quem jogou de que lado. O `time` aqui é o apelido usado na hora ("Branco",
"Preto") — o build descobre sozinho a qual time da planilha cada lado
corresponde, contando quantos jogadores de cada lado aparecem na escalação
daquele jogo e ficando com o mais votado.

```csv
jogador,apelido,time,posicao
Arthur,,Branco,Goleiro
Zaga,,Branco,Linha
Merizi,Meme,Preto,Goleiro
```

A coluna `posicao` só precisa distinguir **Goleiro** de **Linha**: é ela que
diz quem leva o crédito das defesas.

### `<jogo>-lances.csv`

Um lance por linha.

| coluna | o que vai |
|---|---|
| `Hora`,`Minuto`,`Segundo` | quando aconteceu (a `Hora` vira 01 depois dos 60 min) |
| `lance` | o texto livre, do jeito que foi anotado |
| `obs` | `Escanteio` quando o lance gerou um |
| `Chutes` | quem chutou |
| `Defesas` | **o time do goleiro que defendeu** — ou seja, o chute foi do outro |
| `Escanteios` | o time que ganhou o escanteio |
| `Faltas` | quem cometeu |
| `Cagadas` | quem fez |

## Como o texto vira estatística

As regras saíram do `analise_jogo.py` que veio com os dados, de propósito: os
números da tela têm que bater com o PDF e o explorador que já circularam no
grupo. Conferido — batem em todas as categorias.

| classificação | regra |
|---|---|
| bloqueado | a palavra `bloq` aparece no texto |
| gol | o texto **começa** com `Gol ` |
| gol anulado | contém `anulad` — **não** conta como gol |
| no gol | gerou defesa, ou foi gol |
| precisão | no gol ÷ (chutes − bloqueados) |

Chute bloqueado fica fora da conta de precisão porque morreu na canela de
alguém: não diz nada sobre a mira de quem chutou.

O marcador de intervalo é qualquer lance com `2T` no texto. Sem ele, os botões
de 1º e 2º tempo ficam desligados e só sobra o jogo inteiro.

## Nome que não bate

Quem anota no calor do jogo abrevia. O de‑para vive em `ALIASES`, dentro de
`scripts/sumula.py`:

```python
ALIASES = {"garopa": "Garopaba", "meme": "Merizi"}
```

Nome que não bate com ninguém da aba JOGADORES vira **aviso no build**. O lance
continua contando para o time — senão o total do jogo ficaria errado — mas fica
fora da conta individual daquela pessoa, porque não dá para saber de quem é.

## Onde as contas acontecem

O build só **traduz**: lê os CSVs, liga cada nome ao id da planilha, descobre os
times e joga a lista crua de eventos dentro do `index.html`.

Quem soma é o navegador. É isso que deixa o controle de tempo deslizar sem
recarregar nada — e "até o minuto X" é uma pergunta que só faz sentido sendo
interativa.
