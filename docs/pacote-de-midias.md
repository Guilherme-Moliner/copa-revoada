# Pacote de mídias — o plano

Em vez de montar peça por peça no Estúdio, o jogo é marcado uma vez no
Registro e o app gera **o conjunto inteiro de mídias** a partir dessas
marcações. Num passo seguinte, um script dentro do DaVinci importa tudo e
posiciona na timeline.

Estado em 15/11/2026: **a cadeia inteira existe**, com gols, defesaça,
cagada, cartão, abertura, artilheiro e fim de jogo. Falta validar o
posicionamento no DaVinci com o pacote do gabarito: o script do Resolve ainda
não foi rodado nenhuma vez.

**O DaVinci não lê o `.json`.** O arquivo de lances é do gerador. O que o
DaVinci recebe são os `.mov` e `.png` prontos e o `manifesto.tsv`, que o
script lê para pôr cada peça no lugar.

## Etapas

| # | Etapa | Situação |
|---|---|---|
| 1 | Marcar o jogo no Registro com o tempo do vídeo do YouTube | pronta |
| 2 | Regras: cada tipo de lance vira quais peças | gols prontos; os outros tipos, a fazer |
| 3 | Render em lote, fora do navegador, com transparência | pronta (`scripts/pacote.py`) |
| 4 | Script do DaVinci: importar, posicionar | pronto, falta validar no Resolve |

## Como usar, do jogo à timeline

1. **Registro**: escolha o jogo, ou **＋ Novo jogo avulso** para um fut que não
   entra na planilha. Cole o link da prévia, **Carregar vídeo**, e marque.
2. **Baixar lances**: sai o arquivo `lances-<jogo>.json`. Quem marcou em
   outro computador manda esse arquivo, e **Abrir arquivo** carrega ele no
   Registro.
3. **Gerar o pacote**: dois cliques em **`Gerar pacote de midias.bat`**, na
   pasta do projeto. Ele pega o `lances-*.json` mais novo da pasta Downloads
   (ou arraste um arquivo para cima do `.bat`). Se o site local estiver
   desatualizado, ele refaz antes, lendo a planilha.

   As peças saem em `midias/<jogo>/`, com o `manifesto.tsv`. O gerador
   imprime cada gol com o placar calculado: confira antes de seguir.
4. **No DaVinci**, com o projeto e a timeline abertos: *Workspace › Scripts ›
   Copa Revoada - importar pacote*. As peças vão para *IA › Pacote <jogo>* no
   Media Pool e para a timeline, da V2 para cima. O resumo aparece em
   *Workspace › Console*.

O script do DaVinci entra no menu uma vez por computador:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\davinci\instala.ps1
```

Rode de novo sempre que `scripts/davinci/*.lua` mudar.

### O que cada lance vira: `dados/regras-pacote.json`

Um arquivo só manda nisso. O **Registro mostra essas regras ao lado de cada
lance** (as etiquetas douradas; riscada = não entra, com o motivo ao passar o
mouse), e o gerador segue as mesmas. Mudou o arquivo, mudou nos dois.

| Lance | Peça | Camada (trilha) | Entra | Dura |
|---|---|---|---|---|
| Gol | placar com a animação do gol | camada 1 (V4) | no lance | 5 s |
| Gol | GOL em tela cheia | camada 2 (V5) | no lance | 4 s |
| Gol | barra do jogador | camada 3 (V6) | 4 s depois | 6 s |
| Defesaça, Cagada, Cartão | barra do jogador, com o nome do lance | camada 3 (V6) | 1 s depois | 5 s |
| *o jogo* | placar fixo | camada 1 (V4) | o jogo inteiro | até o gol seguinte |
| *o jogo* | placar de abertura | camada 4 (V7) | 1 s do começo | 7 s |
| *o jogo* | artilheiro do dia | camada 4 (V7) | 17 s antes do fim | 7 s |
| *o jogo* | fim de jogo, com o placar final | camada 4 (V7) | 9 s antes do fim | 8 s |

Chute, falta e escanteio não geram peça. Para ligar, desligar ou mudar tempo,
edite o arquivo: cada linha é uma peça. Guia de duração: **1 s a mais do que
parece bastar**, e mais ainda para peça densa.

Regras que o gerador aplica sozinho, e avisa no fim:

- **Peça com jogador precisa do jogador.** Gol marcado sem dono gera só o
  placar.
- **Duas peças no mesmo lugar da tela não se sobrepõem**: a segunda espera a
  primeira sair. Se a espera passar de 8 s, ela fica de fora.
- **Artilheiro do dia só sai quando é fato**: todo gol com jogador e um só na
  frente. Empate não é decidido pelo gerador.

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

## Camadas gráficas

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
