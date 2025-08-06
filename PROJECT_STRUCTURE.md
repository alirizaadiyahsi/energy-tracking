# Project Structure Documentation
# ===============================

This document describes the complete structure of the Energy Tracking IoT Platform.

## 📁 Root Directory Structure

```
energy-tracking/
├── 📄 README.md                    # Main project documentation
├── 📄 .gitignore                   # Git ignore patterns
├── 📄 .env.example                 # Environment variables template
├── 📄 Makefile                     # Build automation (Linux/macOS)
├── 📄 quick-start.ps1              # Quick start script (Windows)
├── 🐳 docker-compose.yml           # Main Docker Compose configuration
├── 🐳 docker-compose.dev.yml       # Development environment
├── 🐳 docker-compose.prod.yml      # Production environment
│
├── 📁 services/                    # Microservices
│   ├── 📁 api-gateway/             # Central API Gateway
│   │   ├── 📁 app/
│   │   │   ├── 📁 api/             # API routes
│   │   │   ├── 📁 core/            # Core functionality
│   │   │   ├── 📁 models/          # Data models
│   │   │   ├── 📁 schemas/         # Pydantic schemas
│   │   │   ├── 📁 services/        # Business logic
│   │   │   └── 📄 main.py          # FastAPI application
│   │   ├── 📁 tests/               # Unit tests
│   │   ├── 📄 Dockerfile           # Production image
│   │   ├── 📄 Dockerfile.dev       # Development image
│   │   ├── 📄 requirements.txt     # Python dependencies
│   │   └── 📄 alembic.ini          # Database migrations
│   │
│   ├── 📁 data-ingestion/          # IoT Data Collection Service
│   │   ├── 📁 app/
│   │   │   ├── 📁 collectors/      # Data collectors
│   │   │   ├── 📁 processors/      # Data processors
│   │   │   ├── 📁 models/          # Data models
│   │   │   └── 📄 main.py          # Service entry point
│   │   ├── 📁 tests/
│   │   ├── 📄 Dockerfile
│   │   ├── 📄 Dockerfile.dev
│   │   └── 📄 requirements.txt
│   │
│   ├── 📁 data-processing/         # Real-time Data Processing
│   │   ├── 📁 app/
│   │   │   ├── 📁 processors/      # Data processors
│   │   │   ├── 📁 validators/      # Data validation
│   │   │   ├── 📁 transformers/    # Data transformation
│   │   │   ├── 📁 celery_app/      # Celery configuration
│   │   │   └── 📄 main.py
│   │   ├── 📁 tests/
│   │   ├── 📄 Dockerfile
│   │   ├── 📄 Dockerfile.dev
│   │   └── 📄 requirements.txt
│   │
│   ├── 📁 analytics/               # Analytics and Forecasting
│   │   ├── 📁 app/
│   │   │   ├── 📁 ml_models/       # Machine learning models
│   │   │   ├── 📁 forecasting/     # Forecasting algorithms
│   │   │   ├── 📁 statistics/      # Statistical analysis
│   │   │   └── 📄 main.py
│   │   ├── 📁 notebooks/           # Jupyter notebooks
│   │   ├── 📁 models/              # Trained ML models
│   │   ├── 📁 tests/
│   │   ├── 📄 Dockerfile
│   │   ├── 📄 Dockerfile.dev
│   │   └── 📄 requirements.txt
│   │
│   └── 📁 notification/            # Notification Service
│       ├── 📁 app/
│       │   ├── 📁 providers/       # Notification providers
│       │   ├── 📁 templates/       # Message templates
│       │   └── 📄 main.py
│       ├── 📁 tests/
│       ├── 📄 Dockerfile
│       ├── 📄 Dockerfile.dev
│       └── 📄 requirements.txt
│
├── 📁 frontend/                    # React Dashboard
│   ├── 📁 public/                  # Static assets
│   ├── 📁 src/
│   │   ├── 📁 components/          # React components
│   │   │   ├── 📁 common/          # Shared components
│   │   │   ├── 📁 charts/          # Chart components
│   │   │   ├── 📁 forms/           # Form components
│   │   │   └── 📁 layout/          # Layout components
│   │   ├── 📁 pages/               # Page components
│   │   │   ├── 📁 dashboard/       # Dashboard pages
│   │   │   ├── 📁 devices/         # Device management
│   │   │   ├── 📁 analytics/       # Analytics pages
│   │   │   └── 📁 settings/        # Settings pages
│   │   ├── 📁 services/            # API services
│   │   ├── 📁 hooks/               # Custom React hooks
│   │   ├── 📁 utils/               # Utility functions
│   │   ├── 📁 types/               # TypeScript types
│   │   ├── 📁 store/               # State management
│   │   └── 📄 App.tsx              # Main App component
│   ├── 📄 package.json             # Node.js dependencies
│   ├── 📄 tsconfig.json            # TypeScript configuration
│   ├── 📄 Dockerfile               # Production image
│   └── 📄 Dockerfile.dev           # Development image
│
├── 📁 infrastructure/              # Infrastructure Configuration
│   ├── 📁 grafana/                 # Grafana Configuration
│   │   ├── 📁 dashboards/          # Pre-built dashboards
│   │   └── 📁 provisioning/        # Grafana provisioning
│   │       ├── 📁 dashboards/      # Dashboard configs
│   │       └── 📁 datasources/     # Data source configs
│   │
│   ├── 📁 mosquitto/               # MQTT Broker Configuration
│   │   ├── 📄 mosquitto.conf       # Main configuration
│   │   ├── 📄 mosquitto.dev.conf   # Development config
│   │   ├── 📄 mosquitto.prod.conf  # Production config
│   │   ├── 📄 passwd               # MQTT user passwords
│   │   └── 📄 acl.conf             # Access control list
│   │
│   ├── 📁 nginx/                   # Nginx Configuration
│   │   ├── 📄 nginx.conf           # Main Nginx config
│   │   ├── 📄 nginx.prod.conf      # Production config
│   │   └── 📁 conf.d/              # Additional configurations
│   │
│   └── 📁 prometheus/              # Prometheus Configuration
│       ├── 📄 prometheus.yml       # Prometheus config
│       └── 📁 rules/               # Alert rules
│
├── 📁 scripts/                     # Utility Scripts
│   ├── 📄 init-db.sql              # Database initialization
│   ├── 📁 backup/                  # Backup scripts
│   ├── 📁 deployment/              # Deployment scripts
│   ├── 📁 data-generator/          # Test data generator
│   │   ├── 📄 generator.py         # Data generation script
│   │   ├── 📄 Dockerfile           # Generator container
│   │   └── 📄 requirements.txt     # Generator dependencies
│   └── 📁 monitoring/              # Monitoring scripts
│
├── 📁 docs/                        # Documentation
│   ├── 📄 API.md                   # API documentation
│   ├── 📄 DEPLOYMENT.md            # Deployment guide
│   ├── 📄 DEVELOPMENT.md           # Development guide
│   ├── 📄 ARCHITECTURE.md          # Architecture overview
│   └── 📁 images/                  # Documentation images
│
├── 📁 tests/                       # Integration Tests
│   ├── 📁 integration/             # Integration test suites
│   ├── 📁 e2e/                     # End-to-end tests
│   └── 📁 performance/             # Performance tests
│
├── 📁 k8s/                         # Kubernetes Manifests (Optional)
│   ├── 📁 base/                    # Base Kubernetes configs
│   ├── 📁 overlays/                # Environment-specific overlays
│   │   ├── 📁 dev/                 # Development K8s configs
│   │   └── 📁 prod/                # Production K8s configs
│   └── 📄 kustomization.yaml       # Kustomize configuration
│
└── 📁 .github/                     # GitHub Configuration
    ├── 📁 workflows/               # GitHub Actions
    │   ├── 📄 ci.yml               # Continuous Integration
    │   ├── 📄 cd.yml               # Continuous Deployment
    │   └── 📄 security.yml         # Security scanning
    └── 📄 dependabot.yml           # Dependency updates
```

