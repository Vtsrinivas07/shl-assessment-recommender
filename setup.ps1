# Setup script for SHL Assessment Recommender
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SHL Assessment Recommender - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python version
Write-Host "Step 1: Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Green

# Step 2: Upgrade pip
Write-Host ""
Write-Host "Step 2: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Step 3: Install dependencies
Write-Host ""
Write-Host "Step 3: Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

# Step 4: Setup environment file
Write-Host ""
Write-Host "Step 4: Setting up environment file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  .env file already exists" -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env file from template" -ForegroundColor Green
    Write-Host "  IMPORTANT: Edit .env and add your GROQ_API_KEY" -ForegroundColor Red
}

# Step 5: Build index from sample data
Write-Host ""
Write-Host "Step 5: Building search index from sample data..." -ForegroundColor Yellow
python -m app.index_builder

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env and add your GROQ_API_KEY" -ForegroundColor White
Write-Host "  2. Run: python run.py" -ForegroundColor White
Write-Host "  3. Test: Invoke-WebRequest http://localhost:8000/health" -ForegroundColor White
Write-Host ""
