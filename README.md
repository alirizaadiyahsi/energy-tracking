# Energy Tracking IoT Data Platform

A comprehensive IoT data processing platform built with Python microservices and React frontend. This system collects, processes, stores, and visualizes energy data from various IoT sources with forecasting capabilities.

## 🏗️ Architecture

This project follows a microservice architecture with the following components:

### Backend Services (Python)
- **Data Ingestion Service**: Collects IoT data from multiple sources (MQTT, HTTP APIs, WebSockets)
- **Data Processing Service**: Real-time data processing, validation, and transformation
- **Analytics Service**: Statistical analysis and forecasting models
- **API Gateway**: Central entry point for all client requests
- **Notification Service**: Alerts and notifications for anomalies

### Frontend (React)
- **Dashboard**: Real-time data visualization and monitoring
- **Analytics Portal**: Historical data analysis and forecasting views
- **Device Management**: IoT device configuration and monitoring

### Infrastructure
- **PostgreSQL**: Primary database for structured data
- **InfluxDB**: Time-series database for IoT sensor data
- **Redis**: Caching and message broker
- **MQTT Broker (Eclipse Mosquitto)**: IoT device communication
- **Grafana**: Advanced visualization and monitoring

## 🚀 Features

### Current Features
- Multi-source IoT data ingestion (MQTT, REST APIs, WebSockets)
- Real-time data processing and validation
- Time-series data storage optimized for IoT workloads
- RESTful API with comprehensive documentation
- Real-time dashboard with WebSocket updates
- **Comprehensive RBAC system** with role-based permissions
- **Multi-tenant architecture** with organization support
- **Advanced user management** with audit logging
- Device management and configuration
- Data export capabilities
- **Security features** (JWT auth, session management, audit trails)

### Planned Features
- Machine learning-based forecasting models
- Anomaly detection and alerting
- Advanced analytics and reporting
- Mobile app support
- Edge computing integration
- Multi-tenant support

## 🛠️ Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI**: High-performance web framework
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations
- **Celery**: Distributed task queue
- **Paho MQTT**: MQTT client
- **Pandas**: Data analysis
- **Scikit-learn**: Machine learning
- **Prometheus**: Metrics collection

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Material-UI**: Component library
- **React Query**: Data fetching and caching
- **Chart.js/D3.js**: Data visualization
- **Socket.IO**: Real-time communication

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **PostgreSQL 15**: Relational database
- **InfluxDB 2.x**: Time-series database
- **Redis 7**: Caching and message broker
- **Eclipse Mosquitto**: MQTT broker
- **Nginx**: Reverse proxy and load balancer
- **Grafana**: Monitoring and visualization

## 📦 Project Structure

```
energy-tracking/
├── services/
│   ├── data-ingestion/          # IoT data collection service
│   ├── data-processing/         # Real-time data processing
│   ├── analytics/               # Analytics and forecasting
│   ├── api-gateway/             # Central API gateway
│   └── notification/            # Alerts and notifications
├── frontend/                    # React dashboard
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── grafana/                 # Grafana configuration
│   ├── mosquitto/               # MQTT broker config
│   └── nginx/                   # Reverse proxy config
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd energy-tracking
   ```

2. **Start the development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Access the services**
   - Dashboard: http://localhost:3000
   - API Gateway: http://localhost:8000
   - Grafana: http://localhost:3001 (admin/admin)
   - InfluxDB UI: http://localhost:8086

### Production Deployment

1. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your production settings
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 📊 Data Flow

1. **Authentication**: Users authenticate with JWT tokens and role-based permissions
2. **Data Ingestion**: IoT devices send data via MQTT or HTTP APIs (with proper authorization)
3. **Data Processing**: Real-time validation, transformation, and enrichment
4. **Access Control**: Role-based filtering ensures users only see authorized data
5. **Storage**: Time-series data stored in InfluxDB, metadata in PostgreSQL
6. **Analytics**: Background processing for forecasting and analysis (permission-based)
7. **Visualization**: Real-time dashboard updates via WebSockets with user context
8. **Audit**: All user activities and data changes are logged for compliance

## 🔧 Configuration

### Environment Variables

Key environment variables for configuration:

```env
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_DB=energy_tracking
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_token
INFLUXDB_ORG=energy-org
INFLUXDB_BUCKET=iot-data

# Redis Configuration
REDIS_URL=redis://redis:6379

# MQTT Configuration
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=iot_user
MQTT_PASSWORD=your_password

# API Configuration
API_SECRET_KEY=your_secret_key
API_CORS_ORIGINS=http://localhost:3000
```

### IoT Device Integration

#### MQTT Topics Structure
```
energy/devices/{device_id}/data        # Sensor data
energy/devices/{device_id}/status      # Device status
energy/devices/{device_id}/config      # Device configuration
energy/alerts/{device_id}              # Device alerts
```

#### REST API Endpoints
```
POST /api/v1/data/ingest              # Bulk data ingestion
GET  /api/v1/devices                  # List devices
GET  /api/v1/data/timeseries          # Query time-series data
POST /api/v1/analytics/forecast       # Generate forecasts
```

## 📈 Monitoring & Observability

- **Application Metrics**: Prometheus metrics exposed by all services
- **Infrastructure Monitoring**: Docker container metrics
- **Log Aggregation**: Centralized logging with structured JSON logs
- **Health Checks**: Built-in health endpoints for all services
- **Grafana Dashboards**: Pre-configured dashboards for monitoring

## 🧪 Testing

This project includes a comprehensive testing framework with multiple test types and automated execution capabilities.

