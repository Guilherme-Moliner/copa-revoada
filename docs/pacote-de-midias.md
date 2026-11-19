# Pacote de mídias

O jogo é marcado uma vez no Registro, e o app planeja e gera **a edição
gráfica inteira**: cada peça, quando entra, quanto dura e em que camada. Um
script dentro do DaVinci importa tudo e posiciona na timeline.

Estado em 19/11/2026: **Fase 1 do briefing "planejamento das peças no portal"
implementada**. O plano é desenhado no Registro e o gerador executa exatamente
esse plano. Falta a importação real no DaVinci da bateria completa. A Fase 2
(código da arte, ficha do jogo com IA) é só proposta:
`docs/proposta-fase-2-codigo-da-arte.md`.

**O DaVinci não lê o `.json`.** O arquivo de lances é do gerador. O DaVinci
recebe os `.mov` e `.png` prontos e o `manifesto.tsv`, que o script lê para
pôr cada peça no lugar.

## Como funciona

```
Registro (lances + plano) ──Baixar lances──▶ lances-<jogo>.json (formato 2)
                                                   │  Gerar pacote de midias.bat
                                                   ▼
             o gerador abre o próprio site, pede PACOTE.planeja(...) e desenha
             cada peça com o código do Estúdio, quadro a quadro
                                                   ▼
                         midias/<jogo>/  (.mov, .png, manifesto.tsv)
                                                   │  DaVinci: Workspace › Scripts ›
                                                   ▼  Copa Revoada - importar pacote
                         peças nas trilhas, da V4 para cima
```

**Um cálculo só.** O plano é a função `PACOTE.planeja`, dentro do site
(`src/app.template.html`). O Registro a chama para desenhar o plano; o
gerador (`scripts/pacote.py`) abre o site num Chromium sem janela e chama a
mesma função. Não há uma segunda versão do plano em Python que possa
divergir.

## Como usar, do jogo à timeline

1. **Registro**: escolha o jogo, ou **＋ Novo jogo avulso** para um fut que não
   entra na planilha. Cole o link da prévia, **Carregar vídeo**, e marque.
2. Embaixo do Registro fica o **Plano da edição**: uma faixa por camada, cada
   peça um bloco. Clicar num bloco leva o vídeo até ela e abre o editor
   (início, duração, desligar, voltar ao automático). **＋ Peça** põe uma arte
   à mão no tempo atual do vídeo.
3. **Baixar lances**: sai `lances-<jogo>.json` com os lances **e o plano**
   (ajustes e peças à mão). **Abrir arquivo** carrega o que outra pessoa
   marcou.
4. **Gerar o pacote**: dois cliques em **`Gerar pacote de midias.bat`**. Ele
   pega o `lances-*.json` mais novo da pasta Downloads (ou arraste um arquivo
   para cima do `.bat`). No fim ele lista as peças geradas, as que esperaram
   na fila, as de fora e o motivo, e quanto tempo levou.
5. **No DaVinci**, com o projeto e a timeline abertos: *Workspace › Scripts ›
   Copa Revoada - importar pacote*. O resumo, com o tempo da importação,
   aparece em *Workspace › Console*.

