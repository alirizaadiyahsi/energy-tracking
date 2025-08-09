# CI/CD Pipeline Documentation

## Overview

The Energy Tracking Platform uses a comprehensive CI/CD pipeline built with GitHub Actions to ensure code quality, security, and reliable deployments. The pipeline consists of multiple workflows that handle different aspects of the development lifecycle.

## Workflow Structure

### 1. Main CI Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Path filtering to run only when relevant code changes

**Jobs:**
1. **Code Quality** - ESLint, Pylint, formatting checks
2. **Unit Tests** - Matrix testing across all services
3. **Integration Tests** - API integration testing with databases
4. **Security Tests** - Basic security scans
5. **Frontend Tests** - React component and E2E testing
6. **Docker Build** - Build and test container images
7. **Test Report** - Aggregate and publish test results
8. **Quality Gate** - Final quality checks and coverage validation

**Key Features:**
- Matrix strategy for parallel service testing
- PostgreSQL and Redis services for integration tests
- Codecov integration for coverage reporting
- Artifact management for test results and reports

### 2. Performance Testing (`performance.yml`)

**Triggers:**
- Scheduled daily at 2 AM UTC
- Manual dispatch with environment selection
- Weekly comprehensive performance analysis

**Test Scenarios:**
- **Light Load** - 10 users, 2 minutes
- **Medium Load** - 50 users, 5 minutes  
- **Heavy Load** - 100 users, 10 minutes
- **Stress Test** - 200 users, 15 minutes
- **Spike Test** - Rapid user increase simulation

**Monitoring:**
- Performance threshold validation
- Trend analysis and comparison
- Automated issue creation on degradation
- Slack notifications for critical performance drops

### 3. End-to-End Testing (`e2e.yml`)

**Triggers:**
- Scheduled twice daily (6 AM and 6 PM UTC)
- Manual dispatch
- Pre-release validation

**Test Types:**
- **API Workflows** - Complete user journey testing
- **Browser Testing** - Selenium across Chrome, Firefox, Safari
- **Critical Path Validation** - Core functionality verification
- **Performance Validation** - Frontend performance metrics

**Features:**
- Screenshot capture on failures
- Video recording of test sessions
- Slack notifications for test failures
- Detailed test reports with failure analysis

### 4. Security Scanning (`security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Daily scheduled security scans
- Manual dispatch

**Security Tools:**
- **Dependency Scanning** - Safety (Python), npm audit (Node.js)
- **SAST** - Bandit (Python), ESLint Security (JavaScript)
- **Container Scanning** - Trivy, Hadolint
- **Secret Detection** - TruffleHog, GitLeaks
- **Infrastructure Scanning** - Checkov, Terrascan
- **License Compliance** - pip-licenses, license-checker

**Reporting:**
- Comprehensive security dashboard
- SARIF uploads to GitHub Security tab
- Automated issue creation for critical vulnerabilities
- Slack alerts for security incidents

### 5. Release Pipeline (`release.yml`)

**Triggers:**
- Tag creation (v*.*.*)
- Manual dispatch

**Release Process:**
1. **Pre-release Validation** - Version and changelog checks
2. **Comprehensive Testing** - All test suites execution
3. **Docker Builds** - Multi-architecture container builds
4. **Image Signing** - Cosign signature verification
5. **Staging Deployment** - Automated staging environment deployment
6. **Production Deployment** - Manual approval required
7. **Post-release Validation** - Health checks and monitoring
8. **Notifications** - Release announcements

**Features:**
- Semantic versioning validation
- Changelog generation and validation
- Container registry management
- Environment-specific deployments
- Rollback capabilities

## Configuration Files

### Environment Variables

```yaml
# Global environment variables used across workflows
PYTHON_VERSION: '3.11'
NODE_VERSION: '18'
DOCKER_REGISTRY: 'ghcr.io'
STAGING_URL: 'https://staging.energy-tracking.com'
PRODUCTION_URL: 'https://energy-tracking.com'
```

### Required Secrets

```yaml
# GitHub Repository Secrets
CODECOV_TOKEN: # Codecov.io integration token
SLACK_WEBHOOK_URL: # Slack notifications webhook
DOCKER_HUB_USERNAME: # Docker Hub username (optional)
DOCKER_HUB_TOKEN: # Docker Hub access token (optional)
STAGING_DEPLOY_KEY: # SSH key for staging deployment
PRODUCTION_DEPLOY_KEY: # SSH key for production deployment
COSIGN_PRIVATE_KEY: # Container signing private key
GITLEAKS_LICENSE: # GitLeaks Pro license (optional)
```

### Branch Protection Rules

Configure the following branch protection rules for `main` and `develop`:

```yaml
Required status checks:
- Code Quality
- Unit Tests (all matrix jobs)
- Integration Tests
- Security Tests
- Frontend Tests

Required reviews:
- 1 review required for develop
- 2 reviews required for main
- Dismiss stale reviews: true
- Require review from code owners: true

Other restrictions:
- Require branches to be up to date: true
- Require conversation resolution: true
- Include administrators: true
```

## Test Configuration

### Unit Testing

**Python Services:**
- Framework: pytest
- Coverage: pytest-cov
- Minimum coverage: 80%
- Configuration: `pytest.ini` in each service

**Frontend:**
- Framework: Vitest
- Coverage: c8
- Minimum coverage: 85%
- Configuration: `vite.config.ts`

### Integration Testing

**Database Testing:**
- PostgreSQL test database
- Redis test instance
- Automatic schema migration
- Test data seeding

**API Testing:**
- FastAPI test client
- Authentication flow testing
- Cross-service communication
- Error handling validation

### Performance Testing

**Load Testing Tool:** Locust

