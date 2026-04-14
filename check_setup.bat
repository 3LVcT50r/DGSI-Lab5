@echo off
echo ========================================
echo 3D Printer Factory Simulator - Health Check
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo.

echo Checking if virtual environment exists...
if not exist venv (
    echo WARNING: Virtual environment not found.
    echo Run setup.bat first to create it.
    echo.
) else (
    echo Virtual environment found.
)

echo Checking requirements.txt...
if not exist requirements.txt (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
) else (
    echo requirements.txt found.
)

echo Checking source files...
if not exist src\main.py (
    echo ERROR: src\main.py not found!
    pause
    exit /b 1
) else (
    echo Backend source files found.
)

if not exist src\ui\app.py (
    echo ERROR: src\ui\app.py not found!
    pause
    exit /b 1
) else (
    echo Frontend source files found.
)

echo.
echo Testing imports...
python -c "from src.main import app; print('✓ Backend imports successfully')"
if %errorlevel% neq 0 (
    echo ERROR: Backend import failed!
    pause
    exit /b 1
)

python -c "import sys; sys.path.append('src'); from ui.app import main; print('✓ Frontend imports successfully')"
if %errorlevel% neq 0 (
    echo ERROR: Frontend import failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ All checks passed! Ready to run.
echo ========================================
echo.
echo To start the application:
echo 1. Run: start_backend.bat (in one terminal)
echo 2. Run: start_frontend.bat (in another terminal)
echo.
echo Or manually:
echo Backend:  python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
echo Frontend: streamlit run src/ui/app.py
echo.
pause