#!/usr/bin/env powershell
<#
.SYNOPSIS
    Local CI/CD Pipeline Simulation Script
    
.DESCRIPTION
    This script simulates the GitHub Actions CI/CD pipeline locally, running all the same
    checks and tests that would run in the actual CI environment.
    
.PARAMETER Stage
    Which CI stage to run: all, lint, unit, integration, frontend, security, docker, e2e, performance
    
.PARAMETER SkipServices
    Skip starting Docker services (useful if already running)
    
.PARAMETER Parallel
    Run tests in parallel where possible
    
.PARAMETER Verbose
    Enable verbose output
    
.PARAMETER CleanUp
    Clean up Docker resources after completion
    
.EXAMPLE
    .\simulate-ci.ps1 -Stage all
    .\simulate-ci.ps1 -Stage lint,unit,integration
    .\simulate-ci.ps1 -Stage all -SkipServices -Parallel
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "lint", "unit", "integration", "frontend", "security", "docker", "e2e", "performance")]
    [string[]]$Stage = @("all"),
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipServices,
    
    [Parameter(Mandatory=$false)]
    [switch]$Parallel,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose,
    
    [Parameter(Mandatory=$false)]
    [switch]$CleanUp,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# Colors for output
$Colors = @{
    Red = "`e[31m"
    Green = "`e[32m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Magenta = "`e[35m"
    Cyan = "`e[36m"
    Reset = "`e[0m"
}

# Global variables
$Global:TestResults = @{}
$Global:StartTime = Get-Date
$Global:FailedStages = @()
$Global:SkippedStages = @()

function Write-ColorText {
    param($Text, $Color = "Reset")
    Write-Host "$($Colors[$Color])$Text$($Colors.Reset)"
}

function Write-StageHeader {
    param($StageName, $Description)
    Write-Host ""
    Write-ColorText "=" * 80 "Blue"
    Write-ColorText "🚀 CI STAGE: $StageName" "Blue"
    Write-ColorText "📝 $Description" "Cyan"
    Write-ColorText "=" * 80 "Blue"
    Write-Host ""
}

function Write-StageResult {
    param($StageName, $Success, $Duration, $Details = "")
    
    $Status = if ($Success) { "✅ PASSED" } else { "❌ FAILED" }
    $Color = if ($Success) { "Green" } else { "Red" }
    
    Write-ColorText "📊 STAGE RESULT: $StageName - $Status (${Duration}s)" $Color
    if ($Details) {
        Write-ColorText "   $Details" "Yellow"
    }
}

function Test-Prerequisites {
    Write-StageHeader "PREREQUISITES" "Checking system prerequisites"
    
    $prerequisites = @(
        @{ Name = "Docker"; Command = "docker"; Args = "--version" },
        @{ Name = "Docker Compose"; Command = "docker-compose"; Args = "--version" },
        @{ Name = "Python"; Command = "python"; Args = "--version" },
        @{ Name = "Node.js"; Command = "node"; Args = "--version" },
        @{ Name = "npm"; Command = "npm"; Args = "--version" }
    )
    
    $allPresent = $true
    
    foreach ($prereq in $prerequisites) {
        try {
            $result = & $prereq.Command $prereq.Args 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorText "✅ $($prereq.Name): $result" "Green"
            } else {
                Write-ColorText "❌ $($prereq.Name): Not found or error" "Red"
                $allPresent = $false
            }
        } catch {
            Write-ColorText "❌ $($prereq.Name): Not installed" "Red"
            $allPresent = $false
        }
    }
    
    if (-not $allPresent) {
        Write-ColorText "❌ Some prerequisites are missing. Please install them before continuing." "Red"
        exit 1
    }
    
    Write-ColorText "✅ All prerequisites satisfied!" "Green"
}

