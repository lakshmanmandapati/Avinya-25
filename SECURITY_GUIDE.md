# 🔐 Security Guide for Tensora Backend

## ⚠️ CRITICAL: Google Cloud Credentials Security

### What We Fixed
Your `gcp_key.json` file contains sensitive Google Cloud service account credentials that should **NEVER** be committed to a public repository. We've implemented secure credential management.

### Changes Made

#### 1. Updated `.gitignore`
```gitignore
# CRITICAL: Google Cloud credentials and other sensitive files
server/gcp_key.json
gcp_key.json
*.json.key
*-key.json
service-account*.json
```

#### 2. Modified Backend (`server/proxy.py`)
- Now uses environment variables instead of local files
- Supports `GOOGLE_CLOUD_CREDENTIALS_JSON` environment variable
- Falls back to local file only for development
- Provides clear error messages and security warnings

#### 3. Updated Docker Configuration
- Dockerfile removes any accidentally copied credential files
- `render.yaml` configured for environment variable usage

## 🚀 Deployment Setup

### For Render (Recommended)

1. **Create Environment Variable Group** (Recommended):
   ```
   Group Name: google-cloud-secrets
   Variables:
   - GOOGLE_CLOUD_CREDENTIALS_JSON = [your entire gcp_key.json content as string]
   ```

2. **Or Set Individual Environment Variable**:
   - Go to your Render service settings
   - Add environment variable: `GOOGLE_CLOUD_CREDENTIALS_JSON`
   - Value: Copy your entire `gcp_key.json` content as a single line string

### For Other Platforms

#### Railway
```bash
railway variables set GOOGLE_CLOUD_CREDENTIALS_JSON='{"type":"service_account",...}'
```

#### Heroku
```bash
heroku config:set GOOGLE_CLOUD_CREDENTIALS_JSON='{"type":"service_account",...}'
```

#### Google Cloud Run
```bash
gcloud run services update tensora-backend \
  --set-env-vars GOOGLE_CLOUD_CREDENTIALS_JSON='{"type":"service_account",...}'
```

## 🛡️ Security Best Practices

### DO ✅
- Use environment variables for all sensitive data
- Use secrets management services (AWS Secrets Manager, Google Secret Manager)
- Rotate credentials regularly
- Use least-privilege access principles
- Monitor credential usage

### DON'T ❌
- Commit credentials to version control
- Share credentials in plain text
- Use production credentials in development
- Hard-code API keys in source code
- Store credentials in Docker images

## 🔧 Local Development Setup

### Option 1: Environment Variable (Recommended)
```bash
export GOOGLE_CLOUD_CREDENTIALS_JSON='{"type":"service_account","project_id":"speech-to-text-api-472410",...}'
```

### Option 2: Local File (Development Only)
Keep your `gcp_key.json` file locally but ensure it's in `.gitignore`

## 🚨 If Credentials Are Already Exposed

If you've already pushed credentials to GitHub:

1. **Immediately revoke the service account**:
   ```bash
   gcloud iam service-accounts delete stt-service-account@speech-to-text-api-472410.iam.gserviceaccount.com
   ```

2. **Create a new service account**:
   ```bash
   gcloud iam service-accounts create new-stt-service-account
   ```

3. **Remove from Git history**:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch server/gcp_key.json' --prune-empty --tag-name-filter cat -- --all
   ```

## 📊 Monitoring

- Monitor Google Cloud audit logs for unusual activity
- Set up alerts for credential usage
- Regularly review service account permissions
- Use Google Cloud Security Command Center

## 🔄 Credential Rotation

1. Create new service account
2. Update environment variables in deployment platform
3. Test the new credentials
4. Delete old service account
5. Update local development environment

Remember: Security is not optional - it's essential for protecting your application and users!
