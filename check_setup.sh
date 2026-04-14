#!/bin/bash

echo "========================================"
echo "3D Printer Factory Simulator - Health Check"
echo "========================================"
echo ""

echo "Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python not found!"
    exit 1
fi
echo ""

echo "Checking if virtual environment exists..."
if [ ! -d "venv" ]; then
    echo "WARNING: Virtual environment not found."
    echo "Run setup.sh first to create it."
    echo ""
else
    echo "Virtual environment found."
fi

echo "Checking requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    exit 1
else
    echo "requirements.txt found."
fi

echo "Checking source files..."
if [ ! -f "src/main.py" ]; then
    echo "ERROR: src/main.py not found!"
    exit 1
else
    echo "Backend source files found."
fi

if [ ! -f "src/ui/app.py" ]; then
    echo "ERROR: src/ui/app.py not found!"
    exit 1
else
    echo "Frontend source files found."
fi

echo ""
echo "Testing imports..."
python3 -c "from src.main import app; print('✓ Backend imports successfully')"
if [ $? -ne 0 ]; then
    echo "ERROR: Backend import failed!"
    exit 1
fi

python3 -c "import sys; sys.path.append('src'); from ui.app import main; print('✓ Frontend imports successfully')"
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend import failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "✓ All checks passed! Ready to run."
echo "========================================"
echo ""
echo "To start the application:"
echo "1. Run: ./start_backend.sh (in one terminal)"
echo "2. Run: ./start_frontend.sh (in another terminal)"
echo ""
echo "Or manually:"
echo "Backend:  python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload"
echo "Frontend: streamlit run src/ui/app.py"
echo ""