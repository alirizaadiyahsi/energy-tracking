# Energy Tracking System Test Runner - PowerShell Edition
# Compatible with Windows PowerShell

param(
    [switch]$Unit,
    [switch]$Integration,
    [switch]$Frontend,
    [switch]$Coverage,
    [switch]$InstallDeps,
    [switch]$All,
    [switch]$Help
)

# Color definitions
$Colors = @{
    Blue = "Cyan"
    Green = "Green"
    Yellow = "Yellow"
    Red = "Red"
    White = "White"
}

function Write-Colored {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-Dependencies {
    Write-Colored "🔍 Checking dependencies..." "Blue"
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Colored "❌ Python is not installed or not in PATH" "Red"
            return $false
        }
    }
    catch {
        Write-Colored "❌ Python is not installed or not in PATH" "Red"
        return $false
    }
    
    # Check Node.js (if frontend exists)
    if (Test-Path "frontend") {
        try {
            $nodeVersion = node --version 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Colored "❌ Node.js is not installed or not in PATH" "Red"
                return $false
            }
        }
        catch {
            Write-Colored "❌ Node.js is not installed or not in PATH" "Red"
            return $false
        }
    }
    
    # Check Python packages
    $requiredPackages = @("pytest", "pytest-asyncio", "pytest-cov", "httpx")
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        try {
            python -c "import $package" 2>$null
            if ($LASTEXITCODE -ne 0) {
                $missingPackages += $package
            }
        }
        catch {
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Colored "❌ Missing Python packages: $($missingPackages -join ', ')" "Red"
        Write-Colored "Run: pip install -r test-requirements.txt" "Yellow"
        return $false
    }
    
    # Check frontend dependencies
    if ((Test-Path "frontend") -and !(Test-Path "frontend/node_modules")) {
        Write-Colored "❌ Frontend dependencies not installed" "Red"
        Write-Colored "Run: cd frontend && npm install" "Yellow"
        return $false
    }
    
    Write-Colored "✅ All dependencies are installed" "Green"
    return $true
}

function Install-Dependencies {
    Write-Colored "📦 Installing dependencies..." "Blue"
    
    # Install Python dependencies
    Write-Colored "Installing Python test dependencies..." "Blue"
    python -m pip install -r test-requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Colored "❌ Failed to install Python dependencies" "Red"
        return $false
    }
    
    # Install frontend dependencies if frontend exists
    if (Test-Path "frontend") {
        Write-Colored "Installing frontend dependencies..." "Blue"
        Set-Location frontend
        npm install
        $npmResult = $LASTEXITCODE
        Set-Location ..
        
        if ($npmResult -ne 0) {
            Write-Colored "❌ Failed to install frontend dependencies" "Red"
            return $false
        }
    }
    
    Write-Colored "✅ Dependencies installed successfully" "Green"
    return $true
}

function Test-ServicesRunning {
    Write-Colored "🔍 Checking if services are running..." "Blue"
    
    $services = @(
        @{ Url = "http://localhost:8000/health"; Name = "API Gateway" },
        @{ Url = "http://localhost:8005/health"; Name = "Auth Service" }
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -ne 200) {
                return $false
            }
        }
        catch {
            return $false
        }
    }
    
    return $true
}

function Start-Services {
    Write-Colored "🐳 Starting services with Docker Compose..." "Blue"
    
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Colored "❌ Failed to start services" "Red"
        return $false
    }
    
    Write-Colored "⏳ Waiting for services to be ready..." "Yellow"
    Start-Sleep -Seconds 30
    
    if (Test-ServicesRunning) {
        Write-Colored "✅ Services are ready" "Green"
        return $true
    }
    else {
        Write-Colored "❌ Services failed to start properly" "Red"
        return $false
    }
}

function Run-UnitTests {
    Write-Colored "🧪 Running unit tests..." "Blue"
    
    python -m pytest tests/unit/ -v -m unit
    $result = $LASTEXITCODE -eq 0
    
    if ($result) {
        Write-Colored "✅ Unit tests passed" "Green"
    }
    else {
        Write-Colored "❌ Unit tests failed" "Red"
    }
    
    return $result
}

function Run-IntegrationTests {
    Write-Colored "🔗 Running integration tests..." "Blue"
    
    # Check if services are running
    if (!(Test-ServicesRunning)) {
        Write-Colored "⚠️ Services not running, starting them..." "Yellow"
        if (!(Start-Services)) {
            return $false
        }
    }
    
    python -m pytest tests/integration/ -v -m integration
    $result = $LASTEXITCODE -eq 0
    
    if ($result) {
        Write-Colored "✅ Integration tests passed" "Green"
    }
    else {
        Write-Colored "❌ Integration tests failed" "Red"
    }
    
    return $result
}

function Run-FrontendTests {
    Write-Colored "⚛️ Running frontend tests..." "Blue"
    
    if (!(Test-Path "frontend")) {
        Write-Colored "⚠️ Frontend directory not found, skipping" "Yellow"
        return $true
    }
    
    Set-Location frontend
    npm test -- --run
    $result = $LASTEXITCODE -eq 0
    Set-Location ..
    
    if ($result) {
        Write-Colored "✅ Frontend tests passed" "Green"
    }
    else {
        Write-Colored "❌ Frontend tests failed" "Red"
    }
    
    return $result
}

function Run-CoverageTests {
    Write-Colored "📊 Running tests with coverage..." "Blue"
    
    python -m pytest tests/ --cov=services --cov-report=html --cov-report=term --cov-fail-under=80
    $result = $LASTEXITCODE -eq 0
    
    if ($result) {
        Write-Colored "✅ Coverage tests passed" "Green"
        Write-Colored "📋 Coverage report generated in htmlcov/" "Blue"
    }
    else {
        Write-Colored "❌ Coverage tests failed" "Red"
    }
    
    return $result
}

function Show-Summary {
    param([hashtable]$Results)
    
    Write-Colored "`n$('=' * 60)" "Blue"
    Write-Colored "📋 TEST SUMMARY" "Blue"
    Write-Colored "$('=' * 60)" "Blue"
    
    $totalTests = $Results.Count
    $passedTests = ($Results.Values | Where-Object { $_ -eq $true }).Count
    
    foreach ($testType in $Results.Keys) {
        $success = $Results[$testType]
        $status = if ($success) { "✅ PASSED" } else { "❌ FAILED" }
        $color = if ($success) { "Green" } else { "Red" }
        
        Write-Colored "$($testType.ToUpper().PadRight(20, '.')) $status" $color
    }
    
    Write-Colored "$('=' * 60)" "Blue"
    
    if ($passedTests -eq $totalTests) {
        Write-Colored "🎉 ALL TESTS PASSED ($passedTests/$totalTests)" "Green"
    }
    else {
        Write-Colored "⚠️ SOME TESTS FAILED ($passedTests/$totalTests)" "Red"
    }
    
    Write-Colored "$('=' * 60)" "Blue"
    
    return $passedTests -eq $totalTests
}

function Show-Help {
    Write-Colored "Energy Tracking System Test Runner - PowerShell Edition" "Blue"
    Write-Colored ""
    Write-Colored "Usage: .\run-tests.ps1 [OPTIONS]" "White"
    Write-Colored ""
    Write-Colored "Options:" "White"
    Write-Colored "  -Unit           Run unit tests only" "White"
    Write-Colored "  -Integration    Run integration tests only" "White"
    Write-Colored "  -Frontend       Run frontend tests only" "White"
    Write-Colored "  -Coverage       Run coverage tests" "White"
    Write-Colored "  -InstallDeps    Install dependencies" "White"
    Write-Colored "  -All            Run all tests" "White"
    Write-Colored "  -Help           Show this help message" "White"
    Write-Colored ""
    Write-Colored "Examples:" "Yellow"
    Write-Colored "  .\run-tests.ps1 -Unit" "White"
    Write-Colored "  .\run-tests.ps1 -All -InstallDeps" "White"
    Write-Colored "  .\run-tests.ps1 -Coverage" "White"
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

Write-Colored "🚀 Energy Tracking System Test Runner" "Blue"
Write-Colored "$('=' * 50)" "Blue"

# Install dependencies if requested
if ($InstallDeps -or $All) {
    if (!(Install-Dependencies)) {
        exit 1
    }
}

# Check dependencies
if (!(Test-Dependencies)) {
    Write-Colored "Run with -InstallDeps to install missing dependencies" "Yellow"
    exit 1
}

# Initialize results
$TestResults = @{}

# Determine which tests to run
if ($Unit) {
    $TestResults["unit"] = Run-UnitTests
}
elseif ($Integration) {
    $TestResults["integration"] = Run-IntegrationTests
}
elseif ($Frontend) {
    $TestResults["frontend"] = Run-FrontendTests
}
elseif ($Coverage) {
    $TestResults["coverage"] = Run-CoverageTests
}
elseif ($All) {
    $TestResults["unit"] = Run-UnitTests
    $TestResults["integration"] = Run-IntegrationTests
    $TestResults["frontend"] = Run-FrontendTests
    $TestResults["coverage"] = Run-CoverageTests
}
else {
    # Default: run unit and integration tests
    $TestResults["unit"] = Run-UnitTests
    $TestResults["integration"] = Run-IntegrationTests
}

# Show summary and exit with appropriate code
$allPassed = Show-Summary -Results $TestResults

if ($allPassed) {
    exit 0
}
else {
    exit 1
}
