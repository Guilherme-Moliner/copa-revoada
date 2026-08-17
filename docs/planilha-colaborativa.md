# Marcar os lances juntos, gravando na planilha

O app é um site estático: não tem servidor. Para ele escrever no Google Sheets
precisa de um intermediário, e o intermediário é um **Google Apps Script**
publicado como Web App, ligado à própria planilha.

São 10 minutos, feitos uma vez só.

---

## O que fica protegido, e o que não fica

Vale ser honesto antes de você montar isso achando que é cofre.

**Ler é livre.** Qualquer um que abrir o app vê os lances já marcados. É de
propósito: o grupo inteiro acompanha.

**Escrever exige a chave.** Cada aba de jogo tem uma chave na célula **B2**. Quem
for marcar digita no app, o script confere, e só então grava.

**A chave não fica no código do site.** Ela é digitada na hora e guardada só na
memória da aba do navegador (`sessionStorage`) — fecha a aba, some. O que fica
público é o endereço do Web App, e endereço sem chave não escreve nada.

O que isso **não** é: segurança de verdade. Quem tiver a chave escreve, e quem
receber a chave pode repassar. Para uma copa entre amigos resolve — serve para
ninguém apagar os lances do jogo por engano, não para resistir a alguém
determinado a atrapalhar. Se um dia isso importar, o caminho é login de verdade,
e aí não é mais um site estático.

---

## Passo a passo

### 1. Suba a planilha para o Google Sheets

Se ainda não fez: suba `dados/COPA_REVOADA_planilha.xlsx` para o Drive e abra
com Google Sheets. Ela já vem com as abas **LANCES 2026-04** e **LANCES 2026-08**.

**Antes de usar, troque a chave.** A célula **B2** de cada aba vem com o
marcador `TROQUE-ESTA-CHAVE`. Digite ali a chave que vocês quiserem — ela só
existe de verdade na planilha do Drive.

> Por que não já vem preenchida: o `.xlsx` deste repositório é **público**.
> Chave que passa por repositório público deixa de ser chave. Eu cheguei a
> gerar duas e tive que descartá-las por isso mesmo.

> As abas dos jogos seguintes o próprio script cria, com uma chave nova, na
> primeira vez que alguém gravar naquele jogo.

### 2. Cole o script

Na planilha: **Extensões → Apps Script**. Apague o que estiver lá e cole o
conteúdo de [`scripts/apps-script.gs`](../scripts/apps-script.gs). Salve.

### 3. Publique como Web App

**Implantar → Nova implantação → Tipo: App da Web**

| campo | valor |
|---|---|
| Descrição | Copa Revoada — lances |
| Executar como | **Eu** |
| Quem pode acessar | **Qualquer pessoa** |

Clique em Implantar, autorize quando pedir, e **copie a URL** que termina em
`/exec`.

> "Qualquer pessoa" assusta, mas é o que faz o app conseguir falar com a
> planilha sem cada um do grupo ter que fazer login do Google. Quem manda na
> escrita é a chave, não o acesso à URL.

### 4. Diga ao app onde está

No GitHub: **Settings → Secrets and variables → Actions → Variables →
New repository variable**

- Nome: `LANCES_URL`
- Valor: a URL `/exec` que você copiou

Rode o workflow (**Actions → Publicar site → Run workflow**). Enquanto a
variável não existir, o painel avisa que a gravação está desligada e a marcação
vive só na aba do navegador.

Para testar aqui antes:

```bash
LANCES_URL="https://script.google.com/macros/s/SEU_ID/exec" .venv/Scripts/python.exe scripts/build.py
```

---

## Como se usa no jogo

No Estúdio, arte **Análise do jogo**:

1. Escolha o jogo, escreva seu nome e clique em **Carregar** — vem o que o grupo
   já marcou.
2. Vá marcando os lances: minuto, time, tipo, jogador e o xG.
3. Digite a chave e clique em **Gravar**.

Quem estiver com o app aberto clica em Carregar e recebe o que você acabou de
gravar.

### Uma escolha de projeto que vale saber

O app grava **a lista inteira**, não linha por linha. A aba passa a refletir
exatamente o que estava na tela de quem gravou.

Isso evita linha duplicada quando duas pessoas marcam ao mesmo tempo, mas tem um
custo: **a última gravação vale**. Se dois estiverem marcando o mesmo jogo em
paralelo sem carregar antes, quem gravar por último sobrescreve o outro.

Na prática, combine que **uma pessoa marca por jogo**. Se for dividir, clique em
Carregar antes de cada Gravar. As colunas `por` e `em` da planilha registram quem
gravou e quando, então dá para saber o que aconteceu.

---

## Se der errado

| sintoma | o que costuma ser |
|---|---|
| "chave não confere" | a chave é a da **aba daquele jogo**, célula B2; cada jogo tem a sua |
| "não deu para gravar: Failed to fetch" | a implantação não está como "Qualquer pessoa", ou a URL não termina em `/exec` |
| Carregar volta vazio | a aba daquele jogo ainda não existe; ela nasce na primeira gravação |
| Mudei o script e não mudou nada | toda alteração exige **Nova implantação**; editar não republica |

---

## As chaves

Ficam na célula **B2** de cada aba, e só na planilha do Drive. No repositório
elas nunca existem: o `.xlsx` versionado carrega apenas o marcador.

Escolha algo fácil de ditar no grupo e difícil de adivinhar. Trocar é digitar
outra coisa na B2 — vale na hora, sem republicar nada.
