#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Setup and manage monitoring infrastructure for Energy Tracking platform

.DESCRIPTION
    This script manages the monitoring stack including Prometheus, Grafana, AlertManager,
    Jaeger for tracing, and Loki for log aggregation.

.PARAMETER Action
    The action to perform: setup, start, stop, restart, status, logs, cleanup

.PARAMETER Service
    Specific service to target (optional)

.EXAMPLE
    .\setup-monitoring.ps1 -Action setup
    Sets up the monitoring infrastructure

.EXAMPLE
    .\setup-monitoring.ps1 -Action start
    Starts all monitoring services

.EXAMPLE
    .\setup-monitoring.ps1 -Action logs -Service grafana
    Shows logs for Grafana service
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("setup", "start", "stop", "restart", "status", "logs", "cleanup")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$Service = ""
)

# Configuration
$ComposeFile = "docker\docker-compose.monitoring.yml"
$NetworkName = "monitoring"

function Write-StatusMessage {
    param([string]$Message, [string]$Type = "Info")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    switch($Type) {
        "Success" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "Warning" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "Error"   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        default   { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Blue }
    }
}

function Test-Prerequisites {
    Write-StatusMessage "Checking prerequisites..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-StatusMessage "Docker found: $dockerVersion" "Success"
    }
    catch {
        Write-StatusMessage "Docker is not installed or not in PATH" "Error"
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker compose version
        Write-StatusMessage "Docker Compose found: $composeVersion" "Success"
    }
    catch {
        Write-StatusMessage "Docker Compose is not available" "Error"
        exit 1
    }
    
    # Check compose file exists
    if (-not (Test-Path $ComposeFile)) {
        Write-StatusMessage "Monitoring compose file not found: $ComposeFile" "Error"
        exit 1
    }
}

function Setup-Monitoring {
    Write-StatusMessage "Setting up monitoring infrastructure..."
    
    Test-Prerequisites
    
    # Create monitoring network
    Write-StatusMessage "Creating monitoring network..."
    $networkExists = docker network ls --filter name=$NetworkName --format "{{.Name}}" | Select-String $NetworkName
    if (-not $networkExists) {
        docker network create $NetworkName
        Write-StatusMessage "Created monitoring network" "Success"
    } else {
        Write-StatusMessage "Monitoring network already exists" "Warning"
    }
    
    # Create required directories
    Write-StatusMessage "Creating required directories..."
    $directories = @(
        "infrastructure\monitoring",
        "infrastructure\grafana\dashboards",
        "infrastructure\grafana\provisioning\datasources",
        "infrastructure\grafana\provisioning\dashboards"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-StatusMessage "Created directory: $dir" "Success"
        }
    }
    
    Write-StatusMessage "Monitoring infrastructure setup complete!" "Success"
}

function Start-Monitoring {
    Write-StatusMessage "Starting monitoring services..."
    
    try {
        docker compose -f $ComposeFile up -d
        Write-StatusMessage "Monitoring services started successfully!" "Success"
        
        Start-Sleep 5
        Show-ServiceStatus
        Show-AccessUrls
    }
    catch {
        Write-StatusMessage "Failed to start monitoring services: $($_.Exception.Message)" "Error"
        exit 1
    }
}

function Stop-Monitoring {
    Write-StatusMessage "Stopping monitoring services..."
    
    if ($Service) {
        docker compose -f $ComposeFile stop $Service
        Write-StatusMessage "Stopped service: $Service" "Success"
    } else {
        docker compose -f $ComposeFile down
        Write-StatusMessage "All monitoring services stopped" "Success"
    }
}

function Restart-Monitoring {
    Write-StatusMessage "Restarting monitoring services..."
    
    if ($Service) {
        docker compose -f $ComposeFile restart $Service
        Write-StatusMessage "Restarted service: $Service" "Success"
    } else {
        docker compose -f $ComposeFile restart
        Write-StatusMessage "All monitoring services restarted" "Success"
    }
}

function Show-ServiceStatus {
    Write-StatusMessage "Checking service status..."
    docker compose -f $ComposeFile ps
}

function Show-Logs {
    if ($Service) {
        Write-StatusMessage "Showing logs for $Service..."
        docker compose -f $ComposeFile logs -f $Service
    } else {
        Write-StatusMessage "Showing logs for all services..."
        docker compose -f $ComposeFile logs -f
    }
}

function Show-AccessUrls {
    Write-StatusMessage "Monitoring services are available at:" "Success"
    Write-Host ""
    Write-Host "📊 Grafana Dashboard:    http://localhost:3000 (admin/admin123)" -ForegroundColor Cyan
    Write-Host "📈 Prometheus:           http://localhost:9090" -ForegroundColor Cyan
    Write-Host "🚨 AlertManager:         http://localhost:9093" -ForegroundColor Cyan
    Write-Host "🔍 Jaeger Tracing:       http://localhost:16686" -ForegroundColor Cyan
    Write-Host "📝 Loki Logs:            http://localhost:3100" -ForegroundColor Cyan
    Write-Host "💻 Node Exporter:        http://localhost:9100" -ForegroundColor Cyan
    Write-Host ""
}

function Cleanup-Monitoring {
    Write-StatusMessage "Cleaning up monitoring infrastructure..." "Warning"
    
    $confirmation = Read-Host "This will remove all monitoring containers and volumes. Continue? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        docker compose -f $ComposeFile down -v
        docker network rm $NetworkName 2>$null
        Write-StatusMessage "Monitoring infrastructure cleaned up" "Success"
    } else {
        Write-StatusMessage "Cleanup cancelled" "Info"
    }
}

# Main execution
switch ($Action) {
    "setup"   { Setup-Monitoring }
    "start"   { Start-Monitoring }
    "stop"    { Stop-Monitoring }
    "restart" { Restart-Monitoring }
    "status"  { Show-ServiceStatus }
    "logs"    { Show-Logs }
    "cleanup" { Cleanup-Monitoring }
}

Write-StatusMessage "Monitoring script completed" "Success"