## 🔧 Service Details

### API Gateway (`/services/api-gateway/`)
- **Purpose**: Central entry point for all client requests
- **Technology**: FastAPI, SQLAlchemy, Alembic
- **Responsibilities**:
  - Request routing and load balancing
  - Authentication and authorization
  - Rate limiting and caching
  - API documentation generation

### Data Ingestion (`/services/data-ingestion/`)
- **Purpose**: Collect IoT data from multiple sources
- **Technology**: Python, Paho MQTT, AsyncIO
- **Responsibilities**:
  - MQTT message handling
  - HTTP API data collection
  - WebSocket connections
  - Data validation and preprocessing

### Data Processing (`/services/data-processing/`)
- **Purpose**: Real-time data processing and transformation
- **Technology**: Celery, Pandas, Redis
- **Responsibilities**:
  - Real-time data validation
  - Data transformation and enrichment
  - Anomaly detection
  - Background task processing

### Analytics (`/services/analytics/`)
- **Purpose**: Advanced analytics and forecasting
- **Technology**: Scikit-learn, TensorFlow, Pandas
- **Responsibilities**:
  - Statistical analysis
  - Machine learning model training
  - Forecasting and predictions
  - Report generation

### Notification (`/services/notification/`)
- **Purpose**: Alert and notification management
- **Technology**: Celery, SMTP, Push notifications
- **Responsibilities**:
  - Email notifications
  - Push notifications
  - SMS alerts (if configured)
  - Alert escalation

