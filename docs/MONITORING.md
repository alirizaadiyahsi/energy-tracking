# 📊 Monitoring & Observability Infrastructure

This document describes the comprehensive monitoring and observability stack for the Energy Tracking IoT Platform.

## 🏗️ **Architecture Overview**

Our monitoring stack includes:

- **📈 Prometheus**: Metrics collection and storage
- **📊 Grafana**: Visualization and dashboards
- **🚨 AlertManager**: Alert routing and notification
- **🔍 Jaeger**: Distributed tracing
- **📝 Loki**: Log aggregation and analysis
- **💻 Node Exporter**: System metrics
- **🔄 Redis Exporter**: Redis metrics
- **🐘 Postgres Exporter**: PostgreSQL metrics

## 🚀 **Quick Start**

### **1. Setup Monitoring Infrastructure**
```powershell
# Setup and start all monitoring services
.\scripts\setup-monitoring.ps1 -Action setup
.\scripts\setup-monitoring.ps1 -Action start
```

### **2. Access Monitoring Services**
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Jaeger Tracing**: http://localhost:16686
- **Loki Logs**: http://localhost:3100

## 📊 **Available Dashboards**

### **1. Microservices Overview**
- Service health status
- Request rates and response times
- Error rates and system resources
- Real-time monitoring of all services

### **2. Auth Service Dashboard**
- Authentication metrics (logins, registrations)
- Login success rates and response times
- Database and Redis health
- Active sessions and user counts

### **3. System Resources**
- CPU, Memory, and Disk usage
- Network I/O and system load
- Database and cache performance

## 🚨 **Alerting Rules**

### **Critical Alerts**
- **Service Down**: When any service is unavailable for >30s
- **Low Disk Space**: When disk usage >90%
- **Database Issues**: Connection failures or slow queries

### **Warning Alerts**
- **High Error Rate**: >10% error rate for >2 minutes
- **High Response Time**: 95th percentile >1 second
- **High Resource Usage**: CPU >80% or Memory >90%
- **Authentication Issues**: High failed login rates

### **Application-Specific Alerts**
- **Auth Service**: Failed login spikes, account lockouts
- **Data Processing**: Queue backlogs, processing failures
- **Analytics**: Job failures, computation errors

## 📈 **Metrics Collection**

### **Service Metrics**
All services automatically collect:
```
# Request metrics
http_requests_total{method, status, endpoint}
http_request_duration_seconds{method, endpoint}

# Authentication metrics (auth-service)
successful_logins_total
failed_logins_total
successful_registrations_total
registration_conflicts_total

# Health check metrics
database_health_check_duration_seconds
redis_health_check_duration_seconds
system_health_check_duration_seconds

# Custom operation timing
user_login_duration_seconds
user_registration_duration_seconds
```

### **System Metrics**
- CPU usage per core and average
- Memory usage and available memory
- Disk usage and I/O statistics
- Network I/O and connections

### **Database Metrics**
- Connection counts and query performance
- Database size and table statistics
- Slow query detection
- Lock and deadlock monitoring

## 🔍 **Distributed Tracing**

### **Jaeger Integration**
- Automatic trace collection from all services
- Request flow visualization across microservices
- Performance bottleneck identification
- Error propagation tracking

### **Trace Configuration**
Services are configured to send traces to Jaeger:
```python
# Automatic instrumentation in shared libraries
from libs.monitoring.tracing import setup_tracing
setup_tracing("service-name")
```

## 📝 **Log Aggregation**

### **Loki & Promtail**
- Centralized log collection from all services
- Structured JSON log parsing
- Request correlation with trace IDs
- Log-based alerting capabilities

### **Log Structure**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "service": "auth-service",
  "message": "User logged in successfully",
  "request_id": "req-123456",
  "user_id": "user-789",
  "extra": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }
}
```

## 🛠️ **Management Commands**

### **Start/Stop Services**
```powershell
# Start all monitoring services
.\scripts\setup-monitoring.ps1 -Action start

# Stop all services
.\scripts\setup-monitoring.ps1 -Action stop

# Restart specific service
.\scripts\setup-monitoring.ps1 -Action restart -Service grafana
```

### **View Logs**
```powershell
# View all service logs
.\scripts\setup-monitoring.ps1 -Action logs

# View specific service logs
.\scripts\setup-monitoring.ps1 -Action logs -Service prometheus
```

### **Check Status**
```powershell
# Check service status
.\scripts\setup-monitoring.ps1 -Action status
```

## 🔧 **Configuration**

### **Prometheus Configuration**
- Scrape intervals: 5-15 seconds
- Retention: 200 hours
- Auto-discovery of services
- Custom metrics endpoints

### **Grafana Provisioning**
- Automatic dashboard loading
- Pre-configured data sources
- User authentication and permissions
- Custom organization setup

### **AlertManager Routing**
- Email notifications for critical alerts
- Webhook integration with notification service
- Alert grouping and suppression
- Escalation policies

## 📊 **Performance Tuning**

### **Prometheus Optimization**
- Efficient metric naming and labeling
- Proper recording rules for expensive queries
- Storage optimization for high-cardinality metrics
- Query performance monitoring

### **Grafana Optimization**
- Dashboard query optimization
- Efficient visualization choices
- Caching configuration
- User permission management

## 🔐 **Security Considerations**

### **Access Control**
- Grafana authentication and RBAC
- Prometheus query restrictions
- Network segmentation for monitoring
- Secure metric exposition

### **Data Privacy**
- No sensitive data in metrics labels
- Log scrubbing for PII
- Secure storage for monitoring data
- Access audit logging

## 🧪 **Testing Monitoring**

### **Metric Validation**
```bash
# Test Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Test service metrics
curl http://localhost:8005/metrics

# Test alerts
curl http://localhost:9093/api/v1/alerts
```

### **Dashboard Testing**
- Load test dashboards with historical data
- Verify alert threshold accuracy
- Test notification delivery
- Validate metric accuracy

## 🚀 **Next Steps**

1. **Custom Dashboards**: Create service-specific dashboards
2. **Advanced Alerting**: Implement ML-based anomaly detection
3. **Capacity Planning**: Add predictive monitoring
4. **Business Metrics**: Track KPIs and business outcomes
5. **Mobile Dashboards**: Responsive monitoring for mobile devices

## 📖 **Resources**

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

The monitoring infrastructure provides comprehensive observability into the Energy Tracking platform, enabling proactive issue detection, performance optimization, and reliable service operation.
