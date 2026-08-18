# Pendências — Copa Revoada

Lista de trabalho para fechar os dados da copa. O que estiver aqui **não** foi
preenchido por conta própria: célula vazia é célula que precisa de decisão de
vocês.

Site: https://guilherme-moliner.github.io/copa-revoada/

**Como preencher:** editem `dados/COPA_REVOADA_planilha.xlsx` (ou a versão no
Google Sheets, se já tiver migrado — veja `CONTINUAR-EM-OUTRO-PC.md`) e rodem
`python scripts/build.py`. O build reclama do que ainda estiver inconsistente.
Quando o push acontecer, o site republica sozinho.

Estado de hoje: **32 jogadores · 14 times · 13 jogos · 233 escalações**.

---

## Prioridade 0 — resolvido: o site já lê a planilha do Drive

O Apps Script foi republicado e a variável `PLANILHA_URL` está apontada para
ele. O build baixa as 11 abas a cada publicação, e o `.xlsx` do repositório
virou cópia de segurança: ele só entra se o endpoint falhar, e nesse caso o
build avisa e segue.

Editem no Google Sheets. O que aparece no site é o que estiver lá.

As abas `LANCES *` e a `CONFIG` ficam fora desse JSON de propósito: as
primeiras podem crescer muito, e a segunda guarda a chave.

---

## Prioridade 1 — as duas decisões que travam número no site

### 1.1 Ago/2026: qual Leo?

Na aba ESCALACOES, o `leo` aparece **nos dois times** do mesmo jogo:

| jogo_id | jogador_id | time_id | gols |
|---|---|---|---|
| 2026-08 | leo | ferroviagra26 | 1 |
| 2026-08 | leo | dentro26 | 0 |

Em **Abr/2026** vocês já resolveram assim: o do Ferroviagra era o **Leo
Bittencourt**, e o do Dentro é o **Leonardo Zanette**. Falta dizer se em Ago/2026
vale a mesma regra.

**Por que importa:** é justamente nessa linha que está o **gol do VAR**, com
assistência do Zaga. Dependendo da resposta, o gol muda de dono.

> **Ação:** trocar o `jogador_id` da linha certa para `leobittencourt`, ou
> confirmar que os dois são o Leonardo Zanette mesmo.

### 1.2 Campeão — faltam 2 de 13

Preenchidos 11. Continuam vazios **Dez/2020** e **Jul/2021**. O primeiro
terminou 6×7 e o segundo 10×10 — num empate, campeão vazio é a resposta certa;
se teve decisão por pênalti, é só dizer quem levou.

### 1.2b Como isso entra no site

**Nenhum dos 13 jogos** tem `campeao_time_id` preenchido na aba JOGOS.

Hoje o título de cada jogador sai da coluna `campeao` (SIM/NAO) da aba
ESCALACOES, que veio da importação. A coluna da aba JOGOS existe e está vazia —
preenchendo, o site passa a mostrar o campeão na tela de cada jogo.

Lembrete do que já foi decidido: **Ago/2022 (Liverpool 1×1 Borussia) não teve
título**, porque não houve penalidades.

---

## Prioridade 2 — o que dá mais resultado por hora gasta

### 2.1 Números de camisa — 31 de 32 vazios

Aba **JOGADORES**, coluna `numero_camisa`.

Enquanto estiver vazio, o Estúdio usa a ordem da lista no lugar do número. Com
os números, a escalação, a formação no campo e a chamada do batedor ficam com o
número certo de cada um.

### 2.2 Posição — 28 de 32 vazios

Aba **JOGADORES**, coluna `posicao`. Valores: `GOL`, `DEF`, `MEI`, `ATA`.

Já marcados como goleiro: **Arthur, Merizi, Be Correa e Be Marucco**.

É o que faz a formação no campo posicionar cada um na faixa certa e a lista
mostrar a tarja colorida por posição.

### 2.3 Vídeos — 8 de 13 preenchidos

Aba **JOGOS**, coluna do link do YouTube. Pode colar a **URL inteira**: o build
extrai o id sozinho, e aceita link normal, `youtu.be`, `embed` e `shorts`.