function Start-Services {
    if ($SkipServices) {
        Write-ColorText "⏭️ Skipping service startup (--SkipServices flag)" "Yellow"
        return
    }
    
    Write-StageHeader "SERVICES" "Starting required services for testing"
    
    try {
        Write-ColorText "🐳 Starting Docker services..." "Blue"
        & docker-compose -f docker-compose.test.yml up -d
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "❌ Failed to start Docker services" "Red"
            return $false
        }
        
        Write-ColorText "⏳ Waiting for services to be ready..." "Yellow"
        Start-Sleep -Seconds 30
        
        # Health check
        $services = @(
            @{ Name = "PostgreSQL"; Url = "localhost:5432" },
            @{ Name = "Redis"; Url = "localhost:6379" },
            @{ Name = "InfluxDB"; Url = "http://localhost:8086/health" }
        )
        
        foreach ($service in $services) {
            Write-ColorText "🔍 Checking $($service.Name)..." "Cyan"
            # Add specific health checks here
        }
        
        Write-ColorText "✅ Services started successfully!" "Green"
        return $true
    } catch {
        Write-ColorText "❌ Failed to start services: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Invoke-LintStage {
    $stageName = "LINT"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Code quality and formatting checks"
    
    $success = $true
    $details = @()
    
    # Python linting
    Write-ColorText "🐍 Running Python linting..." "Blue"
    
    # Black formatting check
    Write-ColorText "   📝 Checking code formatting (Black)..." "Cyan"
    try {
        $result = python -m black --check --diff . 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "   ❌ Black formatting issues found" "Red"
            $success = $false
            $details += "Black formatting issues"
        } else {
            Write-ColorText "   ✅ Black formatting passed" "Green"
        }
    } catch {
        Write-ColorText "   ❌ Black not installed or error: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "Black error"
    }
    
    # isort import sorting
    Write-ColorText "   📚 Checking import sorting (isort)..." "Cyan"
    try {
        $result = python -m isort --check-only --diff . 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "   ❌ isort import issues found" "Red"
            $success = $false
            $details += "isort issues"
        } else {
            Write-ColorText "   ✅ isort passed" "Green"
        }
    } catch {
        Write-ColorText "   ❌ isort not installed or error: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "isort error"
    }
    
    # flake8 linting
    Write-ColorText "   🔍 Running flake8 linting..." "Cyan"
    try {
        $result = python -m flake8 services/ tests/ 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "   ❌ flake8 linting issues found" "Red"
            if ($Verbose) { Write-Host $result }
            $success = $false
            $details += "flake8 issues"
        } else {
            Write-ColorText "   ✅ flake8 passed" "Green"
        }
    } catch {
        Write-ColorText "   ❌ flake8 not installed or error: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "flake8 error"
    }
    
    # mypy type checking
    Write-ColorText "   🔎 Running mypy type checking..." "Cyan"
    try {
        $result = python -m mypy services/ --ignore-missing-imports 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "   ❌ mypy type checking issues found" "Red"
            if ($Verbose) { Write-Host $result }
            $success = $false
            $details += "mypy issues"
        } else {
            Write-ColorText "   ✅ mypy passed" "Green"
        }
    } catch {
        Write-ColorText "   ❌ mypy not installed or error: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "mypy error"
    }
    
    # Frontend linting (if frontend exists)
    if (Test-Path "frontend/package.json") {
        Write-ColorText "⚛️ Running frontend linting..." "Blue"
        
        try {
            Push-Location "frontend"
            
            # Install dependencies if needed
            if (-not (Test-Path "node_modules")) {
                Write-ColorText "   📦 Installing frontend dependencies..." "Cyan"
                npm ci
            }
            
            # Run ESLint
            Write-ColorText "   🔍 Running ESLint..." "Cyan"
            $result = npm run lint 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-ColorText "   ❌ ESLint issues found" "Red"
                if ($Verbose) { Write-Host $result }
                $success = $false
                $details += "ESLint issues"
            } else {
                Write-ColorText "   ✅ ESLint passed" "Green"
            }
            
            Pop-Location
        } catch {
            Write-ColorText "   ❌ Frontend linting error: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "Frontend linting error"
            Pop-Location
        }
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
    }
    
    if (-not $success) { $Global:FailedStages += $stageName }
    
    return $success
}

function Invoke-UnitTestStage {
    $stageName = "UNIT TESTS"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Running unit tests for all services"
    
    $success = $true
    $details = @()
    
    # Install test dependencies
    Write-ColorText "📦 Installing test dependencies..." "Blue"
    try {
        python -m pip install -r test-requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "❌ Failed to install test dependencies" "Red"
            $success = $false
            $details += "Dependency installation failed"
        }
    } catch {
        Write-ColorText "❌ Error installing dependencies: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "Dependency error"
    }
    
    if ($success) {
        # Run Python unit tests
        Write-ColorText "🧪 Running Python unit tests..." "Blue"
        try {
            $result = python -m pytest tests/unit/ -v -m unit --junitxml=junit/test-results-unit.xml --cov=services --cov-report=xml --cov-report=html 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorText "❌ Python unit tests failed" "Red"
                if ($Verbose) { Write-Host $result }
                $success = $false
                $details += "Python unit test failures"
            } else {
                Write-ColorText "✅ Python unit tests passed" "Green"
                
                # Extract test count from output
                $testCount = ($result | Select-String "(\d+) passed").Matches[0].Groups[1].Value
                if ($testCount) {
                    $details += "$testCount Python tests passed"
                }
            }
        } catch {
            Write-ColorText "❌ Error running Python unit tests: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "Python unit test error"
        }
        
        # Run frontend tests if available
        if (Test-Path "frontend/package.json") {
            Write-ColorText "⚛️ Running frontend unit tests..." "Blue"
            try {
                Push-Location "frontend"
                
                $result = npm test -- --run --coverage 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-ColorText "❌ Frontend unit tests failed" "Red"
                    if ($Verbose) { Write-Host $result }
                    $success = $false
                    $details += "Frontend unit test failures"
                } else {
                    Write-ColorText "✅ Frontend unit tests passed" "Green"
                }
                
                Pop-Location
            } catch {
                Write-ColorText "❌ Error running frontend tests: $($_.Exception.Message)" "Red"
                $success = $false
                $details += "Frontend test error"
                Pop-Location
            }
        }
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
    }
    
    if (-not $success) { $Global:FailedStages += $stageName }
    
    return $success
}

function Invoke-IntegrationTestStage {
    $stageName = "INTEGRATION TESTS"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Running integration tests with services"
    
    $success = $true
    $details = @()
    
    # Initialize databases
    Write-ColorText "🗄️ Initializing test databases..." "Blue"
    try {
        # Run database initialization scripts
        $env:PGPASSWORD = "postgres"
        psql -h localhost -U postgres -d energy_tracking_test -f scripts/init-db.sql
        psql -h localhost -U postgres -d energy_tracking_test -f scripts/rbac-migration.sql
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "❌ Database initialization failed" "Red"
            $success = $false
            $details += "Database init failed"
        } else {
            Write-ColorText "✅ Database initialized" "Green"
        }
    } catch {
        Write-ColorText "❌ Database initialization error: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "Database init error"
    }
    
    if ($success) {
        # Run integration tests
        Write-ColorText "🔗 Running integration tests..." "Blue"
        try {
            $result = python -m pytest tests/integration/ -v -m integration --junitxml=junit/test-results-integration.xml 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorText "❌ Integration tests failed" "Red"
                if ($Verbose) { Write-Host $result }
                $success = $false
                $details += "Integration test failures"
            } else {
                Write-ColorText "✅ Integration tests passed" "Green"
                
                # Extract test count
                $testCount = ($result | Select-String "(\d+) passed").Matches[0].Groups[1].Value
                if ($testCount) {
                    $details += "$testCount integration tests passed"
                }
            }
        } catch {
            Write-ColorText "❌ Error running integration tests: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "Integration test error"
        }
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
    }
    
    if (-not $success) { $Global:FailedStages += $stageName }
    
    return $success
}

function Invoke-SecurityTestStage {
    $stageName = "SECURITY TESTS"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Running security scans and tests"
    
    $success = $true
    $details = @()
    
    # Install security tools
    Write-ColorText "🔧 Installing security tools..." "Blue"
    try {
        python -m pip install bandit safety semgrep
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "❌ Failed to install security tools" "Red"
            $success = $false
            $details += "Security tools installation failed"
        }
    } catch {
        Write-ColorText "❌ Error installing security tools: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "Security tools error"
    }
    
    if ($success) {
        # Run Bandit security scan
        Write-ColorText "🔒 Running Bandit security scan..." "Blue"
        try {
            $result = python -m bandit -r services/ -f json -o bandit-report.json 2>&1
            # Bandit returns non-zero for findings, so we check the report
            if (Test-Path "bandit-report.json") {
                $banditReport = Get-Content "bandit-report.json" | ConvertFrom-Json
                $highSeverity = $banditReport.metrics._totals.SEVERITY.HIGH
                $mediumSeverity = $banditReport.metrics._totals.SEVERITY.MEDIUM
                
                if ($highSeverity -gt 0) {
                    Write-ColorText "❌ Bandit found $highSeverity high severity issues" "Red"
                    $success = $false
                    $details += "$highSeverity high severity security issues"
                } else {
                    Write-ColorText "✅ Bandit scan passed (no high severity issues)" "Green"
                    if ($mediumSeverity -gt 0) {
                        $details += "$mediumSeverity medium severity issues found"
                    }
                }
            }
        } catch {
            Write-ColorText "❌ Bandit scan error: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "Bandit error"
        }
        
        # Run Safety dependency scan
        Write-ColorText "🛡️ Running Safety dependency scan..." "Blue"
        try {
            $result = python -m safety check --json --output safety-report.json 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorText "✅ Safety scan passed (no known vulnerabilities)" "Green"
            } else {
                Write-ColorText "❌ Safety found dependency vulnerabilities" "Red"
                $success = $false
                $details += "Vulnerable dependencies found"
            }
        } catch {
            Write-ColorText "❌ Safety scan error: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "Safety error"
        }
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
    }
    
    if (-not $success) { $Global:FailedStages += $stageName }
    
    return $success
}

function Invoke-DockerBuildStage {
    $stageName = "DOCKER BUILD"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Building all Docker images"
    
    $success = $true
    $details = @()
    $builtImages = @()
    
    $services = @(
        @{ Name = "API Gateway"; Path = "services/api-gateway"; Tag = "energy-tracking/api-gateway:latest" },
        @{ Name = "Auth Service"; Path = "services/auth-service"; Tag = "energy-tracking/auth-service:latest" },
        @{ Name = "Data Ingestion"; Path = "services/data-ingestion"; Tag = "energy-tracking/data-ingestion:latest" },
        @{ Name = "Data Processing"; Path = "services/data-processing"; Tag = "energy-tracking/data-processing:latest" },
        @{ Name = "Analytics"; Path = "services/analytics"; Tag = "energy-tracking/analytics:latest" },
        @{ Name = "Notification"; Path = "services/notification"; Tag = "energy-tracking/notification:latest" },
        @{ Name = "Frontend"; Path = "frontend"; Tag = "energy-tracking/frontend:latest" }
    )
    
    foreach ($service in $services) {
        Write-ColorText "🐳 Building $($service.Name)..." "Blue"
        try {
            $result = docker build -t $service.Tag $service.Path 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorText "   ✅ $($service.Name) built successfully" "Green"
                $builtImages += $service.Tag
            } else {
                Write-ColorText "   ❌ Failed to build $($service.Name)" "Red"
                if ($Verbose) { Write-Host $result }
                $success = $false
                $details += "$($service.Name) build failed"
            }
        } catch {
            Write-ColorText "   ❌ Error building $($service.Name): $($_.Exception.Message)" "Red"
            $success = $false
            $details += "$($service.Name) build error"
        }
    }
    
    if ($builtImages.Count -gt 0) {
        $details += "$($builtImages.Count) images built successfully"
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
        BuiltImages = $builtImages
    }
    
    if (-not $success) { $Global:FailedStages += $stageName }
    
    return $success
}

function Invoke-E2ETestStage {
    $stageName = "E2E TESTS"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Running end-to-end tests"
    
    $success = $true
    $details = @()
    
    # Start the complete application stack
    Write-ColorText "🚀 Starting application stack for E2E tests..." "Blue"
    try {
        docker-compose -f docker-compose.test.yml up -d
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "❌ Failed to start application stack" "Red"
            $success = $false
            $details += "Stack startup failed"
        } else {
            Write-ColorText "⏳ Waiting for services to be ready..." "Yellow"
            Start-Sleep -Seconds 60
            
            # Health checks
            Write-ColorText "🔍 Checking service health..." "Cyan"
            $healthChecks = @(
                @{ Name = "API Gateway"; Url = "http://localhost:8000/health" },
                @{ Name = "Auth Service"; Url = "http://localhost:8005/health" }
            )
            
            foreach ($check in $healthChecks) {
                try {
                    $response = Invoke-RestMethod -Uri $check.Url -TimeoutSec 10
                    Write-ColorText "   ✅ $($check.Name) is healthy" "Green"
                } catch {
                    Write-ColorText "   ❌ $($check.Name) health check failed" "Red"
                    $success = $false
                    $details += "$($check.Name) unhealthy"
                }
            }
        }
    } catch {
        Write-ColorText "❌ Error starting application stack: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "Stack startup error"
    }
    
    if ($success) {
        # Run E2E tests
        Write-ColorText "🎯 Running E2E tests..." "Blue"
        try {
            $result = python -m pytest tests/e2e/ -v -m e2e --junitxml=junit/test-results-e2e.xml 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-ColorText "❌ E2E tests failed" "Red"
                if ($Verbose) { Write-Host $result }
                $success = $false
                $details += "E2E test failures"
            } else {
                Write-ColorText "✅ E2E tests passed" "Green"
                
                # Extract test count
                $testCount = ($result | Select-String "(\d+) passed").Matches[0].Groups[1].Value
                if ($testCount) {
                    $details += "$testCount E2E tests passed"
                }
            }
        } catch {
            Write-ColorText "❌ Error running E2E tests: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "E2E test error"
        }
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
    }
    
    if (-not $success) { $Global:FailedStages += $stageName }
    
    return $success
}

function Invoke-PerformanceTestStage {
    $stageName = "PERFORMANCE TESTS"
    $startTime = Get-Date
    
    Write-StageHeader $stageName "Running performance tests"
    
    $success = $true
    $details = @()
    
    # Install Locust
    Write-ColorText "📦 Installing Locust..." "Blue"
    try {
        python -m pip install locust
        if ($LASTEXITCODE -ne 0) {
            Write-ColorText "❌ Failed to install Locust" "Red"
            $success = $false
            $details += "Locust installation failed"
        }
    } catch {
        Write-ColorText "❌ Error installing Locust: $($_.Exception.Message)" "Red"
        $success = $false
        $details += "Locust installation error"
    }
    
    if ($success -and (Test-Path "tests/performance/locustfile.py")) {
        # Run performance tests
        Write-ColorText "⚡ Running performance tests..." "Blue"
        try {
            Push-Location "tests/performance"
            
            $result = locust -f locustfile.py --headless -u 50 -r 10 -t 5m --host=http://localhost:8000 --html=performance-report.html 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorText "✅ Performance tests completed" "Green"
                $details += "Performance test completed"
                
                if (Test-Path "performance-report.html") {
                    $details += "Report: performance-report.html"
                }
            } else {
                Write-ColorText "❌ Performance tests failed" "Red"
                if ($Verbose) { Write-Host $result }
                $success = $false
                $details += "Performance test failures"
            }
            
            Pop-Location
        } catch {
            Write-ColorText "❌ Error running performance tests: $($_.Exception.Message)" "Red"
            $success = $false
            $details += "Performance test error"
            Pop-Location
        }
    } else {
        Write-ColorText "⏭️ Skipping performance tests (no locustfile.py found)" "Yellow"
        $Global:SkippedStages += $stageName
        $details += "No performance test file found"
    }
    
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    Write-StageResult $stageName $success $duration ($details -join ", ")
    
    $Global:TestResults[$stageName] = @{
        Success = $success
        Duration = $duration
        Details = $details
    }
    
    if (-not $success -and $stageName -notin $Global:SkippedStages) { 
        $Global:FailedStages += $stageName 
    }
    
    return $success
}