**Test Configuration:**
```python
# Example Locust configuration
class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://staging.energy-tracking.com"
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/dashboard")
    
    @task(1)
    def add_device(self):
        self.client.post("/api/devices", json={...})
```

**Performance Thresholds:**
- Response time 95th percentile: < 2000ms
- Error rate: < 1%
- Throughput: > 100 RPS

### E2E Testing

**Browser Matrix:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest, macOS only)

**Test Scenarios:**
- User registration and login
- Device management workflow
- Data visualization
- Settings configuration
- Analytics dashboard

## Security Configuration

### Dependency Scanning

**Python (Safety):**
```yaml
# .safety-policy.json
{
    "security": {
        "ignore-unpinned-requirements": false,
        "continue-on-vulnerability-error": false
    }
}
```

**Node.js (npm audit):**
```yaml
# package.json audit configuration
{
    "scripts": {
        "audit": "npm audit --audit-level=moderate"
    }
}
```

### Code Security (SAST)

**Bandit Configuration:**
```yaml
# .bandit
[bandit]
exclude_dirs = tests,migrations
skips = B101,B601
```

**ESLint Security:**
```json
{
    "extends": ["plugin:security/recommended"],
    "plugins": ["security", "no-secrets"]
}
```

### Container Security

**Trivy Configuration:**
```yaml
# .trivyignore
# Ignore specific CVEs that are false positives
CVE-2021-12345
```

**Hadolint Configuration:**
```yaml
# .hadolint.yaml
ignored:
  - DL3008  # Pin versions in apt get install
  - DL3009  # Delete apt cache
```

## Deployment Configuration

### Staging Environment

**Infrastructure:**
- Single-node deployment
- PostgreSQL database
- Redis cache
- NGINX reverse proxy
- SSL certificate (Let's Encrypt)

**Deployment Strategy:**
- Blue-green deployment
- Automatic database migration
- Health check validation
- Automatic rollback on failure

### Production Environment

**Infrastructure:**
- Multi-node deployment with load balancing
- PostgreSQL cluster with replication
- Redis cluster
- NGINX with high availability
- SSL certificate with auto-renewal

**Deployment Strategy:**
- Rolling deployment
- Manual approval required
- Comprehensive health checks
- Database migration with backup
- Monitoring and alerting

## Monitoring and Alerting

### Health Checks

**Application Health:**
```python
# Example health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": os.getenv("APP_VERSION"),
        "database": await check_database(),
        "redis": await check_redis()
    }
```

**Infrastructure Health:**
- CPU usage < 80%
- Memory usage < 85%
- Disk usage < 90%
- Database connections < 80% of max

### Notifications

**Slack Integration:**
- Build failures
- Deployment status
- Security alerts
- Performance degradation

**GitHub Issues:**
- Automatic issue creation for:
  - Critical security vulnerabilities
  - Performance degradation
  - Test failures in main branch

## Troubleshooting

### Common Issues

**1. Test Failures:**
```bash
# Debug test failures locally
cd services/auth-service
python -m pytest tests/ -v --tb=short

# Check test coverage
python -m pytest tests/ --cov=. --cov-report=html
```

**2. Docker Build Failures:**
```bash
# Build locally with verbose output
docker build --no-cache --progress=plain -t test-image .

# Check layer caching
docker history test-image
```

**3. Security Scan False Positives:**
```bash
# Add to .trivyignore for container scans
echo "CVE-2021-12345" >> .trivyignore

# Add to .bandit for Python code scans
echo "B101: assert_used" >> .bandit
```

**4. Performance Test Failures:**
```bash
# Run performance tests locally
pip install locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Debug Workflow Issues

**1. Check Workflow Logs:**
- Go to Actions tab in GitHub
- Select the failed workflow run
- Expand the failed job/step
- Check detailed logs and error messages

**2. Validate Workflow Syntax:**
```bash
# Use act to test workflows locally
act -n  # Dry run
act push  # Simulate push event
```

**3. Test Secret Access:**
```yaml
# Add debug step to workflow
- name: Debug Secrets
  run: |
    echo "Checking secret availability..."
    echo "CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN && 'available' || 'missing' }}"
```

## Best Practices

### Code Quality

1. **Always run tests locally** before pushing
2. **Maintain high test coverage** (>80% for backend, >85% for frontend)
3. **Follow security best practices** in code
4. **Keep dependencies updated** regularly
5. **Use semantic versioning** for releases

### CI/CD Pipeline

1. **Keep workflows fast** - optimize for parallel execution
2. **Use caching** for dependencies and build artifacts
3. **Fail fast** - put quick checks first
4. **Provide clear feedback** in notifications
5. **Monitor resource usage** and optimize as needed

### Security

1. **Never commit secrets** to the repository
2. **Regular dependency updates** for security patches
3. **Monitor security advisories** for used packages
4. **Validate all inputs** in applications
5. **Use least privilege** for service accounts

### Deployment

1. **Always test in staging** before production
2. **Use feature flags** for risky changes
3. **Have rollback plans** ready
4. **Monitor after deployments** closely
5. **Document all changes** in changelog

## Maintenance

### Regular Tasks

**Weekly:**
- Review dependency security advisories
- Check performance trends
- Update documentation
- Review and merge dependency updates

**Monthly:**
- Security audit of the CI/CD pipeline
- Performance optimization review
- Workflow efficiency analysis
- Update base images and tools

**Quarterly:**
- Complete security assessment
- Infrastructure capacity planning
- Workflow modernization
- Tool evaluation and updates

### Updating the Pipeline

1. **Test changes in feature branch** first
2. **Use workflow dispatch** for testing
3. **Monitor initial runs** closely
4. **Update documentation** accordingly
5. **Communicate changes** to the team

For more information or support, please refer to the [GitHub Actions documentation](https://docs.github.com/en/actions) or contact the DevOps team.
