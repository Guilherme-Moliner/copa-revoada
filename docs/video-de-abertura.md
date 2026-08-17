# Abertura do estádio — como fazer aquele zoom do espaço até o campo

Você mandou os frames certos. Vale começar por uma coisa que muda tudo no seu planejamento.

---

## O que aquele vídeo do EA realmente é

Repara no canto inferior esquerdo dos seus prints: escrito **Google**, e embaixo *"Data SIO, NOAA, U.S. Navy, NGA, GEBCO · Landsat / Copernicus"*. Aquilo não é IA e não é render. É **Google Earth Studio** — a ferramenta que a própria Google fez pra animar câmera dentro do Google Earth. O EA anima a câmera lá, exporta e compõe os escudos e as caixas verdes por cima no After Effects.

Isso é ótima notícia: **a parte difícil é gratuita e o resultado é geograficamente correto**, o que nenhum modelo de vídeo consegue entregar hoje. Nenhum gerador vai desenhar a Ponte Hercílio Luz no lugar certo, nem os dois campos do Paula Ramos dentro da rede de proteção.

Minha recomendação: **Earth Studio pro movimento de câmera, Gemini pros planos de atmosfera, DaVinci pra juntar.**

---

## Caminho A — Earth Studio (o do EA)

**earth.google.com/studio** · gratuito, roda só no Chrome desktop, e você precisa entrar com a conta Google e pedir acesso por um formulário. A Google responde por e-mail aceitando ou não — vale pedir hoje, porque a aprovação demora.

Dois avisos que importam pra você:

- A licença cobre uso jornalístico, educacional, de pesquisa e sem fins lucrativos. A copinha entre amigos cabe; se um dia virar patrocínio, muda a conversa.
- A atribuição do Google e dos provedores de imagem tem que ficar **na tela o tempo todo** do trecho que usa a imagem. É aquela linha pequenininha do canto — não apaga.
- O export de **dados de câmera 3D só sai pro After Effects**. No DaVinci você importa a sequência de imagens normalmente, mas não ganha o track 3D de graça. Pra fixar o escudo em cima do campo, você resolve no Fusion com o tracker planar, ou simplesmente com keyframe na mão — são 4 segundos, dá pra fazer no olho.

### A sequência, plano a plano

Coordenada de chegada: **-27.5933, -48.5175** — os dois campos do Paula Ramos.

| # | plano | altitude | dur |
|---|---|---|---|
| 1 | Terra inteira, Atlântico Sul centralizado, giro lento | 12.000 km | 4s |
| 2 | Mergulho no Brasil, litoral sul resolvendo | 12.000 → 800 km | 4s |
| 3 | Santa Catarina, câmera inclinando de topo pra oblíqua | 800 → 60 km | 3s |
| 4 | Ilha de Florianópolis, Ponte Hercílio Luz entrando no quadro | 60 → 4 km | 4s |
| 5 | Trindade, giro sobre os telhados, campos aparecendo | 4 km → 600 m | 4s |
| 6 | Plano baixo sobre os dois campos, câmera quase parada | 600 → 250 m | 4s |

No Earth Studio: `File > New > Blank Project`, 1920×1080, 30 fps. Coloca um keyframe de câmera no início e outro no fim de cada trecho, e usa **Ease In/Ease Out** em todos — o que dá o peso cinematográfico é a desaceleração, não a velocidade.

O truque do plano 6: deixa a câmera **quase parando** nos últimos 30 quadros. É onde o escudo entra por cima.

Exporta como **sequência PNG**, joga a pasta no DaVinci como *image sequence* — exatamente o mesmo fluxo que você já usa com as artes do Estúdio.

---

## Caminho B — Gemini

O gerador de vídeo do Gemini é bom em atmosfera e péssimo em geografia e em texto. Então usa ele pro que ele faz bem: **as transições e o clima**, não os planos que precisam ser o lugar certo.

Duas coisas antes de colar o prompt:

- **Escreve em inglês.** Os modelos de vídeo foram treinados com legendas majoritariamente em inglês e respondem visivelmente melhor.
- **Não pede texto nem escudo dentro do vídeo.** Vai sair borrado e torto. Escudo, nome do campo e placar entram por cima, no DaVinci, com as fontes que você já usa.

### Prompt principal — o mergulho

```
Cinematic aerial descent, single continuous camera move, no cuts.
Opening frame: planet Earth seen from orbit against black space, South
America centred, sunlit western edge, thin blue atmospheric rim.
The camera falls toward the planet, accelerating, then decelerating.
It punches through a broken layer of low cumulus clouds, moisture
streaking past the lens.
It emerges over a green subtropical coastal city on an island: red
clay rooftops, dense low buildings, palm trees, a wide bay of dark
blue water.
The move ends slowing to a near hover roughly 200 metres above two
adjacent rectangular synthetic-turf football pitches, side by side,
enclosed by tall dark protective netting, surrounded by apartment
blocks and warehouse roofs.
Late morning, high sun, clean warm light, faint haze.
Photorealistic satellite-to-drone aerial look, natural colour, subtle
lens vignette, no text, no logos, no people visible.
Slow deliberate pacing, heavy camera weight.
```

