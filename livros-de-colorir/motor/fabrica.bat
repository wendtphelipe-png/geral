@echo off
rem Comando da fabrica de livros de colorir (usado pelos agentes da STARNET).
rem Exemplo: fabrica status
set HF_HOME=%~dp0modelos
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
"%~dp0.venv\Scripts\python.exe" "%~dp0fabrica.py" %*
