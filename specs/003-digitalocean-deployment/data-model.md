# Data Model: DigitalOcean Production Deployment

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)  
**Date**: 2025-12-28

## Overview

This document defines the data entities and their relationships for the production deployment infrastructure. Unlike typical application features, this deployment feature focuses on configuration entities, service states, and operational data rather than business domain models.

---

## Entity Definitions

### 1. Deployment Configuration

**Description**: Complete set of configuration parameters required to deploy and run the application in production.

**Attributes**:
- `environment_name`: String - Environment identifier (e.g., "production", "staging")
- `telegram_bot_token`: Secret String - Telegram bot authentication token
- `telegram_webhook_url`: URL - HTTPS endpoint for Telegram webhook callbacks
- `database_url`: Connection String - PostgreSQL connection string (includes credentials)
- `database_password`: Secret String - PostgreSQL password
- `redis_url`: Connection String - Redis connection string
- `stripe_api_key`: Secret String - Payment provider API key
- `log_level`: Enum - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `allowed_origins`: List[String] - CORS allowed origins (if applicable)
- `max_workers`: Integer - Number of worker processes/threads
- `deployment_tag`: String - Git tag or SHA of deployed version

**Relationships**:
- Referenced by: Service Instance (configuration used to start service)
- Contains: Service-specific configuration for bot, PostgreSQL, Redis

**Validation Rules**:
- `telegram_bot_token` must match pattern: `\d+:[A-Za-z0-9_-]+`
- `telegram_webhook_url` must use HTTPS protocol
- `database_url` must be valid PostgreSQL connection string
- `log_level` must be one of: DEBUG, INFO, WARNING, ERROR
- `deployment_tag` should match semantic version pattern or Git SHA

**Storage**:
- File: `/opt/toogoodtogo/.env.production` (not in Git)
- Template: `.env.production.template` (in Git, no secrets)
- Backup: Encrypted copy in operator's secure storage

**Lifecycle**:
- Created: During initial droplet setup
- Updated: When secrets rotate or configuration changes
- Validated: On every deployment before services start

---

### 2. Service Instance

**Description**: A running instance of a service (bot, PostgreSQL, or Redis) with its current runtime state and resource consumption.

**Attributes**:
- `service_name`: String - Unique service identifier ("bot", "postgres", "redis", "nginx")
- `container_id`: String - Docker container ID
- `image_tag`: String - Docker image tag (e.g., "postgres:16-alpine")
- `status`: Enum - Current service state (starting, healthy, degraded, unhealthy, stopped)
- `health_check_status`: Enum - Latest health check result (pass, fail, unknown)
- `started_at`: Timestamp - When the service started
- `restart_count`: Integer - Number of restarts since last deployment
- `last_restart_at`: Timestamp - Most recent restart time
- `cpu_usage_percent`: Float - Current CPU utilization
- `memory_usage_mb`: Integer - Current memory consumption
- `disk_usage_mb`: Integer - Disk space used by service
- `port_bindings`: Map[Integer, Integer] - Container port to host port mappings
- `environment_variables`: Map[String, String] - Service-specific env vars
- `version`: String - Application version (for bot service)

**Relationships**:
- References: Deployment Configuration (uses config for initialization)
- Contains: Health Status (current health state)
- Part of: Deployment Artifact (service is instance of artifact)

**State Transitions**:
```
stopped → starting → healthy
healthy → degraded (partial functionality)
degraded → healthy (recovery) OR degraded → unhealthy (failure)
unhealthy → stopped (automatic restart)
any state → stopped (manual intervention)
```

**Validation Rules**:
- `restart_count` < max_restart_threshold (configured in Docker Compose)
- `memory_usage_mb` < allocated memory limit
- `health_check_status` must transition to `pass` within `start_period`

**Storage**:
- Runtime: Docker Engine state
- Monitoring: Time-series metrics (if Prometheus enabled)
- Logs: Structured logs with service_name tag

**Lifecycle**:
- Created: When `docker compose up` is executed
- Updated: Continuously during operation (metrics refreshed every 30s)
- Destroyed: When service is stopped or replaced during deployment

---

### 3. Health Status

**Description**: Detailed health information for a service, including dependency health and diagnostic data.

**Attributes**:
- `service_name`: String - Service being checked
- `overall_status`: Enum - Aggregated health (healthy, degraded, unhealthy)
- `timestamp`: Timestamp - When health check was performed
- `response_time_ms`: Integer - Time taken for health check to complete
- `postgres_connected`: Boolean - PostgreSQL connection successful (bot only)
- `postgres_response_time_ms`: Integer - Database query latency
- `redis_connected`: Boolean - Redis connection successful (bot only)
- `redis_response_time_ms`: Integer - Cache query latency
- `version`: String - Application version (bot only)
- `uptime_seconds`: Integer - Service uptime since last restart
- `error_message`: String - Error details if unhealthy (nullable)

