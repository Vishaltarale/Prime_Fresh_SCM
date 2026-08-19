# ⚡ Vercel Deployment - Quick Start Guide

## 🚀 Fast Deployment Steps (5 minutes)

### Step 1: Login to Vercel
```powershell
vercel login
```

### Step 2: Set Environment Variables

#### Option A: Via CLI
```powershell
# Backend variables
vercel env add DJANGO_SECRET_KEY
vercel env add DJANGO_DEBUG
vercel env add DJANGO_ALLOWED_HOSTS
vercel env add DATABASE_URL
vercel env add MONGODB_URI

# Frontend variables
vercel env add VITE_API_BASE_URL
```

#### Option B: Via Dashboard
1. Go to https://vercel.com/dashboard
2. Select your project
3. Settings → Environment Variables
4. Add variables from `.env.example`

### Step 3: Deploy Backend
```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"

# Preview deployment (test)
vercel

# Production deployment
vercel --prod
```

### Step 4: Deploy Frontend
```powershell
cd react-web

# Preview deployment
vercel

# Production deployment
vercel --prod
```

### Step 5: Verify Deployment
```powershell
# Check deployment status
vercel list

# View logs
vercel logs --prod

# Test API
curl https://your-backend.vercel.app/api/health/
```

---

## 📋 Deployment Checklist

### Before Deployment

- [ ] Copy `.env.example` to `.env`
- [ ] Update all environment variables
- [ ] Test locally: `python manage.py runserver`
- [ ] Test frontend: `npm run dev`
- [ ] Commit changes to Git
- [ ] Push to main branch

### Backend

- [ ] Vercel CLI installed: `vercel --version`
- [ ] Logged into Vercel: `vercel login`
- [ ] `requirements.txt` up to date: `pip freeze > requirements.txt`
- [ ] Database credentials set
- [ ] `DJANGO_ALLOWED_HOSTS` configured
- [ ] `SECRET_KEY` changed for production

### Frontend

- [ ] `package.json` properly configured
- [ ] Build script works: `npm run build`
- [ ] `VITE_API_BASE_URL` set to backend URL
- [ ] Environment variables exported
- [ ] `.gitignore` includes `dist/` and `node_modules/`

---

## 💻 One-Command Deployment

### Using PowerShell Script

```powershell
# Navigate to project root
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"

# Run deployment script
.\deploy.ps1

# Or with options:
.\deploy.ps1 -Target backend -Env prod          # Deploy backend to production
.\deploy.ps1 -Target frontend -Env preview      # Deploy frontend to preview
.\deploy.ps1 -Target both -Env prod -Force      # Deploy both with force rebuild
.\deploy.ps1 -Target frontend -BuildOnly        # Build only, don't deploy
```

---

## 🔗 Environment Variable Mapping

### Backend (Django)
```
DJANGO_SECRET_KEY → Secret key for session signing
DJANGO_DEBUG → Debug mode (False in production)
DJANGO_ALLOWED_HOSTS → Comma-separated allowed domains
DATABASE_URL → PostgreSQL connection string
MONGODB_URI → MongoDB connection string
```

### Frontend (React)
```
VITE_API_BASE_URL → Backend API URL
VITE_APP_NAME → Application name
NODE_ENV → Environment (production/development)
```

---

## 🌐 Domain Setup

### Backend Domain
1. Vercel Dashboard → Your Backend Project
2. Settings → Domains
3. Add domain or use default `.vercel.app`

### Frontend Domain
1. Vercel Dashboard → Your Frontend Project
2. Settings → Domains
3. Add custom domain if desired

### Update CORS
In `SCM/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'https://your-frontend-domain.vercel.app',
    'https://your-custom-domain.com',
]
```

---

## 📊 URLs After Deployment

```
Backend API:        https://prime-fresh-scm.vercel.app
Frontend:           https://prime-fresh-scm-web.vercel.app
API Docs:           https://prime-fresh-scm.vercel.app/api/docs/
Admin Panel:        https://prime-fresh-scm.vercel.app/admin/
```

---

## 🔍 Verification Commands

```powershell
# Check deployment
vercel list

# View logs (real-time)
vercel logs --prod --follow

# Check specific project
vercel logs prime-fresh-scm --prod

# Inspect environment
vercel env list

# Get project info
vercel projects list
```

---

## 🐛 Common Issues & Fixes

### Issue 1: "requirements.txt not found"
```powershell
pip freeze > requirements.txt
vercel --prod
```

### Issue 2: "Module not found"
```powershell
# Update requirements
pip install -r requirements.txt
pip freeze > requirements.txt
vercel --prod --force
```

### Issue 3: "API calls returning 404"
```powershell
# Check VITE_API_BASE_URL
vercel env list

# Update in Vercel Dashboard and redeploy
vercel --prod --force
```

### Issue 4: "Database connection failed"
```powershell
# Verify DATABASE_URL
vercel env list

# Test connection
python manage.py dbshell

# Redeploy
vercel --prod
```

### Issue 5: "Static files not loading"
```powershell
# Collect static files
python manage.py collectstatic --noinput

# Verify STATIC_URL and STATIC_ROOT in settings.py
vercel --prod --force
```

---

## 📱 Check Deployment Status

Open these URLs to verify:

1. **Backend Health Check**
   ```
   https://your-backend.vercel.app/api/health/
   ```

2. **Frontend Homepage**
   ```
   https://your-frontend.vercel.app/
   ```

3. **API Authentication**
   ```
   https://your-backend.vercel.app/api/auth/login/
   ```

4. **Frontend API Integration**
   - Open browser DevTools → Network tab
   - Log in to frontend
   - Verify API calls to backend

---

## 🔐 Security Reminders

⚠️ **IMPORTANT**

1. **Never commit `.env` files** → Add to `.gitignore`
2. **Use environment variables** → All sensitive data
3. **Change `SECRET_KEY`** → Generate new one for production
4. **Set `DEBUG=False`** → No stack traces exposed
5. **CORS settings** → Only allow your domains
6. **HTTPS enforced** → Vercel does this automatically

---

## 📞 Useful Commands Reference

```powershell
# Login/Auth
vercel login                          # Login to Vercel
vercel logout                         # Logout
vercel whoami                         # Current user

# Project Management
vercel link                           # Link local project
vercel list                           # List projects
vercel projects list                  # List all projects

# Deployment
vercel                                # Deploy to preview
vercel --prod                         # Deploy to production
vercel --prod --force                 # Force rebuild
vercel build                          # Build only

# Environment
vercel env list                       # List variables
vercel env add NAME                   # Add variable
vercel env rm NAME                    # Remove variable
vercel env pull                       # Download to .env

# Logs & Monitoring
vercel logs                           # View logs
vercel logs --prod                    # Production logs
vercel logs --follow                  # Real-time logs
vercel logs --limit 100               # Last 100 lines

# Cleanup
vercel remove                         # Remove deployment
vercel rollback                       # Rollback to previous
```

---

## 📚 Resources

- [Vercel Docs](https://vercel.com/docs)
- [Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Vite Guide](https://vitejs.dev/)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)

---

## ✅ After Successful Deployment

1. ✅ Test all features in production
2. ✅ Monitor logs for errors
3. ✅ Set up domain aliases
4. ✅ Configure monitoring/alerts
5. ✅ Document deployment process
6. ✅ Set up backup strategy
7. ✅ Plan CI/CD pipeline

---

**Last Updated:** August 18, 2026
**Status:** Ready for Deployment ✓
