# 👋 START HERE - Vercel Deployment Setup

Welcome! Your application is ready to deploy. Follow these steps **exactly** in order.

---

## ⏱️ Time Required: ~15-20 minutes

---

## 🎯 What You're About to Do

1. Create `.env` file with your settings
2. Login to Vercel
3. Deploy backend (Django API)
4. Deploy frontend (React)
5. Verify everything works

---

## 📋 Step-by-Step Instructions

### STEP 1: Create Your Environment File

1. **Copy** `.env.example` file
2. **Paste** and rename to `.env` (in same directory)
3. **Edit** `.env` with your values:

```env
# Edit these values
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=your-database-url-here
MONGODB_URI=your-mongodb-url-here
VITE_API_BASE_URL=http://localhost:8000  # Update after backend deployment
```

⚠️ **IMPORTANT**: Never share or commit `.env` file! It has secrets!

---

### STEP 2: Open PowerShell

```powershell
# Open PowerShell and navigate to project
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"

# Verify you're in the right place
pwd  # Should show: C:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM
```

---

### STEP 3: Verify Vercel CLI

```powershell
vercel --version
```

Expected output: `Vercel CLI 58.7.1` (or higher)

✅ Already installed! ✓

---

### STEP 4: Login to Vercel

```powershell
vercel login
```

This opens a browser. Follow the prompts to:
1. Sign up for Vercel (if you don't have account)
2. Or log in to existing account
3. Authorize Vercel CLI

After login, you'll return to PowerShell.

---

### STEP 5: Verify Login

```powershell
vercel whoami
```

Shows your Vercel username. ✓

---

### STEP 6: Create Backend on Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Create new project: Name it `prime-fresh-scm-backend`
4. Don't import from GitHub yet (we'll link it manually)
5. Note the project name

---

### STEP 7: Create Frontend on Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Create new project: Name it `prime-fresh-scm-web`
4. Note the project name

---

### STEP 8: Generate Requirements File

```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"
pip freeze > requirements.txt
```

This creates a list of Python packages.

---

### STEP 9: Link Backend to Vercel

```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"
vercel link --project prime-fresh-scm-backend
```

Choose options:
- Project: `prime-fresh-scm-backend`
- Build: `N` (no)
- Files: `./` (default)

---

### STEP 10: Add Backend Environment Variables

Run each command separately and paste values when prompted:

```powershell
vercel env add DJANGO_SECRET_KEY
# Paste: your-super-secret-key-from-.env

vercel env add DJANGO_DEBUG
# Type: False

vercel env add DJANGO_ALLOWED_HOSTS
# Type: localhost,127.0.0.1

vercel env add DATABASE_URL
# Paste: your-database-url

vercel env add MONGODB_URI
# Paste: your-mongodb-uri
```

---

### STEP 11: Deploy Backend (Preview First!)

```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"
vercel
```

This deploys to **PREVIEW** (for testing).

Follow prompts:
- Set up and deploy? → `Y`
- Scope? → Your username
- Link to existing? → `N` (already linked)

After successful deploy, you'll see a preview URL like:
```
✅ Production: https://prime-fresh-scm-backend.vercel.app [copied to clipboard]
```

**✨ Save this URL!** You'll need it for frontend.

---

### STEP 12: Test Backend

```powershell
# Test with your actual URL
curl https://prime-fresh-scm-backend.vercel.app/api/health/
```

If you see a response (even if error 404), the backend deployed! ✓

---

### STEP 13: Deploy Backend to Production

```powershell
vercel --prod
```

This is your **LIVE** backend URL.

---

### STEP 14: Navigate to Frontend

```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM\react-web"
```

---

### STEP 15: Link Frontend to Vercel

```powershell
vercel link --project prime-fresh-scm-web
```

---

### STEP 16: Update Frontend API URL

Create/edit file: `react-web\.env.production`

```env
VITE_API_BASE_URL=https://prime-fresh-scm-backend.vercel.app
```

Replace with your actual backend URL from STEP 11.

---

### STEP 17: Install Dependencies

```powershell
npm install
```

This downloads all JavaScript packages. Takes ~2-3 minutes.

---

### STEP 18: Build Frontend Locally

```powershell
npm run build
```

If successful, you see:
```
✓ built in 12.34s
```

⚠️ If it fails, check error messages and fix before proceeding.

