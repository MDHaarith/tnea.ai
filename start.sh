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
    pip install -r requirements.txt
else
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env file to add your NVIDIA_API_KEY"
    exit 1
fi

echo "✅ Environment configured successfully!"

# Parse command line arguments
MODE="gui"  # default mode
if [ $# -gt 0 ]; then
    MODE=$1
fi

case $MODE in
    "gui"|"streamlit"|"web")
        echo "🚀 Launching Enhanced Streamlit UI..."
        cd src
        streamlit run enhanced_streamlit_app.py --server.port=8501 --server.address=0.0.0.0
        ;;
    "cli"|"terminal")
        echo "🚀 Launching Enhanced CLI Mode..."
        cd src
        python run.py --mode cli
        ;;
    "enhanced-gui")
        echo "🚀 Launching Enhanced Streamlit UI..."
        cd src
        streamlit run enhanced_streamlit_app.py --server.port=8501 --server.address=0.0.0.0
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [mode]"
        echo "Modes:"
        echo "  gui (default)     - Launch enhanced Streamlit UI"
        echo "  cli               - Launch enhanced CLI mode"
        echo "  help              - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                - Launch GUI (default)"
        echo "  $0 cli            - Launch CLI mode"
        echo "  $0 gui            - Launch GUI mode"
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo "Run '$0 help' for usage information"
        ;;
esac