# Como adicionar um clipe ao seu perfil

Um clipe é um lance seu num vídeo de jogo: um gol, uma defesa, uma jogada. Ele
aparece em **Melhores momentos**, no seu perfil do site. Clicando nele, o vídeo
abre no YouTube já no segundo do lance.

**Não precisa cortar vídeo nenhum.** É uma linha na planilha.

## Antes de tudo: acesso à planilha

Para adicionar, você precisa poder **editar** a planilha da copa. Quem libera é
o dono da planilha. Peça no grupo.

## Passo a passo

### 1. Ache o lance no vídeo

Os vídeos dos jogos estão na aba **Vídeos** do site. Abra o vídeo no YouTube e
**pause no começo do lance**. Anote o tempo que aparece na barra do vídeo — por
exemplo, `12:34`.

Se quiser, anote também onde o lance acaba.

### 2. Copie o link do vídeo

No YouTube: **Compartilhar › Copiar**. Serve o link do jeito que vier, inteiro.

### 3. Descubra o seu id

O site identifica cada jogador por um **id**, que nem sempre é o apelido. Está
na coluna `id` da aba **JOGADORES**. Exemplos: `zaga`, `leo`, `pairobson`
(o Mauro).

Use o id exatamente como está lá, em minúsculas.

### 4. Preencha uma linha na aba CLIPES

Numa linha vazia, **abaixo das linhas de EXEMPLO**:

| coluna | o que escrever | exemplo |
|---|---|---|
| `jogador_id` | o seu id | `zaga` |
| `titulo` | uma frase curta sobre o lance | `Gol de cabeça no fim` |
| `video_youtube` | o link que você copiou | `https://youtu.be/giYKafoWa7U` |
| `inicio_seg` | quando o lance começa | `12:34` |
| `fim_seg` | quando acaba (opcional) | `12:48` |
| `temporada` | o ano do jogo | `2026` |

O tempo pode ir como `12:34`, como `1:02:03` (vídeo com mais de uma hora) ou
em segundos (`754`).

As linhas que começam com `EXEMPLO` são só modelo e o site ignora.

### 5. Espere a próxima atualização

O site se atualiza sozinho **algumas vezes por dia**. O clipe aparece na
próxima atualização, não na hora.

Para saber quando foi a última, olhe o **selo no canto inferior esquerdo** do
site: ele mostra a data e a hora em que a planilha foi lida.

## Se o clipe não aparecer

| O que aconteceu | Por quê | Como resolver |
|---|---|---|
| Não aparece em lugar nenhum | a atualização ainda não passou | veja a hora no selo do canto |
| Não aparece no seu perfil | o id está errado — foi o apelido no lugar do id | copie o id da aba JOGADORES |
| O vídeo abre no começo | o tempo não foi entendido | escreva `12:34`, com dois pontos |
| O `12:34` virou `12:34:00` na célula | a planilha achou que era uma hora do dia | ver abaixo |

## Uma vez só, para quem administra a planilha

O Google Sheets transforma `12:34` digitado numa célula em **hora do dia**
(meio-dia e trinta e quatro), e o tempo do clipe se perde no caminho.

Para evitar: na aba **CLIPES**, selecione as colunas **D e E** (`inicio_seg` e
`fim_seg`) e vá em **Formatar › Número › Texto simples**. Feito isso uma vez,
qualquer um digita `12:34` e fica `12:34`.

Até isso ser feito, dá para escrever o tempo em segundos (`754`) ou com um
apóstrofo na frente (`'12:34`).

## Outras coisas que vocês podem preencher

Tudo na planilha, do mesmo jeito:

- **Apelido de perfil** — aba JOGADORES, coluna `Apelido Perfil`: o apelido de
  zoeira que aparece em destaque no perfil.
- **Número da camisa** e **posição** — aba JOGADORES.
- **Nota de desempenho** de 1 a 5 em cada time por onde você passou — aba
  DESEMPENHO.

A lista completa do que ainda falta está em `PENDENCIAS.md`.
