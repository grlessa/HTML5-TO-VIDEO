# 📦 GitHub Setup Guide

Quick guide to push this project to GitHub and deploy it.

## 🚀 Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** icon → **"New repository"**
3. Repository settings:
   - **Name**: `html5-to-video`
   - **Description**: `Convert HTML5 animations to high-quality video with auto-detection`
   - **Visibility**: Public (required for free Streamlit deployment)
   - ✅ Add README file: **NO** (we already have one)
   - ✅ Add .gitignore: **NO** (we already have one)
4. Click **"Create repository"**

## 📤 Step 2: Push Code to GitHub

Run these commands in your terminal:

```bash
# Navigate to project directory
cd "/Users/lessafilms/Documents/HTML5 TO VIDEO"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: HTML5 to Video Converter with auto-detection"

# Add your GitHub repository as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/html5-to-video.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 🌐 Step 3: Deploy to Streamlit Cloud (FREE!)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign in"** (use your GitHub account)
3. Click **"New app"**
4. Fill in the details:
   - **Repository**: `YOUR_USERNAME/html5-to-video`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click **"Deploy!"**

Wait 2-3 minutes and your app will be live at:
```
https://YOUR_USERNAME-html5-to-video.streamlit.app
```

## ✅ That's it!

Your app is now:
- ✅ Hosted on GitHub
- ✅ Deployed to the web (FREE!)
- ✅ Auto-updates when you push changes
- ✅ Has a public URL you can share

## 🔄 Making Updates

Whenever you make changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

Streamlit Cloud will automatically detect the changes and redeploy!

## 🎨 Customize Your Deployment

### Custom Domain
1. Go to your app settings on Streamlit Cloud
2. Click "Settings" → "General"
3. Add your custom domain

### Environment Variables
If you need secrets (API keys, etc):
1. Go to app settings → "Secrets"
2. Add your secrets in TOML format

### Resource Limits
Free tier includes:
- 1 GB RAM
- Unlimited bandwidth
- 3 apps per account

Need more? Upgrade to Streamlit Cloud Pro.

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [GitHub Documentation](https://docs.github.com)
- [Streamlit Community](https://discuss.streamlit.io)

## 🆘 Troubleshooting

### Push rejected?
```bash
git pull origin main --rebase
git push
```

### Deployment failed?
Check Streamlit Cloud logs:
1. Go to your app
2. Click "Manage app"
3. Check "Logs" tab

### Need help?
[Open an issue](https://github.com/YOUR_USERNAME/html5-to-video/issues)
