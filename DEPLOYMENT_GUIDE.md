# 🚀 Vercel Deployment Guide - Backend & Frontend

This guide walks you through deploying your Django backend and React frontend to Vercel.

---

## 📋 Prerequisites

Before you begin, ensure you have:

1. **Vercel CLI installed** ✅ (Already confirmed)
   ```powershell
   vercel --version  # Should show version
   ```

2. **Vercel Account** - Sign up at https://vercel.com

3. **Git repository** - Your project should be in a Git repo (GitHub, GitLab, Bitbucket)

4. **Environment variables** - Database URLs, API keys, etc.

---

## 🏗️ Project Structure for Deployment

```
Prime_Fresh_SCM/
├── react-web/                    # Frontend (React + Vite)
├── react-native-app/             # Mobile app
├── api/                           # Django API app
├── SCM/                           # Django settings
├── manage.py                      # Django management
├── requirements.txt               # Python dependencies
├── vercel.json                    # Vercel backend config
├── react-web/vercel.json          # Vercel frontend config
└── .env.example                   # Environment variables template
```

---

## 📝 Step 1: Prepare Your Environment

### 1.1 Create Environment Variables File

Create `.env.production` in the root directory:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-backend-domain.vercel.app,your-domain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/dbname
VITE_API_BASE_URL=https://your-backend-domain.vercel.app
```

### 1.2 Update Django Settings

Edit `SCM/settings.py`:

```python
import os
from pathlib import Path

# Security settings for production
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

# CORS settings
CORS_ALLOWED_ORIGINS = [
    os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'scm'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### 1.3 Create Backend vercel.json

Create `vercel.json` in the root directory:

```json
{
  "version": 2,
  "buildCommand": "pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput",
  "outputDirectory": ".",
  "env": {
    "DJANGO_SECRET_KEY": "@DJANGO_SECRET_KEY",
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": "@DJANGO_ALLOWED_HOSTS",
    "DATABASE_URL": "@DATABASE_URL",
    "MONGODB_URI": "@MONGODB_URI"
  },
  "functions": {
    "api/index.py": {
      "runtime": "python3.11"
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/wsgi.py"
    }
  ]
}
```

### 1.4 Create Backend WSGI File

Create `api/wsgi.py`:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SCM.settings')

application = get_wsgi_application()
```

### 1.5 Create Frontend vercel.json

Create `react-web/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_BASE_URL": "@VITE_API_BASE_URL"
  }
}
```

---

## 🚀 Step 2: Deploy Backend

### 2.1 Initialize Vercel for Backend

```powershell
# Navigate to root directory
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"

# Login to Vercel
vercel login

# Link project to Vercel
vercel link --project prime-fresh-scm-backend
```

### 2.2 Add Environment Variables

```powershell
# Add environment variables to Vercel
vercel env add DJANGO_SECRET_KEY
vercel env add DJANGO_DEBUG
vercel env add DJANGO_ALLOWED_HOSTS
vercel env add DATABASE_URL
vercel env add MONGODB_URI
```

Or use Vercel Dashboard:
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add each variable

### 2.3 Deploy Backend

```powershell
# Deploy to production
vercel --prod

# Or deploy to preview/staging
vercel
```

---

## 🎨 Step 3: Deploy Frontend

### 3.1 Update API URL in Frontend

Edit `react-web/.env.production`:

```env
VITE_API_BASE_URL=https://your-backend-domain.vercel.app
```

Update `react-web/src/lib/apiClient.ts`:

```typescript
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});
```

### 3.2 Build and Test Locally

```powershell
# Navigate to react-web
cd react-web

# Install dependencies
npm install

# Build
npm run build

# Preview production build
npm run preview
```

### 3.3 Deploy Frontend

```powershell
# Option 1: Deploy with Vercel CLI
vercel --prod

# Option 2: From root, deploy react-web
vercel ./react-web --prod
```

### 3.4 Configure Frontend Domain

In Vercel Dashboard:
1. Select your frontend project
2. Go to Settings → Domains
3. Add your custom domain (if applicable)

---

## 📱 Step 4: Deploy React Native App (Optional)

For React Native on Expo/EAS:

```powershell
# Navigate to react-native-app
cd react-native-app