---

### STEP 19: Add Frontend Environment Variables

```powershell
vercel env add VITE_API_BASE_URL
# Paste: https://prime-fresh-scm-backend.vercel.app
```

---

### STEP 20: Deploy Frontend (Preview)

```powershell
vercel
```

Follow prompts. Gets you a preview URL like:
```
✅ Preview: https://prime-fresh-scm-web.vercel.app [copied to clipboard]
```

**✨ Save this URL!**

---

### STEP 21: Deploy Frontend to Production

```powershell
vercel --prod
```

Your live frontend! 🚀

---

### STEP 22: Go Back to Backend & Update CORS

```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"
```

Edit: `SCM/settings.py`

Find this section:
```python
CORS_ALLOWED_ORIGINS = [...]
```

Update to:
```python
CORS_ALLOWED_ORIGINS = [
    'https://prime-fresh-scm-web.vercel.app',
]
```

Replace with your actual frontend URL.

---

### STEP 23: Redeploy Backend

```powershell
vercel --prod --force
```

---

### STEP 24: Test Everything Works

1. **Open Frontend**: https://prime-fresh-scm-web.vercel.app
2. **Try to Login**: Enter test credentials
3. **Open DevTools**: Press `F12`
4. **Go to Network tab**: Watch API calls
5. **Check that calls go to**: `prime-fresh-scm-backend.vercel.app`

If you see data loading → Success! ✅

---

## 🎉 Success Indicators

When everything works, you should see:

✅ Frontend loads
✅ Login page appears
✅ Can type in inputs
✅ Can click submit
✅ No red errors in console
✅ API calls show in Network tab

---

## 🆘 If Something Goes Wrong

### Backend Won't Deploy
```powershell
# Check logs
vercel logs --prod

# Rebuild requirements
pip freeze > requirements.txt
vercel --prod --force
```

### Frontend Won't Deploy
```powershell
cd react-web
# Check for errors
npm run build

# Clean and rebuild
rm -r dist node_modules
npm install
npm run build
vercel --prod --force
```

### API Calls Failing
```powershell
# Check environment variables
vercel env list

# Check CORS settings in SCM/settings.py
# Check VITE_API_BASE_URL in react-web/.env.production

# Redeploy
vercel --prod --force
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Check status | `vercel list` |
| View logs | `vercel logs --prod` |
| Real-time logs | `vercel logs --prod --follow` |
| List variables | `vercel env list` |
| Rollback | `vercel rollback` |
| Force rebuild | `vercel --prod --force` |

---

## 📚 More Help

- **Quick Reference**: Read `VERCEL_QUICK_START.md`
- **Copy-Paste Commands**: Read `DEPLOY_COMMANDS.md`
- **Complete Guide**: Read `DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: Read `DEPLOYMENT_GUIDE.md` → "Troubleshooting" section

---

## ✅ Checklist

- [ ] Created `.env` file with values
- [ ] Logged into Vercel
- [ ] Created backend project on Vercel
- [ ] Created frontend project on Vercel
- [ ] Generated `requirements.txt`
- [ ] Set backend environment variables
- [ ] Deployed backend (preview)
- [ ] Tested backend API
- [ ] Deployed backend (production)
- [ ] Created `.env.production` in react-web
- [ ] Installed frontend dependencies
- [ ] Built frontend locally
- [ ] Set frontend environment variables
- [ ] Deployed frontend (preview)
- [ ] Deployed frontend (production)
- [ ] Updated CORS in Django
- [ ] Redeployed backend with CORS
- [ ] Tested login in frontend
- [ ] Verified API calls working

---

## 🎊 When All Steps Complete

Your application is now:

🌍 **LIVE ON THE INTERNET**

Access it at:
- Frontend: `https://prime-fresh-scm-web.vercel.app`
- Backend: `https://prime-fresh-scm-backend.vercel.app`

Share these URLs with others to access your app!

---

## 🚀 Next Steps

1. **Test thoroughly** - Try all features
2. **Monitor logs** - Check for errors
3. **Set custom domain** - Use your own domain (optional)
4. **Set up analytics** - Track usage
5. **Plan backups** - For your database

---

**Happy Deploying!** 🎉

Got stuck? Read the detailed guides or check Vercel docs: https://vercel.com/docs

---

Created: August 18, 2026
