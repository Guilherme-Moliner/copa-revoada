@echo off
rem Copa Revoada - gera o pacote de midias do jogo.
rem Dois cliques: usa o lances-*.json mais novo da pasta Downloads.
rem Ou arraste um arquivo de lances para cima deste .bat.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta preparar este computador: rode scripts\prepara-maquina.ps1
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\pacote.py gerar %*
echo.
pause
