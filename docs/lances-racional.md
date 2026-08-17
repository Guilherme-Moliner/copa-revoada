# Estúdio · Lances — racional e integração (v2)

Acompanha `estudio-lances.html`. Para a explicação em linguagem de grupo de WhatsApp, ver `como-funciona-a-chance-de-gol.md` — esse é o que vale mandar pros amigos.

**O que mudou da v1:** o mapa e a análise viajam em código; o chute ganhou campo inteiro e os dois lados; o clima ganhou entrada e saída; o placar foi refeito do zero no formato de transmissão; e entrou a Análise do jogo.

---

## 1. O campo do Paula Ramos

Coordenadas (o pino "Paris Saint-Germain Academy" no Maps): **-27.5933, -48.5175**, Av. Madre Benvenuta 340, Trindade. São dois campos de futebol suíço idênticos, sintéticos, fechados por rede.

### O que consegui medir pelo satélite

Segmentei a grama sintética (cor bem distinta das árvores: R≈83 G≈107 B≈109 contra R≈98 G≈132 B≈107) e ajustei o menor retângulo de cada campo:

| | pixels | proporção |
|---|---|---|
| Campo norte | 647 × 270 | 2,40 : 1 |
| Campo sul | 653 × 286 | 2,28 : 1 |

**A proporção 2,3–2,4 : 1 é firme** — sai direto da imagem, não depende de escala.

### O que não fecha

A escala absoluta. Quatro referências na mesma imagem discordam:

- vagas de estacionamento (2,4 m): ≈ 0,102 m/px → campo de **65 m**
- vans (5,9–7 m): ≈ 0,101 m/px → **65 m**
- profundidade da grande área (se for 6 m): ≈ 0,076 m/px → **49 m**
- boca do gol (se for 5 m): ≈ 0,083 m/px → **54 m**

O borrão do satélite é de 2–3 px; num objeto de 60 px já dá 5% de erro, e nas marcações finas muito mais. Então o campo tem **entre 50 e 65 m de comprimento e 22 a 28 m de largura**. Padrão do app: **57 × 24 m**, boca de 4 m.

### Travar de vez (2 minutos)

Google Earth Pro → cola `-27.5933, -48.5175` → ferramenta Régua → mede fundo a fundo, lateral a lateral e a boca do gol → digita no painel Campo. Todo o resto do sistema lê desses três números.

Vale medir o Elase e o Kretzer também e guardar como preset por estádio — o `DADOS.jogos[].estadio` já existe.

**Azimute do eixo maior:** ≈ 156° / 336°. Os campos ficam girados uns 24° em relação ao norte.

---

## 2. O racional da chance de gol

### A estrutura

Tudo somado em **log-odds**, só no fim vira porcentagem:

```
z  = base geométrica + soma dos modificadores
xG = 1 / (1 + e^-z)
```

Somar em log-odds resolve duas coisas: o resultado nunca escapa de 0–100%, e cada fator vira um número explicável sozinho sem que a soma estoure.

### A base: só geometria

```
z₀ = 1,47 · ln(θ°) − 0,080 · d − 4,21
```

- **d** = distância da bola ao meio do gol, em metros
- **θ** = ângulo que a boca do gol ocupa visto da bola

Os coeficientes saíram de resolver o sistema para três âncoras: **5 m de frente ≈ 47%**, **12 m ≈ 10%**, **20 m ≈ 2%**. A constante foi ajustada pro pênalti (7 m, goleiro na linha) cair em ~34%.

### Goleiro e zagueiros: medidos

Para cada obstáculo, projeta-se a **sombra sobre a linha do gol**, do ponto de vista da bola, e mede-se quanto da boca fica tapado:

```
k         = dx_gol / dx_obstáculo
y_centro  = y_bola + (y_obst − y_bola)·k
meia_som  = raio · k
sombra    = [y_centro − meia_som, y_centro + meia_som] ∩ [−boca/2, +boca/2]
```

As sombras são unidas antes de somar, então dois zagueiros enfileirados não contam duas vezes.

