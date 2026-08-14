# Continuar a Copa Revoada em outro computador

Cole o bloco abaixo como primeira mensagem para o Claude Code no outro PC.
Antes disso, só isso aqui:

```bash
gh repo clone Guilherme-Moliner/copa-revoada
```

---

## Prompt para colar

> Este repositório é o site da Copa Revoada, uma copa de futebol entre amigos.
> É um site estático: o `index.html` é **gerado** por `scripts/build.py` a partir
> da planilha em `dados/` e das imagens em `assets/`. Já está publicado em
> https://guilherme-moliner.github.io/copa-revoada/ via GitHub Pages, com deploy
> automático a cada push na `main` (`.github/workflows/publicar.yml`).
>
> Antes de mexer em qualquer coisa, leia `README.md`, `PENDENCIAS.md` e
> `scripts/build.py`. O `PENDENCIAS.md` lista o que ainda não fechou nos dados —
> não tente resolver sozinho, é decisão minha e dos meus amigos.
>
> **Regras que valem sempre:**
> - Nunca invente dado na planilha nem preencha célula vazia. Se faltar
>   informação, me avise.
> - Não edite o `index.html` à mão. Ele é gerado. Visual vai em
>   `src/app.template.html`, dados vão na planilha.
> - Não altere `dados/planilha-original-agosto-2026.xlsx`, é referência.
> - Não instale nada global sem perguntar.
> - Commits e comentários em português.
> - Antes de qualquer coisa irreversível, me pergunte.
>
> **Ambiente:** precisa de Python 3.12, e das dependências
> `openpyxl`, `pillow` e `opencv-python-headless<5` (a versão 5 não traz as
> cascatas de detecção de rosto). Prefira um `.venv` dentro do projeto a instalar
> global. Confira também se o `gh` está autenticado.
>
> Para rodar:
> ```bash
> python -m venv .venv
> .venv/Scripts/python.exe -m pip install openpyxl pillow "opencv-python-headless<5"
> .venv/Scripts/python.exe scripts/build.py
> ```
>
> Hoje o build deve dizer: **32 jogadores, 14 times, 13 jogos, 233 escalações**.
> Se der outro número, pare e me explique antes de seguir.
>
> **O que eu quero fazer neste fim de semana:** revisar os dados com meus amigos
> e gerar os elementos de vídeo para a edição. O plano é passar a planilha para o
> Google Sheets para revisarmos juntos, e depois ligar o site nela.

---

## Estado atual, para o Claude se situar

### Como o site é montado

```
dados/COPA_REVOADA_planilha.xlsx   ← toda a informação
assets/<arquivo>.jpg|png           ← fotos de jogador, fotos e escudos de time
        ↓  scripts/build.py
img/                               ← derivadas leves, geradas no build (não versionado)
index.html                         ← o site inteiro num arquivo só
```

O build faz, além de montar o HTML:

- **detecção de rosto** (OpenCV) para centralizar o recorte dos retratos;
- **remoção de fundo chapado** dos escudos, por preenchimento a partir das quinas;
- **conferência de placar** contra os gols lançados, jogo a jogo, já contando gol
  contra e gol anulado pelo VAR;
- avisos no fim sobre tudo que está faltando.

### Telas

Jogadores · Times · Recordes · Troféus · Vídeos · Estúdio.

### Estúdio — 21 artes

| Grupo | Artes |
|---|---|
| Gol | barra inferior, tela cheia, histórico de gols, artilheiro do dia |
| Arbitragem | falta, checagem do VAR, pênalti, cartão |
| Pênaltis | placar da disputa, chamada do batedor |
| Partida | placar de abertura, fim de jogo, fim do 1º tempo, escalação, formação, substituição |
| Especiais | marco da copinha |
| Equipe | arbitragem, sala do VAR |
| Outros | replay (com modo hyper motion), ficha do jogador |

Cada uma exporta em **PNG**, **sequência PNG (.zip)** com alpha de verdade, e
**WebM em fundo verde**.

### Decisões de dados já tomadas

- Os três primeiros jogos (`2020-12`, `2021-07`, `2021-12`) **contam só título**,
  não jogos/gols/assistências. É a constante `SO_TITULO` no topo do build. Por
  isso o site mostra "10 jogos válidos · 13 presenças".
- `gols_contra` e `conta_no_placar` na aba ESCALACOES cuidam do gol contra do Leo
  em Dez/2024 e do gol do VAR em Ago/2026.
- Jogadores escondidos do site mas mantidos na planilha: constante
  `EXCLUIR_DO_SITE` no build.

---

## Passar a planilha para o Google Sheets

O build já aceita isso. Passo a passo:

1. Suba `dados/COPA_REVOADA_planilha.xlsx` para o Google Drive e abra com
   Google Sheets (**Arquivo → Importar → Substituir planilha**, se preferir criar
   antes uma planilha vazia).
2. Pegue o ID da URL:
   `https://docs.google.com/spreadsheets/d/`**`ESTE_PEDAÇO`**`/edit`
3. Deixe a planilha acessível por link: **Compartilhar → Qualquer pessoa com o
   link → Leitor**.
4. No GitHub: **Settings → Secrets and variables → Actions → Variables →
   New repository variable**
   - Nome: `PLANILHA_URL`
   - Valor: `https://docs.google.com/spreadsheets/d/SEU_ID/export?format=xlsx`
5. Rode o workflow (**Actions → Publicar site → Run workflow**).

A partir daí, todo build baixa a planilha do Sheets. Se o Sheets estiver fora do
ar, o build usa a última cópia baixada e avisa. Para voltar ao arquivo do
repositório, é só apagar a variável.

Para testar localmente antes:

```bash
PLANILHA_URL="https://docs.google.com/spreadsheets/d/SEU_ID/export?format=xlsx" .venv/Scripts/python.exe scripts/build.py
```

> **Cuidado:** o Sheets não preserva as cores de célula e a formatação amarela das
> colunas a preencher. Os **nomes das abas e das colunas** é que importam — se
> alguém renomear uma aba ou coluna, o build para e diz qual não achou.

---

## O que está aberto

Está tudo em `PENDENCIAS.md`, que é o documento para trabalhar com os amigos.
Os pontos que dependem de decisão de vocês:

1. **Ago/2026** — o `leo` aparece nos dois times, e é onde está o gol do VAR.
2. **Números de camisa** — 32 jogadores, nenhum número cadastrado.
3. **Aba DESEMPENHO** — 155 pares (time, jogador) esperando nota de 1 a 5.
4. **Escudo do Borussia 2022** é o brasão do Boca Juniors; o Boca 2023 está sem escudo.
5. **Fotos** — 10 jogadores sem foto; a do André é de corpo inteiro.
6. **Vídeos** — nenhum jogo tem ID do YouTube lançado.

## Limitações conhecidas para a edição

- **Cinco fotos foram tiradas contra parede verde** (Garopaba, Borba, Bala,
  Leo Godinho e Vitor). Em qualquer arte que mostre essas fotos, **não use o WebM
  verde** — o Chroma Key vai comer o fundo da foto junto. Use a sequência PNG,
  que tem alpha de verdade.
- **Três escudos** (Criseúma, D Boa, Jumentus) são desenho claro sobre fundo
  claro: o build não consegue tirar o fundo sem comer o escudo. Se quiser fundo
  transparente neles, suba o PNG já recortado.
