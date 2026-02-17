#!/bin/bash

# TNEA AI Enhanced Edition Startup Script
# Use this script to easily launch the enhanced TNEA AI application

echo "🎓 TNEA AI - Expert Engineering Counsellor (Enhanced Edition)"
echo "=============================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️ Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
else
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
fi

# Always check for new requirements
echo "📦 Checking dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env file to add your NVIDIA_API_KEY"
    exit 1
fi

echo "✅ Environment configured successfully!"

# Default to GUI mode
echo "🚀 Launching TNEA AI Streamlit UI..."
cd src
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0