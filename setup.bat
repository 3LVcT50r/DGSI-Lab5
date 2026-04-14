@echo off
REM Script para configurar y ejecutar el proyecto 3D Printer Factory Simulator

echo === Configurando entorno virtual ===
if not exist venv (
    python -m venv venv
    echo Entorno virtual creado.
) else (
    echo Entorno virtual ya existe.
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r requirements.txt

echo ===
echo Entorno configurado correctamente!
echo ===
echo Para ejecutar:
echo   1. API Server: python -m uvicorn src.main:app --reload
echo   2. UI Streamlit: streamlit run src/ui/app.py
echo   3. Tests: python -m pytest tests/
echo ===
echo Presiona cualquier tecla para continuar...
pause > nul