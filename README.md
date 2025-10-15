# 🎬 HTML5 to Video Converter

A professional-grade web application that converts HTML5 content (animations, banners, ads) into high-quality video files with automatic parameter detection.

![Dark Mode Orange Theme](https://img.shields.io/badge/Theme-Dark%20Orange-ff8c42?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red?style=for-the-badge&logo=streamlit)

## ✨ Features

- 🤖 **Auto-Detection**: Automatically detects resolution, FPS, and duration from HTML5 content
- 🎨 **Dark Mode UI**: Beautiful dark theme with orange accents
- 🎯 **One-Click Conversion**: Upload ZIP → Click Convert → Download Video
- ⚙️ **Manual Override**: Full control over all encoding parameters when needed
- 🎬 **Professional Quality**: Uses Selenium + FFmpeg for production-grade output
- 📦 **Multiple Codecs**: H.264, H.265, VP9, and ProRes support
- 🚀 **Cloud Ready**: Deploy to Streamlit Cloud in minutes

## 🚀 Quick Start

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/html5-to-video.git
   cd html5-to-video
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system requirements**
   - **FFmpeg**: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
   - **Chrome/Chromium**: Download from [google.com/chrome](https://www.google.com/chrome/)

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**
   ```
   http://localhost:8501
   ```

## ☁️ Deploy to Streamlit Cloud

1. **Fork this repository** to your GitHub account

2. **Go to [Streamlit Cloud](https://streamlit.io/cloud)**

3. **Click "New app"** and select:
   - Repository: `yourusername/html5-to-video`
   - Branch: `main`
   - Main file: `app.py`

4. **Click "Deploy"** - That's it! 🎉

The app will automatically install all dependencies listed in `requirements.txt` and `packages.txt`.

## 📖 How to Use

### Auto Mode (Recommended)

1. **Upload** your HTML5 ZIP file (must contain HTML, CSS, JS, images, etc.)
2. The app automatically detects:
   - Resolution (width/height)
   - FPS (based on animation complexity)
   - Duration (from animation timing)
3. **Click "Convert to Video"**
4. **Download** your video when complete

### Manual Mode

1. Switch to **Manual** mode in the sidebar
2. Configure all settings:
   - Resolution (width/height)
   - FPS (1-120)
   - Duration (seconds)
   - Codec (H.264, H.265, VP9, ProRes)
   - Preset (speed vs quality)
   - CRF (quality level)
   - Bitrate
3. **Click "Convert to Video"**
4. **Download** your video

## 🎨 Supported Formats

### Input
- ZIP files containing HTML5 content
- Must include at least one `.html` file
- Can include CSS, JavaScript, images, fonts, etc.

### Output
- MP4 (H.264) - Default, widely compatible
- MP4 (H.265) - Better compression
- WebM (VP9) - Web-optimized
- MOV (ProRes) - Professional editing

## ⚙️ Configuration

### Quality Presets

| Preset | Speed | Quality | Use Case |
|--------|-------|---------|----------|
| `slow` | ⭐⭐ | ⭐⭐⭐⭐⭐ | Best quality (default) |
| `medium` | ⭐⭐⭐ | ⭐⭐⭐⭐ | Balanced |
| `fast` | ⭐⭐⭐⭐ | ⭐⭐⭐ | Quick previews |

### CRF Values

- **0-18**: High quality (large files)
- **18-23**: Good quality (recommended)
- **24-51**: Lower quality (smaller files)

## 🛠️ Technology Stack

- **Streamlit**: Web UI framework
- **Selenium**: HTML5 rendering engine
- **FFmpeg**: Video encoding
- **Python**: Backend logic

## 📋 Requirements

### System Requirements
- Python 3.9+
- FFmpeg
- Chrome/Chromium browser

### Python Dependencies
- streamlit >= 1.31.0
- selenium >= 4.15.0
- Pillow >= 10.0.0

## 🐛 Troubleshooting

### "Browser not found" error
- Install Chrome: `brew install --cask google-chrome`
- Or use Chromium: `brew install chromium`

### "FFmpeg not found" error
- Install FFmpeg: `brew install ffmpeg` (macOS)
- Or: `apt install ffmpeg` (Linux)

### Upload size limit
- Streamlit Cloud: Max 200MB per file
- Local: Configurable in `.streamlit/config.toml`

## 📝 License

MIT License - feel free to use for personal or commercial projects.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💡 Use Cases

- Convert HTML5 banner ads to video ads
- Archive animated web content
- Create video previews of web animations
- Convert interactive HTML5 content to video presentations
- Generate video from HTML5 email templates

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

## 📧 Support

For issues, questions, or suggestions, please [open an issue](https://github.com/yourusername/html5-to-video/issues).

---

Made with ❤️ by [Your Name]
