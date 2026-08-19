# EMERGENCY FIX - Deploy NOW!
# This script will force deploy both backend and frontend

Write-Host "🚀 EMERGENCY DEPLOYMENT FIX" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""

$ProjectRoot = "c:\Users\Capricon\Documents\SCM\Prime_Fresh_SCM"

# Step 1: Backend Deployment
Write-Host "STEP 1: Deploying Backend..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Set-Location $ProjectRoot

Write-Host ""
Write-Host "Running: vercel --prod --force" -ForegroundColor Yellow
Write-Host ""

vercel --prod --force

Write-Host ""
Write-Host "✅ Backend deployment initiated!" -ForegroundColor Green
Write-Host "Wait for it to complete..." -ForegroundColor Green
Write-Host ""
Read-Host "Press ENTER when backend deployment is complete"

# Step 2: Frontend Deployment  
Write-Host ""
Write-Host "STEP 2: Deploying Frontend..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Set-Location "$ProjectRoot\react-web"

Write-Host ""
Write-Host "Building frontend..." -ForegroundColor Yellow
npm run build

Write-Host ""
Write-Host "Running: vercel --prod --force" -ForegroundColor Yellow
Write-Host ""

vercel --prod --force

Write-Host ""
Write-Host "✅ Frontend deployment initiated!" -ForegroundColor Green
Write-Host ""
Read-Host "Press ENTER when frontend deployment is complete"

# Step 3: Verification
Write-Host ""
Write-Host "STEP 3: Verifying Deployments..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Set-Location $ProjectRoot

Write-Host ""
Write-Host "Checking deployments..." -ForegroundColor Yellow
vercel list

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "URLS:" -ForegroundColor Cyan
Write-Host "  Backend:  https://prime-fresh-scm-backend.vercel.app" -ForegroundColor Gray
Write-Host "  Frontend: https://prime-fresh-scm-web.vercel.app" -ForegroundColor Gray
Write-Host ""
Write-Host "Go check them in your browser!" -ForegroundColor Green
