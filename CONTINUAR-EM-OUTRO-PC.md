# Continuar a Copa Revoada em outro computador

Atualizado em 16/09/2026.

## 1. No computador novo

Precisa de três programas. **Instalar é decisão sua**; se algum faltar, os
comandos estão ao lado.

| Programa | Para quê | Se faltar |
|---|---|---|
| Git | baixar o projeto | `winget install Git.Git` |
| GitHub CLI (`gh`) | acesso ao repositório e às URLs da planilha | `winget install GitHub.cli` |
| Python 3.12 | rodar o build | `winget install Python.Python.3.12` |

Depois de instalar, **feche e abra o terminal** e rode:

```powershell
gh auth login
gh repo clone Guilherme-Moliner/copa-revoada C:\copa-revoada
cd C:\copa-revoada
powershell -ExecutionPolicy Bypass -File scripts\prepara-maquina.ps1
```

**Use uma pasta de caminho curto**, como `C:\copa-revoada`. O Windows limita
caminhos a 260 caracteres, e numa pasta funda a instalação quebra com
`WinError 206`. Aconteceu no teste deste script.

O script confere o Python, cria o `.venv` dentro do projeto, instala as
dependências ali, busca a URL da planilha no GitHub e roda o build. Não instala
nada fora da pasta. No fim deve aparecer algo como:

```
planilha lida do Google Sheets — 14 abas, 766 linhas
32 jogadores (32 com foto)
14 times (14 com escudo, 9 com foto) · 13 jogos (9 com vídeo)
```

Os números mudam conforme vocês editam a planilha. O que importa é a primeira
linha dizer **Google Sheets**. Se o script avisar que usou a cópia `.xlsx`, foi
falha passageira do Google: rode de novo.

Para abrir o Claude Code, rode `claude` **dentro da pasta**. Ele lê o
`CLAUDE.md` sozinho, e as regras do projeto vêm junto.

## 2. O que NÃO vai para o outro computador

| O quê | Por quê | O que fazer |
|---|---|---|
| Lances marcados no Registro e ainda não gravados | ficam salvos só no navegador onde foram marcados | clique em **Gravar** antes de trocar de computador |
| A chave de acesso | mora só na planilha, de propósito | pegue na aba CONFIG, célula B2 |
| `.venv` e `img/` | são gerados | o script refaz |
| A memória do Claude desta máquina | é local | as regras estão no `CLAUDE.md` |
| Login do `gh` | é por máquina | `gh auth login` |

## 3. Pendência antes do próximo jogo

**Republicar o Apps Script na versão 2.** Ela grava o tempo do vídeo de cada
lance. A versão publicada hoje descarta esse tempo sem dar erro.

Na planilha: **Extensões › Apps Script** → cole o conteúdo de
`scripts/apps-script.gs` → **Implantar › Gerenciar implantações › lápis ›
Versão: Nova versão › Implantar**. A URL continua a mesma. Detalhes em
`docs/planilha-colaborativa.md`.

## 4. Onde o projeto está

**Telas:** Jogadores · Times · Recordes · Troféus · Vídeos · Estatísticas ·
Registro · Análise Tática · Estúdio.

**Estúdio:** 36 artes, incluindo as de estatística da súmula (comparativo,
corrida de chutes, quem mais apareceu, desempenho de jogador, elenco do time)
e as de fim de vídeo (premiação, campeão, próxima partida).

**Dados:** a planilha do Google é a fonte de verdade. O site republica sozinho
de hora em hora.

**Registro com vídeo:** cole o link do YouTube da prévia, e cada lance grava o
tempo exato do vídeo. Clicar no tipo do lance pausa e guarda o instante;
clicar em quem fez grava.

## 5. Próximo capítulo: pacote de mídias

O plano completo está em **`docs/pacote-de-midias.md`**. Em resumo: marcar o
jogo no Registro e o app gerar o conjunto inteiro de artes, com transparência
de verdade, para um script dentro do DaVinci importar e posicionar na timeline.

Decisões já tomadas:

- **DaVinci Resolve gratuito.** O script roda pelo menu *Workspace › Scripts*.
- **Marcação pelo Registro do app**, com o vídeo da prévia no YouTube.
- **Instalar ffmpeg e Playwright dentro do projeto está autorizado**, no
  computador que tem o DaVinci. O que isso implica está no documento.
- **Validar primeiro com o jogo de Agosto/2026**, que já tem súmula e edição
  manual para comparar.

## Mensagem para começar no computador novo

Abra o Claude Code dentro da pasta do projeto e cole:

> Estou continuando a Copa Revoada em outro computador — este é o que tem o
> DaVinci Resolve (versão gratuita). Já rodei `scripts/prepara-maquina.ps1` e o
> build leu a planilha do Google Sheets.
>
> Leia `CLAUDE.md`, `CONTINUAR-EM-OUTRO-PC.md` e `docs/pacote-de-midias.md`.
>
> Quero começar o pacote de mídias. A instalação do ffmpeg e do Playwright
> dentro da pasta do projeto está autorizada. Antes de instalar, me diga o que
> vai baixar e onde vai ficar. Depois, vamos validar o modelo no jogo de
> Agosto/2026.
