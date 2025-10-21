# HTML5 to Video Converter

Convert HTML5 ads and animations to video files. Simple web interface, automatic settings detection.

## What it does

Takes a ZIP file or HTML file with HTML5 content and converts it to an MP4 video. Useful for turning banner ads into video ads or previewing animations.

## Quick Start

### Run Locally (Flask - Recommended)

```bash
# Install dependencies
pip install -r requirements-flask.txt

# Install system dependencies
# macOS:
brew install chromium ffmpeg

# Linux:
sudo apt-get install chromium chromium-driver ffmpeg

# Run the app
python flask_app.py
```

Open http://localhost:5000

### Run Locally (Streamlit Alternative)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## Deploy Online

### Render.com (Recommended)

1. Push this repo to GitHub
2. Go to https://render.com
3. Click "New Web Service"
4. Connect your GitHub repo
5. Render auto-detects `render.yaml`
6. Click "Create Web Service"

**Done!** Your app will be live in a few minutes.

### Railway.app

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select this repo
4. Set start command: `gunicorn flask_app:app`
5. Deploy

### Streamlit Cloud

1. Go to https://share.streamlit.io
2. Connect your GitHub repo
3. Set main file: `app.py`
4. Deploy

## How to Use

1. **Upload** your HTML5 file (.zip or .html)
2. **Review** auto-detected settings (resolution, FPS, duration)
3. **Adjust** duration or format if needed
4. **Convert** and download your video

### Auto-Detection

- **Resolution**: Detected from HTML viewport/canvas
- **FPS**: Set based on animation complexity (24/30/60)
- **Duration**: Detected from animation timings
- **Format**: Auto-selects best fit (Square 1080x1080 or Vertical 1080x1920)

### Manual Override

- Custom duration (1-300 seconds)
- Force square or vertical format
- All settings adjustable

## Output Settings

Default settings optimized for quality:
- **Codec**: H.264 (universal compatibility)
- **Quality**: CRF 18 (high quality)
- **Preset**: Slow (better compression)
- **Bitrate**: 10M (high quality)

## Requirements

### Python Dependencies
- Flask (web framework)
- Selenium (browser automation)
- Pillow (image processing)
- Gunicorn (production server)

### System Dependencies
- Python 3.9+
- Chromium/Chrome browser
- FFmpeg
- ChromeDriver (for Selenium)

## Project Structure

```
├── flask_app.py          # Flask web application
├── app.py                # Streamlit alternative UI
├── converter.py          # Core conversion logic
├── templates/
│   └── index.html        # Web interface
├── requirements-flask.txt # Flask dependencies
├── requirements.txt      # Streamlit dependencies
├── packages.txt          # System packages (for cloud)
├── Procfile              # For Heroku/Render
└── render.yaml           # Render.com config
```

## Troubleshooting

**"Browser not found":**
Install Chromium or Chrome browser.

**"FFmpeg not found":**
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

**Conversion fails:**
Check the debug output (expandable section) for detailed logs.

**File too large:**
Maximum file size is 50MB. Reduce your HTML5 assets.

## How It Works

1. **Extract**: Unzips your HTML5 content
2. **Analyze**: Detects optimal settings from HTML
3. **Render**: Uses headless Chrome to render each frame
4. **Encode**: FFmpeg combines frames into video
5. **Download**: Video ready in MP4 format

## License

MIT - use it however you want.
