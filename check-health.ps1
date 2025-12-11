# EcoInvest - Docker Health Check Script

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🏥 EcoInvest - Service Health Check" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to docker-compose directory
Push-Location -Path "backend\carbon-intelligence"

# Get service status
$services = docker-compose ps --format json | ConvertFrom-Json

# Service health mapping
$serviceChecks = @{
    "carbon_postgres" = @{ name = "PostgreSQL"; port = 5432 }
    "carbon_backend" = @{ name = "Flask Backend"; port = 5001 }
    "carbon_pathway" = @{ name = "gRPC Server"; port = 50051 }
    "kafka" = @{ name = "Kafka"; port = 29092 }
    "redis" = @{ name = "Redis"; port = 6379 }
    "debezium" = @{ name = "Debezium"; port = 8083 }
    "carbon_scrapers" = @{ name = "Data Scrapers"; port = $null }
}

Write-Host "📊 Service Status:" -ForegroundColor Yellow
Write-Host ""

$allHealthy = $true

foreach ($service in $services) {
    $name = $service.Name
    $state = $service.State
    
    if ($serviceChecks.ContainsKey($name)) {
        $info = $serviceChecks[$name]
        $displayName = $info.name
        $port = $info.port
        
        if ($state -eq "running") {
            Write-Host "✅ $displayName" -ForegroundColor Green -NoNewline
            if ($port) {
                Write-Host " (port $port)" -ForegroundColor Gray
            } else {
                Write-Host ""
            }
        } else {
            Write-Host "❌ $displayName" -ForegroundColor Red -NoNewline
            Write-Host " - $state" -ForegroundColor Yellow
            $allHealthy = $false
        }
    }
}

Write-Host ""

if ($allHealthy) {
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "✅ All services are running!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Test endpoints:" -ForegroundColor Cyan
    Write-Host "   Backend API: http://localhost:5001/api/companies" -ForegroundColor Gray
    Write-Host "   Health Check: http://localhost:5001/api/health" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📊 View logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
} else {
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "⚠️  Some services are not running" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run: docker-compose up -d" -ForegroundColor Yellow
    Write-Host "Or: docker-compose restart" -ForegroundColor Yellow
}

Pop-Location
