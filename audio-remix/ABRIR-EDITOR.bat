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
cd /d "%~dp0editor"
"%PY%" servidor.py
pause
