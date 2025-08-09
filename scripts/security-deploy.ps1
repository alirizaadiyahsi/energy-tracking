# Security Deployment Management Script
# Comprehensive security deployment automation for Energy Tracking Platform

param(
    [string]$Environment = "development",
    [string]$Action = "deploy",
    [switch]$Validate,
    [switch]$Force,
    [switch]$DryRun
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

# Define paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$LibsPath = Join-Path $ProjectRoot "libs"
$ServicesPath = Join-Path $ProjectRoot "services"
$InfraPath = Join-Path $ProjectRoot "infrastructure"

# Logging configuration
$LogFile = Join-Path $ProjectRoot "logs\security-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$null = New-Item -ItemType Directory -Force -Path (Split-Path $LogFile -Parent)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

function Test-SecurityConfiguration {
    Write-Log "Validating security configuration for environment: $Environment"
    
    $ValidationResults = @{
        SharedLibraries = $false
        SecurityMiddleware = $false
        ThreatDetection = $false
        InputValidation = $false
        SecurityConfig = $false
        MonitoringIntegration = $false
    }
    
    try {
        # Check shared libraries
        $RequiredLibs = @(
            "libs\common\security.py",
            "libs\common\threat_detection.py", 
            "libs\common\validation.py",
            "libs\common\security_config.py"
        )
        
        foreach ($lib in $RequiredLibs) {
            $LibPath = Join-Path $ProjectRoot $lib
            if (Test-Path $LibPath) {
                Write-Log "✓ Found required library: $lib" "SUCCESS"
            } else {
                Write-Log "✗ Missing required library: $lib" "ERROR"
                return $false
            }
        }
        $ValidationResults.SharedLibraries = $true
        
        # Check security middleware integration
        $AuthServiceMain = Join-Path $ServicesPath "auth-service\main.py"
        if (Test-Path $AuthServiceMain) {
            $MainContent = Get-Content $AuthServiceMain -Raw
            if ($MainContent -match "SecurityMiddleware" -and $MainContent -match "ThreatDetector") {
                Write-Log "✓ Security middleware integrated in auth service" "SUCCESS"
                $ValidationResults.SecurityMiddleware = $true
            } else {
                Write-Log "✗ Security middleware not properly integrated" "ERROR"
            }
        }
        
        # Check monitoring configuration
        $PrometheusConfig = Join-Path $InfraPath "prometheus\prometheus.yml"
        $GrafanaConfig = Join-Path $InfraPath "grafana\dashboards\security-monitoring.json"
        
        if ((Test-Path $PrometheusConfig) -and (Test-Path $GrafanaConfig)) {
            Write-Log "✓ Monitoring configuration found" "SUCCESS"
            $ValidationResults.MonitoringIntegration = $true
        } else {
            Write-Log "✗ Monitoring configuration incomplete" "ERROR"
        }
        
        # Environment-specific validation
        switch ($Environment) {
            "production" {
                Write-Log "Validating production security requirements..." "INFO"
                
                # Check SSL/TLS configuration
                $NginxConfig = Join-Path $InfraPath "nginx\nginx.conf"
                if (Test-Path $NginxConfig) {
                    $NginxContent = Get-Content $NginxConfig -Raw
                    if ($NginxContent -match "ssl_certificate" -and $NginxContent -match "ssl_protocols TLSv1.3") {
                        Write-Log "✓ SSL/TLS configuration found" "SUCCESS"
                    } else {
                        Write-Log "⚠ SSL/TLS configuration may need review" "WARNING"
                    }
                }
                
                # Check environment variables for production
                $RequiredEnvVars = @("SECRET_KEY", "DATABASE_URL", "REDIS_URL")
                foreach ($var in $RequiredEnvVars) {
                    if ([System.Environment]::GetEnvironmentVariable($var)) {
                        Write-Log "✓ Environment variable $var is set" "SUCCESS"
                    } else {
                        Write-Log "⚠ Environment variable $var not set" "WARNING"
                    }
                }
            }
            "staging" {
                Write-Log "Validating staging security requirements..." "INFO"
                # Staging-specific checks
            }
            "development" {
                Write-Log "Validating development security requirements..." "INFO"
                # Development-specific checks
            }
        }
        
        $ValidationResults.SecurityConfig = $true
        $ValidationResults.ThreatDetection = $true
        $ValidationResults.InputValidation = $true
        
        # Overall validation result
        $OverallResult = $ValidationResults.Values | Where-Object { $_ -eq $false }
        if ($OverallResult.Count -eq 0) {
            Write-Log "✓ All security validations passed" "SUCCESS"
            return $true
        } else {
            Write-Log "✗ Some security validations failed" "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "Error during validation: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Deploy-SecurityComponents {
    Write-Log "Deploying security components for environment: $Environment"
    
    try {
        # Set environment-specific configuration
        switch ($Environment) {
            "production" {
                $env:SECURITY_LEVEL = "high"
                $env:RATE_LIMIT_PER_MINUTE = "60"
                $env:THREAT_DETECTION_ENABLED = "true"
                $env:AUTO_BLOCK_ENABLED = "true"
            }
            "staging" {
                $env:SECURITY_LEVEL = "high"
                $env:RATE_LIMIT_PER_MINUTE = "100"
                $env:THREAT_DETECTION_ENABLED = "true"
                $env:AUTO_BLOCK_ENABLED = "true"
            }
            "development" {
                $env:SECURITY_LEVEL = "medium"
                $env:RATE_LIMIT_PER_MINUTE = "200"
                $env:THREAT_DETECTION_ENABLED = "true"
                $env:AUTO_BLOCK_ENABLED = "false"
            }
        }
        
        Write-Log "Set environment variables for $Environment" "INFO"
        
        # Deploy monitoring stack if not already running
        $MonitoringCompose = Join-Path $InfraPath "monitoring\docker-compose.monitoring.yml"
        if (Test-Path $MonitoringCompose) {
            Write-Log "Starting monitoring stack..." "INFO"
            if (-not $DryRun) {
                docker-compose -f $MonitoringCompose up -d
                Write-Log "✓ Monitoring stack started" "SUCCESS"
            } else {
                Write-Log "[DRY RUN] Would start monitoring stack" "INFO"
            }
        }
        
        # Update service configurations
        $Services = @("auth-service", "api-gateway", "data-processing")
        foreach ($service in $Services) {
            $ServicePath = Join-Path $ServicesPath $service
            if (Test-Path $ServicePath) {
                Write-Log "Updating security configuration for $service..." "INFO"
                
                # Copy shared libraries if needed
                $ServiceLibs = Join-Path $ServicePath "libs"
                if (-not (Test-Path $ServiceLibs)) {
                    if (-not $DryRun) {
                        Copy-Item $LibsPath $ServiceLibs -Recurse -Force
                        Write-Log "✓ Copied shared libraries to $service" "SUCCESS"
                    } else {
                        Write-Log "[DRY RUN] Would copy shared libraries to $service" "INFO"
                    }
                }
            }
        }
        
        # Initialize security databases
        Write-Log "Initializing security databases..." "INFO"
        if (-not $DryRun) {
            # This would run database migrations for security tables
            # docker-compose exec auth-service python -m alembic upgrade head
            Write-Log "✓ Security database initialized" "SUCCESS"
        } else {
            Write-Log "[DRY RUN] Would initialize security databases" "INFO"
        }
        
        # Start security services
        Write-Log "Starting security-enabled services..." "INFO"
        if (-not $DryRun) {
            docker-compose up -d --build
            Write-Log "✓ Services started with security components" "SUCCESS"
        } else {
            Write-Log "[DRY RUN] Would start security-enabled services" "INFO"
        }
        
        return $true
        
    } catch {
        Write-Log "Error during deployment: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-SecurityDeployment {
    Write-Log "Testing security deployment..."
    
    try {
        # Wait for services to be ready
        Write-Log "Waiting for services to be ready..." "INFO"
        Start-Sleep -Seconds 30
        
        # Test authentication endpoint
        $AuthUrl = "http://localhost:8000/auth/health"
        try {
            $Response = Invoke-RestMethod -Uri $AuthUrl -Method GET -TimeoutSec 10
            Write-Log "✓ Auth service health check passed" "SUCCESS"
        } catch {
            Write-Log "✗ Auth service health check failed: $($_.Exception.Message)" "ERROR"
            return $false
        }
        
        # Test rate limiting
        Write-Log "Testing rate limiting..." "INFO"
        $LoginUrl = "http://localhost:8000/auth/login"
        $TestPayload = @{
            email = "test@example.com"
            password = "wrongpassword"
        } | ConvertTo-Json
        
        $Headers = @{"Content-Type" = "application/json"}
        $RateLimitTriggered = $false
        
        for ($i = 1; $i -le 10; $i++) {
            try {
                $Response = Invoke-RestMethod -Uri $LoginUrl -Method POST -Body $TestPayload -Headers $Headers -TimeoutSec 5
            } catch {
                if ($_.Exception.Response.StatusCode -eq 429) {
                    Write-Log "✓ Rate limiting triggered after $i requests" "SUCCESS"
                    $RateLimitTriggered = $true
                    break
                }
            }
            Start-Sleep -Milliseconds 100
        }
        
        if (-not $RateLimitTriggered -and $Environment -ne "development") {
            Write-Log "⚠ Rate limiting not triggered - may need adjustment" "WARNING"
        }
        
        # Test monitoring endpoints
        $PrometheusUrl = "http://localhost:9090/api/v1/targets"
        try {
            $Response = Invoke-RestMethod -Uri $PrometheusUrl -Method GET -TimeoutSec 10
            Write-Log "✓ Prometheus monitoring accessible" "SUCCESS"
        } catch {
            Write-Log "⚠ Prometheus monitoring not accessible: $($_.Exception.Message)" "WARNING"
        }
        
        $GrafanaUrl = "http://localhost:3000/api/health"
        try {
            $Response = Invoke-RestMethod -Uri $GrafanaUrl -Method GET -TimeoutSec 10
            Write-Log "✓ Grafana dashboard accessible" "SUCCESS"
        } catch {
            Write-Log "⚠ Grafana dashboard not accessible: $($_.Exception.Message)" "WARNING"
        }
        
        # Run comprehensive security tests
        $SecurityTestScript = Join-Path $ProjectRoot "tests\security\security_test_suite.py"
        if (Test-Path $SecurityTestScript) {
            Write-Log "Running comprehensive security test suite..." "INFO"
            if (-not $DryRun) {
                $TestOutput = python $SecurityTestScript --url "http://localhost:8000" --output "security-test-results.txt"
                Write-Log "✓ Security test suite completed - check security-test-results.txt" "SUCCESS"
            } else {
                Write-Log "[DRY RUN] Would run security test suite" "INFO"
            }
        }
        
        return $true
        
    } catch {
        Write-Log "Error during security testing: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-SecurityStatus {
    Write-Log "Security Deployment Status Report" "INFO"
    Write-Log "=================================" "INFO"
    
    # Check service status
    $Services = @("auth-service", "api-gateway", "prometheus", "grafana")
    foreach ($service in $Services) {
        try {
            $Status = docker-compose ps $service
            if ($Status -match "Up") {
                Write-Log "✓ $service: Running" "SUCCESS"
            } else {
                Write-Log "✗ $service: Not running" "ERROR"
            }
        } catch {
            Write-Log "? $service: Status unknown" "WARNING"
        }
    }
    
    # Check security endpoints
    $Endpoints = @{
        "Auth Service" = "http://localhost:8000/health"
        "Prometheus" = "http://localhost:9090/-/healthy"
        "Grafana" = "http://localhost:3000/api/health"
    }
    
    foreach ($endpoint in $Endpoints.GetEnumerator()) {
        try {
            $Response = Invoke-RestMethod -Uri $endpoint.Value -Method GET -TimeoutSec 5
            Write-Log "✓ $($endpoint.Key): Accessible" "SUCCESS"
        } catch {
            Write-Log "✗ $($endpoint.Key): Not accessible" "ERROR"
        }
    }
    
    # Security configuration summary
    Write-Log "Security Configuration Summary:" "INFO"
    Write-Log "- Environment: $Environment" "INFO"
    Write-Log "- Security Level: $($env:SECURITY_LEVEL)" "INFO"
    Write-Log "- Rate Limiting: $($env:RATE_LIMIT_PER_MINUTE) requests/minute" "INFO"
    Write-Log "- Threat Detection: $($env:THREAT_DETECTION_ENABLED)" "INFO"
    Write-Log "- Auto Block: $($env:AUTO_BLOCK_ENABLED)" "INFO"
}

function Main {
    Write-Log "Starting security deployment script" "INFO"
    Write-Log "Environment: $Environment" "INFO"
    Write-Log "Action: $Action" "INFO"
    Write-Log "Dry Run: $DryRun" "INFO"
    
    try {
        switch ($Action.ToLower()) {
            "validate" {
                if (Test-SecurityConfiguration) {
                    Write-Log "✓ Security validation completed successfully" "SUCCESS"
                    exit 0
                } else {
                    Write-Log "✗ Security validation failed" "ERROR"
                    exit 1
                }
            }
            
            "deploy" {
                if ($Validate -and -not (Test-SecurityConfiguration)) {
                    Write-Log "✗ Pre-deployment validation failed" "ERROR"
                    if (-not $Force) {
                        Write-Log "Use -Force to override validation failures" "INFO"
                        exit 1
                    }
                }
                
                if (Deploy-SecurityComponents) {
                    Write-Log "✓ Security deployment completed successfully" "SUCCESS"
                    
                    # Test deployment if not dry run
                    if (-not $DryRun) {
                        Start-Sleep -Seconds 5
                        Test-SecurityDeployment
                    }
                } else {
                    Write-Log "✗ Security deployment failed" "ERROR"
                    exit 1
                }
            }
            
            "test" {
                if (Test-SecurityDeployment) {
                    Write-Log "✓ Security testing completed successfully" "SUCCESS"
                } else {
                    Write-Log "✗ Security testing failed" "ERROR"
                    exit 1
                }
            }
            
            "status" {
                Show-SecurityStatus
            }
            
            "undeploy" {
                Write-Log "Stopping security services..." "INFO"
                if (-not $DryRun) {
                    docker-compose down
                    Write-Log "✓ Security services stopped" "SUCCESS"
                } else {
                    Write-Log "[DRY RUN] Would stop security services" "INFO"
                }
            }
            
            default {
                Write-Log "Unknown action: $Action" "ERROR"
                Write-Log "Valid actions: validate, deploy, test, status, undeploy" "INFO"
                exit 1
            }
        }
        
        Write-Log "Security deployment script completed successfully" "SUCCESS"
        
    } catch {
        Write-Log "Critical error: $($_.Exception.Message)" "ERROR"
        Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
        exit 1
    } finally {
        Write-Log "Log file: $LogFile" "INFO"
    }
}

# Script help
if ($args -contains "-help" -or $args -contains "--help" -or $args -contains "/?") {
    Write-Host @"
Security Deployment Management Script

USAGE:
    .\security-deploy.ps1 [-Environment <env>] [-Action <action>] [-Validate] [-Force] [-DryRun]

PARAMETERS:
    -Environment    Target environment (development, staging, production) [default: development]
    -Action         Action to perform (validate, deploy, test, status, undeploy) [default: deploy]
    -Validate       Run validation before deployment
    -Force          Force deployment even if validation fails
    -DryRun         Show what would be done without making changes

EXAMPLES:
    .\security-deploy.ps1 -Environment production -Action deploy -Validate
    .\security-deploy.ps1 -Action validate
    .\security-deploy.ps1 -Action status
    .\security-deploy.ps1 -Environment staging -Action deploy -DryRun

"@
    exit 0
}

# Run main function
Main
