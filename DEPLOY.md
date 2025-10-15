# 🚀 Deployment Guide

This guide covers deploying the HTML5 to Video Converter to various platforms.

## ☁️ Streamlit Cloud (Recommended - Free!)

**Easiest and completely free option**

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/html5-to-video.git
   git push -u origin main
   ```

2. **Deploy**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file: `app.py`
   - Click "Deploy"

3. **Done!** Your app will be live at `https://yourusername-html5-to-video.streamlit.app`

### Limitations
- Max 200MB file upload
- 1GB RAM
- Shared resources

---

## 🐳 Docker (Self-Hosted)

**Best for: Full control, unlimited resources**

1. **Build the image**
   ```bash
   docker build -t html5-to-video .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 html5-to-video
   ```

3. **Access at**: `http://localhost:8501`

### Deploy to Cloud Services

#### AWS ECS
```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker tag html5-to-video:latest your-account.dkr.ecr.us-east-1.amazonaws.com/html5-to-video:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/html5-to-video:latest

# Create ECS service with the image
```

#### Google Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/your-project/html5-to-video

# Deploy
gcloud run deploy html5-to-video \
  --image gcr.io/your-project/html5-to-video \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 3600
```

#### Azure Container Instances
```bash
# Push to Azure Container Registry
az acr build --registry yourregistry --image html5-to-video .

# Deploy
az container create \
  --resource-group yourgroup \
  --name html5-to-video \
  --image yourregistry.azurecr.io/html5-to-video \
  --dns-name-label html5-to-video \
  --ports 8501
```

---

## 🌊 Heroku

**Good for: Simple deployment with add-ons**

1. **Create `Procfile`**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Add buildpacks**
   ```bash
   heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
   heroku buildpacks:add --index 2 heroku/python
   ```

3. **Create `Aptfile`**
   ```
   chromium
   chromium-driver
   ffmpeg
   ```

4. **Deploy**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

---

## 🔷 Railway

**Good for: Easy deployment, free tier**

1. **Push to GitHub** (if not already)

2. **Deploy**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-detects Dockerfile

3. **Configure**
   - Set memory to 4GB+ (in Settings)
   - Set timeout to 3600s

---

## 🎯 DigitalOcean App Platform

1. **Push to GitHub**

2. **Create App**
   - Go to [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Select GitHub repository
   - Choose "Dockerfile" as build method

3. **Configure**
   - Set instance size: Basic ($12/mo for 2GB RAM)
   - Set HTTP Port: 8501

---

## 🖥️ VPS (Ubuntu/Debian)

**Best for: Maximum control, custom domain**

1. **SSH into your server**
   ```bash
   ssh user@your-server-ip
   ```

2. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install -y python3-pip chromium chromium-driver ffmpeg
   ```

3. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/html5-to-video.git
   cd html5-to-video
   pip3 install -r requirements.txt
   ```

4. **Run with systemd**
   Create `/etc/systemd/system/html5-to-video.service`:
   ```ini
   [Unit]
   Description=HTML5 to Video Converter
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/html5-to-video
   ExecStart=/usr/local/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable html5-to-video
   sudo systemctl start html5-to-video
   ```

6. **Setup Nginx reverse proxy**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

---

## 🔒 SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Monitoring

### Health Check Endpoint
All deployments expose: `http://your-app/_stcore/health`

### Recommended Monitoring
- **Uptime Robot**: Free uptime monitoring
- **New Relic**: Performance monitoring
- **Sentry**: Error tracking

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid |
|----------|-----------|------|
| Streamlit Cloud | ✅ Unlimited | N/A |
| Railway | $5 credit/mo | ~$10/mo |
| Heroku | ❌ (discontinued) | ~$7/mo |
| Google Cloud Run | 2M requests/mo | Pay per use |
| AWS ECS | ❌ | ~$15/mo |
| DigitalOcean | ❌ | $12/mo |
| VPS | ❌ | $5-20/mo |

---

## ✅ Recommended Setup

**For Personal Use**: Streamlit Cloud (Free)

**For Production**:
- VPS with Nginx + SSL
- Or Google Cloud Run (scalable)

**For Enterprise**:
- Kubernetes cluster
- Load balancer
- Auto-scaling

---

## 🆘 Troubleshooting

### Out of Memory
- Increase container memory to 4GB+
- Add swap space
- Process smaller files

### Browser Timeout
- Increase timeout settings
- Use faster preset
- Reduce FPS/duration

### Chrome Driver Issues
```bash
# Update Chrome/Chromium
apt update && apt upgrade chromium
```

---

Need help? [Open an issue](https://github.com/yourusername/html5-to-video/issues)