# Update API endpoint
# Edit .env.production
EXPO_PUBLIC_API_BASE_URL=https://your-backend-domain.vercel.app

# Build and publish
eas build --platform all --auto-submit
```

---

## 🔗 Step 5: Connect Frontend to Backend

### 5.1 Update CORS Settings

Edit `SCM/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    'https://your-frontend-domain.vercel.app',
    'https://www.your-frontend-domain.com',
]
```

### 5.2 Update Frontend API Base URL

In `react-web/src/lib/apiClient.ts`:

```typescript
const API_BASE_URL = process.env.VITE_API_BASE_URL || 
  (process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-domain.vercel.app'
    : 'http://localhost:8000');
```

---

## 🔍 Step 6: Verify Deployment

### 6.1 Test Backend API

```powershell
# Test the backend
curl https://your-backend-domain.vercel.app/api/health/

# Check specific endpoints
curl https://your-backend-domain.vercel.app/api/auth/login/
```

### 6.2 Test Frontend

1. Open https://your-frontend-domain.vercel.app
2. Check browser console for errors
3. Test login functionality
4. Verify API calls are working

### 6.3 Check Logs

```powershell
# View backend logs
vercel logs --prod

# View frontend logs
vercel logs your-frontend-project --prod

# Real-time logs
vercel logs --prod --follow
```

---

## 🔐 Security Checklist

- [ ] Never commit `.env` files to Git
- [ ] Use environment variables for all secrets
- [ ] Set `DEBUG = False` in production
- [ ] Enable HTTPS (automatic with Vercel)
- [ ] Configure CORS properly
- [ ] Use strong `SECRET_KEY`
- [ ] Validate all user inputs
- [ ] Keep dependencies updated
- [ ] Use environment-specific settings
- [ ] Enable authentication/authorization

---

## 🐛 Troubleshooting

### Backend Deployment Issues

**Issue: "Module not found" errors**
```powershell
# Ensure requirements.txt is up to date
pip freeze > requirements.txt
vercel redeploy --prod
```

**Issue: Database connection failures**
- Check DATABASE_URL environment variable
- Ensure database is accessible from Vercel IPs
- Check database credentials

**Issue: Static files not loading**
```powershell
# Run collectstatic locally
python manage.py collectstatic --noinput

# Redeploy
vercel --prod
```

### Frontend Deployment Issues

**Issue: API calls failing with 404**
- Verify VITE_API_BASE_URL is set correctly
- Check backend is deployed and accessible
- Check CORS configuration

**Issue: Build fails**
```powershell
cd react-web
npm install --force
npm run build
```

**Issue: Environment variables not loading**
```powershell
# Verify variables in Vercel Dashboard
vercel env list

# Rebuild after adding variables
vercel --prod --force
```

---

## 📊 Monitoring & Maintenance

### 1. Set Up Monitoring
- Vercel Analytics Dashboard
- Error tracking with Sentry
- Performance monitoring

### 2. Scheduled Tasks
- Database backups
- Dependency updates
- Security patches

### 3. CI/CD Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/action@v4
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-args: '--prod'
```

---

## 🔄 Redeployment

To redeploy after making changes:

```powershell
# Commit changes to Git
git add .
git commit -m "Update configuration"
git push origin main

# Option 1: Automatic (if linked to GitHub)
# Vercel will automatically deploy on push

# Option 2: Manual redeploy
vercel --prod

# Option 3: Force rebuild
vercel --prod --force
```

---

## 📞 Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Vite Build Guide](https://vitejs.dev/guide/build.html)
- [Vercel Community](https://github.com/vercel/community)

---

## 🎉 Deployment Complete!

Your application is now deployed on Vercel. Access it at:

- **Backend**: https://your-backend-domain.vercel.app
- **Frontend**: https://your-frontend-domain.vercel.app
- **API Docs**: https://your-backend-domain.vercel.app/api/docs

---

Last Updated: August 18, 2026
