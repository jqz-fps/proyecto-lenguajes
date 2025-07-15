@echo off
echo Iniciando el sistema...

REM Ejecutar Flask
if exist ".venv\Scripts\python.exe" (
  start /b .venv\Scripts\python.exe web.py
) else (
  start /b python web.py
)

REM Ejecutar reconocimiento facial
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe main.py
) else (
  python main.py
)

pause