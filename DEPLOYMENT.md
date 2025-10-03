# Deployment Guide

## 🚀 Complete CI/CD Pipeline Setup

### 1. GitHub Actions CI
- ✅ **Added**: `.github/workflows/ci.yml`
- **Runs**: Tests on every push/PR, smoke tests on main branch
- **Requires**: GitHub secrets (see below)

### 2. Docker Setup
- ✅ **Added**: `Dockerfile` with health checks
- **Command**: `uvicorn app.api:app --host 0.0.0.0 --port 8000`
- **Health Check**: `/health` endpoint

### 3. Backend Deployment (Render)
1. **Connect GitHub repo** to Render
2. **Choose**: Docker deployment
3. **Branch**: `main`
4. **Auto-deploy**: On push
5. **Environment Variables**:
   ```
   OPENAI_API_KEY=your_key_here
   APP_ENV=staging
   ```
6. **Note the staging URL** (e.g., `https://fitness-app-abc123.onrender.com`)

### 4. Frontend Deployment (Vercel)
1. **Connect GitHub repo** to Vercel
2. **Root Directory**: `frontend/`
3. **Framework**: Next.js
4. **Auto-deploy**: On push
5. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_BASE=https://your-staging-api-url.onrender.com
   PREVIEW_USER=admin
   PREVIEW_PASS=your_secure_password
   ```

### 5. GitHub Secrets Setup
Go to **GitHub repo → Settings → Secrets and variables → Actions**

Add these secrets:
```
STAGING_API_URL=https://your-staging-api-url.onrender.com
PREVIEW_USER=admin
PREVIEW_PASS=your_secure_password
```

### 6. Branch Protection
1. **GitHub repo → Settings → Branches**
2. **Add rule** for `main` branch
3. **Require**: Status checks to pass before merging
4. **Require**: CI workflow to pass

## 🔄 Deployment Flow

### Every Push:
1. **CI runs** → Tests pass
2. **Render deploys** → Backend API
3. **Vercel deploys** → Frontend UI
4. **Smoke tests run** → Health check + API test

### Access:
- **Frontend**: Vercel URL (password protected)
- **Backend**: Render URL (public API)
- **Health**: `https://your-api-url.onrender.com/health`

## 🧪 Testing

### Manual Smoke Test:
```bash
curl -s https://your-staging-url.onrender.com/health
curl -s https://your-staging-url.onrender.com/chat \
  -X POST -H "content-type: application/json" \
  -d '{"user_id":"u1","text":"I ate 1 lb 90% lean ground beef, 2 cups rice"}'
```

### Frontend Testing:
1. Visit Vercel URL
2. Enter Basic Auth credentials
3. Test nutrition logging workflow

## 🔒 Security

- **Frontend**: Basic Auth protection
- **Backend**: Environment variables for API keys
- **CI**: Secrets for staging URLs
- **Branch Protection**: CI must pass to merge

## 📝 Environment Variables Reference

### Backend (Render):
- `OPENAI_API_KEY` - Your OpenAI API key
- `APP_ENV` - `staging` or `production`

### Frontend (Vercel):
- `NEXT_PUBLIC_API_BASE` - Backend API URL
- `PREVIEW_USER` - Basic auth username
- `PREVIEW_PASS` - Basic auth password

### GitHub Actions:
- `STAGING_API_URL` - For smoke tests
- `PREVIEW_USER` - For frontend tests
- `PREVIEW_PASS` - For frontend tests