**O alcance do goleiro cresce com a distância do chute**, porque de perto ele não tem tempo de esticar:

```
alcance_útil(d) = 1,9 · (1 − e^(−d/8))
```

Aos 5 m cobre 0,88 m; aos 20 m, 1,74 m. É o que explica por que sair do gol funciona.

### Os modificadores

| fator | peso em z | origem |
|---|---|---|
| Goleiro tapando o gol | −1,70 × fração | geometria, automático |
| Defesa na frente | −1,15 × fração | geometria, automático |
| Colocação do goleiro | −0,55 × (−1 a +1) | julgamento |
| Goleiro sem visão | +0,30 | automático |
| Pressão no batedor | −0,32 por zagueiro a < 2,2 m | automático |
| Quem chutou | +0,30 × (nota − 3) | 1 a 5 |
| Pé ruim / cabeça / de primeira | −0,35 / −0,45 / −0,28 | seleção |
| Contra-ataque / rebote / dividida | +0,40 / +0,30 / +0,55 | seleção |
| Bola parada | −0,20 | seleção |

### A nota do batedor sai dos seus dados

Você já tem `gols`, `jogos` e `presencas` em `DADOS.jogadores`. Com encolhimento bayesiano pra não premiar quem jogou duas vezes:

```js
function notaBatedor(p){
  const media = 0.62;                      // gols por jogo do elenco
  const peso  = 6;                         // jogos "fantasma" puxando pra média
  const taxa  = (p.gols + media*peso) / (p.jogos + peso);
  const z     = (taxa - media) / 0.45;
  return clamp(Math.round(3 + z), 1, 5);
}
```

Recalcula sozinho a cada temporada e ninguém reclama de favorecimento.

### A decomposição — novidade da v2

O `calculaXG()` agora devolve `passos`: o modelo aplica **um fator de cada vez** e registra quantos pontos percentuais cada um moveu.

```js
let z = z0, ant = sig(z0);
for(const [nome, w] of Object.entries(m)){
  z += w;
  passos.push({ nome, w, pp: (sig(z) - ant) * 100 });
  ant = sig(z);
}
```

Isso aparece de duas formas: como barras no painel lateral, e — se você ligar **"Mostrar a conta na arte"** — dentro do próprio PNG que vai pro vídeo. É o que transforma o número numa coisa defensável ao vivo em vez de uma caixa-preta.

Nota técnica: a ordem importa, porque a sigmoide não é linear. Os fatores são aplicados na ordem em que estão no objeto, do geométrico pro subjetivo. Não é uma decomposição de Shapley — é uma ordem fixa e declarada. Pra a nossa finalidade, resolve.

### xG e xGOT

O número grande é **antes do chute**. O **xGOT** entra a execução (`+0,62 × nota de −2 a +2`) e responde: dado como ele pegou na bola, qual era a chance? O par vale mais que qualquer um sozinho.

### Como se comporta

| cenário | dist | gol livre | xG |
|---|---|---|---|
| 2 m, gol vazio | 2,0 m | 100% | 90,4% |
| 5 m, gol vazio | 5,0 m | 100% | 71,9% |
| 5 m, um contra um | 5,0 m | 37% | 46,7% |
| 5 m, goleiro no poste errado | 5,0 m | 85% | 66,4% |
| 7 m, goleiro na linha | 7,0 m | 43% | 34,3% |
| 12 m de frente | 12,0 m | 19% | 9,8% |
| 12 m, ângulo fechado | 12,0 m | 23% | 7,1% |
| 15 m com dois na frente | 15,0 m | 0% | 1,8% |
| 20 m de frente | 20,0 m | 8% | 2,2% |
| 30 m de frente | 30,0 m | 4% | 0,5% |

### Campo inteiro e os dois lados — novidade da v2

A geometria virou simétrica. `chute.lado` vale +1 (ataca o gol da direita) ou −1 (o da esquerda), e a matemática toda trabalha num espaço espelhado:

