# PowerShell script for API documentation generation
# Usage: .\generate-api-docs.ps1

param(
    [switch]$Serve,
    [switch]$Postman,
    [switch]$Validate
)

Write-Host "🚀 Energy Tracking API Documentation Generator" -ForegroundColor Blue

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Install required packages if not present
Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
pip install httpx pyyaml openapi-spec-validator | Out-Null

# Generate documentation
Write-Host "📡 Generating API documentation..." -ForegroundColor Cyan
python scripts/generate_api_docs.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ API documentation generated successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to generate API documentation" -ForegroundColor Red
    exit 1
}

# Serve documentation if requested
if ($Serve) {
    Write-Host "🌐 Starting documentation server..." -ForegroundColor Cyan
    Set-Location docs/api
    Start-Process "http://localhost:8080"
    python -m http.server 8080
}

# Open Postman collection if requested
if ($Postman) {
    $postmanFile = "docs/api/postman_collection.json"
    if (Test-Path $postmanFile) {
        Write-Host "📬 Postman collection available at: $postmanFile" -ForegroundColor Green
        # Try to open in default JSON viewer
        Start-Process $postmanFile
    } else {
        Write-Host "❌ Postman collection not found" -ForegroundColor Red
    }
}

# Validate OpenAPI specs if requested
if ($Validate) {
    Write-Host "🔍 Validating OpenAPI specifications..." -ForegroundColor Cyan
    Set-Location docs/api
    
    Get-ChildItem -Filter "*.json" | ForEach-Object {
        Write-Host "Validating $($_.Name)..." -ForegroundColor Yellow
        try {
            openapi-spec-validator $_.FullName
            Write-Host "✅ $($_.Name) is valid" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ $($_.Name) validation failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "🎉 Documentation generation completed!" -ForegroundColor Green
