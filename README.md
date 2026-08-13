# Copa Revoada

Site da copa: perfil de cada jogador, histórico de times e temporadas, livro de
recordes, arquivo de vídeos e um estúdio que gera as artes da transmissão.

Site estático, sem servidor e sem banco. Toda a informação sai de uma planilha.

## Como funciona

```
dados/COPA_REVOADA_planilha.xlsx   ← onde a informação é digitada
fotos/<id>.jpg                     ← uma foto por jogador
assets/logo.png                    ← logo oficial
        ↓  python3 scripts/build.py
index.html                         ← o site inteiro num arquivo só
```

O `index.html` é gerado, não editado à mão. Quem mexe no visual mexe em
`src/app.template.html` e roda o build de novo.

## Rodar localmente

```bash
pip install openpyxl pillow
python3 scripts/build.py
```

Depois abra o `index.html` no navegador.

> Para testar o **Estúdio com fotos de jogador**, sirva por HTTP em vez de abrir o
> arquivo direto — aberto como `file://` o navegador bloqueia a exportação de imagem:
> ```bash
> python3 -m http.server 8000    # depois: http://localhost:8000
> ```

O build imprime um resumo e avisa sobre inconsistências: time que não existe,
jogador não cadastrado, jogo sem escalação lançada.

## Publicar

**Settings → Pages → Source: GitHub Actions.** É a única configuração necessária.

A partir daí, todo push na `main` roda `scripts/build.py` e republica o site.
Isso inclui editar a planilha pela interface do GitHub: quem tiver acesso ao
repositório atualiza os dados sem precisar instalar nada.

## Estrutura

| Caminho | O que é |
|---|---|
| `index.html` | site gerado — não editar à mão |
| `src/app.template.html` | o app de verdade, com o marcador `// __DADOS__` |
| `scripts/build.py` | lê a planilha e as fotos, escreve o `index.html` |
| `dados/COPA_REVOADA_planilha.xlsx` | fonte de toda a informação |
| `dados/ranking-legado.json` | totais da planilha antiga, usados enquanto as escalações não estão lançadas |
| `fotos/` | retratos dos jogadores (veja o LEIA-ME de lá) |
| `assets/` | logo oficial em três versões |
| `dados/planilha-original-agosto-2026.xlsx` | a planilha antiga, guardada como está, para conferência |
| `PENDENCIAS.md` | o que não fechou na importação e precisa de decisão humana |
| `TAREFAS-EQUIPE.md` | o que falta preencher e quem pegou o quê |

## A aba que importa

`ESCALACOES` — uma linha por jogador por jogo. É de onde saem jogos, gols,
assistências, títulos, elenco de cada time e histórico por temporada.

Ela já veio preenchida com 233 lançamentos importados da planilha antiga, cobrindo
os 13 jogos. Os totais individuais só passam a sair inteiramente daí quando todos
os jogos tiverem gol lançado por jogador — hoje faltam os de 2020 e 2021, e nesses
casos o total de gols vem do ranking antigo. Veja `PENDENCIAS.md`.

A coluna `nota_1a5` vira o rostinho de condição do jogador naquele jogo:
1 apagado, 2 abaixo, 3 normal, 4 bom, 5 inspirado.

## Estúdio

Sete artes: gol em barra inferior, gol em tela cheia, replay, escalação animada,
substituição, ficha do jogador e cartão. Cada uma exporta de três formas:

- **PNG** — quadro parado, fundo transparente.
- **Sequência PNG (.zip)** — 30 fps com alpha de verdade. No DaVinci Resolve,
  importe a pasta como *image sequence*. É o caminho de melhor qualidade.
- **WebM verde** — arquivo único, exige Chroma Key na edição.

Também serve de *browser source* no OBS: ative o fundo verde e aplique Chroma Key.
