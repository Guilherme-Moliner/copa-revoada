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

| Lance | Peça | Trilha | Entra | Dura |
|---|---|---|---|---|
| Gol | placar com a animação do gol | V2 | no lance | 5 s |
| Gol | GOL em tela cheia | V3 | no lance | 4 s |
| Gol | barra do jogador | V4 | 4 s depois | 6 s |
| Defesaça, Cagada, Cartão | barra do jogador, com o nome do lance | V4 | 1 s depois | 5 s |
| *o jogo* | placar fixo | V2 | o jogo inteiro | até o gol seguinte |
| *o jogo* | placar de abertura | V3 | 1 s do começo | 7 s |
| *o jogo* | artilheiro do dia | V3 | 17 s antes do fim | 7 s |
| *o jogo* | fim de jogo, com o placar final | V3 | 9 s antes do fim | 8 s |

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
