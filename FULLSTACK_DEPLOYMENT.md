# 🚀 Full-Stack Deployment Guide: Render + Vercel

## Overview
- **Backend**: Render (Docker-based Python Flask API)
- **Frontend**: Vercel (React/Vite application)
- **Database**: TinyDB (file-based, included in backend)

## 📋 Prerequisites
- GitHub account
- Render account (free tier available)
- Vercel account (free tier available)
- Your Google Cloud credentials JSON

---

## 🔧 Part 1: Backend Deployment on Render

### Step 1: Prepare Your Repository
```bash
# Make sure all files are committed
git add .
git commit -m "Secure backend with environment variables"
git push origin main
```

### Step 2: Create Render Service
1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repository

### Step 3: Configure Render Service
```yaml
# These settings will be auto-detected from render.yaml
Name: tensora-backend
Environment: Docker
Build Command: (auto-detected from Dockerfile)
Start Command: (auto-detected from Dockerfile)
```

### Step 4: Set Environment Variables
In Render dashboard, go to **Environment** tab and add:

```
GOOGLE_CLOUD_CREDENTIALS_JSON=[YOUR_COMPLETE_GCP_SERVICE_ACCOUNT_JSON_HERE]

PORT=4000
FLASK_ENV=production
PYTHONPATH=/app
```

**Note**: Replace `[YOUR_COMPLETE_GCP_SERVICE_ACCOUNT_JSON_HERE]` with your actual Google Cloud service account JSON content as a single line string.

### Step 5: Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Your backend will be available at: `https://tensora-backend.onrender.com`

---

## 🎨 Part 2: Frontend Deployment on Vercel

### Step 1: Prepare Frontend Configuration
Create production environment configuration:

```bash
# Create .env.production file
echo "VITE_API_URL=https://tensora-backend.onrender.com" > .env.production
```

### Step 2: Update Frontend API Configuration
Find your API configuration file and update it to use environment variables:

```javascript
// In your API config file (likely in src/config or similar)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000';

export const API_ENDPOINTS = {
  chat: `${API_BASE_URL}/proxy/ai`,
  conversations: `${API_BASE_URL}/conversations`,
  speechToText: `${API_BASE_URL}/speech-to-text`,
  health: `${API_BASE_URL}/health`
};
```

### Step 3: Deploy to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"New Project"**
3. Import your GitHub repository
4. Configure project:
   ```
   Framework Preset: Vite
   Root Directory: ./
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

### Step 4: Set Environment Variables
In Vercel dashboard, go to **Settings** → **Environment Variables**:
```
VITE_API_URL = https://tensora-backend.onrender.com
```

### Step 5: Deploy
1. Click **"Deploy"**
2. Wait for deployment (2-5 minutes)
3. Your frontend will be available at: `https://tensora-ui.vercel.app`

---

## 🔗 Part 3: Connect Frontend to Backend

### Update CORS Settings
Your backend already has CORS configured, but ensure it includes your Vercel domain:

```python
# In server/proxy.py (already configured)
CORS(app, origins=[
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
    "http://localhost:4000", 
    "https://tensora-ui.vercel.app",  # Add your Vercel domain
    "*"
])
```

---

## 🧪 Part 4: Testing Your Deployment

### Backend Health Check
```bash
curl https://tensora-backend.onrender.com/health
```

### Frontend Testing
1. Visit your Vercel URL
2. Test chat functionality
3. Test voice recording
4. Test conversation management

---

## 🔧 Troubleshooting

### Common Issues:

1. **Backend not starting**: Check Render logs for environment variable issues
2. **CORS errors**: Ensure your Vercel domain is in CORS origins
3. **API calls failing**: Verify VITE_API_URL is set correctly
4. **Speech-to-text not working**: Check Google Cloud credentials format

### Debugging Commands:
```bash
# Check backend logs
# Go to Render dashboard → Your service → Logs

# Check frontend build logs  
# Go to Vercel dashboard → Your project → Functions tab
```

---

## 📊 Monitoring

### Render Monitoring
- Health checks: `/health` endpoint
- Logs: Available in Render dashboard
- Metrics: CPU, Memory usage

### Vercel Monitoring
- Analytics: Built-in Vercel analytics
- Performance: Core Web Vitals
- Error tracking: Runtime logs

---

## 🚀 Going Live Checklist

- [ ] Backend deployed and health check passing
- [ ] Frontend deployed and loading
- [ ] Environment variables configured
- [ ] CORS properly configured
- [ ] Speech-to-text working
- [ ] Conversation management working
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active
- [ ] Monitoring set up

Your full-stack Tensora application is now live! 🎉
