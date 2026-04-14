@echo off
REM Script para ejecutar componentes del proyecto

if "%1"=="api" goto api
if "%1"=="ui" goto ui
if "%1"=="test" goto test
if "%1"=="all" goto all
goto help

:api
echo Iniciando servidor API...
call venv\Scripts\activate.bat
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
goto end

:ui
echo Iniciando interfaz Streamlit...
call venv\Scripts\activate.bat
streamlit run src/ui/app.py
goto end

:test
echo Ejecutando tests...
call venv\Scripts\activate.bat
python -m pytest tests/ -v
goto end

:all
echo Iniciando API y UI...
start cmd /k "call venv\Scripts\activate.bat && python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak > nul
start cmd /k "call venv\Scripts\activate.bat && streamlit run src/ui/app.py"
goto end

:help
echo Uso: run.bat [comando]
echo.
echo Comandos disponibles:
echo   api    - Iniciar servidor API (http://127.0.0.1:8000)
echo   ui     - Iniciar interfaz Streamlit (http://localhost:8501)
echo   test   - Ejecutar tests
echo   all    - Iniciar API y UI simultaneamente
echo.
echo Ejemplos:
echo   run.bat api
echo   run.bat ui
echo   run.bat test
echo   run.bat all
goto end

:end