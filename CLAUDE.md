# Copa Revoada — instruções para o Claude Code

Site de uma copa de futebol entre amigos, com estatísticas, troféus, registro de
lances e um Estúdio que gera as artes do vídeo de cada jogo.

Publicado em https://guilherme-moliner.github.io/copa-revoada/

## Regras que valem sempre

- **Nunca invente dado nem preencha célula vazia.** Se faltar informação,
  pergunte. Isso vale também para "deduzir" um valor que parece óbvio.
- **Não edite o `index.html` à mão.** Ele é gerado por `scripts/build.py`.
  Visual e comportamento vão em `src/app.template.html`.
- **Não altere `dados/planilha-original-agosto-2026.xlsx`.** É referência.
- **Não instale nada global sem perguntar.** Dependência vai no `.venv` do projeto.
- **Nunca coloque chave de acesso no repositório.** Ele é público. A chave mora
  só na planilha do Google (aba CONFIG, célula B2). Não peça a chave ao usuário.
- **Commits, comentários e mensagens em português.**
- Pergunte antes de qualquer coisa irreversível.

## Como o projeto funciona

```
Google Sheets (fonte de verdade)
   │  lido pelo Apps Script publicado (scripts/apps-script.gs, ação "planilha")
   ▼
scripts/build.py  ── + assets/ (fotos e escudos) + dados/sumulas/ (lances)
   ▼
index.html  ── o site inteiro num arquivo só
```

- O deploy roda a cada push na `main` e **de hora em hora**, lendo a planilha
  (`.github/workflows/publicar.yml`). A rodada agendada só republica se o
  `index.html` mudou.
- A planilha é privada. Quem lê é o Apps Script; a URL dele está nas variáveis
  do repositório `PLANILHA_URL` e `LANCES_URL` (`gh variable get PLANILHA_URL`).
- Sem `PLANILHA_URL`, o build usa `dados/COPA_REVOADA_planilha.xlsx`, que é só
  cópia de segurança.
- O Apps Script é a única parte com escrita: grava apenas nas abas
  `LANCES <jogo>`, e só com a chave. **Mudou o `apps-script.gs`? O usuário
  precisa republicar** (Implantar › Gerenciar implantações › lápis › Nova versão).

## Rodar localmente

```powershell
powershell -ExecutionPolicy Bypass -File scripts\prepara-maquina.ps1
```

Ou à mão:

```powershell
$env:PLANILHA_URL = gh variable get PLANILHA_URL
.venv\Scripts\python.exe scripts\build.py
.venv\Scripts\python.exe -m http.server 8123
```

## Onde está cada coisa

| Assunto | Arquivo |
|---|---|
| Continuar o projeto em outro computador | `CONTINUAR-EM-OUTRO-PC.md` |
| O que falta nos dados | `PENDENCIAS.md` e `scripts/pendencias.py` |
| Planilha colaborativa e Apps Script | `docs/planilha-colaborativa.md` |
| Súmula minuto a minuto, Estatísticas e artes | `docs/sumula-minuto-a-minuto.md` |
| **Próximo capítulo: pacote de mídias** | `docs/pacote-de-midias.md` |
| Modelo de chance de gol | `docs/como-funciona-a-chance-de-gol.md` |
| Diagnóstico de vídeo exportado | `scripts/checa-webm.py` |

## Lições que custaram caro

- **Edição do template por script Python:** faça `assert` em cada âncora e só
  grave no final. Âncora que não casa tem que abortar antes de escrever, e não
  gravar metade das mudanças em silêncio.
- **Nada verde nas artes.** O vídeo sai em fundo verde para chroma key; cor de
  time passa por `corSegura()`.
- **Vídeo gravado no navegador:** o MediaRecorder do Chrome gera MP4
  fragmentado, que o DaVinci recusou. Por isso o plano do pacote de mídias
  renderiza fora do navegador e com transparência.
- **Verifique contra o dado de verdade antes de concluir.** Mais de uma vez, a
  primeira hipótese estava errada: um "bug" era o dado da planilha, e uma
  "inversão" vinha de um build antigo.
- `requestAnimationFrame` congela em aba oculta: use temporizador em
  gravações e testes automatizados.
