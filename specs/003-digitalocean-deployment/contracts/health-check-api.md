# Health Check API Contract

**Feature**: DigitalOcean Production Deployment  
**Version**: 1.0.0  
**Date**: 2025-12-28

## Overview

This contract defines the health check endpoint that all services must expose for monitoring and orchestration. The health check API is used by Docker health checks, deployment scripts, and monitoring systems to determine service availability.

---

## Endpoint Specification

### Health Check Endpoint

**HTTP Method**: `GET`  
**Path**: `/health`  
**Port**: Application-specific (internal only, not exposed externally)  
**Protocol**: HTTP (internal traffic, behind reverse proxy)

**Purpose**: Report overall service health and dependency status

**Authentication**: None (internal endpoint only, firewall-protected)

**Rate Limiting**: None (frequent polling required for health checks)

---

## Request

### Headers

None required. Standard HTTP headers accepted.

### Query Parameters

None

### Request Body

None (GET request)

---

## Response

### Success Response (200 OK)

**When**: Service is healthy and all dependencies are responsive

**Headers**:
```
Content-Type: application/json
Cache-Control: no-cache
```

**Body**:
```json
{
  "status": "healthy",
  "version": "1.2.0",
  "uptime_seconds": 86400,
  "timestamp": "2025-12-28T10:30:00Z",
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 3
    }
  }
}
```

**Field Definitions**:
- `status` (string, required): Overall health status. Values: `"healthy"`, `"degraded"`, `"unhealthy"`
- `version` (string, required): Application semantic version (e.g., "1.2.0")
- `uptime_seconds` (integer, required): Time in seconds since service started
- `timestamp` (string, required): ISO 8601 timestamp when health check was performed
- `dependencies` (object, required): Health status of each dependency
  - `postgres` (object, required for bot service): PostgreSQL health
    - `status` (string, required): `"healthy"` or `"unhealthy"`
    - `response_time_ms` (integer, required): Query latency in milliseconds
  - `redis` (object, required for bot service): Redis health
    - `status` (string, required): `"healthy"` or `"unhealthy"`
    - `response_time_ms` (integer, required): Query latency in milliseconds

---

### Degraded Response (200 OK)

**When**: Service is operational but one or more dependencies are experiencing issues

**Headers**:
```
Content-Type: application/json
Cache-Control: no-cache
```

**Body**:
```json
{
  "status": "degraded",
  "version": "1.2.0",
  "uptime_seconds": 86400,
  "timestamp": "2025-12-28T10:30:00Z",
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "redis": {
      "status": "unhealthy",
      "response_time_ms": null,
      "error": "Connection timeout after 5000ms"
    }
  },
  "warnings": [
    "Redis cache unavailable - using PostgreSQL fallback",
    "Rate limiting temporarily disabled"
  ]
}
```

**Additional Fields**:
- `warnings` (array of strings, optional): Human-readable warnings about degraded functionality

**Note**: Returns 200 OK because service is still operational, but status field indicates degradation.

---

### Error Response (503 Service Unavailable)

**When**: Service is unhealthy and cannot serve requests

**Headers**:
```
Content-Type: application/json
Cache-Control: no-cache
```

**Body**:
```json
{
  "status": "unhealthy",
  "version": "1.2.0",
  "uptime_seconds": 120,
  "timestamp": "2025-12-28T10:30:00Z",
  "dependencies": {
    "postgres": {
      "status": "unhealthy",
      "response_time_ms": null,
      "error": "Connection refused at postgres:5432"
    },
    "redis": {
      "status": "unhealthy",
      "response_time_ms": null,
      "error": "ECONNREFUSED redis:6379"
    }
  },
  "errors": [
    "Critical: Database connection failed",
    "Critical: Cache connection failed"
  ]
}
```

**Additional Fields**:
- `errors` (array of strings, required for unhealthy): Critical errors preventing operation
- `error` (string, optional): Error message for each failed dependency

**Status Code**: `503 Service Unavailable`

---

## Health Status Determination Rules

### Status: `healthy`
- All dependencies report `"healthy"`
- All dependency response times < 1000ms
- Service has been running for at least `start_period` (40 seconds for bot)

### Status: `degraded`
- Service can respond to health checks
- At least one dependency is `"unhealthy"`
- Service can still process requests (potentially with reduced functionality)

### Status: `unhealthy`
- Multiple critical dependencies are `"unhealthy"`, OR
- Service cannot process requests, OR
- Health check response time > 10 seconds

