# 🚀 Vercel Deployment - Copy & Paste Commands

Just copy and paste the commands in order. Follow the interactive prompts.

---

## 📋 Phase 1: Initial Setup

### 1.1 Verify Vercel CLI is installed
```powershell
vercel --version
```
Expected output: `Vercel CLI 58.7.x` (or similar)

### 1.2 Login to Vercel
```powershell
vercel login
```
Follow the browser login prompt.

### 1.3 Verify Login
```powershell
vercel whoami
```
Shows your Vercel username.

---

## 🔧 Phase 2: Backend Setup

### 2.1 Navigate to project root
```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"
```

### 2.2 Generate/Update requirements.txt
```powershell
pip freeze > requirements.txt
```

### 2.3 Create/update .env file
```powershell
Copy .env.example to .env
# Edit .env with your actual values
```

Contents of `.env`:
```env
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-backend.vercel.app
DATABASE_URL=postgresql://user:password@host/dbname
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/dbname
VITE_API_BASE_URL=https://your-backend.vercel.app
```

### 2.4 Link backend to Vercel (first time only)
```powershell
vercel link --project prime-fresh-scm-backend
```
Or use Vercel Dashboard to create project first.

### 2.5 Set Environment Variables - Method A (CLI)
```powershell
vercel env add DJANGO_SECRET_KEY
# Paste: your-super-secret-key-here

vercel env add DJANGO_DEBUG
# Type: False

vercel env add DJANGO_ALLOWED_HOSTS
# Type: localhost,127.0.0.1,your-backend.vercel.app

vercel env add DATABASE_URL
# Paste: your-database-url

vercel env add MONGODB_URI
# Paste: your-mongodb-uri
```

### 2.5 Alternative - Set Variables via Dashboard
```
1. Go to https://vercel.com/dashboard
2. Click "prime-fresh-scm-backend" project
3. Go to Settings → Environment Variables
4. Add each variable from above
```

### 2.6 Test Backend Build Locally
```powershell
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```
Open http://localhost:8000/api/health/ in browser

### 2.7 Deploy Backend to Preview (Test First!)
```powershell
vercel
```
Follow prompts. This creates a preview URL for testing.

### 2.8 Deploy Backend to Production
```powershell
vercel --prod
```
⚠️ This is the live URL. Be sure to test preview first!

### 2.9 Get Backend URL
```powershell
vercel list
```
Look for your backend project. Note the production URL.
Example: `https://prime-fresh-scm.vercel.app`

---

## 🎨 Phase 3: Frontend Setup

### 3.1 Navigate to frontend directory
```powershell
cd "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM\react-web"
```

### 3.2 Install dependencies
```powershell
npm install
```

### 3.3 Create .env.production
```powershell
# Create file react-web\.env.production
```

Contents:
```env
VITE_API_BASE_URL=https://your-backend.vercel.app
VITE_APP_NAME=Prime Fresh SCM
```

Replace `your-backend.vercel.app` with actual backend URL from step 2.9

### 3.4 Build locally to test
```powershell
npm run build
```
If successful, you'll see "dist/" folder created.

### 3.5 Preview build locally
```powershell
npm run preview
```
Open http://localhost:4173 in browser

### 3.6 Navigate back to project root
```powershell
cd ..
```

### 3.7 Link frontend to Vercel (first time only)
```powershell
cd react-web
vercel link --project prime-fresh-scm-web
cd ..
```

### 3.8 Set Frontend Environment Variables
```powershell
cd react-web
vercel env add VITE_API_BASE_URL
# Paste: https://your-backend.vercel.app
cd ..
```

### 3.9 Deploy Frontend to Preview
```powershell
cd react-web
vercel
cd ..
```

### 3.10 Deploy Frontend to Production
```powershell
cd react-web
vercel --prod
cd ..
```

---

## ✅ Phase 4: Verification

### 4.1 Get all deployment URLs
```powershell
vercel list
```

### 4.2 Test Backend Health
```powershell
# Replace with your actual backend URL
curl https://your-backend.vercel.app/api/health/
```

### 4.3 Test Frontend
1. Open https://your-frontend.vercel.app in browser
2. Open DevTools (F12)
3. Go to Network tab
4. Try to log in
5. Check that API calls go to backend

