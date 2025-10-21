# Deployment Guide

## ✅ What Works

- **Render.com** - Full support, recommended
- **Railway.app** - Full support
- **Streamlit Cloud** - Works with `app.py`
- **Local** - Works perfectly

## ❌ What Doesn't Work

- **Vercel** - Not compatible (no long-running processes, no Chromium/FFmpeg)
- **Netlify** - Not compatible (static hosting only)
- **GitHub Pages** - Not compatible (static hosting only)

---

## Deploy to Render.com (Recommended)

### Step 1: Push to GitHub
```bash
git push
```

### Step 2: Create Web Service
1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select repository: **HTML5-TO-VIDEO**
5. Render auto-detects `render.yaml` ✓

### Step 3: Configure (if needed)
If Render doesn't auto-detect, manually enter:

**Build Command:**
```bash
apt-get update && apt-get install -y chromium chromium-driver ffmpeg fonts-liberation && pip install -r requirements-flask.txt
```

**Start Command:**
```bash
gunicorn flask_app:app --timeout 300 --workers 2
```

### Step 4: Deploy
Click **"Create Web Service"**

Wait 5-10 minutes for:
- System packages to install (Chromium, FFmpeg)
- Python packages to install
- Build to complete

### Step 5: Test
Once deployed, visit your Render URL (e.g., `https://your-app.onrender.com`)

---

## Expected Behavior

### ✅ Working correctly:
1. Upload HTML5 file → Settings appear
2. Click "Convert" → Spinner shows
3. Wait 1-3 minutes (conversions are CPU-intensive)
4. Video preview appears
5. Download button works

### ❌ Common Issues on Render:

**Issue: "Conversion failed" error**
- **Cause**: Chromium/FFmpeg not installed
- **Fix**: Check Render build logs, ensure `buildCommand` ran successfully

**Issue: Request timeout**
- **Cause**: Conversion takes too long (>5 minutes)
- **Fix**: Reduce duration or FPS in settings

**Issue: Video doesn't preview**
- **Cause**: Browser security blocking blob URLs
- **Fix**: Click download button instead, video will download

**Issue: 404 error on homepage**
- **Cause**: Flask app not starting
- **Fix**: Check Render logs, ensure `startCommand` is correct

---

## Check Render Logs

1. Go to your Render dashboard
2. Click on your web service
3. Click **"Logs"** tab
4. Look for:
   - ✅ `Starting gunicorn`
   - ✅ `Booting worker`
   - ❌ Any Python errors

---

## Local Testing (before deploying)

```bash
# Install dependencies
pip install -r requirements-flask.txt

# Install system packages (macOS)
brew install chromium ffmpeg

# Run locally
python flask_app.py
```

Open http://localhost:5000

If it works locally, it will work on Render.

---

## Performance Tips

### For faster conversions:
- Use lower FPS (30 instead of 60)
- Shorter duration (5s instead of 10s)
- Simpler HTML (less animations)

### For better quality:
- Use 60 FPS
- Higher resolution source files
- Let auto-detection work (it's optimized)

---

## Still Having Issues?

### Debug Steps:
1. **Check browser console** (F12 → Console tab)
   - Look for JavaScript errors
   - Check fetch responses

2. **Check Render logs**
   - Build logs for installation errors
   - App logs for runtime errors

3. **Test locally first**
   - If it works locally but not on Render, it's a deployment issue
   - If it doesn't work locally, fix locally first

### Common Debug Output:
- Browser console shows: `Received video blob: X bytes` → Video downloaded successfully
- Browser console shows: `Conversion error: ...` → Check error message
- Render logs show: `ERROR: Failed to create WebDriver` → Chromium not installed
- Render logs show: `FileNotFoundError: ffmpeg` → FFmpeg not installed

---

## Alternative: Streamlit Cloud

If Flask gives you trouble, use the Streamlit version:

1. Go to https://share.streamlit.io
2. Connect GitHub repo
3. Deploy `app.py`
4. Done!

Streamlit Cloud has Chromium and FFmpeg pre-installed.
