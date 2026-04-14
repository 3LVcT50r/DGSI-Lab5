#!/bin/bash

echo "Starting 3D Printer Factory Simulator Frontend..."
echo ""
echo "Frontend will be available at: http://localhost:8501"
echo "Make sure the backend is running at http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run src/ui/app.py