### 4.4 Check Logs
```powershell
# Backend logs
vercel logs prime-fresh-scm --prod

# Frontend logs  
vercel logs prime-fresh-scm-web --prod

# Real-time
vercel logs --prod --follow
```

### 4.5 Verify Environment Variables
```powershell
vercel env list
```

---

## 🔄 Phase 5: Post-Deployment Configuration

### 5.1 Update Django CORS Settings
Edit `SCM/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'https://your-frontend.vercel.app',
    'https://www.your-custom-domain.com',  # if using custom domain
]
```

Then redeploy:
```powershell
vercel --prod --force
```

### 5.2 Connect Custom Domain (Optional)
```
Backend:
1. Vercel Dashboard → Backend Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as shown

Frontend:
1. Vercel Dashboard → Frontend Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as shown
```

### 5.3 Update Frontend API URL (if using custom domain)
```powershell
# Edit react-web/.env.production
VITE_API_BASE_URL=https://api.your-custom-domain.com
# or use custom domain from step 5.2

# Redeploy
cd react-web
vercel --prod
cd ..
```

---

## 🔐 Phase 6: Security & Monitoring

### 6.1 Enable HTTPS (Automatic on Vercel ✓)
Already done! Vercel handles SSL automatically.

### 6.2 Set Up Monitoring
```
1. Vercel Dashboard → Analytics
2. Enable Web Vitals
3. Enable Performance Monitoring
```

### 6.3 Check Security Headers
```powershell
curl -I https://your-backend.vercel.app
```
Look for:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

---

## 🚀 Quick Redeploy (After Code Changes)

### When you make changes to code:

```powershell
# 1. Commit to Git
git add .
git commit -m "Your message"
git push origin main

# 2a. If using GitHub integration: Automatic deployment
# (Vercel auto-deploys on push to main)

# 2b. Or manual redeploy
vercel --prod

# For frontend only:
cd react-web
vercel --prod
cd ..
```

---

## 💡 Useful Quick Commands

```powershell
# View deployment status
vercel list

# View latest logs
vercel logs --prod

# View real-time logs
vercel logs --prod --follow

# View environment variables
vercel env list

# Rollback to previous deployment
vercel rollback

# Force complete rebuild
vercel --prod --force

# Remove a deployment
vercel remove [url]
```

---

## 🔗 Your Deployment URLs

After successful deployment, access:

**Backend**
- URL: `https://your-backend.vercel.app`
- API: `https://your-backend.vercel.app/api/`
- Docs: `https://your-backend.vercel.app/api/docs/`
- Admin: `https://your-backend.vercel.app/admin/`

**Frontend**
- URL: `https://your-frontend.vercel.app`

---

## ❌ If Deployment Fails

### Backend Issues

**Error: "Module not found"**
```powershell
# Rebuild requirements
pip install -r requirements.txt
pip freeze > requirements.txt
vercel --prod --force
```

**Error: "Database connection failed"**
```powershell
# Check DATABASE_URL
vercel env list

# Update in dashboard and redeploy
vercel --prod --force
```

**Error: "Static files missing"**
```powershell
python manage.py collectstatic --noinput
vercel --prod --force
```

### Frontend Issues

**Error: "API calls 404"**
```powershell
# Update VITE_API_BASE_URL
cd react-web
# Edit .env.production with correct backend URL
vercel env add VITE_API_BASE_URL
vercel --prod --force
cd ..
```

**Error: "Build fails"**
```powershell
cd react-web
npm install --force
npm run build
vercel --prod --force
cd ..
```

---

## ✨ Success Indicators

When deployment is complete, you should see:

✅ Backend URL working
✅ Frontend URL loading
✅ API calls going through
✅ Login/Authentication working
✅ Data displaying correctly
✅ No console errors

---

## 📞 Support

If you encounter issues:

1. Check logs: `vercel logs --prod`
2. Check environment: `vercel env list`
3. Read full guide: `DEPLOYMENT_GUIDE.md`
4. Vercel Docs: https://vercel.com/docs

---

**Ready to Deploy? Start with Phase 1!** 🚀

Last Updated: August 18, 2026