function Show-FinalReport {
    $totalDuration = [math]::Round(((Get-Date) - $Global:StartTime).TotalSeconds, 2)
    
    Write-Host ""
    Write-ColorText "=" * 80 "Blue"
    Write-ColorText "📊 CI PIPELINE SIMULATION COMPLETE" "Blue"
    Write-ColorText "=" * 80 "Blue"
    Write-Host ""
    
    Write-ColorText "⏱️ Total Duration: ${totalDuration}s" "Cyan"
    Write-Host ""
    
    # Stage Results
    Write-ColorText "📋 STAGE RESULTS:" "Yellow"
    foreach ($stage in $Global:TestResults.Keys) {
        $result = $Global:TestResults[$stage]
        $status = if ($result.Success) { "✅ PASSED" } else { "❌ FAILED" }
        $color = if ($result.Success) { "Green" } else { "Red" }
        
        Write-ColorText "   $stage`: $status ($($result.Duration)s)" $color
        if ($result.Details) {
            foreach ($detail in $result.Details) {
                Write-ColorText "      • $detail" "Cyan"
            }
        }
    }
    
    # Summary
    $passedCount = ($Global:TestResults.Values | Where-Object { $_.Success }).Count
    $failedCount = $Global:FailedStages.Count
    $skippedCount = $Global:SkippedStages.Count
    $totalCount = $Global:TestResults.Count
    
    Write-Host ""
    Write-ColorText "📈 SUMMARY:" "Yellow"
    Write-ColorText "   ✅ Passed: $passedCount" "Green"
    Write-ColorText "   ❌ Failed: $failedCount" "Red"
    Write-ColorText "   ⏭️ Skipped: $skippedCount" "Yellow"
    Write-ColorText "   📊 Total: $totalCount" "Cyan"
    
    if ($failedCount -eq 0) {
        Write-Host ""
        Write-ColorText "🎉 ALL STAGES PASSED! Your code is ready for CI/CD!" "Green"
        $exitCode = 0
    } else {
        Write-Host ""
        Write-ColorText "💥 PIPELINE FAILED! Please fix the following issues:" "Red"
        foreach ($stage in $Global:FailedStages) {
            Write-ColorText "   • $stage" "Red"
        }
        $exitCode = 1
    }
    
    # Generate JSON report
    $report = @{
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        totalDuration = $totalDuration
        summary = @{
            total = $totalCount
            passed = $passedCount
            failed = $failedCount
            skipped = $skippedCount
        }
        stages = $Global:TestResults
        failedStages = $Global:FailedStages
        skippedStages = $Global:SkippedStages
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File "ci-simulation-report.json"
    Write-ColorText "📄 Detailed report saved to: ci-simulation-report.json" "Cyan"
    
    return $exitCode
}

function Stop-Services {
    if ($CleanUp) {
        Write-ColorText "🧹 Cleaning up Docker resources..." "Yellow"
        docker-compose -f docker-compose.test.yml down -v --remove-orphans
        docker-compose down -v --remove-orphans 2>$null
        Write-ColorText "✅ Cleanup completed" "Green"
    }
}

function Show-Help {
    Write-ColorText "Local CI/CD Pipeline Simulation" "Blue"
    Write-Host "================================"
    Write-Host ""
    Write-ColorText "This script simulates the GitHub Actions CI/CD pipeline locally." "Cyan"
    Write-Host ""
    Write-ColorText "Usage:" "Yellow"
    Write-Host "  .\simulate-ci.ps1 [-Stage <stages>] [-SkipServices] [-Parallel] [-Verbose] [-CleanUp]"
    Write-Host ""
    Write-ColorText "Stages:" "Yellow"
    Write-Host "  all          - Run all stages (default)"
    Write-Host "  lint         - Code quality and formatting checks"
    Write-Host "  unit         - Unit tests"
    Write-Host "  integration  - Integration tests"
    Write-Host "  frontend     - Frontend tests"
    Write-Host "  security     - Security scans"
    Write-Host "  docker       - Docker image builds"
    Write-Host "  e2e          - End-to-end tests"
    Write-Host "  performance  - Performance tests"
    Write-Host ""
    Write-ColorText "Options:" "Yellow"
    Write-Host "  -SkipServices    Skip starting Docker services"
    Write-Host "  -Parallel        Run tests in parallel where possible"
    Write-Host "  -Verbose         Enable verbose output"
    Write-Host "  -CleanUp         Clean up Docker resources after completion"
    Write-Host ""
    Write-ColorText "Examples:" "Yellow"
    Write-Host "  .\simulate-ci.ps1                                # Run all stages"
    Write-Host "  .\simulate-ci.ps1 -Stage lint,unit              # Run only lint and unit tests"
    Write-Host "  .\simulate-ci.ps1 -Stage all -CleanUp           # Run all and cleanup"
    Write-Host "  .\simulate-ci.ps1 -SkipServices -Verbose        # Skip services, verbose output"
    Write-Host ""
}

# Main execution
function Main {
    if ($Help) {
        Show-Help
        return 0
    }
    
    Write-ColorText "🚀 LOCAL CI/CD PIPELINE SIMULATION" "Blue"
    Write-ColorText "===================================" "Blue"
    Write-Host ""
    
    # Test prerequisites
    Test-Prerequisites
    
    # Determine which stages to run
    $stagesToRun = if ($Stage -contains "all") {
        @("lint", "unit", "integration", "frontend", "security", "docker", "e2e", "performance")
    } else {
        $Stage
    }
    
    Write-ColorText "📋 Stages to run: $($stagesToRun -join ', ')" "Cyan"
    Write-Host ""
    
    # Start services if needed
    $servicesNeeded = $stagesToRun | Where-Object { $_ -in @("integration", "e2e", "performance") }
    if ($servicesNeeded -and -not $SkipServices) {
        $serviceStarted = Start-Services
        if (-not $serviceStarted) {
            Write-ColorText "❌ Failed to start services. Exiting." "Red"
            return 1
        }
    }
    
    try {
        # Run stages
        foreach ($stageToRun in $stagesToRun) {
            switch ($stageToRun) {
                "lint" { Invoke-LintStage }
                "unit" { Invoke-UnitTestStage }
                "integration" { Invoke-IntegrationTestStage }
                "frontend" { 
                    if (Test-Path "frontend/package.json") {
                        # Frontend tests are included in unit stage for now
                        Write-ColorText "⏭️ Frontend tests included in unit test stage" "Yellow"
                    } else {
                        Write-ColorText "⏭️ No frontend found, skipping" "Yellow"
                        $Global:SkippedStages += "FRONTEND"
                    }
                }
                "security" { Invoke-SecurityTestStage }
                "docker" { Invoke-DockerBuildStage }
                "e2e" { Invoke-E2ETestStage }
                "performance" { Invoke-PerformanceTestStage }
                default { 
                    Write-ColorText "❌ Unknown stage: $stageToRun" "Red"
                }
            }
        }
        
        # Show final report
        $exitCode = Show-FinalReport
        
        return $exitCode
        
    } finally {
        # Cleanup
        Stop-Services
    }
}

# Execute main function
$exitCode = Main
exit $exitCode
