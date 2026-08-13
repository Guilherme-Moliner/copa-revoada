# Copa Revoada — o que falta para o app ficar pronto

Estamos montando um site da copa: perfil de cada jogador, histórico de todos os
times e temporadas, e um estúdio que gera as artes da transmissão.
O esqueleto já está de pé com os dados que estavam na planilha antiga.
O que falta é quase tudo dado, não código — e é aí que preciso de vocês.

**Meta:** no ar antes da próxima live.

---

## 1. Dados (o gargalo)

Tudo entra pela planilha `COPA_REVOADA_planilha.xlsx`. Célula amarela é o que falta.

| # | Tarefa | Onde | Responsável | Prazo |
|---|---|---|---|---|
| 1.1 | Conferir os 33 apelidos e completar nome, posição e número | aba JOGADORES | | |
| 1.2 | Resolver 3 divergências de datas e placares (listadas na aba LEIA-ME) | aba JOGOS | | |
| 1.3 | Confirmar o nome oficial de cada time por temporada e as cores | aba TIMES | | |
| 1.4 | **Lançar escalação de cada jogo: quem jogou, em que time, gols e assistências** | aba ESCALACOES | | |
| 1.5 | Marcar o time campeão de cada jogo | aba JOGOS, coluna `campeao_time_id` | | |
| 1.6 | Lançar os troféus já entregues por ano, incluindo a piroquinha | aba TROFEUS | | |
| 1.7 | Colar o ID do YouTube de cada partida | aba JOGOS, coluna `video_youtube` | | |

> **A 1.4 é a mais importante e a mais chata.** Sem ela o app só mostra o total
> acumulado de cada um — não dá pra saber em que time alguém jogou, nem quantos
> gols fez em 2023. Com ela, tudo o resto se calcula sozinho.
>
> Sugestão: dividir por temporada, uma pessoa por ano. Quem lembra melhor de 2022
> pega 2022. A aba **CONFERE** avisa quando os gols lançados não batem com o placar.

## 2. Imagens

| # | Tarefa | Detalhe | Responsável | Prazo |
|---|---|---|---|---|
| 2.1 | Uma foto por jogador | JPG quadrado, 600×600, rosto centralizado. Nome do arquivo = id da planilha (`fanta.jpg`) | | |
| 2.2 | Foto de quem não temos | pedir no grupo, ou tirar um retrato no próximo jogo | | |
| 2.3 | Escudo de cada time | hoje são gerados automaticamente pelas cores. Se alguém quiser desenhar os de verdade, melhor ainda | | |
| 2.4 | Garimpar o Instagram @coparevoada | imagens antigas, artes de convocação, prints de premiação | | |

## 3. Vídeo

| # | Tarefa | Detalhe | Responsável | Prazo |
|---|---|---|---|---|
| 3.1 | Conferir se todos os jogos estão na playlist do YouTube | 9 vídeos hoje, 12 partidas registradas | | |
| 3.2 | Indicar melhores momentos | **não precisa cortar nada.** Só mandar: nome do jogador + link do jogo + minuto do lance | | |
| 3.3 | Escolher um lance por jogador para a estreia | pelo menos os que têm mais jogos | | |

> O pedido para o grupo grande é só o 3.2, e cabe numa mensagem:
> *"Manda aí o link do jogo e o minuto do teu melhor lance que a gente coloca no teu perfil."*

## 4. Memória da copa (quem quiser garimpar)

| # | Tarefa | Responsável | Prazo |
|---|---|---|---|
| 4.1 | Levantar a história dos nomes dos times ano a ano | | |
| 4.2 | Escrever a origem da piroquinha e de cada troféu | | |
| 4.3 | Listar recordes de zoeira: maior goleada, jejum mais longo, frango do ano | | |
| 4.4 | Definir se o app fica público ou só com o link | | |

## 5. Publicação

| # | Tarefa | Responsável | Prazo |
|---|---|---|---|
| 5.1 | Subir no GitHub Pages e gerar o link | | |
| 5.2 | Rodar um teste: abrir no celular de três pessoas diferentes | | |
| 5.3 | Ensaiar a abertura do app durante a live | | |

---

## O que já está pronto

- Menu inicial estilo jogo de futebol antigo, navegável por teclado
- Seleção de jogador estilo tela de personagem, com os 33 do ranking
- Seleção de time no formato Team Select, comparando os dois times da temporada lado a lado
- Livro de recordes: presença, artilharia, garçons, títulos e participações
- Aba de vídeos com a playlist embutida
- Estúdio com 7 artes: gol em barra, gol em tela cheia, replay, escalação animada,
  substituição, ficha do jogador e cartão — todas exportam PNG, sequência animada
  com fundo transparente, ou WebM em fundo verde

## Como você ajuda mais rápido

Se for pegar uma coisa só, pegue **uma temporada da aba ESCALACOES**.
É o que destrava a maior parte do app.
