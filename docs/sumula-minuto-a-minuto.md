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
Maurinho,Robson,Preto,Linha
```

A coluna `apelido` é a ponte quando o nome anotado não é o que está na aba
JOGADORES: `Meme` é o Merizi, e `Maurinho` era como quem anotou chamou o
Robson. Sem ela, o build avisa e os lances daquela pessoa ficam fora da conta
individual.

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

## Levar os gráficos para o vídeo

O Estúdio tem três artes que saem da mesma súmula, no grupo **Estatísticas do
jogo**:

| arte | o que é |
|---|---|
| Comparativo do jogo | as barras espelhadas, número contra número |
| Corrida de chutes — animada | o gráfico se desenhando na velocidade do jogo |
| Quem mais apareceu | os seis que mais finalizaram ou defenderam |
| Desempenho de um jogador | a ficha de uma pessoa só, com o que ela fez no jogo |
| Elenco do time | todos os números de todo o elenco, ninguém de fora |

E três peças de encerramento, no grupo **Fim de vídeo**, que não dependem de
súmula para existir:

| arte | o que é |
|---|---|
| Premiação | um troféu e quem levou |
| Campeão | escudo grande e o elenco inteiro |
| Próxima partida | chamada de tela cheia, sem data |

No **Elenco do time**, quem não finalizou aparece igual, com a linha zerada.
Jogador ausente da peça parece esquecimento; zero é informação. O goleiro
encabeça a lista e recebe defesas em vez de chutes.

A **Premiação** usa o mesmo desenho de troféu da tela de Troféus, virado em
imagem — assim a peça de vídeo nunca diverge do site.

A **Próxima partida** é a única arte que pinta a tela toda, de propósito: não é
sobreposição e sim um trecho do vídeo. Exportada em MP4 vira um clipe comum, e
não há chroma a fazer.

Cada uma tem dois campos próprios: **Jogo** (a mesma lista da aba
Estatísticas — súmula nova aparece nos dois lugares sozinha) e **Momento**:
jogo todo, só o 1º tempo, só o 2º, ou **até o minuto** que você digitar.

O corte vem de `SUMULA.recorte()`, o mesmo que a aba usa. Isso é de propósito:
se cada lado tivesse a própria conta, a arte exportada diria um número e o
site diria outro.

Na **Corrida de chutes** o tempo da animação É o tempo do jogo, e o placar do
cabeçalho acompanha. No 42' a peça mostra 0×1, porque o gol do Zaga só sai aos
63' — mostrar 1×1 desde o começo entregaria o final antes da hora.

No **Desempenho de um jogador** o jogador vem do mesmo seletor das outras
fichas. **Goleiro recebe caixas diferentes**: chute e precisão não descrevem
goleiro, então entram defesas, gols sofridos, finalizações sofridas e quanto
por cento ele segurou. Quem é goleiro sai do `posicao` do CSV, não da contagem
de defesas — goleiro que passou o jogo sem trabalho continua sendo goleiro, e
a ficha dele mostra "0 defesas" em vez de virar ficha de jogador de linha.

Os botões de download são os mesmos das outras artes:

- **PNG** — quadro parado, com fundo transparente.
- **MP4** — animado, H.264 sobre fundo verde. **É o formato para o DaVinci.**
- **WebM** — animado, VP9 sobre fundo verde.
- **Sequência PNG (.zip)** — um arquivo por quadro, sem compressão.

## Por que MP4 e não WebM

O Resolve no Windows não traz decodificador de VP9, que é o que o navegador
usa no WebM. O arquivo fica íntegro no disco e mesmo assim a renderização
falha com "could not be decoded correctly".

A gravação conta os quadros antes de entregar o arquivo: são `duração x fps`,
e cada quadro é pedido explicitamente ao codificador com `requestFrame()`. Se
algum não entrar, o download é recusado com a contagem no lugar de sair um
arquivo pela metade.

**Mantenha a janela do navegador em primeiro plano durante a gravação.** Em
segundo plano o Chrome limita os temporizadores a cerca de um disparo por
segundo; o arquivo sai completo, mas mais longo do que deveria — e o app avisa,
com o fps real medido. Nesse caso dá para interpretar o clipe no fps certo
dentro do Resolve, ou regravar com a janela à frente.

Para quadro exato garantido, sem depender de nada disso, a **sequência PNG** é
o caminho: um arquivo por quadro, sem compressão temporal.

Essas três artes **não usam verde em lugar nenhum**, nem na prévia. Cor de time
passa por `corSegura()`, então time de camisa verde vira azul de brilho
equivalente em vez de sumir no chroma.
