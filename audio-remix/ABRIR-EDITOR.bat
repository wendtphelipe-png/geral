@echo off
chcp 65001 >nul
title Audio Remix - editor
rem Abre o editor por oitos em http://127.0.0.1:3060 . Feche esta janela para desligar.
set "PY=D:\Projetos\remix-py\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"
if not exist "%PY%" (
  echo Rode primeiro PREPARAR-ANALISADOR.bat
  pause & exit /b 1
)
rem A biblioteca do Google (para o Lyria) entrou depois: instala se faltar
"%PY%" -c "import google.genai" >nul 2>nul || "%PY%" -m pip install google-genai
rem Detector de batidas mais preciso (Beat This!): instala se faltar
"%PY%" -c "import beat_this" >nul 2>nul || "%PY%" -m pip install beat_this
cd /d "%~dp0editor"
"%PY%" servidor.py
pause
