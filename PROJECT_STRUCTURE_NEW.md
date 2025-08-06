# Project Structure - Energy Tracking System

## 📁 Complete Directory Structure

```
energy-tracking/
├── 📁 services/                          # Backend Microservices
│   ├── 📁 api-gateway/                   # Central API Gateway (Port 8000)
│   │   ├── 📁 api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py                 # Main routing logic
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # Authentication middleware
│   │   │   ├── config.py                 # Configuration management
│   │   │   └── database.py               # Database connections
│   │   ├── 📁 middleware/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py                # Request logging
│   │   │   └── rate_limit.py             # Rate limiting
│   │   ├── Dockerfile                    # Container configuration
│   │   ├── main.py                       # FastAPI application entry
│   │   └── requirements.txt              # Python dependencies
│   │
│   ├── 📁 auth-service/                  # Authentication Service (Port 8005)
│   │   ├── 📁 api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # Login/logout endpoints
│   │   │   ├── permissions.py            # Permission management
│   │   │   ├── roles.py                  # Role management
│   │   │   └── users.py                  # User management
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── cache.py                  # Redis caching
│   │   │   ├── config.py                 # Service configuration
│   │   │   ├── database.py               # Database setup
│   │   │   └── security.py               # Security utilities
│   │   ├── 📁 models/
│   │   │   ├── __init__.py
│   │   │   ├── permission.py             # Permission model
│   │   │   ├── role.py                   # Role model
│   │   │   ├── session.py                # Session model
│   │   │   └── user.py                   # User model
│   │   ├── 📁 schemas/
│   │   │   ├── __init__.py
│   │   │   └── auth.py                   # Pydantic schemas
│   │   ├── 📁 services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py           # Auth business logic
│   │   │   └── user_service.py           # User business logic
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── README.md
│   │   └── requirements.txt
│   │
│   ├── 📁 data-ingestion/                # IoT Data Collection (Port 8001)
│   │   ├── 📁 core/
│   │   │   └── config.py                 # Configuration
│   │   ├── Dockerfile
│   │   ├── main.py                       # MQTT and HTTP ingestion
│   │   └── requirements.txt
│   │
│   ├── 📁 data-processing/               # Data Processing Engine (Port 8002)
│   │   ├── 📁 api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py                 # Processing endpoints
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # Configuration
│   │   │   └── database.py               # Database connections
│   │   ├── 📁 models/
│   │   │   ├── __init__.py
│   │   │   └── processing.py             # Processing models
│   │   ├── 📁 services/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detection.py      # ML-based anomaly detection
│   │   │   ├── data_aggregation.py       # Data aggregation logic
│   │   │   ├── influx_service.py         # InfluxDB service
│   │   │   └── processing_service.py     # Core processing
│   │   ├── 📁 tasks/
│   │   │   ├── __init__.py
│   │   │   └── processing_tasks.py       # Celery tasks
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   ├── 📁 analytics/                     # Analytics Engine (Port 8003)
│   │   ├── 📁 api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py                 # Analytics endpoints
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── 📁 models/
│   │   │   ├── __init__.py
│   │   │   └── analytics.py              # Analytics models
│   │   ├── 📁 services/
│   │   │   ├── __init__.py
│   │   │   ├── analytics_service.py      # Core analytics
│   │   │   └── reporting_service.py      # Report generation
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   └── 📁 notification/                  # Notification System (Port 8004)
│       ├── 📁 api/
│       │   ├── __init__.py
│       │   └── routes.py                 # Notification endpoints
│       ├── 📁 core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── database.py
│       ├── 📁 models/
│       │   ├── __init__.py
│       │   └── notification.py           # Notification models
│       ├── 📁 services/
│       │   ├── __init__.py
│       │   └── email_service.py          # Email service
│       ├── 📁 tasks/
│       │   ├── __init__.py
│       │   └── email_tasks.py            # Celery email tasks
│       ├── 📁 templates/
│       │   ├── alert.html                # HTML email template
│       │   ├── alert.txt                 # Text email template
│       │   └── daily_report.html         # Daily report template
│       ├── Dockerfile
│       ├── main.py
│       ├── requirements.txt
│       └── worker.py                     # Celery worker
│
├── 📁 frontend/                          # React Frontend Application (Port 3000)
│   ├── 📁 public/
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── 📁 auth/
│   │   │   │   ├── LoginForm.tsx         # Login component
│   │   │   │   └── ProtectedRoute.tsx    # Route protection
│   │   │   ├── 📁 common/
│   │   │   │   ├── Button.tsx            # Reusable button
│   │   │   │   ├── Card.tsx              # Card component
│   │   │   │   ├── Input.tsx             # Input component
│   │   │   │   ├── LoadingSpinner.tsx    # Loading indicator
│   │   │   │   └── Modal.tsx             # Modal component
│   │   │   ├── 📁 dashboard/
│   │   │   │   ├── DashboardStats.tsx    # Stats cards
│   │   │   │   ├── DeviceList.tsx        # Device listing
│   │   │   │   ├── EnergyChart.tsx       # Energy consumption chart
│   │   │   │   └── RealtimeUpdates.tsx   # Real-time data
│   │   │   ├── 📁 devices/
│   │   │   │   ├── DeviceCard.tsx        # Device card
│   │   │   │   ├── DeviceForm.tsx        # Device form
│   │   │   │   └── DeviceModal.tsx       # Device modal
│   │   │   └── 📁 layout/
│   │   │       ├── Header.tsx            # App header
│   │   │       ├── Layout.tsx            # Main layout
│   │   │       ├── Navigation.tsx        # Navigation menu
│   │   │       └── Sidebar.tsx           # Sidebar navigation
│   │   ├── 📁 contexts/
│   │   │   └── AuthContext.tsx           # Authentication context
│   │   ├── 📁 hooks/
│   │   │   ├── useApi.ts                 # API hooks
│   │   │   ├── useAuth.ts                # Authentication hooks
│   │   │   └── useWebSocket.ts           # WebSocket hooks
│   │   ├── 📁 pages/
│   │   │   ├── Dashboard.tsx             # Main dashboard
│   │   │   ├── Devices.tsx               # Device management
│   │   │   ├── Login.tsx                 # Login page
│   │   │   └── NotFound.tsx              # 404 page
│   │   ├── 📁 services/
│   │   │   ├── api.ts                    # API client
│   │   │   ├── auth.ts                   # Auth service
│   │   │   └── websocket.ts              # WebSocket service
│   │   ├── 📁 types/
│   │   │   └── index.ts                  # TypeScript types
│   │   ├── 📁 utils/
│   │   │   ├── constants.ts              # App constants
│   │   │   ├── formatters.ts             # Data formatters
│   │   │   └── validators.ts             # Form validators
│   │   ├── App.tsx                       # Main app component
│   │   ├── index.css                     # Global styles
│   │   └── main.tsx                      # App entry point
│   ├── Dockerfile.dev                    # Development Dockerfile
│   ├── Dockerfile.prod                   # Production Dockerfile
│   ├── index.html
│   ├── package.json                      # Dependencies
│   ├── tailwind.config.js                # Tailwind configuration
│   ├── tsconfig.json                     # TypeScript config
│   └── vite.config.ts                    # Vite configuration
│
├── 📁 infrastructure/                    # Infrastructure Configuration
│   ├── 📁 grafana/
│   │   ├── 📁 dashboards/                # Pre-built dashboards
│   │   └── 📁 provisioning/              # Grafana config
│   ├── 📁 mosquitto/                     # MQTT Broker Config
│   │   ├── mosquitto.dev.conf            # Development config
│   │   ├── mosquitto.prod.conf           # Production config
│   │   └── passwd                        # MQTT authentication
│   └── 📁 nginx/                         # Reverse Proxy Config
│       ├── nginx.conf                    # Main config
│       └── 📁 conf.d/                    # Site configs
│
├── 📁 scripts/                           # Database & Utility Scripts
│   ├── init-db.sql                       # Database initialization
│   └── rbac-migration.sql                # RBAC system setup
│
├── 📁 docs/                              # Documentation
│   └── RBAC_SYSTEM.md                    # RBAC documentation
│
├── 📄 docker-compose.yml                 # Main orchestration
├── 📄 docker-compose.dev.yml             # Development environment
├── 📄 docker-compose.prod.yml            # Production environment
├── 📄 Makefile                           # Build automation
├── 📄 package.json                       # Root package config
├── 📄 quick-start.ps1                    # Windows quick start
├── 📄 README.md                          # Project documentation
├── 📄 PROJECT_STRUCTURE.md               # This file
└── 📄 IMPLEMENTATION_STATUS.md           # Implementation status
```

