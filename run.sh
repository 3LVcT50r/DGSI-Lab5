#!/bin/bash
# Script para ejecutar componentes del proyecto

# Activar entorno virtual
source venv/bin/activate

case "$1" in
    "api")
        echo "Iniciando servidor API..."
        python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
        ;;
    "ui")
        echo "Iniciando interfaz Streamlit..."
        streamlit run src/ui/app.py
        ;;
    "test")
        echo "Ejecutando tests..."
        python -m pytest tests/ -v
        ;;
    "all")
        echo "Iniciando API y UI..."
        # Iniciar API en background
        python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000 &
        API_PID=$!

        # Esperar un poco
        sleep 2

        # Iniciar UI
        streamlit run src/ui/app.py &
        UI_PID=$!

        echo "API PID: $API_PID, UI PID: $UI_PID"
        echo "Presiona Ctrl+C para detener ambos"

        # Esperar a que terminen
        wait $API_PID $UI_PID
        ;;
    *)
        echo "Uso: ./run.sh [comando]"
        echo ""
        echo "Comandos disponibles:"
        echo "  api    - Iniciar servidor API (http://127.0.0.1:8000)"
        echo "  ui     - Iniciar interfaz Streamlit (http://localhost:8501)"
        echo "  test   - Ejecutar tests"
        echo "  all    - Iniciar API y UI simultaneamente"
        echo ""
        echo "Ejemplos:"
        echo "  ./run.sh api"
        echo "  ./run.sh ui"
        echo "  ./run.sh test"
        echo "  ./run.sh all"
        ;;
esac