# Energy Tracking - Data Processing Service

This service handles the processing and analysis of energy consumption data collected from IoT devices.

## Features

- **Data Aggregation**: Hourly and daily energy consumption aggregation
- **Anomaly Detection**: Machine learning-based anomaly detection using Isolation Forest
- **Background Processing**: Celery-based task queue for asynchronous processing
- **Data Cleanup**: Automated cleanup of old processed data
- **InfluxDB Integration**: Direct integration with InfluxDB for time-series data
- **RESTful API**: FastAPI-based REST endpoints for processing management

## Architecture

- **FastAPI**: Web framework for REST API
- **SQLAlchemy**: ORM for PostgreSQL database operations
- **Celery**: Distributed task queue for background processing
- **InfluxDB**: Time-series database for raw energy data
- **Redis**: Message broker and result backend for Celery
- **Pandas & NumPy**: Data processing libraries
- **Scikit-learn**: Machine learning for anomaly detection

## API Endpoints

### Processing Jobs
- `GET /api/v1/jobs` - List processing jobs
- `POST /api/v1/jobs` - Create new processing job
- `GET /api/v1/jobs/{job_id}` - Get specific job details

### Energy Metrics
- `GET /api/v1/metrics` - Get processed energy metrics
- `POST /api/v1/aggregate` - Trigger data aggregation

### Statistics
- `GET /api/v1/stats` - Get processing statistics

## Background Tasks

### Scheduled Tasks
- **Hourly Aggregation**: Runs every hour to aggregate energy data
- **Daily Anomaly Detection**: Runs daily to detect consumption anomalies
- **Weekly Cleanup**: Runs weekly to clean up old processed data

### On-Demand Tasks
- **Device Data Processing**: Process specific device data batches
- **Report Generation**: Generate energy consumption reports

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `INFLUXDB_URL` - InfluxDB server URL
- `INFLUXDB_TOKEN` - InfluxDB access token
- `INFLUXDB_ORG` - InfluxDB organization
- `INFLUXDB_BUCKET` - InfluxDB bucket for energy data
- `CELERY_BROKER_URL` - Celery broker URL
- `LOG_LEVEL` - Logging level

## Running the Service

### Development
```bash
pip install -r requirements.txt
python main.py
```

### With Docker
```bash
docker build -t data-processing-service .
docker run -p 8002:8002 data-processing-service
```

### Celery Workers
```bash
# Start worker
celery -A celery_app worker --loglevel=info

# Start scheduler (beat)
celery -A celery_app beat --loglevel=info
```

## Data Models

### ProcessingJob
- Tracks background processing jobs
- Stores job parameters and results
- Monitors job status and execution time

### EnergyMetrics
- Stores aggregated energy consumption metrics
- Supports multiple time periods (hourly, daily, weekly, monthly)
- Includes anomaly detection results

## Processing Algorithms

### Data Aggregation
- Groups raw energy readings by time periods
- Calculates statistical measures (mean, max, min)
- Estimates energy costs based on consumption

### Anomaly Detection
- Uses Isolation Forest algorithm
- Detects unusual consumption patterns
- Assigns anomaly scores to energy metrics

## Health Monitoring

The service includes health check endpoints and comprehensive logging for monitoring processing jobs and system performance.

## Integration

This service integrates with:
- **Data Ingestion Service**: Receives processed data requests
- **Analytics Service**: Provides aggregated data for analysis
- **API Gateway**: Exposes processing endpoints
- **Auth Service**: Validates user permissions for processing operations
