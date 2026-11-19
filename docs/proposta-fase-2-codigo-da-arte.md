# Proposta — Fase 2: código da arte e ficha do jogo com IA

Escrita em 19/11/2026, para decisão. **Nada aqui está implementado.** A Fase 1
(plano de peças no Registro, artes que já têm dado e a bateria completa) está
em `docs/pacote-de-midias.md`.

## O problema que a Fase 2 resolve

Hoje o pacote só põe no vídeo o que sai sozinho de algum lugar: dos lances
do Registro, da súmula ou da planilha. Ficam de fora as artes que precisam de
um dado que ninguém lançou em lugar nenhum: escalação de quem jogou de fato,
arbitragem, condições do jogo, próxima partida, campeão, premiação, VAR,
pênalti, e as artes desenhadas à mão (mapa tático, chance de gol, jogada).

A regra continua: **dado que não existe não é inventado**. A Fase 2 cria um
jeito de o dado existir, e de chegar ao plano do jogo.

## 1. O código da arte

### Como funciona para quem usa

1. No **Estúdio**, você monta a arte com os dados reais (exemplo: a
   escalação com quem jogou de fato).
2. Clica em **Copiar código**. Sai um texto curto, copiável, que guarda o
   tipo da arte e os dados dela.
3. Clica em **Atribuir ao jogo** e escolhe o jogo (e, se fizer sentido, o
   time).
4. No **Registro**, em "＋ Peça", aparece a lista **Artes deste jogo**. Você
   escolhe uma e solta no instante atual do vídeo. Ou cola um código que
   alguém mandou.

### O formato

O Estúdio já tem um código: o do mapa tático e da jogada, `RVD1.…` — um JSON
`{t: tipo, v: versão, d: dados}`, comprimido e em base64. A proposta é
**usar o mesmo para todas as artes**, sem inventar outro:

```
RVD1.<base64 do JSON comprimido>

{
  "t": "escalacao",        tipo da arte (o mesmo id do Estúdio)
  "v": 1,                  versão dos dados DAQUELA arte
  "d": { ...campos... },   só os campos que a arte usa
  "jogo": "2026-08",       opcional: a que jogo foi atribuída
  "time": "dentro26",      opcional
  "por": "Guilherme",      quem montou
  "em": "2026-11-19"
}
```

**Como sobrevive às mudanças nas artes:**

- Cada arte tem a **própria versão** (`v`). Quando uma arte ganhar um campo,
  ela sobe de versão e ganha uma função que traduz o código antigo para o novo.
  Código velho continua abrindo.
- Campo que o código não traz fica no padrão **só se o padrão não for dado**
  (cor, tamanho, posição). Campo de dado que falta (um nome, um número) faz a
  peça ficar de fora com aviso, como hoje.
- Campo que a arte não conhece mais é ignorado, sem erro.
- Tipo de arte que deixou de existir: a peça fica de fora com aviso.

### Onde a arte atribuída mora

| Opção | A favor | Contra |
|---|---|---|
| **Aba ARTES na planilha** | todo mundo vê, sobrevive a trocar de computador, o site já lê a planilha | exige Apps Script v3 (gravar nessa aba) e republicar |
| **Dentro do arquivo de lances** (`plano.manuais[].codigo`) | já existe, viaja com o plano, não exige nada novo | a arte vale só para aquele arquivo |
| **Só no navegador** | zero trabalho | some ao trocar de navegador; não serve para a equipe |
| **Arquivo no repositório** | versionado | **o repositório é público**: escalação, nomes e notas de jogo ficariam abertos na internet |

**Recomendação: as duas primeiras juntas.** A peça manual leva o código dentro
do plano (funciona já, sem planilha), e a aba ARTES guarda o acervo por jogo e
por time para reusar. Nada no repositório.

A aba ARTES teria: `jogo_id`, `time_id`, `arte`, `codigo`, `por`, `em`,
`obs`. Gravação com a mesma chave das abas LANCES.

### Como o gerador desenha a partir do código

O caminho já existe. Uma peça manual ganha o campo `codigo`. O `PACOTE.prepara`
do site lê o código, confere tipo e versão, põe os dados nos campos do
Estúdio e o gerador desenha como desenha as outras. A área na tela vem de
`dados/areas-artes.json` pelo tipo, então a fila funciona igual.

### As telas

- **Estúdio:** dois botões novos no painel da arte, **Copiar código** e
  **Atribuir ao jogo** (escolhe o jogo e, opcionalmente, o time). Um campo
  **Colar código** que abre a arte com os dados.
- **Registro, em "＋ Peça":** uma lista **Artes deste jogo** (e do time) lida
  da aba ARTES, e um campo **Colar código**. A peça entra no plano como as
  outras manuais, com o rótulo da arte.

## 2. Ficha do jogo com IA

Uma ficha estruturada por jogo, pensada para uma IA preencher a partir de
texto livre (mensagens do grupo, anotações, áudio transcrito). Ela não vira
peça direto: vira **códigos de arte**, e entra no plano pelo caminho de cima.

### Formato da ficha