## 🔧 Service Architecture

### Microservices Pattern
Each service follows the same architectural pattern:

```
service-name/
├── 📁 api/              # REST API endpoints
├── 📁 core/             # Core functionality (config, db, auth)
├── 📁 models/           # Database models
├── 📁 schemas/          # Pydantic validation schemas
├── 📁 services/         # Business logic
├── 📁 tasks/            # Celery background tasks (if needed)
├── Dockerfile           # Container definition
├── main.py              # FastAPI application entry
└── requirements.txt     # Python dependencies
```

### Frontend Architecture
The React application follows modern patterns:

```
frontend/src/
├── 📁 components/       # Reusable UI components
│   ├── auth/           # Authentication components
│   ├── common/         # Common UI elements
│   ├── dashboard/      # Dashboard specific components
│   ├── devices/        # Device management components
│   └── layout/         # Layout components
├── 📁 contexts/        # React contexts
├── 📁 hooks/           # Custom React hooks
├── 📁 pages/           # Top-level page components
├── 📁 services/        # API and external services
├── 📁 types/           # TypeScript type definitions
└── 📁 utils/           # Utility functions
```

## 🗄️ Database Architecture

### PostgreSQL Tables
- **users** - User accounts and profiles
- **roles** - User roles (admin, manager, operator, viewer)  
- **permissions** - Granular permissions
- **user_roles** - User-role assignments
- **role_permissions** - Role-permission assignments
- **sessions** - User sessions
- **devices** - IoT device registry
- **notifications** - Notification history
- **notification_templates** - Email templates
- **processing_jobs** - Background job tracking
- **energy_metrics** - Processed energy data

