@echo off
chcp 65001 >nul
title Audio Remix - preparar o analisador
rem Cria o ambiente Python do Audio Remix fora do repositorio (D:\Projetos\remix-py)
rem e instala tudo o que o analisador precisa. Rode uma vez (e de novo se der erro).
set "AMBIENTE=D:\Projetos\remix-py"
set "PY=%AMBIENTE%\Scripts\python.exe"

if not exist "%PY%" (
  echo Criando o ambiente Python em %AMBIENTE% ...
  where py >nul 2>nul && (py -3 -m venv "%AMBIENTE%") || (python -m venv "%AMBIENTE%")
)
if not exist "%PY%" (
  echo Nao encontrei o Python. Instale o Python 3.11 ou 3.12 em python.org e rode de novo.
  pause & exit /b 1
)

echo.
echo Instalando o PyTorch com suporte a placa de video (pode demorar, uns 2 GB)...
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126

echo.
echo Instalando o analisador...
"%PY%" -m pip install --upgrade -r "%~dp0analisador\requirements.txt"

echo.
where ffmpeg >nul 2>nul || (
  echo Instalando o FFmpeg...
  winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
)
where deno >nul 2>nul || (
  echo Instalando o Deno ^(o YouTube exige para o download funcionar^)...
  winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements
)

echo.
"%PY%" -c "import torch; print('Placa de video:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NAO encontrada (vai usar o processador, mais lento)')"
echo.
echo Pronto. Feche esta janela e rode ANALISAR-PLAYLIST.bat
pause