```json
{
  "formato": "copa-revoada-ficha/1",
  "jogo": "2026-08",
  "pre": {
    "local": null,
    "hora": null,
    "condicoes": {"tempo": null, "temperatura": null, "gramado": null},
    "arbitragem": [{"funcao": "Árbitro", "nome": null}],
    "sala_var": [{"funcao": "VAR", "nome": null}],
    "escalacoes": {
      "casa": [{"jogador": null, "posicao": null}],
      "fora": [{"jogador": null, "posicao": null}]
    },
    "formacao": {"casa": null, "fora": null},
    "proxima_partida": {"data": null, "chamada": null}
  },
  "pos": {
    "campeao": null,
    "premiacao": [{"trofeu": null, "jogador": null}],
    "destaques": [{"jogador": null, "motivo": null}],
    "lances_var": [{"seg_video": null, "decisao": null}],
    "penaltis": [{"seg_video": null, "batedor": null, "convertido": null}],
    "disputa_penaltis": null
  },
  "fontes": ["de onde a IA tirou cada informação"]
}
```

### Regras para a IA

- **Campo que a IA não souber fica `null`.** Nunca preencher por suposição.
- Jogador é o **apelido do site**. Nome que não bate com ninguém vai para uma
  lista `nao_reconhecidos`, e não para o campo.
- Cada informação diz a **fonte** (qual mensagem, qual anotação).
- A ficha passa por você antes de virar arte.

### Da ficha ao plano

Um botão no Registro, **Abrir ficha do jogo**, lê o arquivo, mostra o que
veio e o que está vazio, e gera os códigos de arte. Artes com campo vazio
aparecem na lista riscadas, com o motivo, como as etiquetas de hoje.

## 3. Mapa das 37 artes

As 36 do Estúdio, mais o ranking de cagadas, que entrou na Fase 1.

| Arte | De onde vem o dado | Fase |
|---|---|---|
| Gol — barra inferior | Registro | 1 (pronta) |
| Gol — tela cheia | Registro | 1 (pronta) |
| Histórico de gols na copa | planilha | 1 (pronta) |
| Artilheiro do dia | Registro | 1 (pronta) |
| Falta | Registro (barra) | 1 (só na bateria) |
| Checagem do VAR | ficha (`lances_var`) | 2 |
| Pênalti | ficha (`penaltis`) | 2 |
| Cartão | Registro, com a cor | 1 (pronta) |
| Placar da disputa de pênaltis | ficha (`disputa_penaltis`) | 2 |
| Chamada do batedor | ficha (`disputa_penaltis`) | 2 |
| Placar de abertura | Registro / planilha | 1 (pronta) |
| Fim de jogo | Registro | 1 (pronta) |
| Fim do 1º tempo | Registro / súmula | 1 (pronta) |
| Escalação do time | ficha (`escalacoes`) ou código | 2 |
| Formação no campo | ficha (`formacao`) ou código | 2 |
| Substituição | Registro | 1 (pronta) |
| Mapa tático do lance | código (desenho à mão no Estúdio) | 2 |
| Chance de gol (xG) | código (desenho à mão) | 2 |
| Jogada completa | código (desenho à mão) | 2 |
| Análise do jogo | Registro | 1 (pronta) |
| Comparativo do jogo | súmula | 1 (pronta) |
| Corrida de chutes | súmula | 1 (pronta) |
| Quem mais apareceu | súmula | 1 (pronta) |
| Desempenho de um jogador | súmula | 1 (pronta) |
| Elenco do time | planilha | fora do vídeo (redes sociais) |
| Placar de transmissão | Registro | 1 (pronta) |
| Condições de jogo | ficha (`condicoes`) | 2 |
| Marco da copinha | planilha (cálculo do Nº gol) | 2 — o cálculo por gol ainda não existe |
| Especial 100 Gols | código | fora do vídeo (peça especial) |
| Premiação | ficha (`premiacao`) + planilha | 2 |
| Campeão | ficha (`campeao`) + planilha | 2 |
| Próxima partida | ficha (`proxima_partida`) | 2 |
| Arbitragem | ficha (`arbitragem`) | 2 |
| Sala do VAR | ficha (`sala_var`) | 2 |
| Replay | Registro | 1 (pronta) |
| Ficha do jogador | planilha | 1 (pronta, peça à mão) |
| Ranking de cagadas | Registro | 1 (pronta) |

## 4. O que a Fase 2 depende de decidir

1. **Apps Script v3.** A aba ARTES exige. E tem um motivo a mais: hoje a
   aba `LANCES` da planilha guarda 8 colunas, e **perde a assistência, a cor
   do cartão, quem saiu na substituição e o fim do replay** — os campos novos
   da Fase 1. No jogo avulso não importa (não vai para a planilha). Num jogo
   da copa marcado e gravado na planilha, esses campos ficam só no navegador e
   no arquivo baixado. A v3 acrescenta uma coluna `extras` e resolve os dois.
2. **Onde a arte mora:** a recomendação acima (plano + aba ARTES), ou outra.
3. **Ficha com IA:** se o formato acima serve, ou se falta algum campo.
4. **Marco da copinha:** só entra quando o cálculo do Nº gol sair da
   planilha sem suposição — precisa da ordem dos gols de todos os jogos, que
   a planilha não guarda hoje.