**Relationships**:
- Owned by: Service Instance
- Triggers: Health Check Event (failed health triggers restart policy)

**State Derivation**:
```
overall_status = healthy IF:
  - postgres_connected = true
  - redis_connected = true
  - response_time_ms < 10000 (10 seconds)
  
overall_status = degraded IF:
  - One dependency unhealthy but service responding
  
overall_status = unhealthy IF:
  - Multiple dependencies failing OR response timeout
```

**Storage**:
- Recent history: Docker health check results (last 5 checks)
- Long-term: Application logs (structured log entries)
- Metrics: Prometheus time-series (if enabled)

**Lifecycle**:
- Created: Every health check interval (30 seconds)
- Retained: Last 5 health check results per service
- Logged: All status changes logged to application logs

---

### 4. Deployment Artifact

**Description**: A versioned, immutable package containing application code and dependencies ready for deployment.

**Attributes**:
- `artifact_id`: String - Unique identifier (Git SHA or semantic version tag)
- `created_at`: Timestamp - When artifact was built
- `git_commit_sha`: String - Git commit SHA
- `git_tag`: String - Semantic version tag (e.g., "v1.2.0") (optional)
- `docker_image_uri`: String - Full Docker image reference with tag
- `docker_image_digest`: String - SHA256 digest of image
- `size_mb`: Integer - Total artifact size
- `changelog`: String - Changes included in this version
- `deployed`: Boolean - Whether this artifact is currently deployed
- `deployed_at`: Timestamp - When this artifact was deployed (nullable)
- `rollback_from`: String - Previous artifact ID if this is a rollback (nullable)

**Relationships**:
- Deployed as: Service Instance (artifact instantiated as running service)
- Replaces: Previous Deployment Artifact (deployment history)

**Validation Rules**:
- `git_commit_sha` must be valid SHA-1 hash (40 hex characters)
- `git_tag` (if present) must match semantic versioning: `v\d+\.\d+\.\d+`
- `docker_image_digest` must be SHA256 hash
- Only one artifact can have `deployed = true` at a time

**Storage**:
- Container Registry: Docker Hub or DigitalOcean Container Registry
- Metadata: Deployment database or JSON file (`/opt/toogoodtogo/deployment/artifacts.json`)
- Git Repository: Source code and build configuration

**Lifecycle**:
- Created: On Git tag push (CI/CD build)
- Deployed: When deployment script executes successfully
- Archived: Retained for 30 days (configurable) for rollback capability
- Pruned: Old images cleaned up (`docker image prune`)

---

### 5. Deployment Event

**Description**: Audit record of a deployment operation, capturing who deployed what and the outcome.

**Attributes**:
- `event_id`: String - Unique event identifier (UUID)
- `event_type`: Enum - Type of operation (deploy, rollback, restart, config_update)
- `started_at`: Timestamp - When deployment started
- `completed_at`: Timestamp - When deployment completed (nullable if in progress)
- `duration_seconds`: Integer - Total deployment duration
- `triggered_by`: Enum - Who/what initiated deployment (github_action, manual, automated)
- `operator`: String - Username or system identifier
- `artifact_id`: String - Artifact being deployed
- `previous_artifact_id`: String - Artifact being replaced
- `status`: Enum - Deployment outcome (in_progress, success, failed, rolled_back)
- `error_message`: String - Failure reason if status = failed (nullable)
- `health_check_passed`: Boolean - Whether post-deployment health check succeeded
- `backup_created`: Boolean - Whether pre-deployment backup was created
- `migration_applied`: Boolean - Whether database migrations ran

**Relationships**:
- References: Deployment Artifact (deployed artifact)
- Creates: Service Instances (new instances created during deployment)
- Precedes: Next Deployment Event (deployment history chain)

**State Transitions**:
```
in_progress → success (health checks pass)
in_progress → failed (deployment error)
failed → rolled_back (automatic rollback)
success → (terminal state)
rolled_back → (terminal state, creates new event for rollback deployment)
```

**Storage**:
- Audit Log: Structured log file (`/var/log/toogoodtogo/deployments.log`)
- Metrics: Deployment frequency and duration metrics
- Notification: Sent to operations team (email, Slack) on completion