```js
const L = chute.lado, gxr = L*CAMPO.comp/2;
const dx = (gxr - b.x) * L;          // sempre > 0 quando a bola está antes do gol
const ox = (o.x - b.x) * L;          // idem pros obstáculos
```

Um único sinal resolve. `chute.visao` escolhe entre meia quadra e campo inteiro, e trocar de lado espelha as peças automaticamente (`o.x = -o.x`) pra você não ter que reposicionar tudo na mão.

### O aviso honesto

Não é um xG treinado. É um modelo de forma sensata calibrado no olho. Se um dia quiser calibrar de verdade: marca 150–200 chutes com posição, goleiro e resultado — a aba **Análise do jogo** já é o lugar certo pra isso — e roda uma regressão logística nesses mesmos regressores. Os coeficientes daqui viram o chute inicial.

---

## 3. Clima

**Open-Meteo**, sem chave, CC BY 4.0. O app escolhe a rota sozinho:

- data até ~80 dias atrás → `api.open-meteo.com/v1/forecast`
- mais antiga → `archive-api.open-meteo.com/v1/archive` (ERA5, desde 1940)

O arquivo ERA5 tem ~5 dias de atraso, por isso o corte.

```
https://api.open-meteo.com/v1/forecast
  ?latitude=-27.5933&longitude=-48.5175
  &start_date=2026-08-08&end_date=2026-08-08
  &hourly=temperature_2m,apparent_temperature,relative_humidity_2m,
          precipitation,weather_code,wind_speed_10m,cloud_cover
  &timezone=America/Sao_Paulo
```

### A animação — novidade da v2

Duas peças pequenas fazem todo o trabalho e servem pras outras artes também:

```js
function envelope(u, ent=.14, sai=.14){        // opacidade de entrada/saída
  const A = u<ent ? easeOut(u/ent) : 1;
  const B = u>1-sai ? 1-easeIO((u-(1-sai))/sai) : 1;
  return {a:clamp(A*B,0,1), e:A};
}
function entra(u, i, total, ent=.30){          // escalonamento entre blocos
  const passo = ent/Math.max(total,1);
  return clamp(easeOut(clamp((u - i*passo)/(ent - passo*(total-1)/2), 0, 1)), 0, 1);
}
```

Os seis blocos do boletim entram escalonados, cada um subindo 26 px enquanto aparece. A curva de temperatura se desenha da esquerda pra direita com um `clip()` que abre — mais convincente que fade puro, e é uma linha de código.

**Ideia pro futuro:** rodar isso pros 13 jogos do `DADOS.jogos` e guardar no próprio JSON. Aí você ganha uma estatística que ninguém tem — *"o Garopaba fez 9 gols num jogo de 31°"*.

---

## 4. Placar de transmissão — refeito

O seu modelo antigo era caixa preta e branca empilhada. O novo segue a lógica do scorebug da Copa: **uma pílula única, arredondada, com o relógio numa pastilha separada.**

### Anatomia

```
        ┌─────────── COPA REVOADA 2026 — FINAL ───────────┐
   ╭────┴──────────────────────────────────────────────┴──╮  ╭──────────╮
   │ [esc] DEN   1  (⬤)  1   FER [esc]                    │  │ 22:36 +6 │
   ╰───────────────────────────────────────────────────────╯  ╰──────────╯
```

Larguras derivadas de uma única variável `h`, então trocar o tamanho não quebra nada:

| peça | largura |
|---|---|
| escudo | `h × 0,78` |
| sigla | `h × 1,42` |
| placar | `h × 0,62` |
| emblema central | `h × 0,66` |
| pastilha do relógio | `h × 2,05` |

O gradiente de cor de cada time sai da borda e morre no meio — é o que dá a leitura instantânea de quem é quem sem precisar de escudo grande.

### A animação de gol

Linha do tempo dentro de `u`:

| trecho | o que acontece |
|---|---|
| 0 → 0,20 | pílula entra deslizando com fade |
| 0,30 → 0,64 | flash dourado no lado que marcou, subindo e descendo |
| ~0,40 | o número **vira** — pop de escala 1,55× |
| 0,30 → 0,64 | faixa "G O L · NOME DO TIME" varre por baixo, com um brilho correndo |
| 0,86 → 1 | sai |

Detalhe que importa na hora de usar: **você digita o placar já somado.** A animação subtrai um gol, mostra o antigo e faz virar. Você não precisa exportar dois estados.

### Escudos de verdade

O `escudo()` desenha um brasão com as duas cores do time e a sigla, porque no protótipo não tenho os PNGs. No seu app, `t.escudo` já aponta pro arquivo:

```js
function escudo(c,x,y,r,t){
  const img = IMGS[t.escudo];
  if(img && img.complete){ c.drawImage(img, x-r, y-r, r*2, r*2); return; }
  /* … desenho vetorial como reserva … */
}
```

Vale manter o desenho vetorial como reserva — dois dos seus times ainda estão com `escudo: ""`.

### Enquadramento

Testei as 27 combinações de escala (0,6 / 1,0 / 1,6), posição (topo esquerda / topo centro / rodapé) e evento. Todas cabem em 1920×1080 no estado assentado. No topo esquerdo a pílula **ancora pela borda esquerda** em vez de centralizar, senão em 1,6× ela vazava.

---

## 5. Análise do jogo — módulo novo

### Como se usa durante a partida

Marca minuto, time, tipo do lance, quem foi e o xG. Cada tipo já vem com um xG padrão razoável, e o botão **"Mandar pra Análise"** da aba Chute leva o número exato daquele lance montado na tela.

Tipos: gol, chute no gol, chute pra fora, chute bloqueado, chance perdida, falta, escanteio, cartão, defesaça.

### Três vistas do mesmo dado

**Corrida de xG** — a curva escada acumulada dos dois times. É a que conta a história do jogo num quadro só: quem pressionou quando, quem fez o gol contra a corrente. Os gols viram bolotas com o nome do autor.

**Números** — barras espelhadas no estilo do FC, com gols, xG, finalizações, no alvo, faltas, escanteios e cartões. Embaixo, aproveitamento e o **saldo contra o xG** — o número que diz se o time foi eficiente ou se comeu bola.

**Chutes** — linha do tempo com uma barra por finalização, altura proporcional ao xG do lance, time de cada lado do eixo.

### O modelo de dados

```js
{ min: 19, t: 'A', tipo: 'gol', j: 'Letti', xg: 0.22 }
```

Cinco campos. É de propósito: cabe no código de compartilhamento e mapeia direto pro `DADOS.escalacoes` que você já tem.

### Onde isso vai dar

Quando você tiver 5 ou 6 jogos marcados assim, aparecem coisas que hoje ninguém sabe: quem cria chance e não converte, quem só chuta de longe, qual time começa melhor. E é o conjunto de dados que permite calibrar o xG de verdade.

---

## 6. O código de compartilhamento

O mapa tático e a análise viajam num código de texto. Nada de servidor, nada de conta.

```
JSON → deflate-raw (CompressionStream nativa) → base64 url-safe → "RVD1.<dados>"
```

`RVD0` é a reserva pra navegador sem `CompressionStream` — o mesmo JSON sem comprimir.

Tamanhos reais: **um mapa de 7 peças e 4 atualizações dá 467 caracteres. Uma análise de 11 lances dá 343.** Cabe numa mensagem de WhatsApp sem quebrar.

O que entra no pacote:

- **mapa**: título, subtítulo, autor, número de atualizações, duração, as peças com todas as posições, e as medidas do campo
- **análise**: título, times, duração, autor, vista, e a lista de lances

As posições são arredondadas em 2 casas e os eventos viram array posicional (`[min, time, tipo, jogador, xg]`) em vez de objeto — economiza uns 40% do tamanho.

O importador confere o tipo antes de aplicar: se você colar um código de análise na aba do mapa, ele avisa em vez de quebrar. Código inválido também é recusado com mensagem legível.