O script do DaVinci entra no menu uma vez por computador, e de novo sempre
que o `.lua` mudar:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\davinci\instala.ps1
```

## Marcação no Registro

| Lance | Como marca | Vai junto |
|---|---|---|
| Gol | tipo **Gol**, depois quem fez | o clique seguinte no mesmo time é a **assistência** (ou "sem assistência") |
| Chute ao gol, chute pra fora, defesaça, cagada | tipo, depois quem fez | — |
| Cartão | tipo **Cartão**, escolhe **Amarelo / Vermelho**, depois quem levou | a cor |
| Substituição | tipo **Substituição**, clica em quem **sai**, depois em quem **entra** | quem saiu |
| Falta, escanteio | tipo, depois **Registrar** (vale para o time) | — |
| Replay | botão **▶ Início do replay** na coluna do jogo; o mesmo botão vira **■ Fim do replay** | o fim do replay |
| Fim do 1º tempo | botão **⏸ Fim do 1º tempo** na coluna do jogo | — (marcar de novo corrige) |

Replay e fim do 1º tempo usam o tempo atual do vídeo: precisam do vídeo
carregado.

**Limite conhecido:** a aba `LANCES` da planilha (Apps Script v2) guarda 8
colunas e **perde assistência, cor do cartão, quem saiu e o fim do replay**.
Jogo avulso não usa a planilha. Num jogo da copa, esses campos ficam no
navegador e no arquivo baixado; o Apps Script v3 da Fase 2 resolve.

## Camadas gráficas

**V1, V2 e V3 são das câmeras.** Os gráficos começam na V4, que é a camada
gráfica 1. **Cada tipo de peça tem a sua camada**; a mais alta fica por cima
no DaVinci, e as inserções que cobrem a tela inteira vão no topo. A conta
camada → trilha mora só em `dados/regras-pacote.json`
(`camadas.primeira_trilha`).

| Camada | Trilha | Peças |
|---|---|---|
| 1 · placar | V4 | placar fixo o jogo inteiro e placar com a animação do gol |
| 2 · barras de lance | V5 | barra de gol, defesaça, cagada e falta |
| 3 · cartão | V6 | cartão, com a cor |
| 4 · substituição | V7 | substituição |
| 5 · replay | V8 | selo de replay, do início ao fim do replay |
| 6 · GOL tela cheia | V9 | GOL em tela cheia |
| 7 · histórico de gols | V10 | histórico de gols na copa, depois da barra do gol |
| 8 · cartões do jogo | V11 | abertura, fim do 1º tempo, artilheiro, fim de jogo |
| 9 · estatísticas | V12 | comparativo, corrida de chutes, quem mais apareceu, desempenho, ranking de cagadas, ficha do jogador |
| 10 · tela cheia | V13 | análise do jogo (cobre a tela) |

Proteções nos dois lados: o gerador recusa `primeira_trilha` abaixo de 4, e o
script do DaVinci recusa qualquer peça abaixo da V4, diga o manifesto o que
disser.

A proposta de 5 camadas por região da tela (de 18/11) foi **descartada**: as
camadas são por tipo de peça, e a sobreposição é resolvida pela fila.

## A fila: nada em cima de nada

Duas peças **não aparecem juntas** se estão na mesma camada **ou se as áreas
que ocupam na tela se cruzam** — mesmo em camadas diferentes. A área de cada
arte foi **medida** desenhando a arte e lendo o canvas
(`dados/areas-artes.json`; refazer com `pacote.py mede-artes`).

- O placar não entra na conta de área: ele fica no ar o jogo inteiro, e as
  outras peças passam por cima dele. Só disputa a própria camada.
- **Os momentos do jogo têm hora marcada** e entram primeiro. Lances e peças
  à mão esperam por eles.
- A peça que chega com a área ocupada **espera** a outra sair. Se a espera
  passar de `espera_maxima` (8 s), ela **fica de fora**, com o motivo.
- No Registro: tracejado = esperou; riscado = de fora.

## O que entra no vídeo: `dados/regras-pacote.json`

**Por lance:**

| Lance | Peça | Camada | Entra | Dura |
|---|---|---|---|---|
| Gol | placar com a animação do gol | 1 | no lance | 5 s |
| Gol | GOL em tela cheia | 6 | no lance | 4 s |
| Gol | barra do gol (com a assistência) | 2 | 4 s depois | 6 s |
| Gol | histórico de gols na copa (só jogo da copa) | 7 | 10 s depois | 7 s |
| Defesaça | barra azul, com o contador ("2ª defesaça do jogo · 1ª de Fulano") | 2 | 1 s depois | 5 s |
| Cagada | barra marrom, com o contador | 2 | 1 s depois | 5 s |
| Falta | barra (**desligada**; só a bateria liga) | 2 | 1 s depois | 5 s |
| Cartão | cartão com a cor | 3 | 1 s depois | 5 s |
| Substituição | sai / entra | 4 | no lance | 6 s |
| Replay | selo de replay | 5 | no início | até o fim do replay |

**Por momento do jogo**, em sequência, uma peça depois da outra (quem fica
de fora não ocupa tempo):

| Momento | Peças, na ordem | Âncora |
|---|---|---|
| Abertura | placar de abertura (7 s) | 1 s depois do começo |
| Intervalo | fim do 1º tempo (7 s), comparativo do 1º tempo (9 s), análise do 1º tempo (8 s) | **terminam** no fim do 1º tempo marcado |
| Fim | comparativo (9 s), corrida de chutes (9 s), quem mais apareceu (9 s), ranking de cagadas (8 s), artilheiro (7 s), desempenho do artilheiro (9 s), fim de jogo (8 s) | **terminam** no fim do vídeo |

**À mão (＋ Peça):** ficha do jogador, desempenho de um jogador, histórico de
gols, comparativo, corrida de chutes, quem mais apareceu, ranking de cagadas,
análise do jogo, selo de replay.

**Quando a peça fica de fora (e o plano diz):**

- gol, barra, cartão, substituição sem jogador; jogador que não está no site;
- cartão sem cor; substituição sem quem saiu; replay sem o fim;
- estatísticas (comparativo, corrida, quem mais apareceu, desempenho) em jogo
  **sem súmula minuto a minuto** — hoje só Agosto/2026 tem;
- artilheiro e desempenho do artilheiro com empate ou gol sem jogador;
- histórico de gols em jogo que não conta para a copa;
- ranking de cagadas sem cagada com jogador;
- intervalo sem o fim do 1º tempo marcado;
- falta fora da bateria; peça desligada no plano.

**Guia de duração:** 1 s a mais do que parece bastar; mais ainda para peça
densa. Para mudar tempo, camada ou desligar uma peça para todos os jogos,
edite o `regras-pacote.json`. Para mudar só neste jogo, use o Plano no
Registro.

## O arquivo de lances, formato 2

`copa-revoada-lances/2` acrescenta ao formato 1: `sumula` (de que súmula saem
as estatísticas), `perfil` (ex.: `bateria`), `competicao` (texto do placar,
ex.: "BATERIA DE TESTE"), os campos novos de cada lance (`a`, `cor`, `sai`,
`fim`) e o `plano`:

```json
"plano": {
  "ajustes": { "gol-02/barra": {"seg": 3835, "dura": 7}, "falta-01/barra": {"off": true} },
  "manuais": [ {"id": "manual-lx3k", "peca": "stat", "seg": 150, "dura": 8, "jogador": "Zaga"} ]
}
```

O formato 1 continua sendo lido: é um formato 2 sem plano.

## Ferramentas de linha de comando

```powershell
.venv\Scripts\python.exe scripts\pacote.py gerar lances.json [--video jogo.mp4]
.venv\Scripts\python.exe scripts\pacote.py da-sumula 2026-08
.venv\Scripts\python.exe scripts\pacote.py bateria 2026-08 --video jogo.mp4
.venv\Scripts\python.exe scripts\pacote.py mede-artes
.venv\Scripts\python.exe scripts\pacote.py teste
```

- **`da-sumula`** converte a súmula em lances, sem inventar: gol (com a
  assistência lida do texto), chute, falta, escanteio, cagada, e o **fim do 1º
  tempo** (o marco 2T). Defesa comum de goleiro não vira defesaça.
- **`bateria`** gera lances DE TESTE com todas as artes da Fase 1, em três
  blocos (começo, meio, fim), com colisões de propósito: um gol durante a
  abertura, um cartão colado numa cagada, dois gols colados, um bloco
  encostado no intervalo e um gol no meio das estatísticas do fim. Perfil
  `bateria` (liga a falta), placar "BATERIA DE TESTE", estatísticas da súmula
  verdadeira do jogo.
- **`mede-artes`** mede de novo a área de cada arte.

### Instalar as ferramentas num computador novo

Tudo dentro da pasta do projeto, fora do Git (`ferramentas/` e `midias/`
estão no `.gitignore`):

- **ffmpeg**: baixar o "release essentials" em gyan.dev, conferir o SHA-256
  publicado ao lado e copiar só a pasta `bin` para `ferramentas\ffmpeg\`.
- **Playwright**: `.venv\Scripts\python.exe -m pip install playwright`
- **Chromium do Playwright**, dentro do projeto:

  ```powershell
  $env:PLAYWRIGHT_BROWSERS_PATH = 'C:\copa-revoada\ferramentas\ms-playwright'
  .venv\Scripts\python.exe -m playwright install chromium --only-shell
  ```

## O que o DaVinci já mostrou

- **19/11, Resolve 19.0 beta:** o script parou na linha 104 porque essa versão
  devolve listas com números misturados aos objetos. Corrigido: toda lista do
  Resolve passa por um filtro que só deixa objetos.
- **19/11, segunda rodada:** 16 de 18 peças no lugar certo. Os dois primeiros
  placares fixos não entraram: `placar-fixo-0x0.png` e `placar-fixo-0x1.png`
  terminam em número, e o DaVinci juntou os dois numa "sequência de imagens"
  com outro nome. Corrigido: todo arquivo termina em letra
  (`placar-0x1-fixo.png`) e o script acha o clipe também pelo caminho do
  arquivo. Imagem parada longa é emendada em pedaços pelo script — esperado.
- **Cagada parecia gol** na barra. Corrigido: barra de cagada marrom, de
  defesaça azul, as duas com contador; e o ranking de cagadas no fim.

---

*Daqui para baixo, o histórico das decisões, na ordem em que foram tomadas.*

## Camadas gráficas (18/11/2026, substituída)

**V1, V2 e V3 são das câmeras** (os replays usam vários ângulos). Os gráficos
começam na V4, que é a **camada gráfica 1**. Para quem edita, a conversa é
sempre por camada; a conta camada → trilha mora só em
`dados/regras-pacote.json` (`camadas.primeira_trilha`), para os outros
projetos reaproveitarem mudando um número.

| Camada | Trilha | O que vai |
|---|---|---|
| 1 · placar | V4 | placar fixo no canto e placar com a animação do gol |
| 2 · GOL tela cheia | V5 | GOL em tela cheia |
| 3 · barras | V6 | barras de jogador (gol, defesaça, cagada, cartão) |
| 4 · cartões do jogo | V7 | abertura, artilheiro do dia, fim de jogo |

Proteções, nos dois lados: o gerador recusa regra com `primeira_trilha`
abaixo de 4, e o script do DaVinci recusa qualquer peça abaixo da V4, diga o
manifesto o que disser. O script dá nome às trilhas ("Gráfico 1 · placar"),
sem renomear trilha que alguém já batizou. O manifesto traz `camada` e
`camada_nome` além da trilha, e o Registro mostra a camada em cada etiqueta.

## Revisão das 36 artes do Estúdio (17/11/2026)

Medido, não estimado: cada arte foi desenhada no Estúdio e a área ocupada de
verdade foi lida do canvas. "Opaca" = cobre o vídeo inteiro.

**Regiões da tela:**

- **Topo esquerdo** — placar de transmissão (x 72–1120, y 40–236).
- **Topo direito** — selo de replay (x 1360–1848, y 72–256).
- **Rodapé** — barras de gol, falta, cartão (x 80–1196, y 772–1008),
  substituição (y 684–1012) e fim do 1º tempo, que é larga (x 180–1736,
  y 632–1076).
- **Centro** — quase todo o resto: GOL tela cheia (x 564–1356, y 120–788),
  abertura, fim de jogo, artilheiro, VAR, pênalti, estatísticas, premiação…
- **Tela cheia opaca** — mapa tático, chance de gol, jogada, análise do jogo,
  condições de jogo, próxima partida. Escondem o jogo: são inserções.

| Arte | Região | No pacote hoje | Deveria entrar? Quando | Camada proposta | O que falta para entrar |
|---|---|---|---|---|---|
| Gol — barra inferior | rodapé | sim (gol, defesaça, cagada, cartão) | — | barras | — |
| Gol — tela cheia | centro | sim | — | centro | — |
| Histórico de gols na copa | centro | não | talvez: depois da barra, em gol de jogo da copa | centro | regra nova |
| Artilheiro do dia | centro | sim | — | centro | — |
| Falta | rodapé | não | não: é lance comum, encheria a tela | barras | — |
| Checagem do VAR | centro | não | sim, se houver lance de VAR | centro | tipo de lance VAR no Registro |
| Pênalti | centro | não | sim, no pênalti | centro | tipo de lance pênalti no Registro |
| Cartão | rodapé | não (sai como barra "CARTÃO") | sim, com a cor | barras | Registro gravar amarelo/vermelho |
| Placar da disputa | centro | não | sim, em disputa de pênaltis | centro | marcação da disputa |
| Chamada do batedor | centro | não | sim, em disputa de pênaltis | centro | marcação da disputa |
| Placar de abertura | centro | sim | — | centro | — |
| Fim de jogo | centro | sim | — | centro | — |
| Fim do 1º tempo | rodapé (largo) | não | sim, no intervalo | barras | marco de intervalo no Registro (a súmula já tem) |
| Escalação do time | lateral esquerda / rodapé | não | sim, logo depois da abertura | centro | escalação lançada na planilha |
| Formação no campo | quase tela cheia | não | talvez, na abertura | centro | formação de cada time |
| Substituição | rodapé | não | sim, na troca | barras | tipo de lance substituição |
| Mapa tático do lance | tela cheia opaca | não | não automático: o desenho é feito à mão | tela cheia | — |
| Chance de gol (xG) | tela cheia opaca | não | idem | tela cheia | — |
| Jogada completa | tela cheia opaca | não | idem | tela cheia | — |
| Análise do jogo | tela cheia opaca | não | talvez, no intervalo e no fim | tela cheia | súmula do jogo |
| Comparativo do jogo | centro | não | sim, no intervalo e no fim | centro | súmula do jogo |
| Corrida de chutes | centro | não | sim, no fim | centro | súmula do jogo |
| Quem mais apareceu | centro | não | sim, no fim | centro | súmula do jogo |
| Desempenho de um jogador | centro | não | talvez, depois do artilheiro | centro | súmula do jogo |
| Elenco do time | quase tela cheia | não | não: é peça de redes sociais | — | — |
| Placar de transmissão | topo esquerdo | sim (fixo + animação) | — | placar | — |
| Condições de jogo | tela cheia opaca | não | talvez, na abertura | tela cheia | local e hora do jogo |
| Marco da copinha | centro | não | sim, quando o marco acontece (100º gol…) | centro | cálculo automático do marco |
| Especial 100 Gols | centro | não | não: é peça especial | — | — |
| Premiação | centro | não | sim, no fim, em jogo da copa | centro | troféus do jogo |
| Campeão | quase tela cheia | não | sim, no fim, em jogo da copa | centro | campeão na aba JOGOS |
| Próxima partida | tela cheia opaca | não | sim, nos últimos segundos | tela cheia | data da próxima |
| Arbitragem | centro | não | talvez, na abertura | centro | nomes da arbitragem |
| Sala do VAR | centro | não | talvez, na abertura | centro | nomes |
| Replay | topo direito | não | **sim, em todo replay** | selo | marcação de replay no Registro |
| Ficha do jogador | centro | não | talvez, depois do artilheiro | centro | — |

**Conflitos encontrados:**

1. **GOL tela cheia e os cartões do jogo ocupam o mesmo centro, em camadas
   diferentes.** A fila só olha a própria camada, então um gol nos primeiros
   8 s ou nos últimos 17 s do vídeo poria o GOL em cima da abertura ou do
   artilheiro. Juntar os dois na mesma camada resolve: a fila passa a ver.
2. **Fim do 1º tempo, substituição e as barras dividem o rodapé.** Se
   entrarem, vão para a camada das barras, para entrar em fila.
3. **As inserções opacas cobrem tudo, inclusive o placar.** Precisam ficar na
   trilha mais alta, e o placar fixo continua por baixo delas.
4. **Placar e GOL tela cheia aparecem juntos no gol**: conferido no quadro, o
   logo do GOL fica ao lado do placar, sem encostar. Não é conflito.

**Divisão final proposta (5 camadas, por região da tela):**

| Camada | Trilha | Região | Peças |
|---|---|---|---|
| 1 · placar | V4 | topo esquerdo | placar fixo, placar anima (e o placar da disputa de pênaltis fica no centro) |
| 2 · barras | V5 | rodapé | barras de lance, falta, cartão, substituição, fim do 1º tempo |
| 3 · centro | V6 | centro | GOL tela cheia, abertura, fim, artilheiro, VAR, pênalti, estatísticas, premiação, campeão, marco, escalação |
| 4 · selo | V7 | topo direito | replay |
| 5 · tela cheia | V8 | tudo, opaco | mapa, chance, jogada, análise, condições, próxima partida |

A regra por trás: **uma camada por região da tela**. Assim a fila de cada
camada garante que nada se sobrepõe, e a ordem das trilhas decide quem fica
por cima. **Ainda não implementada** — está aqui para decisão. Hoje vale a
tabela de 4 camadas acima.

## Teste com o jogo de Agosto/2026

Vídeo: "Revoada Jogo 2 — Tempos Jogados", https://youtu.be/O0UMFeoH050 (cerca
de 70 min). A súmula `dados/sumulas/2026-08-lances.csv` vai até 1:09:02 e foi
anotada nesse vídeo — **a primeira conferência é se os tempos batem**: o gol
do Vitão tem que estar em 37:02, e o do Zaga em 1:03:49.

```powershell
# os lances verdadeiros, convertidos da súmula
.venv\Scripts\python.exe scripts\pacote.py da-sumula 2026-08
.venv\Scripts\python.exe scripts\pacote.py gerar midias\lances\lances-2026-08-sumula.json --video C:\caminho\jogo.mp4

