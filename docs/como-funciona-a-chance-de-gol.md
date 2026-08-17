# Como a Revoada calcula a chance de gol

*Pra mandar no grupo. Sem fórmula, sem enrolação.*

---

## A pergunta

Toda vez que alguém chuta, dá pra perguntar: **de cada 100 vezes que um jogador nosso chutasse exatamente dali, naquela situação, quantas viravam gol?**

Se a resposta é 40, o lance vale **0,40 de gol esperado** — ou 40%. É isso que o número na tela significa. Nada mais.

Um jogo pode terminar 1×0 com o vencedor somando 0,6 de gol esperado e o perdedor 2,4. Aí você não precisa discutir: os números dizem quem mereceu.

---

## O que a conta olha

### Primeiro, só a geometria

Duas coisas mandam mais que todo o resto junto:

**Quão longe você está.** Óbvio. Cada metro a mais derruba a chance.

**Quanto de gol você enxerga.** Essa é a que o pessoal esquece. Chute de 12 m de frente e chute de 12 m lá da quina são a mesma distância e chances completamente diferentes — porque da quina o gol vira uma frestinha.

O app mede isso literalmente: traça uma linha da bola até cada trave e vê que abertura sobra no meio.

### Depois, quem está no caminho

Aqui está a parte que ninguém mais faz e que a nossa faz.

O app pega o goleiro e cada zagueiro, e **projeta a sombra deles em cima da linha do gol**, do ponto de vista da bola. Depois mede: dos 4 metros de boca de gol, quantos estão tapados?

É por isso que na tela aparece "goleiro tapa 63%". Não é chute — é a conta de quanto do gol dá pra ver de onde a bola estava.

**E o alcance do goleiro não é fixo.** De 20 metros ele tem tempo de esticar tudo, os quase dois metros de envergadura. De 5 metros ele mal tira o pé do lugar. A conta encolhe o alcance conforme o chute é mais perto — é exatamente por isso que sair do gol funciona, e por que um chute rasteiro de 5 metros no canto entra mesmo com o goleiro "bem posicionado".

### Por último, o resto

Coisas que a geometria não vê e que a gente marca na mão:

- **Quem chutou.** Nota de 1 a 5. Sai dos gols por jogo do cara na copa, então não tem favorecimento — é o histórico dele.
- **Como chutou.** Pé ruim, cabeça e de primeira derrubam. Pé bom não mexe.
- **A situação.** Contra-ataque e dividida com o goleiro sobem; bola parada desce.
- **A colocação do goleiro.** Se ele ficou plantado ou saiu bem.
- **Zagueiro na cara do batedor.** Pressão derruba.
- **Zagueiro tapando a visão do goleiro.** Essa *sobe* a chance — o goleiro reage tarde.

Cada um desses mexe pouco. Quem manda no número é a geometria.

---

## Uns exemplos pra calibrar a cabeça

| situação | chance |
|---|---|
| 2 m, gol vazio | **90%** |
| 5 m, gol vazio | **72%** |
| 5 m, um contra um com o goleiro | **47%** |
| 5 m, goleiro no poste errado | **66%** |
| 7 m de frente, goleiro na linha | **34%** |
| 12 m de frente | **10%** |
| 12 m de ângulo fechado | **7%** |
| 15 m com dois zagueiros na frente | **2%** |
| 20 m de frente | **2%** |
| 30 m de frente | **0,5%** |

Repara no pulo entre 5 m e 12 m. É de longe o maior salto da tabela. **Chegar mais perto vale mais que qualquer outra coisa que você faça.**

E repara que 20 m e 30 m dão quase a mesma coisa. Depois de certa distância, tanto faz — já era.

---

## Os dois números: xG e xGOT

Eles respondem perguntas diferentes e é o par que vale.

**xG** é *antes* do chute. Não sabe se a bola foi no ângulo ou na rua. Só olha a posição e a situação.

**xGOT** entra depois: *dado como ele pegou na bola*, qual era a chance?

Aí você lê o jogo:

- xG **8%**, xGOT **45%** → chutaço. Ele achou onde não tinha.
- xG **60%**, xGOT **12%** → perdeu um gol feito.
- xG **60%**, xGOT **70%**, não entrou → o goleiro fez milagre.

---

## O aviso que precisa estar aqui

Isso **não é o xG da Premier League**. Os de verdade saem de centenas de milhares de finalizações rotuladas por gente pagada pra isso.

O nosso é um modelo de forma sensata, calibrado no olho pra dar números que batem com o que a gente vê no Paula Ramos. Ele tem uma vantagem sobre o profissional, e é de propósito: **cada número é explicável**. Você consegue abrir a conta e ver de onde saiu cada ponto percentual — o app até desenha isso na arte se você ligar a opção.

Então serve pra discutir jogo. Não serve pra apostar, e quem perdeu o gol feito continua tendo perdido o gol feito.

---

## Se quiser brincar

Abre o Estúdio, aba **Chute & xG**, e arrasta as peças. Vale testar:

1. Põe a bola a 12 m de frente. Agora arrasta o goleiro dois metros pra fora do gol e vê a chance despencar.
2. Deixa o goleiro parado e leva a bola de 12 m pra 6 m. Vê o salto.
3. Põe um zagueiro colado no goleiro, dentro da linha de tiro. A chance **sobe** — goleiro sem enxergar.

Em três minutos você entende o modelo inteiro melhor que lendo isso aqui.
