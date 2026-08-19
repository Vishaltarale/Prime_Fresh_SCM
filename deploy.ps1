# Vercel Deployment Script for Prime Fresh SCM
# This script helps deploy both backend and frontend to Vercel

param(
    [string]$Target = "both",  # "backend", "frontend", or "both"
    [string]$Env = "preview",  # "preview" or "prod"
    [switch]$Force = $false,   # Force rebuild
    [switch]$BuildOnly = $false  # Build only, don't deploy
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommandPath

Write-Host "=====================================" -ForegroundColor Green
Write-Host "Prime Fresh SCM - Vercel Deployment" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Check Vercel CLI
Write-Host "✓ Checking Vercel CLI..." -ForegroundColor Cyan
$vercelVersion = vercel --version
Write-Host "  Vercel CLI: $vercelVersion" -ForegroundColor Gray

# Check if logged in
Write-Host ""
Write-Host "✓ Checking Vercel login..." -ForegroundColor Cyan
$vercelUser = vercel whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Not logged in. Logging in..." -ForegroundColor Yellow
    vercel login
} else {
    Write-Host "  Logged in as: $vercelUser" -ForegroundColor Gray
}

# Backend Deployment
if ($Target -eq "backend" -or $Target -eq "both") {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Blue
    Write-Host "Deploying BACKEND" -ForegroundColor Blue
    Write-Host "=====================================" -ForegroundColor Blue
    
    Set-Location $ProjectRoot
    
    # Check requirements.txt
    if (-not (Test-Path "$ProjectRoot\requirements.txt")) {
        Write-Host "⚠ requirements.txt not found. Creating..." -ForegroundColor Yellow
        pip freeze | Out-File requirements.txt
    }
    
    # Verify vercel.json exists
    if (-not (Test-Path "$ProjectRoot\vercel.json")) {
        Write-Host "✗ vercel.json not found in root directory!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Building backend..." -ForegroundColor Cyan
    
    if ($BuildOnly) {
        Write-Host "Build only mode - skipping deployment" -ForegroundColor Yellow
        $cmd = "vercel build"
    } else {
        if ($Env -eq "prod") {
            Write-Host "Deploying to PRODUCTION" -ForegroundColor Red
            if ($Force) {
                $cmd = "vercel --prod --force"
            } else {
                $cmd = "vercel --prod"
            }
        } else {
            Write-Host "Deploying to PREVIEW environment" -ForegroundColor Yellow
            if ($Force) {
                $cmd = "vercel --force"
            } else {
                $cmd = "vercel"
            }
        }
    }
    
    Write-Host "  Running: $cmd" -ForegroundColor Gray
    Invoke-Expression $cmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Backend deployment successful!" -ForegroundColor Green
    } else {
        Write-Host "✗ Backend deployment failed!" -ForegroundColor Red
        if ($Target -eq "backend") { exit 1 }
    }
}

# Frontend Deployment
if ($Target -eq "frontend" -or $Target -eq "both") {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Blue
    Write-Host "Deploying FRONTEND" -ForegroundColor Blue
    Write-Host "=====================================" -ForegroundColor Blue
    
    Set-Location "$ProjectRoot\react-web"
    
    # Verify package.json exists
    if (-not (Test-Path "$ProjectRoot\react-web\package.json")) {
        Write-Host "✗ package.json not found in react-web!" -ForegroundColor Red
        exit 1
    }
    
    # Install dependencies
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    npm install
    
    # Build
    Write-Host ""
    Write-Host "Building frontend..." -ForegroundColor Cyan
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Frontend build failed!" -ForegroundColor Red
        exit 1
    }
    
    if (-not $BuildOnly) {
        # Deploy
        Write-Host ""
        Write-Host "Deploying frontend..." -ForegroundColor Cyan
        
        if ($Env -eq "prod") {
            Write-Host "Deploying to PRODUCTION" -ForegroundColor Red
            if ($Force) {
                $cmd = "vercel --prod --force"
            } else {
                $cmd = "vercel --prod"
            }
        } else {
            Write-Host "Deploying to PREVIEW environment" -ForegroundColor Yellow
            if ($Force) {
                $cmd = "vercel --force"
            } else {
                $cmd = "vercel"
            }
        }
        
        Write-Host "  Running: $cmd" -ForegroundColor Gray
        Invoke-Expression $cmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Frontend deployment successful!" -ForegroundColor Green
        } else {
            Write-Host "✗ Frontend deployment failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ Frontend build successful!" -ForegroundColor Green
        Write-Host "  Output: dist/" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✓ All deployments completed!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  Backend: https://your-backend-domain.vercel.app" -ForegroundColor Gray
Write-Host "  Frontend: https://your-frontend-domain.vercel.app" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Update environment variables in Vercel Dashboard" -ForegroundColor Gray
Write-Host "  2. Test your application" -ForegroundColor Gray
Write-Host "  3. Monitor logs: vercel logs --prod" -ForegroundColor Gray
Write-Host ""