### InfluxDB Buckets
- **iot-data** - Raw IoT sensor readings
- **processed-data** - Aggregated and processed metrics
- **alerts** - Alert and anomaly data

### Redis Usage
- **Database 0**: Auth service caching
- **Database 1**: API gateway caching  
- **Database 2**: Data ingestion queues
- **Database 3**: Data processing caching
- **Database 4**: Data processing Celery
- **Database 5**: Analytics caching
- **Database 6**: Analytics Celery
- **Database 7**: Notification caching
- **Database 8**: Notification Celery

## 🌐 Network Architecture

### Service Communication
```
[Frontend:3000] → [Nginx:80] → [API Gateway:8000] → [Services:8001-8005]
                             → [Grafana:3001]
                             
[IoT Devices] → [MQTT:1883] → [Data Ingestion:8001] → [InfluxDB:8086]
                                                    → [PostgreSQL:5432]
```

### Internal Networks
- **energy-network**: Isolated Docker network for all services
- **Subnet**: 172.20.0.0/16
- **Service Discovery**: Automatic via Docker Compose

## 📦 Deployment Configurations

### Development (docker-compose.dev.yml)
- Hot reload enabled
- Debug logging
- Development databases
- Exposed ports for debugging

### Production (docker-compose.prod.yml)  
- Optimized containers
- Production logging
- Persistent volumes
- Health checks
- Resource limits

### Quick Start (docker-compose.yml)
- Balanced configuration
- Ready for immediate use
- All services enabled
- Default credentials

## 🔐 Security Architecture

### Authentication Flow
1. User login via Frontend
2. Credentials sent to Auth Service
3. JWT tokens generated and returned
4. Tokens included in API requests
5. API Gateway validates tokens
6. Services receive authenticated user context

### Authorization Layers
1. **Route Level**: Protected routes in Frontend
2. **API Gateway**: Token validation
3. **Service Level**: Role-based permissions
4. **Database Level**: Row-level security (planned)

## 📊 Data Flow Architecture

### Real-time Data Flow
```
IoT Devices → MQTT → Data Ingestion → InfluxDB
                                   → Processing Queue
                                   → Real-time Dashboard
```

### Batch Processing Flow
```
InfluxDB → Analytics Service → Aggregated Metrics → PostgreSQL
                            → Reports → Notification Service
                            → Forecasts → Dashboard
```

### Notification Flow
```
Alert Trigger → Notification API → Celery Queue → Email Service → SMTP
                                 → Templates → HTML/Text Email
```

This architecture provides:
- **Scalability**: Horizontal scaling of individual services
- **Reliability**: Health checks and restart policies
- **Security**: Multi-layer authentication and authorization
- **Maintainability**: Clear separation of concerns
- **Observability**: Comprehensive logging and monitoring