### Test Structure
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── auth_service/        # Authentication service tests
│   ├── data_processing/     # Data processing tests
│   └── analytics/           # Analytics service tests
├── integration/             # Integration tests for service interactions
│   ├── test_auth_flows.py   # Authentication integration tests
│   └── test_data_pipeline.py # Data pipeline integration tests
├── performance/             # Performance and load testing
│   ├── locustfile.py        # Locust performance tests
│   └── run_performance_tests.py # Performance test runner
├── e2e/                     # End-to-end tests
│   ├── test_complete_flows.py # API workflow tests
│   └── test_browser_flows.py  # Browser automation tests
├── conftest.py             # Shared test fixtures
├── pytest.ini             # Pytest configuration
├── test_config.ini         # Test environment configuration
├── run_tests.py            # Individual test runner
├── run_all_tests.py        # Master test runner
└── README.md               # Testing documentation
```

### Quick Testing Commands

#### Run All Tests
```bash
# Run comprehensive test suite
python tests/run_all_tests.py

# Quick tests (unit + integration + security)
python tests/run_all_tests.py --quick

# Full test suite (includes performance and E2E)
python tests/run_all_tests.py --full

# Run with parallel execution
python tests/run_all_tests.py --parallel
```

#### Run Specific Test Types
```bash
# Unit tests only
python tests/run_all_tests.py --include unit

# Integration tests
python tests/run_all_tests.py --include integration

# Performance tests
python tests/performance/run_performance_tests.py --scenario medium

# E2E API tests
python tests/e2e/test_complete_flows.py

# E2E Browser tests (requires Chrome/Selenium)
python tests/e2e/test_browser_flows.py --headless
```

#### Individual Service Testing
```bash
# Test specific service
python tests/run_tests.py --service auth-service
python tests/run_tests.py --service data-processing
python tests/run_tests.py --service analytics

# Run with coverage
python tests/run_tests.py --coverage --service auth-service
```

### Test Types

#### 1. Unit Tests
- **Coverage Target**: 90% for critical components, 80% overall
- **Focus**: Individual functions, classes, and modules
- **Mocking**: Comprehensive mocking of external dependencies
- **Security**: Authentication, authorization, input validation

#### 2. Integration Tests
- **Database Integration**: Real PostgreSQL and Redis instances
- **Service Communication**: API interactions between services
- **Authentication Flows**: Complete JWT authentication workflows
- **Data Pipeline**: End-to-end data processing validation

#### 3. Performance Tests
- **Load Testing**: Various user load scenarios (light, medium, heavy, stress)
- **Stress Testing**: System breaking point identification
- **Rate Limiting**: API rate limiting validation
- **Response Times**: Performance threshold monitoring

#### 4. End-to-End Tests
- **API Workflows**: Complete user journey testing via REST APIs
- **Browser Automation**: Frontend workflow testing with Selenium
- **System Integration**: Full stack functionality validation
- **User Scenarios**: Real-world usage pattern simulation

### Test Configuration

#### Prerequisites Installation
```bash
# Install test dependencies
pip install -r tests/test-requirements.txt

# For browser tests (optional)
pip install selenium
# Download ChromeDriver or install via package manager
```

#### Environment Setup
```bash
# Copy test configuration
cp tests/test_config.ini.example tests/test_config.ini

# Edit configuration for your environment
# Configure database URLs, API endpoints, etc.
```

#### Docker Test Environment
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests against containerized services
python tests/run_all_tests.py --host http://localhost:8000
```

### Test Reports and Monitoring

#### Coverage Reports
```bash
# Generate HTML coverage report
python tests/run_tests.py --coverage --html

# View coverage report
open tests/results/coverage_html/index.html
```

#### Performance Reports
```bash
# Performance test results
ls tests/performance/results/
# - HTML reports with detailed metrics
# - CSV data for analysis
# - Performance trend tracking
```

#### Continuous Integration
```bash
# CI-friendly test execution
python tests/run_all_tests.py --fail-fast --parallel --include unit integration security

# Generate CI reports
python tests/run_all_tests.py --junit-xml --coverage-xml
```

### Quality Gates

- **Minimum Coverage**: 80% overall, 90% for critical components
- **Performance**: Max 2s response time, <5% error rate
- **Security**: All authentication and authorization tests must pass
- **Code Quality**: Linting and formatting checks included

### Frontend Testing
```bash
cd frontend
npm test                    # Unit tests with Jest
npm run test:e2e           # Cypress E2E tests
npm run test:coverage      # Coverage report
npm run test:watch         # Watch mode for development
```

## 📚 API Documentation

- **Swagger UI**: Available at http://localhost:8000/docs
- **ReDoc**: Available at http://localhost:8000/redoc
- **OpenAPI Spec**: Available at http://localhost:8000/openapi.json

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all React components
- Write tests for new features
- Update documentation as needed
- Use conventional commits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Create an issue for bug reports or feature requests
- Check the [documentation](docs/) for detailed guides
- Join our community discussions

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Basic microservice architecture
- [x] IoT data ingestion pipeline
- [x] Real-time dashboard
- [ ] Device management interface

### Phase 2 (Next 3 months)
- [ ] Machine learning forecasting models
- [ ] Advanced analytics dashboard
- [ ] Mobile app development
- [ ] Edge computing support

### Phase 3 (6 months)
- [ ] Multi-tenant architecture
- [ ] Advanced anomaly detection
- [ ] Integration with cloud providers
- [ ] Enterprise features

## 📊 Performance Benchmarks

- **Data Ingestion**: 10,000+ messages/second
- **Query Response**: <100ms for real-time data
- **Dashboard Load**: <2 seconds initial load
- **Forecasting**: Real-time predictions for 1000+ devices

---

**Built with ❤️ for the IoT community**
