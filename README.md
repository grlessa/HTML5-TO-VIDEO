# HTML5 to Video Converter

Convert HTML5 ads and animations to video files. Simple web interface, automatic settings detection.

## What it does

Takes a ZIP file with HTML5 content and converts it to an MP4 video. Useful for turning banner ads into video ads or previewing animations.

## Quick start

**Online (easiest):**
1. Go to the deployed app (Streamlit Cloud link here)
2. Upload your HTML5 ZIP file
3. Click convert
4. Download the video

**Local:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

You'll need FFmpeg and Chrome installed.

## How it works

**Auto mode** (recommended):
- Detects resolution from your HTML
- Figures out duration from animations
- Sets frame rate based on content
- Just upload and click convert

**Manual mode**:
- Set your own resolution, FPS, duration
- Adjust quality settings if needed
- Useful if auto-detection gets it wrong

## Output settings

The default settings work well for most cases:
- H.264 codec (compatible everywhere)
- CRF 18 (high quality)
- "slow" preset (good quality/speed balance)

These are optimized for web video players and downloads.

## About animations

**If your HTML has CSS @keyframes or JavaScript animations:**
The video will capture them playing.

**If your HTML only has hover effects:**
The video will be static (just the initial state). This is normal - hover effects don't have a timeline to capture.

## Requirements

- Python 3.9+
- FFmpeg (`brew install ffmpeg`)
- Chrome or Chromium browser
- Streamlit and Selenium (in requirements.txt)

## Troubleshooting

**"Browser not found":**
Install Chrome or Chromium.

**"FFmpeg not found":**
Install FFmpeg with your package manager.

**Video preview doesn't play:**
Download it instead - some browsers have issues with inline video.

## Deploy to Streamlit Cloud

1. Fork this repo
2. Connect it to Streamlit Cloud
3. Deploy with `app.py`

It'll install everything automatically from requirements.txt and packages.txt.

## License

MIT - use it however you want.
