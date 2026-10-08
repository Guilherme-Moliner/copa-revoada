# Continuar a Copa Revoada em outro computador

Atualizado em 08/10/2026.

**O projeto inteiro já está no GitHub.** Não precisa copiar pasta, pendrive nem
o `.rar`: no computador novo você baixa direto de lá. O que fica para trás nesta
máquina é só o que se gera sozinho (`.venv`, `img/`, cópias temporárias).

## 1. No computador novo — três passos

**Passo 1. Instale três programas**, se ainda não tiver. Instalar é decisão sua:

| Programa | Para quê | Comando |
|---|---|---|
| Git | baixar o projeto | `winget install Git.Git` |
| GitHub CLI | acesso ao repositório e às URLs da planilha | `winget install GitHub.cli` |
| Python 3.12 | gerar o site | `winget install Python.Python.3.12` |

Depois de instalar, **feche e abra o terminal** (PowerShell).

**Passo 2. Baixe o projeto e prepare tudo** — cole estas quatro linhas:

```powershell
gh auth login
gh repo clone Guilherme-Moliner/copa-revoada C:\copa-revoada
cd C:\copa-revoada
powershell -ExecutionPolicy Bypass -File scripts\prepara-maquina.ps1
```

No `gh auth login`, escolha **GitHub.com › HTTPS › Login with a web browser**.

Use a pasta **`C:\copa-revoada`**. Caminho comprido quebra a instalação no
Windows (erro `WinError 206`) — aconteceu no teste.

O script confere o Python, cria o ambiente dentro do projeto, instala o que
precisa ali dentro e gera o site. No fim tem que aparecer:

```
planilha lida do Google Sheets — 14 abas, ...
```

Se ele avisar que usou a **cópia .xlsx**, foi falha passageira do Google: rode
o script de novo.

**Passo 3. Abra o Claude Code dentro da pasta** e cole a mensagem do fim deste
arquivo. Ele lê o `CLAUDE.md` sozinho, e as regras do projeto vêm junto.

## 2. Antes de desligar este computador

- [ ] **Lances do Registro ainda não gravados** ficam só neste navegador.
      Se marcou algum, clique em **Gravar**. Hoje não há nenhum pendente.
- [ ] O **`copa-revoada.rar`** na Área de Trabalho é de 16/09 e está velho.
      Não use ele para continuar — o GitHub tem a versão certa.

## 3. O que não viaja, e por quê

| O quê | Por quê | No computador novo |
|---|---|---|
| Login do `gh` | é por máquina | `gh auth login` |
| `.venv` e `img/` | são gerados | o script refaz |
| Lances do Registro não gravados | ficam no navegador | gravar antes de sair |
| A chave de acesso | mora só na planilha, de propósito | aba CONFIG, célula B2 |
| A memória do Claude desta máquina | é local | as regras estão no `CLAUDE.md` |

## 4. Pendências

### Suas, antes do próximo jogo

1. **Republicar o Apps Script — continua pendente.** Conferido em 08/10: o
   script no ar ainda é a versão 1, que **descarta o tempo do vídeo** de cada
   lance marcado no Registro. Na planilha: **Extensões › Apps Script** → cole o
   conteúdo de `scripts/apps-script.gs` → **Implantar › Gerenciar
   implantações › lápis › Versão: Nova versão › Implantar**. A URL não muda.
2. **Aba `LANCES 2026-08` tem 14 lances de teste**, marcados por
   "teste-sistema", gravados em agosto quando a ligação com a planilha foi
   montada. Não são do jogo. Se for marcar esse jogo pelo Registro, apague as
   linhas da linha 5 para baixo antes.
3. **Aba CLIPES: formatar as colunas D e E como texto** (Formatar › Número ›
   Texto simples). Sem isso o Sheets transforma `12:34` em hora do dia.

### De dados, com os amigos

Estão em `PENDENCIAS.md` e na aba PENDENCIAS da planilha. Para atualizar a
lista: `.venv\Scripts\python.exe scripts\pendencias.py`.

## 5. Onde o projeto está

**No ar:** https://guilherme-moliner.github.io/copa-revoada/

**Telas:** Jogadores · Times · Recordes · Troféus · Vídeos · Estatísticas ·
Registro · Análise Tática · Estúdio.

**Dados:** a planilha do Google é a fonte de verdade. O site se atualiza sozinho
algumas vezes por dia (o GitHub roda a cada 3 a 6 horas). Para forçar: GitHub ›
Actions › Publicar site › Run workflow. O selo no canto inferior esquerdo do
site mostra de quando são os dados.

**Se a planilha não responder numa atualização, nada é publicado** e o site
fica como estava. Antes ele publicava uma cópia velha por cima — foi o que
aconteceu em 22/09.

### O que mudou desde 16/09

- **Selo de origem dos dados** no canto do site, com data e hora da leitura.
- **Recordes reorganizados**: 13 jogos na copa, 10 com dados apurados. Presença
  e título contam os 13; gol, assistência e participação contam os 10. Garçons
  virou Assistências. Perfil: "Jogos com dados apurados".
- **Clipes**: os jogadores adicionam pela aba CLIPES com o link inteiro do
  YouTube e o tempo como `12:34`. No perfil, o clipe abre numa gaveta com o
  player já no segundo do lance. Guia: `docs/como-adicionar-clipes.md`.
- **Registro com vídeo**: cola o link da prévia do YouTube e cada lance grava o
  tempo exato do vídeo.

## 6. Próximo capítulo: pacote de mídias

Plano completo em **`docs/pacote-de-midias.md`**. Em resumo: marcar o jogo no
Registro e o app gerar o conjunto inteiro de artes, com transparência de
verdade, para um script dentro do DaVinci importar e posicionar na timeline.

Já decidido:

- **DaVinci Resolve gratuito** — o script roda por *Workspace › Scripts*.
- **Marcação pelo Registro**, assistindo a prévia no YouTube.
- **Instalar ffmpeg e Playwright dentro da pasta do projeto está autorizado**,
  no computador que tem o DaVinci.
- **Validar primeiro no jogo de Agosto/2026**, que já tem súmula e edição manual
  para comparar.

## Mensagem para colar no Claude Code

> Estou continuando a Copa Revoada em outro computador. Já rodei
> `scripts/prepara-maquina.ps1` e o build leu a planilha do Google Sheets.
>
> Leia `CLAUDE.md` e `CONTINUAR-EM-OUTRO-PC.md`. Confira comigo as pendências
> da seção 4 antes de começar qualquer coisa nova.
>
> Se este for o computador com o DaVinci, o próximo passo é o pacote de mídias
> (`docs/pacote-de-midias.md`). A instalação do ffmpeg e do Playwright dentro da
> pasta do projeto está autorizada — mas antes de instalar, me diga o que vai
> baixar e onde vai ficar.
