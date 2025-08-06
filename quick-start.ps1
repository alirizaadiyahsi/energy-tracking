# Energy Tracking IoT Platform - Quick Start Script
# ==================================================
# This script helps you get started with the Energy Tracking platform

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod", "help")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [switch]$Setup,
    
    [Parameter(Mandatory=$false)]
    [switch]$Clean,
    
    [Parameter(Mandatory=$false)]
    [switch]$Status
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Magenta = "`e[35m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-ColorText {
    param($Text, $Color)
    Write-Host "${Color}${Text}${Reset}"
}

function Show-Help {
    Write-ColorText "Energy Tracking IoT Platform - Quick Start" $Blue
    Write-Host "============================================="
    Write-Host ""
    Write-ColorText "Usage:" $Yellow
    Write-Host "  .\quick-start.ps1 [options]"
    Write-Host ""
    Write-ColorText "Options:" $Yellow
    Write-Host "  -Environment <dev|prod>   Environment to start (default: dev)"
    Write-Host "  -Setup                    Run initial setup"
    Write-Host "  -Clean                    Clean up containers and volumes"
    Write-Host "  -Status                   Show current status"
    Write-Host ""
    Write-ColorText "Examples:" $Yellow
    Write-Host "  .\quick-start.ps1 -Setup              # Initial setup"
    Write-Host "  .\quick-start.ps1 -Environment dev    # Start development"
    Write-Host "  .\quick-start.ps1 -Environment prod   # Start production"
    Write-Host "  .\quick-start.ps1 -Status             # Check status"
    Write-Host "  .\quick-start.ps1 -Clean              # Clean everything"
    Write-Host ""
}

function Test-Prerequisites {
    Write-ColorText "Checking prerequisites..." $Blue
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-ColorText "✓ Docker: $dockerVersion" $Green
    } catch {
        Write-ColorText "✗ Docker not found. Please install Docker Desktop." $Red
        return $false
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker compose version
        Write-ColorText "✓ Docker Compose: $composeVersion" $Green
    } catch {
        Write-ColorText "✗ Docker Compose not found. Please update Docker Desktop." $Red
        return $false
    }
    
    return $true
}

function Initialize-Setup {
    Write-ColorText "Setting up Energy Tracking IoT Platform..." $Blue
    
    # Create .env file if not exists
    if (-not (Test-Path ".env")) {
        Write-ColorText "Creating .env file from template..." $Yellow
        Copy-Item ".env.example" ".env"
        Write-ColorText "✓ .env file created" $Green
        Write-ColorText "⚠ Please edit .env file with your configuration!" $Yellow
    } else {
        Write-ColorText "✓ .env file already exists" $Green
    }
    
    # Create directories
    Write-ColorText "Creating project directories..." $Yellow
    $directories = @(
        "data\postgres", "data\influxdb", "data\redis", "data\grafana", "data\mosquitto",
        "logs\api-gateway", "logs\data-ingestion", "logs\data-processing", "logs\analytics", "logs\notification",
        "infrastructure\grafana\dashboards", "infrastructure\nginx\conf.d"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-ColorText "✓ Directories created" $Green
    
    Write-ColorText "Setup completed successfully!" $Green
    Write-ColorText "Next steps:" $Yellow
    Write-Host "  1. Edit .env file with your configuration"
    Write-Host "  2. Run: .\quick-start.ps1 -Environment dev"
}

function Start-Environment {
    param($Env)
    
    Write-ColorText "Starting $Env environment..." $Blue
    
    if ($Env -eq "dev") {
        $composeFile = "docker-compose.dev.yml"
    } else {
        $composeFile = "docker-compose.prod.yml"
    }
    
    # Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-ColorText "✗ .env file not found. Run setup first!" $Red
        Write-ColorText "Usage: .\quick-start.ps1 -Setup" $Yellow
        return
    }
    
    # Pull latest images
    Write-ColorText "Pulling latest images..." $Yellow
    docker compose -f $composeFile pull
    
    # Build and start services
    Write-ColorText "Building and starting services..." $Yellow
    docker compose -f $composeFile up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorText "✓ $Env environment started successfully!" $Green
        
        if ($Env -eq "dev") {
            Write-ColorText "Development services available at:" $Yellow
            Write-Host "  🌐 Dashboard:        http://localhost:3000"
            Write-Host "  🚀 API Gateway:      http://localhost:8000"
            Write-Host "  📚 API Docs:         http://localhost:8000/docs"
            Write-Host "  📊 Grafana:          http://localhost:3001 (admin/admin123)"
            Write-Host "  💾 InfluxDB:         http://localhost:8086"
            Write-Host "  🗄️ PgAdmin:          http://localhost:5050"
            Write-Host "  🔴 Redis Commander:  http://localhost:8081"
            Write-Host ""
            Write-ColorText "To view logs: docker compose -f $composeFile logs -f" $Cyan
            Write-ColorText "To stop: docker compose -f $composeFile down" $Cyan
        }
    } else {
        Write-ColorText "✗ Failed to start $Env environment" $Red
    }
}

function Show-Status {
    Write-ColorText "Current Status:" $Blue
    
    Write-ColorText "Development Environment:" $Yellow
    try {
        docker compose -f docker-compose.dev.yml ps
    } catch {
        Write-Host "  Development environment not running"
    }
    
    Write-Host ""
    Write-ColorText "Production Environment:" $Yellow
    try {
        docker compose -f docker-compose.prod.yml ps
    } catch {
        Write-Host "  Production environment not running"
    }
}

function Clean-Environment {
    Write-ColorText "Cleaning up containers, networks, and volumes..." $Yellow
    
    # Stop all compose services
    docker compose -f docker-compose.dev.yml down -v --remove-orphans 2>$null
    docker compose -f docker-compose.prod.yml down -v --remove-orphans 2>$null
    docker compose down -v --remove-orphans 2>$null
    
    # Clean up Docker system
    docker system prune -f
    
    Write-ColorText "✓ Cleanup completed!" $Green
}

# Main execution
Write-Host ""
Write-ColorText "🔋 Energy Tracking IoT Platform" $Magenta
Write-Host "================================="
Write-Host ""

if ($args -contains "help" -or $Environment -eq "help") {
    Show-Help
    exit 0
}

if (-not (Test-Prerequisites)) {
    Write-ColorText "Prerequisites check failed. Please install required software." $Red
    exit 1
}

if ($Setup) {
    Initialize-Setup
} elseif ($Status) {
    Show-Status
} elseif ($Clean) {
    Write-ColorText "⚠ This will remove all containers, volumes, and data!" $Red
    $confirm = Read-Host "Are you sure? (y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Clean-Environment
    } else {
        Write-Host "Operation cancelled."
    }
} else {
    Start-Environment $Environment
}

Write-Host ""
