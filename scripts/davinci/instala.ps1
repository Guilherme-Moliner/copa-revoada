# Copa Revoada - poe o script do pacote de midias no menu do DaVinci Resolve.
#
#   powershell -ExecutionPolicy Bypass -File scripts\davinci\instala.ps1
#
# Copia "Copa Revoada - importar pacote.lua" para a pasta de scripts do
# Resolve (Workspace > Scripts), trocando __RAIZ__ pela pasta deste projeto.
# E so copia de arquivo: nada e instalado, e apagar o arquivo desfaz.
# Rode de novo sempre que o .lua mudar.
# (Arquivo sem acentos de proposito: o PowerShell 5 le .ps1 sem BOM como ANSI.)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$origem = Join-Path $PSScriptRoot 'Copa Revoada - importar pacote.lua'
$destino = Join-Path $env:APPDATA 'Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility'

New-Item -ItemType Directory -Force $destino | Out-Null
$texto = [IO.File]::ReadAllText($origem, [Text.Encoding]::UTF8).Replace('__RAIZ__', $raiz)
# UTF-8 sem BOM: o Lua do Resolve nao entende o BOM no comeco do arquivo
[IO.File]::WriteAllText((Join-Path $destino (Split-Path -Leaf $origem)), $texto, (New-Object Text.UTF8Encoding $false))

Write-Host "ok  $destino"
Write-Host "No DaVinci: Workspace > Scripts > Copa Revoada - importar pacote"
Write-Host "(se o DaVinci ja estava aberto, o item aparece sem precisar reiniciar)"
