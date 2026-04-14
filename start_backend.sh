#!/bin/bash

echo "Starting 3D Printer Factory Simulator Backend..."
echo ""
echo "Backend will be available at: http://127.0.0.1:8000"
echo "API Documentation at: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload