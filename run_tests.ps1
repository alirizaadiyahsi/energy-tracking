#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Energy Tracking System Test Runner

.DESCRIPTION
    Comprehensive test runner for the Energy Tracking IoT Data Platform.
    Supports multiple test types: unit, integration, performance, and E2E tests.

.PARAMETER TestType
    Type of tests to run: quick, full, unit, integration, performance, e2e, browser, list

.PARAMETER Parallel
    Run tests in parallel where possible

.PARAMETER FailFast
    Stop on first test failure

.PARAMETER Verbose
    Enable verbose output

.PARAMETER Coverage
    Generate code coverage reports

.EXAMPLE
    .\run_tests.ps1 quick
    Run quick test suite (unit + integration + security)

.EXAMPLE
    .\run_tests.ps1 full -Parallel
    Run all tests with parallel execution

.EXAMPLE
    .\run_tests.ps1 performance
    Run performance tests

.EXAMPLE
    .\run_tests.ps1 unit -Coverage
    Run unit tests with coverage report
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("quick", "full", "unit", "integration", "performance", "e2e", "browser", "list", "")]
    [string]$TestType = "quick",
    
    [switch]$Parallel,
    [switch]$FailFast,
    [switch]$Verbose,
    [switch]$Coverage
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Info    = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Header  = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Python found: $pythonVersion" "Success"
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ Python is not installed or not in PATH" "Error"
        Write-ColorOutput "Please install Python 3.11+ and ensure it's in your PATH" "Warning"
        return $false
    }
}

function Test-TestDependencies {
    Write-ColorOutput "🔍 Checking test dependencies..." "Info"
    
    $requiredPackages = @("pytest", "pytest-asyncio", "pytest-cov", "httpx", "bcrypt", "PyJWT")
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        $packageCheck = python -c "import $($package.Replace('-', '_'))" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-ColorOutput "❌ Missing packages: $($missingPackages -join ', ')" "Error"
        Write-ColorOutput "Install with: pip install $($missingPackages -join ' ')" "Warning"
        return $false
    }
    
    Write-ColorOutput "✅ All test dependencies are installed" "Success"
    return $true
}

function Invoke-TestSuite {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-ColorOutput "🧪 $Description" "Header"
    Write-ColorOutput "Command: $Command" "Info"
    
    $startTime = Get-Date
    
    try {
        if ($Verbose) {
            Invoke-Expression $Command
        }
        else {
            Invoke-Expression "$Command 2>&1" | Out-Host
        }
        
        $duration = (Get-Date) - $startTime
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ $Description completed successfully in $($duration.TotalSeconds.ToString("F2"))s" "Success"
            return $true
        }
        else {
            Write-ColorOutput "❌ $Description failed (exit code: $LASTEXITCODE)" "Error"
            return $false
        }
    }
    catch {
        $duration = (Get-Date) - $startTime
        Write-ColorOutput "❌ $Description failed with exception: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Start-TestExecution {
    # Change to project directory
    $projectRoot = Split-Path -Parent $MyInvocation.PSScriptRoot
    if (Test-Path $projectRoot) {
        Set-Location $projectRoot
    }
    
    Write-ColorOutput "=============================================" "Header"
    Write-ColorOutput "Energy Tracking System - Test Runner" "Header"
    Write-ColorOutput "=============================================" "Header"
    Write-ColorOutput "Project Root: $(Get-Location)" "Info"
    Write-ColorOutput "Test Type: $TestType" "Info"
    if ($Parallel) { Write-ColorOutput "Parallel Execution: Enabled" "Info" }
    if ($FailFast) { Write-ColorOutput "Fail Fast: Enabled" "Info" }
    if ($Coverage) { Write-ColorOutput "Coverage: Enabled" "Info" }
    Write-ColorOutput ""
    
    # Check prerequisites
    if (-not (Test-PythonInstallation)) {
        exit 1
    }
    
    if (-not (Test-TestDependencies)) {
        Write-ColorOutput "Installing missing dependencies..." "Warning"
        try {
            pip install pytest pytest-asyncio pytest-cov pytest-mock httpx bcrypt PyJWT factory-boy faker
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput "❌ Failed to install dependencies" "Error"
                exit 1
            }
        }
        catch {
            Write-ColorOutput "❌ Failed to install dependencies: $($_.Exception.Message)" "Error"
            exit 1
        }
    }
    
    # Build command arguments
    $baseArgs = @()
    if ($Parallel) { $baseArgs += "--parallel" }
    if ($FailFast) { $baseArgs += "--fail-fast" }
    
    $baseCommand = "python tests\run_all_tests.py"
    if ($baseArgs.Count -gt 0) {
        $baseCommand += " " + ($baseArgs -join " ")
    }
    
    $success = $true
    
    switch ($TestType) {
        "quick" {
            $command = "$baseCommand --quick"
            $success = Invoke-TestSuite $command "Quick Test Suite (Unit + Integration + Security)"
        }
        "full" {
            $command = "$baseCommand --full"
            $success = Invoke-TestSuite $command "Full Test Suite (All Tests)"
        }
        "unit" {
            $coverageFlag = if ($Coverage) { "--coverage" } else { "" }
            $command = "python tests\run_tests.py --type unit $coverageFlag"
            $success = Invoke-TestSuite $command "Unit Tests"
        }
        "integration" {
            $command = "$baseCommand --include integration"
            $success = Invoke-TestSuite $command "Integration Tests"
        }
        "performance" {
            $command = "python tests\performance\run_performance_tests.py --scenario medium"
            $success = Invoke-TestSuite $command "Performance Tests"
        }
        "e2e" {
            $command = "python tests\e2e\test_complete_flows.py"
            $success = Invoke-TestSuite $command "End-to-End API Tests"
        }
        "browser" {
            $command = "python tests\e2e\test_browser_flows.py --headless"
            $success = Invoke-TestSuite $command "Browser End-to-End Tests"
        }
        "list" {
            Write-ColorOutput "📋 Available Test Suites:" "Header"
            python tests\run_all_tests.py --list
            return
        }
        "" {
            # Default to quick if no parameter provided
            $command = "$baseCommand --quick"
            $success = Invoke-TestSuite $command "Quick Test Suite (Default)"
        }
        default {
            Write-ColorOutput "❌ Unknown test type: $TestType" "Error"
            Write-ColorOutput "Available options: quick, full, unit, integration, performance, e2e, browser, list" "Warning"
            exit 1
        }
    }
    
    # Summary
    Write-ColorOutput ""
    Write-ColorOutput "=============================================" "Header"
    if ($success) {
        Write-ColorOutput "🎉 Test execution completed successfully!" "Success"
        
        # Show coverage report location if generated
        if ($Coverage -and (Test-Path "tests\results\coverage_html\index.html")) {
            Write-ColorOutput "📊 Coverage report: tests\results\coverage_html\index.html" "Info"
        }
        
        # Show test results if available
        $resultsDir = "tests\results"
        if (Test-Path $resultsDir) {
            $latestResults = Get-ChildItem $resultsDir -Filter "*.html" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($latestResults) {
                Write-ColorOutput "📋 Test report: $($latestResults.FullName)" "Info"
            }
        }
    }
    else {
        Write-ColorOutput "💥 Test execution failed!" "Error"
        Write-ColorOutput "Check the output above for error details" "Warning"
        exit 1
    }
}

# Main execution
try {
    Start-TestExecution
}
catch {
    Write-ColorOutput "❌ Unexpected error: $($_.Exception.Message)" "Error"
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" "Error"
    exit 1
}
