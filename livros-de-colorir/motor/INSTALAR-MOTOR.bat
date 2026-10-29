@echo off
rem Instala o motor da fabrica de livros de colorir (dois cliques).
rem Cria o ambiente Python em .venv e a pasta de modelos ao lado deste arquivo.
rem Pode ser rodado de novo sem problema: so instala o que faltar.
chcp 65001 >nul
cd /d "%~dp0"

set DISCO=%~d0
if /i "%DISCO%"=="G:" (
  echo.
  echo  ATENCAO: o motor esta no G: ^(Google Drive^). Nao instale aqui.
  echo  Copie a pasta do repositorio para o SSD e rode de novo.
  pause
  exit /b 1
)
if /i "%DISCO%"=="D:" (
  echo.
  echo  ATENCAO: o disco D: esta com setores defeituosos.
  echo  O recomendado e instalar no SSD novo. Feche esta janela para cancelar,
  echo  ou aperte uma tecla para instalar mesmo assim.
  pause
)

echo.
echo  [1/4] Procurando o Python...
set PY=
where py >nul 2>nul && py -3.12 -c "print()" >nul 2>nul && set PY=py -3.12
if not defined PY where py >nul 2>nul && py -3.11 -c "print()" >nul 2>nul && set PY=py -3.11
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo  Python nao encontrado. Instale o Python 3.12 em python.org
  echo  ^(marque "Add python.exe to PATH"^) e rode este arquivo de novo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo  [2/4] Criando o ambiente Python em .venv ...
  %PY% -m venv .venv || goto erro
) else (
  echo  [2/4] Ambiente Python ja existe.
)

echo  [3/4] Instalando o PyTorch para a placa de video ^(cerca de 3 GB^)...
rem torch 2.7 cu128: a ultima versao que ainda suporta a GTX 1070 Ti (sm_61)
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install "torch==2.7.1" --index-url https://download.pytorch.org/whl/cu128 || goto erro

echo  [4/4] Instalando o restante...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto erro

if not exist modelos mkdir modelos
if not exist config.json copy exemplos\config.exemplo.json config.json >nul

echo.
echo  Pronto. Para testar, abra o Prompt de Comando nesta pasta e digite:
echo     fabrica status
echo     fabrica teste
echo  O primeiro teste baixa os modelos ^(cerca de 7 GB^) e demora.
pause
exit /b 0

:erro
echo.
echo  Algo deu errado. Tire um print desta janela e mande para o Claude.
pause
exit /b 1
