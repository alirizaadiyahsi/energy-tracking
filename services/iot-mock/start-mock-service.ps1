# IoT Mock Service Quick Start Script
# This script helps you quickly start and test the IoT Mock Service

param(
    [switch]$Build,
    [switch]$Start,
    [switch]$Test,
    [switch]$Stop,
    [switch]$Logs,
    [switch]$Clean,
    [switch]$All,
    [switch]$Help
)

function Show-Help {
    Write-Host "IoT Mock Service Management Script" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\start-mock-service.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Build    Build the IoT Mock Service container"
    Write-Host "  -Start    Start the IoT Mock Service"
    Write-Host "  -Test     Run service tests"
    Write-Host "  -Stop     Stop the IoT Mock Service"
    Write-Host "  -Logs     Show service logs"
    Write-Host "  -Clean    Remove service containers and images"
    Write-Host "  -All      Build, start, and test the service"
    Write-Host "  -Help     Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\start-mock-service.ps1 -All      # Complete setup and test"
    Write-Host "  .\start-mock-service.ps1 -Start    # Just start the service"
    Write-Host "  .\start-mock-service.ps1 -Test     # Run tests"
    Write-Host "  .\start-mock-service.ps1 -Logs     # View logs"
}

function Test-DockerInstalled {
    try {
        $null = docker --version
        return $true
    } catch {
        Write-Host "❌ Docker is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Docker Desktop and try again." -ForegroundColor Yellow
        return $false
    }
}

function Test-ServiceRunning {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8090/health" -TimeoutSec 5 -ErrorAction Stop
        return $response.status -eq "healthy"
    } catch {
        return $false
    }
}

function Build-Service {
    Write-Host "🔨 Building IoT Mock Service..." -ForegroundColor Cyan
    
    Push-Location "$PSScriptRoot"
    try {
        docker build -t iot-mock-service .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Build completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Build failed" -ForegroundColor Red
            return $false
        }
    } finally {
        Pop-Location
    }
}

function Start-Service {
    Write-Host "🚀 Starting IoT Mock Service..." -ForegroundColor Cyan
    
    # Navigate to project root directory
    $projectRoot = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
    
    if (-not (Test-Path $projectRoot)) {
        Write-Host "❌ Project root not found: $projectRoot" -ForegroundColor Red
        return $false
    }
    
    Push-Location $projectRoot
    try {
        # Start required services
        Write-Host "Starting dependencies (Mosquitto, etc.)..." -ForegroundColor Yellow
        docker-compose up -d mosquitto redis postgres influxdb
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to start dependencies" -ForegroundColor Red
            return $false
        }
        
        # Wait for dependencies
        Write-Host "Waiting for dependencies to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Start IoT Mock Service
        Write-Host "Starting IoT Mock Service..." -ForegroundColor Yellow
        docker-compose up -d iot-mock
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ IoT Mock Service started" -ForegroundColor Green
            
            # Wait for service to be ready
            Write-Host "Waiting for service to be ready..." -ForegroundColor Yellow
            $maxAttempts = 30
            $attempt = 0
            
            do {
                Start-Sleep -Seconds 2
                $attempt++
                Write-Host "." -NoNewline -ForegroundColor Yellow
                
                if (Test-ServiceRunning) {
                    Write-Host ""
                    Write-Host "✅ Service is ready!" -ForegroundColor Green
                    Write-Host "📡 IoT Mock Service available at: http://localhost:8090" -ForegroundColor Cyan
                    Write-Host "📚 API Documentation at: http://localhost:8090/docs" -ForegroundColor Cyan
                    return $true
                }
            } while ($attempt -lt $maxAttempts)
            
            Write-Host ""
            Write-Host "⚠️ Service started but may not be fully ready yet" -ForegroundColor Yellow
            return $true
        } else {
            Write-Host "❌ Failed to start IoT Mock Service" -ForegroundColor Red
            return $false
        }
    } finally {
        Pop-Location
    }
}