A aba VIDEOS que eu tinha criado **não é mais usada** — o link ao lado do jogo
é mais simples e não duplica informação. A aba CLIPES continua valendo, porque
ela guarda outra coisa: recorte de melhor momento por jogador.

Faltam **Dez/2020, Jul/2021, Out/2023, Abr/2026 e Ago/2026**.

### 2.4 Nota de desempenho por time — 155 pares esperando

Aba **DESEMPENHO**, coluna `nota_1a5`. Uma linha por jogador por time, já
montadas: é só dar a nota.

| nota | significa |
|---|---|
| 1 | apagado |
| 2 | abaixo |
| 3 | normal |
| 4 | bom |
| 5 | inspirado |

É o rostinho que aparece na página do time. Enquanto estiver vazio, o site mostra
um rosto deduzido da produção, apagado, avisando no hover que ainda não foi
julgado.

---

## Prioridade 3 — material que falta

| O quê | Onde | Quanto falta |
|---|---|---|
| Nome completo | aba JOGADORES, `nome_completo` | 31 de 32 |
| Foto de jogador | `assets/<id>.jpg` | 2: **Mauro e Robson**, por opção de vocês |
| Escudo de time | `assets/`, ou coluna `escudo_arquivo` | 2: **Chelsea 2020 e Chelsea 2021** |
| Troféus entregues por ano | aba TROFEUS | tudo, fora os simulados do Fanta |
| Melhores momentos | aba CLIPES | tudo |

Mauro e Robson seguem sem foto por escolha de vocês. Em vez das iniciais, os
dois aparecem com a silhueta de `assets/semperfil.jpeg`, na mesma moldura dos
outros — o perfil não fica com cara de cadastro incompleto.

### Coisas para conferir nas imagens

- **`jogo1-2026.jpg` e `vencedorjogo12026.jpg`** estão em `assets/` sem uso. Se
  quiserem, dá para fazer uma galeria por jogo.

---

## O que já foi decidido e está aplicado

Nada aqui precisa de ação. É registro, para ninguém refazer discussão.

### Contagem de jogos

Os três primeiros jogos (**Dez/2020, Jul/2021, Dez/2021**) contam **só título** —
ninguém anotou gol nem assistência por jogador neles. Por isso o perfil mostra
*Jogos válidos* (10) e *Presenças* (13).

Isso zerou a divergência com o ranking antigo: dos 12 nomes que não batiam,
sobrou zero.

### Gols que não fechavam com o placar

| Jogo | Resolução |
|---|---|
| Dez/2024 · Branco 5×3 Preto | gol contra do Leo, que jogava no Preto |
| Ago/2026 · Dentro 1×1 Ferroviagra | gol do VAR pro Leo, assistência do Zaga, fora do placar |

Duas colunas novas na aba ESCALACOES guardam isso:

- `gols_contra` — vai pro placar do adversário e **não** entra no total de quem fez;
- `conta_no_placar` — `NAO` quando o gol não vale para o resultado.

O build **confere sozinho** placar contra gols lançados, jogo a jogo. Dez jogos
conferidos, todos fechando.

### Quem é quem

Unificados: **Be / Be Correa / Bernardo C** → Be Correa (goleiro) ·
**Be Marucco / Bernardo M** → Be Marucco (goleiro) · **Vitim** → Kretzer ·
**Gordo** → Vitor · **Mito** → Berna · **Dedé** → André.

Renomeados: *Arthur gk* → **Arthur** · *Merizi GK* → **Merizi** ·
*Pai Robson* → **Mauro**.

Escondidos do site, mantidos na planilha (constante `EXCLUIR_DO_SITE` no build):
**Derek, Davi, Dereck, Matheus, Luigi, Dereka, João, Mini Derek**.

