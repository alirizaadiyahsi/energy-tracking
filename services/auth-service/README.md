# Authentication Service

Centralized authentication and authorization microservice for the Energy Tracking IoT platform.

## Features

- **User Authentication**: Register, login, logout with JWT tokens
- **Session Management**: Secure session handling with Redis
- **Password Security**: Bcrypt hashing, strength validation, reset functionality
- **Email Verification**: Email verification for new accounts
- **Account Security**: Failed login attempt tracking, account lockout
- **Token Management**: Access/refresh token system with proper expiration
- **RBAC Ready**: Foundation for Role-Based Access Control (RBAC) system
- **API Documentation**: Automatic OpenAPI/Swagger documentation

## Architecture

```
auth-service/
├── api/                    # API route handlers
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management endpoints
│   ├── roles.py           # Role management (placeholder)
│   └── permissions.py     # Permission management (placeholder)
├── core/                  # Core utilities and configuration
│   ├── config.py          # Application configuration
│   ├── database.py        # Database connection and setup
│   ├── cache.py           # Redis cache management
│   └── security.py        # Security utilities (JWT, password hashing)
├── models/                # Database models
│   ├── user.py            # User model
│   ├── role.py            # Role model
│   ├── permission.py      # Permission model
│   └── session.py         # Session model
├── schemas/               # Pydantic schemas for API validation
│   └── auth.py            # Authentication schemas
├── services/              # Business logic services
│   ├── auth_service.py    # Authentication service
│   └── user_service.py    # User management service
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
├── main.py                # FastAPI application entry point
└── .env.example          # Environment configuration template
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh access token
- `POST /auth/verify-email` - Verify email address
- `POST /auth/password-reset-request` - Request password reset
- `POST /auth/password-reset` - Reset password with token
- `GET /auth/me` - Get current user info

### Users
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update user profile
- `GET /users/` - List users (admin only)
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}/activate` - Activate user (admin only)
- `PUT /users/{user_id}/deactivate` - Deactivate user (admin only)

### System
- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Basic metrics

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/energy_tracking

# Redis
REDIS_URL=redis://:password@redis:6379/0

# JWT Secret (change this!)
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters

# Security Settings
BCRYPT_ROUNDS=12
SESSION_EXPIRE_HOURS=24
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Email Settings
EMAIL_FROM=noreply@energytracking.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the service**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8005 --reload
   ```

## Docker Deployment

The service is configured to run in Docker containers:

```bash
# Build the image
docker build -t energy-auth-service .

# Run the container
docker run -p 8005:8005 energy-auth-service
```

## Database Models

### User Model
- Basic user information (email, name, phone)
- Authentication data (password hash, verification status)
- Security tracking (failed attempts, lockout)
- Timestamps and metadata

### Session Model
- Session tracking with unique session IDs
- Device and location information
- Token storage and expiration
- Session revocation capabilities

### Role Model (RBAC Extension)
- Role definitions with descriptions
- System vs custom roles
- Active status tracking

### Permission Model (RBAC Extension)
- Resource-action based permissions
- Hierarchical permission structure
- System vs custom permissions

## Security Features

- **Password Security**: Bcrypt hashing with configurable rounds
- **JWT Tokens**: Signed tokens with proper expiration
- **Session Management**: Redis-backed session storage
- **Rate Limiting**: Configurable API rate limits
- **Account Lockout**: Automatic lockout after failed attempts
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic schema validation

## Default Admin Users

Two administrative accounts are seeded automatically for convenience:

### Primary System Administrator
- Email: `admin@energy-tracking.com`
- Password: `admin123`
- Role: Super Administrator
- Purpose: Full system lifecycle administration

### Simple Local Administrator
- Email: `admin@mail.com`
- Password: `admin123`
- Role: Super Administrator
- Purpose: Quick local testing with a shorter identifier

> Security: Change these credentials immediately in any non-local environment.

## Monitoring and Health

- **Health Checks**: Database and Redis connectivity
- **Logging**: Structured logging with configurable levels
- **Metrics**: Basic service metrics endpoint
- **Error Handling**: Comprehensive error handling and reporting

## Future Extensions

- **RBAC Implementation**: Full role and permission system
- **OAuth2 Integration**: Third-party authentication
- **Multi-factor Authentication**: SMS/TOTP support
- **Audit Logging**: Comprehensive audit trails
- **Advanced Metrics**: Prometheus metrics integration
- **Email Service**: Integration with email providers

## Integration with Other Services

The authentication service integrates with other platform services:

- **Data Ingestion Service**: Validates API requests
- **Analytics Service**: Authorizes data access
- **Frontend Application**: Provides authentication state
- **Notification Service**: Sends verification emails

All services use the `/auth/me` endpoint to validate user tokens and get user information.
