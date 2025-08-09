#!/usr/bin/env pwsh
# Rebuild All Services Script
# This script ensures all dependencies are fresh and containers are rebuilt from scratch

Write-Host "🧹 Cleaning up existing containers and images..." -ForegroundColor Yellow

# Stop all containers
docker-compose down

# Remove all containers, networks, and volumes (optional - uncomment if needed)
# docker-compose down -v --remove-orphans

# Remove all project images to force rebuild
Write-Host "🗑️ Removing existing images..." -ForegroundColor Yellow
docker images | Select-String "energy-tracking" | ForEach-Object {
    $imageName = ($_ -split '\s+')[0] + ":" + ($_ -split '\s+')[1]
    docker rmi $imageName -f
}

# Clean Docker build cache
Write-Host "🧽 Cleaning Docker build cache..." -ForegroundColor Yellow
docker builder prune -f

# Rebuild all services
Write-Host "🔨 Building all services from scratch..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start all services
Write-Host "🚀 Starting all services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "📊 Service Status:" -ForegroundColor Green
docker-compose ps

Write-Host "✅ All services rebuilt and started successfully!" -ForegroundColor Green
Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔗 API Gateway: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 Grafana: http://localhost:3001" -ForegroundColor Cyan
