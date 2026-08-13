# Prompt para o Claude Code

Abra o terminal **dentro da pasta `copa-revoada`** (a que você acabou de baixar e
descompactar) e rode `claude`. Depois cole o texto abaixo.

Antes disso, confira que você tem o `gh` autenticado — se não tiver, o Claude Code
resolve, mas é mais rápido já chegar pronto:

```bash
gh auth status    # se der erro:  gh auth login
```

---

## Cole isto

```
Esta pasta é o site da Copa Revoada, uma copa de futebol entre amigos. É um site
estático: o index.html é gerado por scripts/build.py a partir da planilha em
dados/ e das fotos em fotos/. O README explica a estrutura.

Quero publicar no GitHub Pages. Faça, nesta ordem, parando pra me perguntar antes
de qualquer coisa irreversível:

1. Leia o README.md e o scripts/build.py pra entender o projeto antes de mexer.

2. Confira o ambiente: python3 disponível, openpyxl e pillow instalados, gh
   autenticado. Me diga o que falta em vez de tentar adivinhar.

3. Rode `python3 scripts/build.py` e me mostre a saída inteira, incluindo os
   avisos. Se der erro, conserte e explique o que estava errado.

4. Abra o index.html gerado e verifique o básico: o marcador // __DADOS__ foi
   substituído, o objeto DADOS tem jogadores, times e jogos, e o JS não tem erro
   de sintaxe. Não precisa abrir navegador, só validar o arquivo.

5. Inicialize o git, faça o primeiro commit com uma mensagem em português
   descrevendo o que é o projeto, e crie o repositório no GitHub com o nome
   `copa-revoada`. Me pergunte se deve ser público ou privado antes de criar.

6. Faça o push da branch main.

7. Me diga exatamente onde clicar pra ligar o GitHub Pages com Source =
   GitHub Actions (o workflow já está em .github/workflows/publicar.yml), e
   depois acompanhe a primeira execução com `gh run watch`. Se falhar, leia o log
   e conserte.

8. No fim, me passe a URL final do site e confirme que ela responde.

Regras:
- Não invente dados na planilha nem preencha nada que esteja vazio. Se algum
  jogador, time ou jogo estiver faltando informação, me avise; não chute.
- Não edite o index.html à mão. Ele é gerado. Alteração de visual vai em
  src/app.template.html.
- Não instale nada global sem me perguntar.
- Commits em português.
```

---

## Depois que estiver no ar

Quando quiser mexer no site, o ciclo é sempre o mesmo:

```bash
# alguém preencheu a planilha, ou você jogou fotos novas em fotos/
python3 scripts/build.py
git add -A && git commit -m "atualiza dados da temporada X" && git push
```

O site republica sozinho em um ou dois minutos.

Se preferir, seus colegas de gestão podem editar `dados/COPA_REVOADA_planilha.xlsx`
direto pela interface do GitHub (botão de upload substituindo o arquivo) — o push
dispara o build e o site atualiza sem ninguém instalar nada.

---

## Prompts para as próximas rodadas

Guarde estes pra quando o material chegar.

**Quando as fotos chegarem no zip:**

```
Descompacte o zip de fotos que coloquei em fotos/. Cada arquivo precisa se chamar
igual ao id da aba JOGADORES da planilha, em minúsculo, com extensão jpg/png/webp.
Me mostre a lista de arquivos que não casaram com nenhum id antes de renomear
qualquer coisa. Depois rode o build e me diga quantos jogadores ficaram com foto.
```

**Quando as escalações estiverem lançadas:**

```
Atualizei dados/COPA_REVOADA_planilha.xlsx com as escalações. Rode o build e me
mostre todos os avisos. Depois confira, direto da planilha, se o total de gols
lançados em ESCALACOES bate com os placares da aba JOGOS, jogo a jogo, e me
mostre uma tabela das diferenças. Não corrija nada sozinho.
```

**Quando quiser mexer no visual:**

```
Quero mudar [descreva]. Isso fica em src/app.template.html. Faça a alteração,
rode o build e me diga o que mudou. Não edite o index.html.
```
