# HTML5 to Video Converter - Flask Version

Simple standalone Flask web app. No Streamlit bullshit.

## Run Locally

```bash
# Install dependencies
pip install -r requirements-flask.txt

# Make sure you have Chromium and FFmpeg installed
# macOS:
brew install chromium ffmpeg

# Linux:
sudo apt-get install chromium chromium-driver ffmpeg

# Run the app
python flask_app.py
```

Open http://localhost:5000

## Deploy to Render

1. Push to GitHub
2. Go to https://render.com
3. Click "New Web Service"
4. Connect your repo
5. Render will auto-detect `render.yaml` and configure everything
6. Click "Create Web Service"

**That's it.**

## Deploy to Railway

1. Push to GitHub
2. Go to https://railway.app
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repo
5. Add this start command: `gunicorn flask_app:app`
6. Done.

## Deploy to Heroku

```bash
git push heroku main
```

Uses the `Procfile` automatically.

## Deploy Anywhere Else

Just run: `gunicorn flask_app:app`

Set the `PORT` environment variable if needed.
