# Pacote de mídias — o plano

Em vez de montar peça por peça no Estúdio, o jogo é marcado uma vez no
Registro e o app gera **o conjunto inteiro de mídias** a partir dessas
marcações. Num passo seguinte, um script dentro do DaVinci importa tudo e
posiciona na timeline.

Estado em 16/09/2026: **a etapa 1 está pronta**; as outras dependem de
instalar ferramentas no computador que tem o DaVinci.

## Etapas

| # | Etapa | Situação |
|---|---|---|
| 1 | Marcar o jogo no Registro com o tempo do vídeo do YouTube | pronta |
| 2 | Regras: cada tipo de lance vira quais peças | a fazer |
| 3 | Render em lote, fora do navegador, com transparência | a fazer — precisa das instalações |
| 4 | Script do DaVinci: importar, posicionar, ajustar | a fazer — DaVinci gratuito |

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

## Validação

O jogo de Agosto/2026 já tem súmula, vídeo e a edição feita à mão. Rodar a
cadeia inteira nele e comparar com a edição manual valida o modelo antes do
próximo jogo.

## Depois: levar para outros grupos

Nome da copa, cores, logo e regras precisam virar configuração — hoje "Copa
Revoada" está fixo em vários pontos do código. Fica para o capítulo seguinte.