## 🗄️ Database Structure

### PostgreSQL (Metadata & Configuration)
- **auth.users**: User accounts and authentication
- **energy.devices**: Device registry and configuration
- **energy.device_groups**: Device grouping and organization
- **energy.alerts**: Alert management
- **analytics.models**: ML model metadata
- **analytics.forecasts**: Forecast results

### InfluxDB (Time-Series Data)
- **iot-data**: Raw sensor measurements
- **processed-data**: Processed and aggregated data
- **alerts**: Alert events with timestamps

## 🌐 Frontend Structure

### React Application (`/frontend/`)
- **Components**: Reusable UI components
- **Pages**: Route-specific page components
- **Services**: API integration layer
- **Hooks**: Custom React hooks for state management
- **Store**: Global state management (Redux/Zustand)

## 📊 Monitoring Stack

### Grafana
- **Dashboards**: Pre-configured visualization dashboards
- **Data Sources**: InfluxDB, PostgreSQL, Prometheus
- **Alerting**: Grafana alert rules and notifications

### Prometheus (Optional)
- **Metrics Collection**: Application and infrastructure metrics
- **Alerting**: Prometheus alert rules
- **Service Discovery**: Automatic service monitoring

## 🔒 Security Considerations

### Development Environment
- Simplified authentication for ease of development
- Open MQTT broker (no authentication)
- Debug logging enabled
- CORS enabled for localhost

### Production Environment
- JWT-based authentication
- MQTT broker with SSL/TLS and authentication
- Rate limiting and security headers
- SSL/TLS encryption for all communications
- Restricted CORS origins

## 📝 Configuration Files

### Environment Variables (`.env`)
- Database credentials and connection strings
- API keys and secrets
- Service configuration parameters
- Feature flags and toggles

### Docker Compose Files
- **docker-compose.yml**: Base configuration
- **docker-compose.dev.yml**: Development overrides
- **docker-compose.prod.yml**: Production configuration

## 🚀 Getting Started

1. **Initial Setup**:
   ```bash
   # Linux/macOS
   make setup
   
   # Windows
   .\quick-start.ps1 -Setup
   ```

2. **Start Development Environment**:
   ```bash
   # Linux/macOS
   make dev
   
   # Windows
   .\quick-start.ps1 -Environment dev
   ```

3. **Access Services**:
   - Dashboard: http://localhost:3000
   - API Gateway: http://localhost:8000
   - Grafana: http://localhost:3001

## 🧪 Testing Structure

### Unit Tests
- Located in each service's `tests/` directory
- Run with pytest
- Include fixtures and mocks

### Integration Tests
- Located in `/tests/integration/`
- Test service-to-service communication
- Database integration testing

### End-to-End Tests
- Located in `/tests/e2e/`
- Full user workflow testing
- Browser automation with Playwright/Selenium

This structure provides a comprehensive foundation for a scalable IoT data processing platform with clear separation of concerns and modern development practices.
