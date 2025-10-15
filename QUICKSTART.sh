#!/bin/bash
# Quick Start Script for HTML5 to Video Converter

echo "🎬 HTML5 to Video Converter - Quick Start"
echo "=========================================="
echo ""

# Check if in correct directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project directory."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found!"
    echo "Installing FFmpeg..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Please install Homebrew first: https://brew.sh"
        exit 1
    fi
else
    echo "✅ FFmpeg found"
fi

# Check Chrome/Chromium
if [ -d "/Applications/Google Chrome.app" ]; then
    echo "✅ Chrome found"
elif [ -d "/Applications/Comet.app" ]; then
    echo "✅ Comet browser found"
else
    echo "⚠️  Chrome not found"
    echo "Installing Chrome..."
    if command -v brew &> /dev/null; then
        brew install --cask google-chrome
    else
        echo "❌ Please install Chrome manually: https://google.com/chrome"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "To start the app:"
echo "  streamlit run app.py"
echo ""
echo "Or:"
echo "  python3 -m streamlit run app.py"
echo ""
echo "The app will open in your browser at:"
echo "  http://localhost:8501"
echo ""