**Lifecycle**:
- Created: When deployment script starts
- Updated: As deployment progresses (status changes)
- Completed: When deployment succeeds or fails
- Retained: Indefinitely for audit compliance

---

### 6. Backup Record

**Description**: Metadata about a database backup, tracking when backups were created and their recovery information.

**Attributes**:
- `backup_id`: String - Unique backup identifier (UUID or timestamp-based)
- `created_at`: Timestamp - When backup was created
- `backup_type`: Enum - Type of backup (scheduled, pre_deployment, manual)
- `file_path`: String - Location of backup file on disk or object storage
- `file_size_mb`: Integer - Backup file size
- `database_name`: String - Name of database backed up
- `pg_dump_version`: String - Version of pg_dump used
- `compressed`: Boolean - Whether backup is gzip compressed
- `verified`: Boolean - Whether backup integrity has been verified
- `verified_at`: Timestamp - When backup was last verified (nullable)
- `retention_until`: Timestamp - When backup should be deleted
- `artifact_id`: String - Application version at time of backup (nullable)

**Relationships**:
- Created by: Deployment Event (pre-deployment backup)
- Restores to: Service Instance (database service)

**Validation Rules**:
- `file_path` must be accessible and readable
- `retention_until` = created_at + retention_days (7 days default)
- `verified` should be true within 24 hours of creation

**Storage**:
- Backup Files: `/opt/backups/postgres/` on droplet
- Off-site: DigitalOcean Spaces or S3 (future enhancement)
- Metadata: JSON file (`/opt/backups/postgres/backup_index.json`)

**Lifecycle**:
- Created: Daily at 03:00 UTC and before each deployment
- Verified: Periodically (gunzip test or test restore)
- Expired: Deleted after retention period
- Restored: On recovery or rollback

---

## Entity Relationships

```
Deployment Configuration
    ↓ (configures)
Service Instance
    ↓ (produces)
Health Status
    ↑ (monitors)

Deployment Artifact
    ↓ (instantiates)
Service Instance

Deployment Event
    → (references) Deployment Artifact
    → (creates) Service Instance
    → (creates) Backup Record

Backup Record
    ← (created before) Deployment Event
    → (restores to) Service Instance (PostgreSQL)
```

---

## Configuration Files as Data

### docker-compose.prod.yml Structure

**Entity Type**: Service Orchestration Configuration

**Key Elements**:
- Service definitions (bot, postgres, redis, nginx)
- Resource limits (CPU, memory)
- Restart policies
- Volume mounts
- Network configuration
- Health check definitions

**Managed By**: Version control (Git)
**Applied Via**: `docker compose up` command

### nginx.conf Structure

**Entity Type**: Reverse Proxy Configuration

**Key Elements**:
- Server blocks (HTTP → HTTPS redirect, HTTPS webhook)
- SSL certificate paths
- Proxy pass rules
- Security headers
- Rate limiting rules

**Managed By**: Deployment scripts (deployed to droplet)
**Applied Via**: `nginx reload`

### systemd Service Unit

**Entity Type**: System Service Definition

**Key Elements**:
- Service dependencies (Docker)
- Start/stop commands
- Restart policy
- Working directory

**Managed By**: Deployment scripts (deployed to droplet)
**Applied Via**: `systemctl enable/start`

---

## Data Flow During Deployment

1. **Pre-Deployment**:
   - Deployment Configuration validated
   - Backup Record created (database snapshot)
   - Deployment Event created (status: in_progress)

2. **Deployment Execution**:
   - Deployment Artifact pulled from registry
   - Previous Service Instances stopped
   - New Service Instances created with new artifact
   - Health Status monitored during startup

3. **Post-Deployment Validation**:
   - Health Status checked for all services
   - Deployment Event updated (status: success or failed)
   - If failed: Automatic rollback using previous Deployment Artifact

4. **Steady State Operation**:
   - Service Instances continuously produce Health Status
   - Backup Records created daily
   - Service Instances may be restarted based on health failures

---

## Notes

- **No Persistent Application Data Changes**: This deployment feature doesn't modify the application's domain models (User, Business, Offer, etc.). Those entities remain unchanged.

- **Infrastructure as Data**: Configuration files (docker-compose.yml, nginx.conf) are treated as versioned data entities.

- **Idempotency**: Deployment operations should be idempotent - running deployment multiple times with same artifact produces same result.

- **Audit Trail**: Deployment Events provide complete audit history of all infrastructure changes.

- **State Management**: Service Instance state is ephemeral (exists only while containers run), while Deployment Event and Backup Record are persistent audit records.