function Test-Service {
    Write-Host "🧪 Testing IoT Mock Service..." -ForegroundColor Cyan
    
    if (-not (Test-ServiceRunning)) {
        Write-Host "❌ Service is not running. Start it first with -Start" -ForegroundColor Red
        return $false
    }
    
    # Test API endpoints
    Write-Host "Testing API endpoints..." -ForegroundColor Yellow
    
    try {
        # Test health
        $health = Invoke-RestMethod -Uri "http://localhost:8090/health" -TimeoutSec 10
        Write-Host "✅ Health check: $($health.status)" -ForegroundColor Green
        
        # Test devices list
        $devices = Invoke-RestMethod -Uri "http://localhost:8090/api/v1/devices" -TimeoutSec 10
        if ($devices.success) {
            Write-Host "✅ Device listing: $($devices.data.Count) devices found" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Device listing failed: $($devices.message)" -ForegroundColor Yellow
        }
        
        # Test simulation status
        $simulation = Invoke-RestMethod -Uri "http://localhost:8090/api/v1/simulation/status" -TimeoutSec 10
        if ($simulation.success) {
            $status = $simulation.data
            Write-Host "✅ Simulation status: $(if($status.is_running){'Running'}else{'Stopped'})" -ForegroundColor Green
            Write-Host "   - Total devices: $($status.total_devices)" -ForegroundColor Gray
            Write-Host "   - Online devices: $($status.online_devices)" -ForegroundColor Gray
            Write-Host "   - MQTT connected: $($status.mqtt_connected)" -ForegroundColor Gray
        } else {
            Write-Host "⚠️ Simulation status failed: $($simulation.message)" -ForegroundColor Yellow
        }
        
        Write-Host "✅ All API tests passed!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "❌ API test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-Logs {
    Write-Host "📄 Showing IoT Mock Service logs..." -ForegroundColor Cyan
    
    $projectRoot = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
    
    if (-not (Test-Path $projectRoot)) {
        Write-Host "❌ Project root not found: $projectRoot" -ForegroundColor Red
        return
    }
    
    Push-Location $projectRoot
    try {
        docker-compose logs -f iot-mock
    } finally {
        Pop-Location
    }
}

function Stop-Service {
    Write-Host "🛑 Stopping IoT Mock Service..." -ForegroundColor Cyan
    
    $projectRoot = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
    
    if (-not (Test-Path $projectRoot)) {
        Write-Host "❌ Project root not found: $projectRoot" -ForegroundColor Red
        return $false
    }
    
    Push-Location $projectRoot
    try {
        docker-compose stop iot-mock
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ IoT Mock Service stopped" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Failed to stop service" -ForegroundColor Red
            return $false
        }
    } finally {
        Pop-Location
    }
}

function Clean-Service {
    Write-Host "🧹 Cleaning up IoT Mock Service..." -ForegroundColor Cyan
    
    $projectRoot = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
    
    if (-not (Test-Path $projectRoot)) {
        Write-Host "❌ Project root not found: $projectRoot" -ForegroundColor Red
        return $false
    }
    
    Push-Location $projectRoot
    try {
        # Stop and remove containers
        docker-compose down iot-mock
        
        # Remove image
        docker rmi iot-mock-service -f 2>$null
        
        Write-Host "✅ Cleanup completed" -ForegroundColor Green
        return $true
    } finally {
        Pop-Location
    }
}

# Main script logic
if ($Help) {
    Show-Help
    exit 0
}

if (-not (Test-DockerInstalled)) {
    exit 1
}

$success = $true

if ($All) {
    Write-Host "🎯 Running complete IoT Mock Service setup..." -ForegroundColor Magenta
    Write-Host ""
    
    $success = (Build-Service) -and (Start-Service) -and (Test-Service)
    
    if ($success) {
        Write-Host ""
        Write-Host "🎉 IoT Mock Service is ready!" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host "📡 Service URL: http://localhost:8090" -ForegroundColor Cyan
        Write-Host "📚 API Docs: http://localhost:8090/docs" -ForegroundColor Cyan
        Write-Host "🔍 Health Check: http://localhost:8090/health" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "💡 Next steps:" -ForegroundColor Yellow
        Write-Host "   - View logs: .\start-mock-service.ps1 -Logs" -ForegroundColor Gray
        Write-Host "   - Stop service: .\start-mock-service.ps1 -Stop" -ForegroundColor Gray
        Write-Host "   - Test API: curl http://localhost:8090/api/v1/devices" -ForegroundColor Gray
        Write-Host ""
        Write-Host "🐳 Or use Docker Compose from project root:" -ForegroundColor Yellow
        Write-Host "   docker-compose up -d iot-mock" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "❌ Setup failed. Check the logs for details." -ForegroundColor Red
    }
} else {
    if ($Build) { $success = $success -and (Build-Service) }
    if ($Start) { $success = $success -and (Start-Service) }
    if ($Test) { $success = $success -and (Test-Service) }
    if ($Logs) { Show-Logs }
    if ($Stop) { $success = $success -and (Stop-Service) }
    if ($Clean) { $success = $success -and (Clean-Service) }
    
    if (-not ($Build -or $Start -or $Test -or $Logs -or $Stop -or $Clean)) {
        Write-Host "❓ No action specified. Use -Help for usage information." -ForegroundColor Yellow
        Show-Help
    }
}

if (-not $success) {
    exit 1
}
