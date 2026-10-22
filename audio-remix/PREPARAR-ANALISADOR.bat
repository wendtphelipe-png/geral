@echo off
chcp 65001 >nul
title Audio Remix - preparar o analisador
rem Cria o ambiente Python do Audio Remix fora do repositorio (D:\Projetos\remix-py)
rem e instala tudo o que o analisador precisa. Pode rodar de novo quantas vezes quiser.
set "AMBIENTE=D:\Projetos\remix-py"
set "PY=%AMBIENTE%\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"

rem O PyTorch e o identificador de musicas ainda nao funcionam no Python 3.14.
rem Por isso o ambiente usa o Python 3.12 (instalado automaticamente se faltar).
py -3.12 --version >nul 2>nul || (
  echo Instalando o Python 3.12 ^(o 3.14 ainda e novo demais para estes programas^)...
  winget install --id Python.Python.3.12 -e --scope user --accept-source-agreements --accept-package-agreements
)
if exist "%PY%" (
  "%PY%" -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" || (
    echo O ambiente existente usa o Python 3.14. Recriando com o 3.12...
    rmdir /s /q "%AMBIENTE%"
  )
)
if not exist "%PY%" (
  echo Criando o ambiente Python em %AMBIENTE% ...
  py -3.12 -m venv "%AMBIENTE%" 2>nul || py -3.11 -m venv "%AMBIENTE%" 2>nul
)
if not exist "%PY%" (
  echo Nao consegui instalar o Python 3.12. Instale manualmente em python.org ^(versao 3.12^),
  echo marcando "Add python.exe to PATH", e rode este arquivo de novo.
  pause & exit /b 1
)
"%PY%" --version

echo.
echo === 1/5 Pacotes basicos ^(download e analise^)
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install --upgrade -r "%~dp0analisador\requirements.txt"
if errorlevel 1 (
  echo.
  echo ERRO ao instalar os pacotes basicos. Mande uma foto desta janela para o Claude.
  pause & exit /b 1
)

echo.
echo === 2/5 PyTorch para a placa de video ^(uns 2 GB, pode demorar^)
"%PY%" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 echo AVISO: o PyTorch nao instalou. A analise funciona, mas sem separar as faixas.

echo.
echo === 3/5 Separador de faixas ^(Demucs^)
"%PY%" -m pip install -r "%~dp0analisador\requirements-separar.txt"
if errorlevel 1 echo AVISO: o separador nao instalou. A analise funciona, mas sem separar as faixas.

echo.
echo === 4/5 Identificador de musicas ^(Shazam^)
"%PY%" -m pip install shazamio
if errorlevel 1 echo AVISO: o identificador nao instalou. A analise funciona, mas sem dizer o nome das musicas.

echo.
echo === 5/5 FFmpeg e Deno
where ffmpeg >nul 2>nul || winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
where deno >nul 2>nul || winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements

echo.
echo === Conferencia
"%PY%" "%~dp0analisador\conferir.py"
echo.
echo Se o FFmpeg ou o Deno acabaram de ser instalados, FECHE esta janela antes de rodar ANALISAR-PLAYLIST.bat.
pause