**Nota de campo:** o código do mapa carrega as medidas do campo junto. Se o amigo tiver medido diferente, o mapa dele chega com a medida dele — e os campos do painel se atualizam. É de propósito: o mapa só faz sentido na escala em que foi desenhado.

---

## 7. Encaixando no `index.html`

Protótipo feito pra ser recortado, não copiado inteiro. Mesmas variáveis de cor, mesmas fontes, mesmo canvas 1920×1080.

### O que dá pra levar direto

| do protótipo | pra onde |
|---|---|
| `CAMPO`, `projecao()`, `desenhaCampo()` | topo do script, perto do `DADOS` |
| `geometria()`, `calculaXG()`, `PARTE`, `JOGADA` | junto das funções de cálculo |
| `envelope()`, `entra()`, `easeOut`, `easeIO` | utilidades — **servem pra todas as artes que você já tem** |
| `pilula()`, `escudo()` | junto das artes de placar |
| `TIPOS`, `estatisticas()`, `curvaXG()` | novo bloco de análise |
| `fazCodigo()`, `leCodigo()`, `b64`, `unb64` | utilidades |
| as cinco `desenhaX()` | junto das outras artes |
| `roundRect`, `txt`, `larguraTxt`, `cond/black/body` | você já tem equivalentes — **usa os seus** |

### Novas opções no `#f-tipo`

```html
<optgroup label="Lances">
  <option value="mapa">Mapa tático do lance</option>
  <option value="chance">Chance de gol</option>
</optgroup>
<optgroup label="Partida">
  <option value="placar2">Placar de transmissão</option>
  <option value="clima">Condições de jogo</option>
  <option value="ficha">Ficha do jogo</option>
</optgroup>
```

### O que precisa de atenção

**A assinatura mudou.** Na v1 o mapa recebia `t` em keyframes. Agora **todas** as artes recebem `u` de 0 a 1, e cada módulo converte pro que precisa. `DURACAO()` diz quantos segundos aquela arte dura. Isso deixa o mesmo botão de exportar sequência servir pra todas.

**O arraste na prévia.** O Estúdio atual não tem interação no canvas. Os handlers de `pointerdown/move/up` e a `pontosArrastaveis()` vão junto, e o canvas precisa de `touch-action:none` no CSS — senão no celular o dedo rola a página em vez de arrastar a peça.

**O painel não pode ser repintado a cada render.** Se `render()` chamar `pintaPainel()`, o input perde o foco no meio da digitação. Por isso existe `atualizaLeitura()`, que troca só os números e as barras da decomposição.

**A sequência PNG.** O protótipo baixa quadro a quadro, o que dispara um monte de downloads. O seu Estúdio já exporta em `.zip` — usa a sua. Só precisa passar `u` de 0 a 1.

**`CompressionStream` no Safari antigo.** O fallback `RVD0` cobre, mas gera código ~3× maior. Se o pessoal usa iPhone velho, vale testar antes de prometer.

**Os campos `f-dist` e `f-xg`** da arte de replay que já existe podem passar a ser preenchidos pelo módulo de chute em vez de digitados na mão.

### O que ficou de fora de propósito

- **Escudos e fotos**: `t.escudo` e `p.foto` já existem no seu `DADOS` — é trocar o desenho vetorial por `drawImage`.
- **Preset de campo por estádio**: um objeto `MEDIDAS = { 'Paula Ramos': {...}, 'Elase': {...}, 'Kretzer Indor': {...} }` lido a partir de `DADOS.jogos[].estadio`.
- **Persistir a análise**: hoje ela vive na memória da aba. O caminho natural é gravar os eventos direto no `DADOS` como uma coleção nova (`DADOS.lances`), aí ela entra nas estatísticas de jogador junto com o resto.
- **Cronômetro rodando**: o placar tem o relógio como texto. Se quiser que ele conte sozinho durante a live, é um `setInterval` e um campo de "começou às".
