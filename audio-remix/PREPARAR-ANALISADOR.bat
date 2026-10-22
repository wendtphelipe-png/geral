@echo off
chcp 65001 >nul
title Audio Remix - preparar o analisador
rem Cria o ambiente Python do Audio Remix fora do repositorio (D:\Projetos\remix-py)
rem e instala tudo o que o analisador precisa. Pode rodar de novo quantas vezes quiser.
set "AMBIENTE=D:\Projetos\remix-py"
set "PY=%AMBIENTE%\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"

rem O PyTorch ainda nao funciona em todas as versoes novas do Python: prefere 3.12, depois 3.11.
if exist "%PY%" (
  "%PY%" -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" || (
    echo O ambiente existente usa uma versao do Python incompativel. Recriando...
    rmdir /s /q "%AMBIENTE%"
  )
)
if not exist "%PY%" (
  echo Criando o ambiente Python em %AMBIENTE% ...
  py -3.12 -m venv "%AMBIENTE%" 2>nul || py -3.11 -m venv "%AMBIENTE%" 2>nul || python -m venv "%AMBIENTE%"
)
if not exist "%PY%" (
  echo Nao encontrei o Python. Instale o Python 3.12 em python.org e rode de novo.
  pause & exit /b 1
)
"%PY%" --version

echo.
echo === 1/4 Pacotes basicos ^(download, analise, identificacao^)
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install --upgrade -r "%~dp0analisador\requirements.txt"
if errorlevel 1 (
  echo.
  echo ERRO ao instalar os pacotes basicos. Mande uma foto desta janela para o Claude.
  pause & exit /b 1
)

echo.
echo === 2/4 PyTorch para a placa de video ^(uns 2 GB, pode demorar^)
"%PY%" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 echo AVISO: o PyTorch nao instalou. A analise funciona, mas sem separar as faixas.

echo.
echo === 3/4 Separador de faixas ^(Demucs^)
"%PY%" -m pip install -r "%~dp0analisador\requirements-separar.txt"
if errorlevel 1 echo AVISO: o separador nao instalou. A analise funciona, mas sem separar as faixas.

echo.
echo === 4/4 FFmpeg e Deno
where ffmpeg >nul 2>nul || winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
where deno >nul 2>nul || winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements

echo.
echo === Conferencia
"%PY%" "%~dp0analisador\conferir.py"
echo.
echo Se o FFmpeg ou o Deno acabaram de ser instalados, FECHE esta janela antes de rodar ANALISAR-PLAYLIST.bat.
pause