# a bateria de teste: todos os tipos de peça no começo, meio e fim
.venv\Scripts\python.exe scripts\pacote.py bateria 2026-08 --video C:\caminho\jogo.mp4
.venv\Scripts\python.exe scripts\pacote.py gerar midias\lances\lances-2026-08-bateria.json --video C:\caminho\jogo.mp4
```

- `da-sumula` não inventa: gol, chute, falta, escanteio e cagada saem de
  linhas da súmula. **Defesa comum não vira defesaça** (a súmula não diz qual
  foi difícil). Resultado: 2 gols (Vitão 37:02, Zaga 1:03:49), 7 cagadas,
  10 faltas, 17 escanteios, 61 chutes; 1 × 1, igual à aba JOGOS.
- `bateria` é teste e diz isso no placar ("BATERIA DE TESTE"): em cada bloco,
  gol, cagada, cartão, defesaça, gol e outro gol 2 s depois (para a fila do
  placar). Jogadores reais do elenco de Agosto, lances inventados.
- O script do DaVinci sempre importa o **último pacote gerado**
  (`midias/ultimo-pacote.txt`). Para trocar de pacote, gere de novo.

## 1. Marcação com o vídeo

Fluxo combinado:

1. Montar o jogo no DaVinci, acertar os ângulos no **multicam**.
2. Renderizar uma **prévia** e subir no YouTube como **Não listado**
   (privado não toca incorporado).
3. No app, **Registro → colar o link → Carregar vídeo**.
4. Assistir e marcar. Clicar no **tipo** pausa o vídeo e guarda o instante;
   clicar em **quem fez** grava e volta a tocar.

Atalhos, com o foco fora dos campos: **Espaço** toca e pausa, **← →** andam
5 s, **Shift + ← →** andam 1 s. Pausado com um lance pendente, andar com as
setas ajusta o instante guardado. Na lista, clicar no tempo leva o vídeo até o
lance, e **⟲** troca o tempo do lance pelo tempo atual do vídeo.

Cada mudança fica salva **neste navegador**, por jogo. Gravar na planilha
exige o Apps Script na versão 2 — ver `planilha-colaborativa.md`.

### O cuidado que decide se o posicionamento automático vai funcionar

O tempo gravado é o **tempo da prévia**. Ele só vale para a timeline final se
a estrutura do corte não mudar depois da marcação.

- **Deslocar o jogo inteiro** (pôr uma abertura de 10 s no começo) é um número
  só de ajuste no script. Não quebra nada.
- **Cortar pedaços no meio** (tirar o intervalo, encurtar uma pausa) depois de
  marcar desalinha tudo o que vem depois do corte.

Então: fechar a estrutura do jogo antes de renderizar a prévia. A timeline do
DaVinci começa em `01:00:00:00` por padrão, e a prévia renderizada do começo
da timeline começa no zero — a conta é `01:00:00:00 + tempo do vídeo`.

## 3 e 4. O que precisa ser instalado, e o que isso implica

Nada disso foi instalado. Fica aqui para decidir com calma.

### O quê

- **ffmpeg** — um executável, sem instalador. Transforma a saída do render nos
  arquivos finais e regrava MP4 sem re-encodar.
- **Playwright + Chromium** — biblioteca Python que vai no `.venv` que já
  existe, e um Chromium próprio que roda sem janela. É ele que desenha as
  artes quadro a quadro.

### Implicações

- **Disco:** algo entre 400 e 600 MB no total.
- **Nada global:** sem administrador, sem mexer no PATH, sem registro do
  Windows, sem serviço rodando em segundo plano. Apagar a pasta desinstala.
- **Um detalhe a controlar:** por padrão o Playwright baixa o navegador para
  uma pasta do usuário, fora do projeto (`%LOCALAPPDATA%\ms-playwright`). Com
  uma variável de ambiente ele vai para dentro do projeto — é o que será feito.
- **Repositório:** tudo em `.gitignore`. Binário grande não pode ir para o
  GitHub, e o repositório é público.
- **Por máquina:** vale só no computador onde for instalado. Um script único
  deixa a instalação num comando.
- **O seu Chrome não é tocado:** o Chromium do Playwright é separado, sem os
  seus logins nem o seu perfil.
- **O site não muda:** o GitHub Actions continua igual; o render é local.
- **DaVinci gratuito:** o script roda de dentro do Resolve, pelo menu
  *Workspace › Scripts*. O arquivo do script é copiado para a pasta de scripts
  do próprio Resolve, que fica fora do projeto — é cópia de arquivo, não
  instalação. Rodar de fora, totalmente automático, é recurso do Studio.

### Por que render fora do navegador

Gravando no navegador, cada clipe grava em tempo real com a janela na frente,
e o Chrome entrega MP4 fragmentado — provável causa de o DaVinci ter recusado
os últimos arquivos. Fora do navegador, quadro a quadro, sai tudo com fps
exato, em qualquer velocidade, e **com transparência de verdade**: sem fundo
verde, sem chroma key para configurar, sem franja na borda.

## Decisões de 14/10/2026

- **Formato: ProRes 4444 em .mov**, com transparência. O Resolve gratuito
  decodifica no Windows. Descartados: WebM VP9 (o Resolve no Windows não
  decodifica), H.264 (não tem transparência) e sequência de PNG (funciona,
  mas são milhares de arquivos; fica como reserva).
- **Uma pasta por jogo**, fora do Git: `midias/<jogo>/`, com os `.mov` e um
  `manifesto.tsv` (lance, peça, arquivo, seg_video, quadro, timecode, trilha,
  duração).
- **Conversão de tempo**: quadro = início da timeline + arredonda(seg × 24).
  O script lê o início e o fps da própria timeline e para se não for 24 fps.
- **Em cada gol**: placar animado + barra do jogador + GOL em tela cheia. O
  placar fica fixo no canto o jogo inteiro, com o placar novo depois de cada
  gol.
- **Script do DaVinci em Lua**, por *Workspace › Scripts*: o Resolve roda Lua
  sem depender do Python instalado. Não mexe na V1 nem na A1. As mídias vão da
  V2 para cima.
- **Ligação direta, sem clique**, exige o Resolve Studio (pago): no gratuito,
  só é possível rodar o script de dentro do programa.

## Validação: fut de 20/09/2026

O jogo de Agosto/2026 deu lugar ao fut de domingo de 20/09: `2026-09`, Misto
Branco × Misto Preto, só vídeo (não conta para a copa).

- Prévia: https://youtu.be/0KRqe7et2cA
- DaVinci: projeto "Fut Domingo 2009 copy", "Timeline 1", 1920x1080, 24 fps,
  começa em 01:00:00:00. Hoje tem V1 (multicam) e A1.
- Tempo do vídeo 00:00 = timeline 01:00:00:00.

O arquivo `midias/teste/lances-gabarito-20-09.json` (fora do Git) tem estes
10 gols, com tempo e time mas **sem jogador** — o gabarito não diz quem fez.
Com ele, o pacote sai só com os placares, o bastante para conferir o
posicionamento.

Gabarito, anotado na timeline à mão (também como marcadores, importados por EDL):

| Tempo | Gol | Placar (Branco × Preto) |
|---|---|---|
| 11:35 | 1º Preto | 0 × 1 |
| 21:35 | 1º Branco | 1 × 1 |
| 31:30 | 2º Branco | 2 × 1 |
| 32:00 | 3º Branco | 3 × 1 |
| 40:35 | 4º Branco | 4 × 1 |
| 41:35 | 2º Preto | 4 × 2 |
| 45:20 | 5º Branco | 5 × 2 |
| 45:50 | 3º Preto | 5 × 3 |
| 51:40 | 4º Preto | 5 × 4 |
| 53:10 | 5º Preto | 5 × 5 (final) |

O que o Registro gravar tem que bater com esta tabela, e o placar calculado
pelo gerador também.

## Depois: levar para outros grupos

Nome da copa, cores, logo e regras precisam virar configuração — hoje "Copa
Revoada" está fixo em vários pontos do código. Fica para o capítulo seguinte.
