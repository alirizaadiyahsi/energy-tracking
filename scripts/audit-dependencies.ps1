#!/usr/bin/env pwsh
# Dependency Audit Script
# This script checks for missing or unused dependencies across all services

Write-Host "🔍 Auditing dependencies across all services..." -ForegroundColor Yellow

$services = @(
    "auth-service",
    "api-gateway", 
    "data-ingestion",
    "data-processing",
    "analytics",
    "notification",
    "iot-mock"
)

$commonDependencies = @{
    "fastapi" = "Web framework"
    "uvicorn" = "ASGI server"
    "pydantic" = "Data validation"
    "pydantic-settings" = "Settings management"
    "httpx" = "HTTP client"
    "python-dotenv" = "Environment variables"
}

$serviceDependencies = @{
    "data-ingestion" = @("paho-mqtt", "influxdb-client", "redis", "asyncpg")
    "iot-mock" = @("paho-mqtt")
    "auth-service" = @("PyJWT", "bcrypt", "python-jose")
    "analytics" = @("pandas", "numpy")
    "notification" = @("celery", "redis")
}

foreach ($service in $services) {
    $requirementsPath = "services/$service/requirements.txt"
    
    if (Test-Path $requirementsPath) {
        Write-Host "`n📦 $service dependencies:" -ForegroundColor Cyan
        
        $requirements = Get-Content $requirementsPath
        $packages = $requirements | Where-Object { $_ -notmatch "^#" -and $_ -ne "" } | ForEach-Object { ($_ -split "==|>=|<=|>|<")[0] }
        
        # Check for expected dependencies
        if ($serviceDependencies.ContainsKey($service)) {
            foreach ($expectedDep in $serviceDependencies[$service]) {
                if ($packages -contains $expectedDep) {
                    Write-Host "  ✅ $expectedDep" -ForegroundColor Green
                } else {
                    Write-Host "  ❌ Missing: $expectedDep" -ForegroundColor Red
                }
            }
        }
        
        # List all packages
        Write-Host "  📋 All packages:"
        foreach ($package in $packages) {
            Write-Host "    - $package" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠️ No requirements.txt found" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Dependency audit complete!" -ForegroundColor Green
