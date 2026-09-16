# Copa Revoada - prepara este computador para trabalhar no projeto.
#
#   powershell -ExecutionPolicy Bypass -File scripts\prepara-maquina.ps1
#
# O "-ExecutionPolicy Bypass" vale so para esta execucao: nao muda nenhuma
# configuracao do Windows.
#
# O que faz, nesta ordem:
#   1. confere se ha Python 3.12 (NAO instala: se faltar, diz o comando)
#   2. cria o .venv dentro do projeto, se ainda nao existir
#   3. instala requirements.txt dentro do .venv
#   4. confere o gh e busca as URLs da planilha nas variaveis do repositorio
#   5. roda o build e mostra o resumo
#
# Nada e instalado fora da pasta do projeto. Apagar o .venv desfaz tudo.
# (Arquivo sem acentos de proposito: o PowerShell 5 le .ps1 sem BOM como ANSI.)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'

function Passo($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Yellow }
function Ok($t)    { Write-Host "   ok  $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "   !!  $t" -ForegroundColor Magenta }

# O Windows limita caminhos a 260 caracteres, e o numpy instala arquivos bem
# fundos dentro do .venv. Numa pasta de caminho longo o pip quebra no meio com
# "WinError 206" - aconteceu no teste deste script.
if ($raiz.Length -gt 70) {
    Aviso "A pasta do projeto tem um caminho longo ($($raiz.Length) caracteres):"
    Aviso "   $raiz"
    Aviso 'Se a instalacao falhar com WinError 206, clone numa pasta curta, como C:\copa-revoada'
}

# --- 1. Python ------------------------------------------------------------
Passo 'Python 3.12'
$pyExe = $null; $pyArgs = @()
try {
    $v = & py -3.12 --version 2>$null
    if ($LASTEXITCODE -eq 0) { $pyExe = 'py'; $pyArgs = @('-3.12') }
} catch {}
if (-not $pyExe) {
    try {
        $v = & python --version 2>$null
        if ($v -match '3\.12') { $pyExe = 'python' }
    } catch {}
}
if (-not $pyExe) {
    Aviso 'Python 3.12 nao encontrado.'
    Aviso 'Instalar e decisao sua. Se quiser, rode:  winget install Python.Python.3.12'
    Aviso 'Depois feche e abra o terminal e rode este script de novo.'
    exit 1
}
Ok $v

# --- 2. .venv -------------------------------------------------------------
Passo 'Ambiente do projeto (.venv)'
$venvPy = Join-Path $raiz '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPy)) {
    & $pyExe @pyArgs -m venv .venv
    Ok '.venv criado'
} else {
    Ok '.venv ja existia'
}

# --- 3. dependencias ------------------------------------------------------
Passo 'Dependencias (requirements.txt)'
& $venvPy -m pip install --quiet --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { Aviso 'pip falhou - veja a mensagem acima'; exit 1 }
$cascata = & $venvPy -c "import cv2,os;print(os.path.isfile(os.path.join(cv2.data.haarcascades,'haarcascade_frontalface_default.xml')))"
if ($cascata -eq 'True') { Ok 'openpyxl, pillow e opencv (com deteccao de rosto)' }
else { Aviso 'opencv instalado sem as cascatas de rosto - os retratos saem sem centralizar' }

# --- 4. gh e planilha -----------------------------------------------------
Passo 'GitHub e planilha'
$temGh = $false
try { & gh auth status 2>$null | Out-Null; if ($LASTEXITCODE -eq 0) { $temGh = $true } } catch {}
if ($temGh) {
    Ok 'gh autenticado'
    # primeiro o repositorio de onde veio o clone; se o gh nao souber qual e
    # (clone de uma pasta local, por exemplo), o repositorio oficial
    foreach ($repo in @($null, 'Guilherme-Moliner/copa-revoada')) {
        if ($env:PLANILHA_URL) { break }
        try {
            $r = @(); if ($repo) { $r = @('-R', $repo) }
            $env:PLANILHA_URL = (& gh variable get PLANILHA_URL @r 2>$null)
            $env:LANCES_URL   = (& gh variable get LANCES_URL @r 2>$null)
        } catch {}
    }
    if ($env:PLANILHA_URL) { Ok 'PLANILHA_URL lida do repositorio (so nesta sessao do terminal)' }
    else { Aviso 'nao achei PLANILHA_URL - o build vai usar a copia .xlsx do repositorio' }
} else {
    Aviso 'gh nao esta autenticado (rode: gh auth login). O build vai usar a copia .xlsx.'
}

# --- 5. build -------------------------------------------------------------
Passo 'Build'
# o build escreve avisos no stderr; no PowerShell 5 isso vira "erro" e, com
# Stop, derrubaria o script no meio de um build que deu certo
$ErrorActionPreference = 'Continue'
$saida = & $venvPy scripts\build.py 2>&1 | ForEach-Object { "$_" }
$codigo = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
$saida | ForEach-Object { Write-Host $_ }
if ($codigo -ne 0) { Aviso 'o build falhou - veja a mensagem acima'; exit 1 }

# Achar a URL nao garante que a planilha foi lida: se o download falhar, o
# build segue com a copia .xlsx do repositorio, que pode estar velha. Melhor
# dizer em voz alta do que deixar trabalhar com dado antigo sem saber.
$texto = $saida -join "`n"
if ($env:PLANILHA_URL -and ($texto -notmatch 'planilha lida do Google Sheets')) {
    Write-Host ""
    Aviso 'ATENCAO: o build NAO conseguiu ler a planilha online e usou a copia .xlsx.'
    Aviso 'Os numeros acima podem estar desatualizados. Rode o script de novo em instantes.'
}

Write-Host ""
Write-Host "Pronto. Para ver o site:" -ForegroundColor Green
Write-Host "   .venv\Scripts\python.exe -m http.server 8123"
Write-Host "   e abra http://localhost:8123"
Write-Host ""
Write-Host "Pendencia sua, se ainda nao fez: republicar o Apps Script (versao 2)." -ForegroundColor Magenta
Write-Host "Veja docs/planilha-colaborativa.md"