---

## Service-Specific Variations

### Bot Service (python-telegram-bot)

**Endpoint**: `http://localhost:8080/health`

**Dependencies Checked**:
- PostgreSQL (critical)
- Redis (critical for rate limiting)

**Implementation Location**: `src/handlers/system/health.py` (to be created)

---

### PostgreSQL Service

**Endpoint**: Via `pg_isready` command (not HTTP)

**Health Check Command**:
```bash
pg_isready -U toogoodtogo -d telegram_marketplace
```

**Success Output**: `telegram_marketplace:5432 - accepting connections`  
**Exit Code**: `0` (success), `1` (not ready), `2` (connection refused)

---

### Redis Service

**Endpoint**: Via `redis-cli ping` command (not HTTP)

**Health Check Command**:
```bash
redis-cli ping
```

**Success Output**: `PONG`  
**Exit Code**: `0` (success), non-zero (failure)

---

### nginx Service

**Endpoint**: Via process check (not HTTP)

**Health Check Command**:
```bash
pgrep nginx
```

**Success**: nginx master process is running  
**Failure**: No nginx process found

---

## Docker Compose Integration

### Bot Service Health Check

```yaml
services:
  bot:
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health', timeout=5).raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### PostgreSQL Service Health Check

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U toogoodtogo -d telegram_marketplace"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
```

### Redis Service Health Check

```yaml
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 5s
```

---

## Response Time SLAs

| Service | Target Response Time | Maximum Response Time |
|---------|---------------------|----------------------|
| Bot /health | < 100ms | 10,000ms (timeout) |
| PostgreSQL pg_isready | < 50ms | 5,000ms (timeout) |
| Redis ping | < 10ms | 3,000ms (timeout) |

---

## Error Scenarios

### Scenario 1: Database Connection Pool Exhausted

**Response**:
```json
{
  "status": "degraded",
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "response_time_ms": 850,
      "warning": "Connection pool at 90% capacity"
    }
  },
  "warnings": ["Database under high load"]
}
```

**HTTP Status**: 200 OK

---

### Scenario 2: Startup Initialization

**Response** (during start_period):
```json
{
  "status": "degraded",
  "uptime_seconds": 15,
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "response_time_ms": 20
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5
    }
  },
  "warnings": ["Service initializing - not ready for traffic"]
}
```

**HTTP Status**: 200 OK

**Note**: Docker will not mark service as healthy until start_period elapses and health check succeeds.

---

### Scenario 3: Complete Service Failure

**Response**: None (connection refused or timeout)

**Docker Behavior**: After `retries` failed attempts, container marked unhealthy → restart policy triggered

---

## Monitoring Integration

### Prometheus Metrics (Future Enhancement)

Health check results can be exposed as Prometheus metrics:

```
# HELP service_health Current health status (1=healthy, 0.5=degraded, 0=unhealthy)
# TYPE service_health gauge
service_health{service="bot"} 1

# HELP service_uptime_seconds Service uptime in seconds
# TYPE service_uptime_seconds counter
service_uptime_seconds{service="bot"} 86400

# HELP dependency_health Dependency health status
# TYPE dependency_health gauge
dependency_health{service="bot",dependency="postgres"} 1
dependency_health{service="bot",dependency="redis"} 1

# HELP dependency_response_time_ms Dependency response time in milliseconds
# TYPE dependency_response_time_ms histogram
dependency_response_time_ms{service="bot",dependency="postgres"} 15
```

---

## Validation Requirements

### Contract Compliance Tests

All services must pass these contract tests:

1. **Health endpoint returns 200 OK when healthy**
   ```bash
   curl -f http://localhost:8080/health
   # Exit code 0 expected
   ```

2. **Health response includes all required fields**
   ```bash
   curl http://localhost:8080/health | jq -e '.status, .version, .uptime_seconds, .dependencies'
   # All fields present
   ```

3. **Health response completes within timeout**
   ```bash
   timeout 10s curl http://localhost:8080/health
   # Completes before timeout
   ```

4. **Dependency status is accurate**
   - Stop PostgreSQL → health check reports postgres.status = "unhealthy"
   - Restart PostgreSQL → health check reports postgres.status = "healthy" within 30s

---

## Changelog

**v1.0.0** (2025-12-28):
- Initial contract definition
- Health check endpoint specification
- Docker health check integration
- Service-specific health check commands
