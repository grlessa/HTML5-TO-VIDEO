# 🔧 Streamlit Cloud Troubleshooting

Common issues when deploying to Streamlit Cloud and how to fix them.

## ❌ FFmpeg Error (exit code 1)

This is the most common issue. Here's how to fix it:

### Solution 1: Verify packages.txt

Make sure your `packages.txt` file contains:
```
chromium
chromium-driver
ffmpeg
```

**Location**: Must be in the **root directory** of your repository (same level as app.py)

### Solution 2: Check FFmpeg Version on Streamlit Cloud

The FFmpeg version on Streamlit Cloud might not support certain codecs or options.

**What was fixed in the latest update:**
- ✅ Better error reporting (shows actual FFmpeg error)
- ✅ Conditional preset usage (only for x264/x265)
- ✅ Added format filter for better compatibility
- ✅ Checks for frame existence before encoding

### Solution 3: Use Compatible Settings

If FFmpeg still fails, the issue might be with codec/preset compatibility:

**Try these settings:**
- Codec: `libx264` (most compatible)
- Preset: `medium` or `fast` (not `slow` on cloud)
- FPS: 30 or 24 (not 60 on limited resources)

### Solution 4: Check Streamlit Cloud Logs

1. Go to your Streamlit Cloud dashboard
2. Click your app → "Manage app"
3. Click "Logs" tab
4. Look for the actual FFmpeg error message
5. The updated app.py now shows error details in an expander

### Solution 5: Memory Limits

Streamlit Cloud free tier has **1GB RAM limit**. If processing large/long videos:

**Reduce resource usage:**
```python
# In manual mode, use:
- Resolution: 1280x720 (instead of 1920x1080)
- Duration: 5s (instead of 10s)
- FPS: 24 (instead of 60)
```

### Solution 6: Test Specific Issues

The updated app now provides:
1. **Error expander** - Click "Show error details" to see what failed
2. **Frame count** - Shows how many frames were captured
3. **Browser detection** - Shows which browser is being used
4. **Detailed FFmpeg output** - Shows actual command and errors

## 🔍 Debugging Steps

### Step 1: Check the Error Details
After you get the error, look for the "Show error details" expander and share that output.

### Step 2: Verify Files Were Uploaded Correctly
Make sure these files are in your GitHub repo:
- ✅ app.py (latest version)
- ✅ requirements.txt
- ✅ packages.txt
- ✅ .streamlit/config.toml

### Step 3: Force Streamlit Cloud to Rebuild
1. Go to your app settings
2. Click "Reboot app"
3. Or push a small change to trigger rebuild

### Step 4: Check Browser Initialization
The app should show: "Using browser: chromium" or similar.
If you see a browser error instead, the issue is with Selenium setup.

## 🆘 Still Not Working?

### Get Detailed Error Info

1. Run the conversion with a small test file
2. When it fails, expand "Show error details"
3. Copy the error message
4. Share it so we can fix the specific issue

### Common FFmpeg Errors and Fixes

| Error Message | Solution |
|---------------|----------|
| `Unknown encoder 'libx264'` | Add `ffmpeg` to packages.txt |
| `Invalid preset` | Use `medium` instead of `slow` |
| `No such file or directory` | Frames weren't created (browser issue) |
| `Invalid argument` | Check codec compatibility |
| `Protocol not found` | File path issue (should be fixed now) |

### Test Locally First

Before deploying, test on your local machine:
```bash
streamlit run app.py
```

If it works locally but not on cloud, it's an environment issue.

## ✅ Updated Files

Make sure you have the latest versions:

### app.py Updates:
- ✅ Better FFmpeg error handling
- ✅ Detailed error reporting
- ✅ Frame existence check
- ✅ Conditional codec options
- ✅ Multiple browser path detection
- ✅ Better compatibility filters

### How to Update:

```bash
cd "/Users/lessafilms/Documents/HTML5 TO VIDEO"
git add app.py
git commit -m "Fix FFmpeg compatibility and error reporting"
git push
```

Streamlit Cloud will auto-detect and redeploy.

## 📊 Resource Limits on Streamlit Cloud

| Resource | Free Tier | Recommendation |
|----------|-----------|----------------|
| RAM | 1 GB | Use 720p, 5-10s max |
| CPU | Shared | Use fast/medium preset |
| Timeout | 10 min | Should be enough |
| Storage | Temp only | Automatic cleanup |

## 💡 Best Practices for Cloud

1. **Start with Auto Mode** - It detects optimal settings
2. **Test with small files first** - Under 5 seconds duration
3. **Use 720p resolution** - 1920x1080 might be too much
4. **Use medium preset** - Faster encoding
5. **Check error details** - Use the new expander to see what failed

## 🔄 Alternative: Use Docker Deployment

If Streamlit Cloud continues having issues, consider:
- Railway.app (similar to Streamlit but more resources)
- Google Cloud Run (scalable)
- Your own VPS (full control)

See DEPLOY.md for instructions.

---

## Quick Checklist

Before asking for help, verify:
- [ ] `packages.txt` exists in root with `chromium`, `chromium-driver`, `ffmpeg`
- [ ] Latest `app.py` is pushed to GitHub
- [ ] App successfully rebooted on Streamlit Cloud
- [ ] Tried with a small test file (5 seconds, 720p)
- [ ] Checked "Show error details" expander for actual error
- [ ] Logs in Streamlit Cloud dashboard checked

If all checked and still failing, share:
1. The error from "Show error details" expander
2. Your Streamlit Cloud log output
3. Settings used (resolution, FPS, duration, codec)
