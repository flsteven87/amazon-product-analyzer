#!/bin/bash

# Web Assistant Frontend Startup Script

echo "🤖 Web Assistant Frontend Startup"
echo "=================================="

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if backend is running
echo "🔍 Checking backend status..."
if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null; then
    echo "✅ Backend is running at http://127.0.0.1:8000"
else
    echo "❌ Backend is not running!"
    echo "Please start the backend first:"
    echo "  cd ../backend && make dev"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starting Streamlit frontend..."
echo "Frontend will be available at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start Streamlit
streamlit run app.py 