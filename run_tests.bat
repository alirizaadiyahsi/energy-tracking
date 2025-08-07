@echo off
REM Energy Tracking Test Runner for Windows
REM Usage: run_tests.bat [options]

echo ==============================================
echo Energy Tracking System - Test Runner
echo ==============================================

REM Change to project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Default to running quick tests if no arguments provided
if "%1"=="" (
    echo Running quick test suite...
    python tests\run_all_tests.py --quick
) else if "%1"=="quick" (
    echo Running quick test suite...
    python tests\run_all_tests.py --quick
) else if "%1"=="full" (
    echo Running full test suite...
    python tests\run_all_tests.py --full
) else if "%1"=="unit" (
    echo Running unit tests...
    python tests\run_all_tests.py --include unit
) else if "%1"=="integration" (
    echo Running integration tests...
    python tests\run_all_tests.py --include integration
) else if "%1"=="performance" (
    echo Running performance tests...
    python tests\performance\run_performance_tests.py --scenario medium
) else if "%1"=="e2e" (
    echo Running E2E tests...
    python tests\e2e\test_complete_flows.py
) else if "%1"=="browser" (
    echo Running browser E2E tests...
    python tests\e2e\test_browser_flows.py --headless
) else if "%1"=="list" (
    echo Available test suites:
    python tests\run_all_tests.py --list
) else (
    echo Usage: run_tests.bat [quick^|full^|unit^|integration^|performance^|e2e^|browser^|list]
    echo.
    echo Options:
    echo   quick       - Run unit, integration, and security tests
    echo   full        - Run all test types including performance and E2E
    echo   unit        - Run unit tests only
    echo   integration - Run integration tests only
    echo   performance - Run performance tests
    echo   e2e         - Run E2E API tests
    echo   browser     - Run browser automation tests
    echo   list        - List all available test suites
    echo.
    echo Examples:
    echo   run_tests.bat quick
    echo   run_tests.bat performance
    echo   run_tests.bat browser
)

REM Pause to see results if run by double-clicking
if "%CMDCMDLINE:~1,7%" == "cmd.exe" pause
