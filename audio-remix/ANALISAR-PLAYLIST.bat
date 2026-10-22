@echo off
chcp 65001 >nul
title Audio Remix - analisar mixes
rem Baixa os audios, faz o raio-x de cada mix e envia SO os relatorios para o GitHub.
rem Os audios ficam em audio-remix\dados (nao vao para o GitHub).
set "PY=D:\Projetos\remix-py\Scripts\python.exe"
set "PADRAO=https://www.youtube.com/watch?v=XRAzF6JNTqs&list=PLVK8RyIvEcpM"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

if not exist "%PY%" (
  echo Rode primeiro PREPARAR-ANALISADOR.bat
  pause & exit /b 1
)

echo Cole o link do video ou da playlist e aperte Enter.
echo ^(So Enter usa a playlist da Brotherhood^)
set "LINK="
set /p "LINK=Link: "
if "%LINK%"=="" set "LINK=%PADRAO%"

echo.
echo === 1/4 Baixando os audios
echo Se pedir login, FECHE o Chrome antes: o programa usa os cookies dele.
"%PY%" analisador\baixar.py "%LINK%" --pasta dados\audios

echo.
echo === 2/4 Analisando ^(separa as faixas na placa de video; alguns minutos por video^)
"%PY%" analisador\analisar.py dados\audios --saida analises

echo.
echo === 3/4 Resumo dos padroes
"%PY%" analisador\resumo.py analises --lista dados\audios\lista.json

echo.
echo === 4/4 Enviando os relatorios para o GitHub
copy /y dados\audios\lista.json analises\lista-videos.json >nul 2>nul
git -C "%~dp0.." pull --no-edit
git -C "%~dp0.." add audio-remix/analises
git -C "%~dp0.." commit -m "Audio Remix: analises dos mixes"
git -C "%~dp0.." push
echo.
echo Pronto. Avise o Claude que as analises foram enviadas.
pause