### Prompts de apoio — os planos curtos

O gerador entrega trechos curtos, então é melhor pedir peças separadas e cortar entre elas do que tentar um plano só de 25 segundos.

**Abertura no espaço**
```
Slow orbital rotation of planet Earth against black space, South
America and the South Atlantic in frame, sharp terminator line between
day and night, city lights glowing on the dark side, thin blue
atmospheric glow on the horizon. Photorealistic, NASA satellite
footage look, very slow drift, no text.
```

**Atravessando as nuvens**
```
First-person camera falling straight down through a thick layer of
white cumulus clouds at high speed, sunlight breaking through gaps,
wisps of vapour streaking past the lens, revealing a green coastal
landscape and dark blue ocean far below. Photorealistic, wide lens,
slight motion blur, no text.
```

**Chegada no campo**
```
Low aerial hover 150 metres above two adjacent synthetic-turf football
pitches with white markings, enclosed by tall black protective netting,
seen from a slightly oblique angle. Surrounding urban blocks, warehouse
roofs, scattered palm trees. Late morning sun casting long soft
shadows across the turf. The camera drifts forward very slowly and
comes to rest. Photorealistic drone footage, warm natural colour
grade, no people, no text, no logos.
```

**Passagem de textura pra cortar entre planos**
```
Extreme close-up of synthetic football turf, green plastic blades with
black rubber infill, a white painted line crossing the frame. Shallow
depth of field, camera glides sideways low over the surface. Morning
light, photorealistic, no text.
```

### Quando o Gemini errar

Ele vai errar. Coisas que costumam resolver:

- saiu genérico demais → aumenta os detalhes concretos (a rede preta alta em volta, os dois campos lado a lado, os telhados de galpão)
- inventou texto ou placar → repete `no text, no logos, no signage` no fim
- movimento rápido demais → `slow deliberate pacing, heavy camera weight, no whip pans`
- pessoas aparecendo → `empty, no people`

---

## Os elementos visuais que você precisa juntar

### Você já tem

| item | onde | pro quê |
|---|---|---|
| `dentro26-escudo.png` | `img/times/` | o escudo que flutua sobre o campo |
| `ferroviagra26-escudo.png` | `img/times/` | o escudo do adversário, ao longe |
| Logo da Copa Revoada | já em base64 no `index.html` | assinatura final |
| Archivo Black + Barlow Condensed | Google Fonts, já carregadas | nome do campo, cidade |
| Paleta `--gold #F2B01E` / `--grass-l #2BE07A` | CSS do app | a caixa verde igual à do EA |
| Prints de satélite do Paula Ramos | os que você subiu | referência de enquadramento pro plano final |

### O que falta

**Os escudos precisam ser PNG com fundo transparente e pelo menos 1024 px.** No frame 6 do EA o escudo do Arsenal ocupa quase um terço da altura da tela — se o seu arquivo for pequeno, vai pixelar feio. Se os seus estiverem baixos, vale redesenhar em vetor.

**Uma foto boa do campo do chão.** Serve pro último frame, o corte do aéreo pra dentro do jogo. Tira numa manhã de sol, do fundo, com o gol enquadrado.

**A caixa verde do canto.** No EA ela traz: nome do estádio em caixa alta, uma linha preta fina embaixo, e os dois escudos lado a lado. Isso você monta no próprio Estúdio — é uma arte nova de 20 linhas, e sai coerente com o resto do pacote em vez de imitada.

**A marca d'água do Google.** Se usar Earth Studio, ela é obrigatória. Melhor tratar como parte do design: canto inferior esquerdo, pequena, e o resto da tua identidade se organiza em volta dela.

### O que dá pra pular

Nome de cidade espalhado pelo mapa, tipo o frame do Liverpool/Manchester/Nottingham. Aquilo funciona porque a Premier League tem 20 clubes em 20 cidades. Sua copa acontece toda em Florianópolis — repetir isso seria imitar a forma sem a razão dela existir.

Se quiser um plano com informação de verdade no meio do mergulho, o que a sua copa tem e a Premier League não é **história**: seis anos, 13 jogos, três campos. Um plano rápido marcando Elase, Paula Ramos e Kretzer no mapa da ilha, com o número de jogos em cada um, diz algo que só a Copa Revoada pode dizer.

---

## Montagem sugerida

```
0:00  Terra girando                      Earth Studio ou Gemini
0:04  Mergulho, Brasil resolvendo        Earth Studio
0:08  Nuvens rasgando                    Gemini
0:10  Ilha, ponte entrando no quadro     Earth Studio
0:14  Trindade, campos aparecendo        Earth Studio
0:18  Plano baixo, câmera parando        Earth Studio
0:20  Escudos entram flutuando           DaVinci (Estúdio)
0:22  Caixa verde: PAULA RAMOS           DaVinci (Estúdio)
0:25  Corte seco pra imagem do jogo
```

Vinte e cinco segundos. Passou disso, cansa antes da bola rolar.
