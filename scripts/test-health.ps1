# PowerShell script to test health endpoints
# Usage: .\test-health.ps1

param(
    [switch]$Detailed,
    [switch]$Watch,
    [int]$Interval = 30
)

# Service endpoints
$services = @{
    "Auth Service" = "http://localhost:8005"
    "API Gateway" = "http://localhost:8000"
    "Data Ingestion" = "http://localhost:8001"
    "Data Processing" = "http://localhost:8002"
    "Analytics" = "http://localhost:8003"
    "Notification" = "http://localhost:8004"
}

function Test-ServiceHealth {
    param($ServiceName, $BaseUrl, $Detailed)
    
    $healthUrl = "$BaseUrl/health"
    
    try {
        $response = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
        
        if ($Detailed) {
            Write-Host "✅ $ServiceName - HEALTHY" -ForegroundColor Green
            Write-Host "   Status: $($response.status)" -ForegroundColor White
            Write-Host "   Uptime: $($response.uptime_seconds)s" -ForegroundColor White
            
            if ($response.checks) {
                foreach ($check in $response.checks.PSObject.Properties) {
                    $checkName = $check.Name
                    $checkStatus = $check.Value.status
                    $color = if ($checkStatus -eq "healthy") { "Green" } else { "Red" }
                    Write-Host "   - $checkName`: $checkStatus" -ForegroundColor $color
                }
            }
            Write-Host ""
        } else {
            $statusColor = if ($response.status -eq "healthy") { "Green" } else { "Red" }
            Write-Host "✅ $ServiceName - $($response.status.ToUpper())" -ForegroundColor $statusColor
        }
        
        return $true
    }
    catch {
        Write-Host "❌ $ServiceName - UNREACHABLE" -ForegroundColor Red
        if ($Detailed) {
            Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host ""
        }
        return $false
    }
}

function Test-AllServices {
    param($Detailed)
    
    Write-Host "🔍 Health Check Report - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Blue
    Write-Host "=" * 60 -ForegroundColor Blue
    
    $totalServices = $services.Count
    $healthyServices = 0
    
    foreach ($service in $services.GetEnumerator()) {
        $isHealthy = Test-ServiceHealth -ServiceName $service.Key -BaseUrl $service.Value -Detailed $Detailed
        if ($isHealthy) {
            $healthyServices++
        }
    }
    
    Write-Host "=" * 60 -ForegroundColor Blue
    Write-Host "📊 Summary: $healthyServices/$totalServices services healthy" -ForegroundColor $(if ($healthyServices -eq $totalServices) { "Green" } else { "Yellow" })
    
    if ($healthyServices -lt $totalServices) {
        Write-Host "⚠️  Some services are unhealthy or unreachable!" -ForegroundColor Yellow
    } else {
        Write-Host "🎉 All services are healthy!" -ForegroundColor Green
    }
    
    return $healthyServices -eq $totalServices
}

# Main execution
if ($Watch) {
    Write-Host "👀 Starting health monitoring (checking every $Interval seconds)..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    while ($true) {
        Clear-Host
        Test-AllServices -Detailed $Detailed
        Start-Sleep -Seconds $Interval
    }
} else {
    $allHealthy = Test-AllServices -Detailed $Detailed
    
    if (-not $allHealthy) {
        exit 1
    }
}
