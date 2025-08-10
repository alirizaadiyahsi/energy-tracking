#!/usr/bin/env pwsh
# Energy Tracking System - Health Check Script
# Verifies that all system components are running and accessible

Write-Host "🚀 Energy Tracking System - Health Check" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Function to check URL accessibility
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$ExpectedStatus = 200
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✅ $Name" -ForegroundColor Green -NoNewline
            Write-Host " - $Url" -ForegroundColor Gray
        } else {
            Write-Host "⚠️  $Name" -ForegroundColor Yellow -NoNewline
            Write-Host " - $Url (Status: $($response.StatusCode))" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ $Name" -ForegroundColor Red -NoNewline
        Write-Host " - $Url (Error: $($_.Exception.Message))" -ForegroundColor Gray
    }
}

# Check Docker containers
Write-Host "🐳 Docker Containers Status:" -ForegroundColor Cyan
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-Object -Skip 1
    foreach ($container in $containers) {
        if ($container -match "energy-") {
            $status = if ($container -match "Up.*healthy") { "✅" } else { "⚠️" }
            Write-Host "$status $container" -ForegroundColor $(if ($status -eq "✅") { "Green" } else { "Yellow" })
        }
    }
} catch {
    Write-Host "❌ Could not check Docker containers. Is Docker running?" -ForegroundColor Red
}

Write-Host ""
Write-Host "🌐 Service Endpoints:" -ForegroundColor Cyan

# Check all service endpoints
Test-Endpoint "http://localhost:3000/" "Frontend Dashboard"
Test-Endpoint "http://localhost:8000/health" "API Gateway"
Test-Endpoint "http://localhost:8000/docs" "API Documentation"
Test-Endpoint "http://localhost:8005/health" "Authentication Service"
Test-Endpoint "http://localhost:8090/health" "IoT Mock Service"
Test-Endpoint "http://localhost:3001/login" "Grafana"
Test-Endpoint "http://localhost:8086/ping" "InfluxDB" 204
Test-Endpoint "http://localhost:8080/" "Nginx Proxy"

Write-Host ""
Write-Host "💾 Database Connections:" -ForegroundColor Cyan

# Check database connections
try {
    $redisCheck = docker exec energy-redis redis-cli ping 2>$null
    if ($redisCheck -eq "PONG") {
        Write-Host "✅ Redis - localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis - localhost:6379" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Redis - Could not connect" -ForegroundColor Red
}

try {
    $postgresCheck = docker exec energy-postgres pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL - localhost:5432" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL - localhost:5432" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ PostgreSQL - Could not connect" -ForegroundColor Red
}

Write-Host ""
Write-Host "📈 Quick System Info:" -ForegroundColor Cyan

# Count healthy containers
try {
    $healthyCount = (docker ps --filter "health=healthy" | Measure-Object -Line).Lines - 1
    Write-Host "🏥 Healthy Containers: $healthyCount" -ForegroundColor Green
} catch {
    Write-Host "🏥 Could not check container health" -ForegroundColor Yellow
}

# Check total containers
try {
    $totalCount = (docker ps --filter "name=energy-" | Measure-Object -Line).Lines - 1
    Write-Host "📦 Total Energy Containers: $totalCount" -ForegroundColor Cyan
} catch {
    Write-Host "📦 Could not count containers" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Magenta
Write-Host "  • Open Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  • View API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Access Grafana: http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host "  • Monitor Logs: docker-compose logs -f [service-name]" -ForegroundColor White
Write-Host ""
Write-Host "💡 For detailed documentation, see README.md and docs/ folder" -ForegroundColor Gray