> **Derek, Mini Derek e Dereck não foram unificados de propósito.** Em Dez/2020 o
> `derek` jogou pelo Chelsea e o `miniderek` pelo PSG; em Abr/2022 o `dereck`
> jogou pelo Borussia e o `derek` pelo Liverpool. Quem se enfrenta não é a mesma
> pessoa. Pela linha do tempo, `miniderek` (2020–21) e `dereck` (2022–23) nunca
> coincidem e provavelmente são a mesma pessoa. Como todos foram escondidos, isso
> deixou de ser urgente — mas fica registrado se um dia quiserem trazer de volta.

### Escudos e nomes de time

Resolvido: `borussetalogo.png` agora traz o BVB de verdade, e chegaram os
escudos do **Boca**, do **Mano Cityfodo** e do **Peguei Sua Gata**. PSG 2020 e
2021 usam o mesmo. **Branco 2024 virou DBOAFC** e **Preto 2024 virou CRISEUMA**.

Quem manda no escudo é a coluna `escudo_arquivo` da aba TIMES; o de‑para dentro
do `build.py` só entra quando a célula está vazia.

### Times por temporada

Chelsea×PSG (2020 e 2021), Liverpool×Borussia (2022), Boca×City (2023),
Branco×Preto (2024), Milan Be×Jumentus (2025), Dentro FC×Ferroviagra (2026).

Confirmados por vocês: **Criseúma FC** é o time preto de 2024, **D Boa FC** o
branco de 2024, e **Peguei Sua Gata** é o PSG de 2020 e 2021.

O ano deixou de aparecer junto do nome do time nas telas e nas artes.

### Coisas que continuam sendo chute meu

- **Cores de cada time**, deduzidas do nome. São elas que desenham o escudo
  quando não há arquivo, e a faixa colorida nas artes.
- **Estádio**: onde faltava, coloquei Paula Ramos.

---

## Para quem vai editar vídeo

Duas limitações que valem saber antes de montar a timeline:

1. **Cinco fotos foram tiradas contra parede verde** — Garopaba, Borba, Bala,
   Leo Godinho e Vitor. Em qualquer arte que mostre essas fotos, **não use o WebM
   verde**: o Chroma Key vai comer o fundo da foto junto com o fundo da tela. Use
   a **sequência PNG**, que tem alpha de verdade.
2. **Três escudos** — Criseúma, D Boa e Jumentus — são desenho claro sobre fundo
   claro, e o build não consegue tirar o fundo sem comer o escudo junto. Se
   quiserem transparência neles, subam o PNG já recortado.

Fora esses casos, o Estúdio já gera tudo **sem nenhum verde dentro da arte**
quando o fundo verde está ligado — inclusive trocando a cor do Dentro FC, que é
verde, por um azul de brilho equivalente.

---

## Estúdio — o que o feedback pediu e ainda não entrou

O grosso do feedback já está no ar: o verde saiu de 24 das 26 artes, entrou o
toggle amarelo/azul, o Dentro FC deixou de ser verde na aba TIMES, e os ajustes
de texto, escudo e layout foram aplicados. Continua aberto:

| item | o que falta |
|---|---|
| Ficha do jogador | modo de comparação, dois jogadores lado a lado, um em amarelo e outro em azul |
| Marco da copinha | animação em sequência passando por temporadas, jogos, gols e artilheiro, terminando na foto do Garopaba |
| Chance de gol | trocar os círculos pelas fotos dos jogadores e animar a entrada das peças |
| Mapa tático | botões de salvar e carregar na planilha |
| Análise do jogo | chave de administração e gravação dos lances na planilha |
| Tela Análise Tática | mover Mapa tático, Chance de gol e Análise do jogo do Estúdio para tela própria |

## Onde o verde ainda existe, de propósito

**Formação no campo** e **Chance de gol** mantêm o gramado verde, como combinado.
Se um dia precisar exportar essas duas em WebM verde, ligue o **fundo verde** no
Estúdio antes: o verde delas também sai.

Fora isso, cinco fotos de jogador foram tiradas contra parede verde — Garopaba,
Borba, Bala, Leo Godinho e Vitor. Isso nenhuma paleta resolve: em arte que mostre
essas fotos, use a sequência PNG em vez do WebM verde.
