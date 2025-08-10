# Copilot Instructions - Energy Tracking IoT Platform

## 🎯 Project Overview
This is an **AI-generated microservices platform** for IoT energy data processing with a React frontend. The system follows distributed architecture patterns with 7 specialized Python services orchestrated via Docker Compose.

## 🏗️ Architecture Essentials

### Service Communication Pattern
- **API Gateway** (`services/api-gateway/`) is the single entry point (port 8000) 
- All external requests route through gateway, which proxies to internal services
- Internal services communicate via HTTP using `httpx.AsyncClient` instances
- Services use shared libraries from `libs/` for database, messaging, and monitoring

### Database Strategy
- **PostgreSQL**: Structured data (users, devices, metadata) via SQLAlchemy async
- **InfluxDB**: Time-series IoT data with retention policies
- **Redis**: Caching, sessions, and Celery task queue
- Use `libs/common/database.py` BaseRepository pattern for consistent CRUD operations

### Authentication & Authorization
- JWT-based auth with role-based access control (RBAC)
- Multi-tenant organization support with hierarchical permissions
- Session management in Redis with audit logging
- Always use `core.auth.verify_token()` and `get_current_user()` dependencies

## 🛠️ Development Workflows

### Environment Setup (Windows)
```powershell
# Development stack (with hot reload)
docker-compose -f docker-compose.dev.yml up -d

# Production stack  
docker-compose -f docker-compose.prod.yml up -d

# Health checks
.\scripts\health-check.ps1  # Comprehensive system status
```

### Service Development Pattern
Each service follows this structure:
- `main.py`: FastAPI app with lifespan management and middleware
- `api/routes.py`: Route definitions
- `core/`: Config, database, auth utilities
- `services/`: Business logic layer
- `models/`: SQLAlchemy models
- `schemas/`: Pydantic validation schemas

### Testing Strategy
- Use `tests/conftest.py` for shared fixtures and test containers
- Tests are organized: `unit/`, `integration/`, `e2e/`, `performance/`, `security/`
- Run with: `make test` or `python -m pytest tests/`
- **Write unit and integration tests for main features only** - skip basic CRUD operations
- Focus on business logic, data processing pipelines, and complex integrations

## 🐙 GitHub Integration

### Issue Management
- **GitHub CLI is available** - use `gh` commands for issue creation
- When creating tickets: `gh issue create --title "Title" --body "Description" --label "bug,enhancement"`
- **Always create missing labels first**: `gh label create "new-label" --description "Label description" --color "color-hex"`
- Issues are tracked in GitHub, not as project documents

### Repository Context
- Project hosted on GitHub: `alirizaadiyahsi/energy-tracking`
- Use GitHub features for collaboration, not local documentation files
- Reference issues in commits: `Fix #123: Description`

## 📝 Code Conventions

### Data Management
- **No hard-coded mock data** - use environment variables, configuration files, or dynamic data generation
- Use `services/iot-mock/` for realistic device simulation with configurable parameters
- Store configuration in `.env` files or `core/config.py` settings classes

### Python Services
- FastAPI with async/await patterns throughout
- Pydantic schemas for validation with `from_attributes=True`
- SQLAlchemy 2.0 async syntax with `AsyncSession`
- Error handling via custom exceptions in `libs/common/exceptions.py`
- Logging with structured format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Frontend (React + TypeScript)
- Vite build system with hot reload
- React Query for server state management
- Tailwind CSS for styling with custom components in `src/components/`
- React Hook Form with Zod validation
- Chart.js and Recharts for data visualization

### Docker Patterns
- Multi-stage builds for production optimization
- Health checks on all services using `/health` endpoints
- Environment-specific compose files with override patterns
- Shared networks and volumes for service communication

## 🔧 Key Integration Points

### MQTT Communication
- Eclipse Mosquitto broker for IoT device communication
- Use `libs/messaging/` for MQTT client abstractions
- Device data flows: MQTT → data-ingestion → data-processing → InfluxDB

### Monitoring Stack
- Prometheus metrics collection with custom exporters
- Grafana dashboards in `infrastructure/grafana/dashboards/`
- Centralized logging via `infrastructure/logging/logging.yaml`
- Alert rules in `infrastructure/monitoring/alert_rules.yml`

### Data Processing Pipeline
1. IoT devices → MQTT/HTTP → data-ingestion service
2. data-ingestion → validates → queues via Celery → Redis
3. data-processing → transforms → stores in InfluxDB/PostgreSQL
4. analytics service → ML processing → forecasting/anomaly detection
5. Frontend → WebSocket updates → real-time dashboard

## 🚨 Critical Patterns

### Error Handling
Always use structured exceptions from `libs/common/exceptions.py`:
```python
from libs.common.exceptions import ResourceNotFoundError, ResourceConflictError
raise ResourceNotFoundError("Device", device_id)
```

### Database Transactions
Use repository pattern with proper async context:
```python
async with AsyncSession() as session:
    repo = BaseRepository(session, Device)
    device = await repo.get_by_id_or_404(device_id)
```

### Service Communication
Internal service calls use consistent HTTP client pattern:
```python
async with httpx.AsyncClient() as client:
    response = await client.post(f"{SERVICE_URL}/endpoint", json=data)
```

### Configuration Management
All services use `core/config.py` with Pydantic Settings:
```python
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    class Config:
        env_file = ".env"
```

## 🚀 Quick Commands

```powershell
# Start development environment
make dev

# Run all tests
make test

# Check system health
.\scripts\health-check.ps1

# Rebuild and restart all services
.\scripts\rebuild-all.ps1

# View service logs
docker-compose logs -f [service-name]
```

## 📁 Key Files to Understand
- `docker-compose.yml` - Service orchestration and networking
- `libs/common/database.py` - Shared database patterns
- `services/api-gateway/main.py` - Central routing and middleware
- `tests/conftest.py` - Test fixtures and utilities
- `infrastructure/monitoring/` - Observability configuration
