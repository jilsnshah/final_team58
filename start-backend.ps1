# EcoInvest - Complete Docker Startup Script (Windows)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "🌱 EcoInvest - Starting All Services" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "❌ Error: backend\.env file not found!" -ForegroundColor Red
    Write-Host "📝 Please create it from backend\.env.example" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run: Copy-Item backend\.env.example backend\.env" -ForegroundColor Cyan
    Write-Host "Then add your API keys (especially GOOGLE_API_KEY)" -ForegroundColor Yellow
    exit 1
}

# Navigate to docker-compose directory
Set-Location -Path "backend\carbon-intelligence"

Write-Host ""
Write-Host "🐳 Starting Docker services..." -ForegroundColor Cyan
Write-Host ""

# Start all services
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
docker-compose ps

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Backend Services Started!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Backend API:  http://localhost:5001" -ForegroundColor Cyan
Write-Host "🗄️  PostgreSQL:   localhost:5432" -ForegroundColor Cyan
Write-Host "🔧 gRPC Server:  localhost:50051" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f scrapers" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Next: Start the frontend with 'npm run dev'" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Return to root directory
Set-Location -Path "..\..\"
