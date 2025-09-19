# Tensora Backend Deployment Guide

## Docker Deployment

### Prerequisites
- Docker installed on your system
- Your project files including the `server/` directory
- Environment variables configured

### Local Testing

1. **Build the Docker image:**
   ```bash
   docker build -t tensora-backend .
   ```

2. **Run the container locally:**
   ```bash
   docker run -d -p 4000:4000 --name tensora-backend tensora-backend
   ```

3. **Test the health endpoint:**
   ```bash
   curl http://localhost:4000/health
   ```

4. **Stop and remove the container:**
   ```bash
   docker stop tensora-backend && docker rm tensora-backend
   ```

## Render Deployment

### Method 1: Using render.yaml (Recommended)

1. **Push your code to GitHub/GitLab**
2. **Connect your repository to Render**
3. **The `render.yaml` file will automatically configure:**
   - Docker build environment
   - Health check endpoint
   - Environment variables
   - Port configuration

### Method 2: Manual Setup

1. **Create a new Web Service on Render**
2. **Configure the following settings:**
   - **Environment:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Port:** 4000
   - **Health Check Path:** `/health`

3. **Set Environment Variables:**
   ```
   PORT=4000
   FLASK_ENV=production
   PYTHONPATH=/app
   GOOGLE_APPLICATION_CREDENTIALS=server/gcp_key.json
   ```

### Important Notes for Render

- Render automatically sets the `PORT` environment variable
- The health check endpoint `/health` is already implemented
- Make sure your `gcp_key.json` is included in the repository (be careful with sensitive data)
- Consider using Render's environment variable groups for sensitive data

## Other Cloud Platforms

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku container:push web
heroku container:release web
```

### Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/tensora-backend
gcloud run deploy --image gcr.io/PROJECT-ID/tensora-backend --platform managed
```

## Environment Variables

Make sure to set these environment variables in your deployment platform:

- `PORT`: The port your application will run on (usually set automatically)
- `FLASK_ENV`: Set to `production` for production deployments
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud credentials file
- Any API keys or secrets your application needs

## Security Considerations

1. **Never commit sensitive files like API keys to version control**
2. **Use environment variables for all sensitive configuration**
3. **Consider using secrets management services**
4. **Enable HTTPS in production**
5. **Review CORS settings for production domains**

## Monitoring and Logs

- Use the `/health` endpoint for health checks
- Monitor application logs through your platform's dashboard
- Set up alerts for application downtime
- Consider implementing structured logging for better debugging

## Troubleshooting

### Common Issues:

1. **Port binding issues:** Make sure your app listens on `0.0.0.0` not `localhost`
2. **File path issues:** Use relative paths and ensure all required files are copied
3. **Environment variables:** Double-check all required env vars are set
4. **Dependencies:** Ensure all Python packages are in `requirements.txt`

### Debug Commands:

```bash
# Check container logs
docker logs tensora-backend

# Execute commands inside container
docker exec -it tensora-backend /bin/bash

# Check running processes
docker ps
```
