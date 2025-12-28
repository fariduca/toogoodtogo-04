# Deployment Scripts Interface Contract

**Feature**: DigitalOcean Production Deployment  
**Version**: 1.0.0  
**Date**: 2025-12-28

## Overview

This contract defines the interface and behavior of deployment automation scripts. These scripts provide a consistent, reliable way to deploy, rollback, backup, and manage the production environment.

---

## Script Inventory

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `deploy.sh` | Deploy new application version | Git tag | Deployment success/failure |
| `rollback.sh` | Revert to previous version | Target version (optional) | Rollback success/failure |
| `backup.sh` | Create database backup | None | Backup file path |
| `restore.sh` | Restore database from backup | Backup file path | Restore success/failure |
| `health-check.sh` | Validate service health | Service name (optional) | Health status |
| `setup-droplet.sh` | Initial droplet configuration | None | Setup success/failure |

---

## Script: deploy.sh

### Purpose
Deploy a new version of the application to production

### Location
`/opt/toogoodtogo/deployment/scripts/deploy.sh`

### Usage
```bash
./deploy.sh <git-tag>
```

### Parameters
- `git-tag` (required): Git tag to deploy (e.g., "v1.2.0")

### Exit Codes
- `0`: Deployment successful
- `1`: Deployment failed (validation error, health check failure)
- `2`: Backup failed (deployment aborted)
- `3`: Migration failed (deployment aborted, rollback initiated)

### Behavior

**Pre-Deployment Phase**:
1. Validate input parameters (git tag exists, format correct)
2. Create pre-deployment database backup via `backup.sh`
3. Verify backup created successfully
4. Fetch latest code from Git repository
5. Checkout specified tag

**Deployment Phase**:
6. Pull new Docker images for specified tag
7. Run database migrations (`alembic upgrade head`)
8. Restart services with new images (`docker compose up -d`)
9. Wait for services to start (max 5 minutes)

**Validation Phase**:
10. Run health checks via `health-check.sh`
11. Verify all services report healthy within timeout
12. Create deployment event log entry

**Rollback on Failure**:
- If any step fails → automatic rollback to previous version
- Restore database from backup if migration failed
- Log failure details

### Output

**Success**:
```
[2025-12-28 10:30:00] INFO: Starting deployment of v1.2.0
[2025-12-28 10:30:05] INFO: Creating pre-deployment backup
[2025-12-28 10:30:15] INFO: Backup created: /opt/backups/postgres/toogoodtogo_20251228_103015.sql.gz
[2025-12-28 10:30:20] INFO: Checking out tag v1.2.0
[2025-12-28 10:30:25] INFO: Pulling Docker images
[2025-12-28 10:32:00] INFO: Running database migrations
[2025-12-28 10:32:10] INFO: Migrations applied successfully
[2025-12-28 10:32:15] INFO: Restarting services
[2025-12-28 10:33:00] INFO: Services started
[2025-12-28 10:33:05] INFO: Running health checks
[2025-12-28 10:33:10] INFO: All services healthy
[2025-12-28 10:33:15] INFO: Deployment successful: v1.2.0
```

**Failure**:
```
[2025-12-28 10:30:00] INFO: Starting deployment of v1.2.0
[2025-12-28 10:30:05] INFO: Creating pre-deployment backup
[2025-12-28 10:30:15] INFO: Backup created: /opt/backups/postgres/toogoodtogo_20251228_103015.sql.gz
[2025-12-28 10:30:20] INFO: Checking out tag v1.2.0
[2025-12-28 10:30:25] INFO: Pulling Docker images
[2025-12-28 10:32:00] INFO: Running database migrations
[2025-12-28 10:32:10] ERROR: Migration failed: Syntax error in migration script
[2025-12-28 10:32:15] ERROR: Deployment failed - initiating rollback
[2025-12-28 10:32:20] INFO: Rolling back to v1.1.0
[2025-12-28 10:33:00] INFO: Rollback complete
[2025-12-28 10:33:05] ERROR: Deployment failed: v1.2.0
```

### Environment Variables Required
```bash
DEPLOY_DIR=/opt/toogoodtogo
BACKUP_DIR=/opt/backups/postgres
DOCKER_COMPOSE_FILE=docker-compose.prod.yml
HEALTH_CHECK_TIMEOUT=120  # seconds
```

---

## Script: rollback.sh

### Purpose
Rollback to a previous application version

### Location
`/opt/toogoodtogo/deployment/scripts/rollback.sh`

### Usage
```bash
./rollback.sh [target-version]
```

### Parameters
- `target-version` (optional): Git tag to rollback to. If omitted, rollback to previous version.

### Exit Codes
- `0`: Rollback successful
- `1`: Rollback failed
- `2`: Target version not found
- `3`: Backup restoration failed

### Behavior

1. Determine target version (from parameter or deployment history)
2. Create current state backup (safety measure)
3. Stop current services
4. Checkout target version
5. Restore database backup from target version deployment
6. Start services with target version
7. Validate health checks
8. Log rollback event

### Output

**Success**:
```
[2025-12-28 11:00:00] INFO: Starting rollback from v1.2.0 to v1.1.0
[2025-12-28 11:00:05] INFO: Creating safety backup
[2025-12-28 11:00:15] INFO: Stopping current services
[2025-12-28 11:00:30] INFO: Checking out v1.1.0
[2025-12-28 11:00:35] INFO: Restoring database backup
[2025-12-28 11:01:00] INFO: Starting services
[2025-12-28 11:02:00] INFO: Health checks passed
[2025-12-28 11:02:05] INFO: Rollback successful: v1.1.0
```

---

## Script: backup.sh

### Purpose
Create a compressed database backup

### Location
`/opt/toogoodtogo/deployment/scripts/backup.sh`

### Usage
```bash
./backup.sh [backup-type]
```

### Parameters
- `backup-type` (optional): Type of backup (`scheduled`, `pre_deployment`, `manual`). Default: `manual`

### Exit Codes
- `0`: Backup successful
- `1`: Backup failed (pg_dump error)
- `2`: Verification failed (corrupted backup)
- `3`: Disk space insufficient

### Behavior

1. Check available disk space (require at least 2GB free)
2. Generate backup filename with timestamp
3. Run `pg_dump` via Docker exec
4. Compress output with gzip
5. Verify backup integrity (`gunzip -t`)
6. Update backup metadata index
7. Cleanup old backups (retain last 7)
8. Optional: Upload to object storage

### Output

**Success**:
```
[2025-12-28 03:00:00] INFO: Starting database backup (type: scheduled)
[2025-12-28 03:00:05] INFO: Available disk space: 25GB
[2025-12-28 03:00:10] INFO: Creating backup: toogoodtogo_20251228_030010.sql.gz
[2025-12-28 03:01:30] INFO: Backup created: 245MB
[2025-12-28 03:01:35] INFO: Verifying backup integrity
[2025-12-28 03:01:40] INFO: Verification successful
[2025-12-28 03:01:45] INFO: Cleaning up old backups
[2025-12-28 03:01:50] INFO: Deleted 2 expired backups
[2025-12-28 03:01:55] INFO: Backup complete: /opt/backups/postgres/toogoodtogo_20251228_030010.sql.gz
```

**Failure**:
```
[2025-12-28 03:00:00] INFO: Starting database backup
[2025-12-28 03:00:05] ERROR: Insufficient disk space: 1.2GB available, 2GB required
[2025-12-28 03:00:10] ERROR: Backup failed
```

### Metadata File

Location: `/opt/backups/postgres/backup_index.json`

Format:
```json
{
  "backups": [
    {
      "backup_id": "toogoodtogo_20251228_030010",
      "created_at": "2025-12-28T03:00:10Z",
      "backup_type": "scheduled",
      "file_path": "/opt/backups/postgres/toogoodtogo_20251228_030010.sql.gz",
      "file_size_mb": 245,
      "verified": true,
      "verified_at": "2025-12-28T03:01:40Z",
      "retention_until": "2025-01-04T03:00:10Z",
      "artifact_id": "v1.2.0"
    }
  ]
}
```

---

## Script: restore.sh

### Purpose
Restore database from backup file

### Location
`/opt/toogoodtogo/deployment/scripts/restore.sh`

### Usage
```bash
./restore.sh <backup-file>
```

### Parameters
- `backup-file` (required): Path to backup file or backup ID

### Exit Codes
- `0`: Restore successful
- `1`: Restore failed
- `2`: Backup file not found or corrupted
- `3`: Database connection failed

### Behavior

1. Validate backup file exists and is readable
2. Verify backup integrity
3. Stop application services (keep database running)
4. Drop existing database (confirmation prompt if interactive)
5. Create fresh database
6. Restore from backup via `psql`
7. Verify restoration (row counts, key tables exist)
8. Restart application services
9. Run health checks

### Output

**Success**:
```
[2025-12-28 12:00:00] INFO: Starting database restore
[2025-12-28 12:00:05] INFO: Backup file: /opt/backups/postgres/toogoodtogo_20251227_030010.sql.gz
[2025-12-28 12:00:10] INFO: Verifying backup integrity
[2025-12-28 12:00:15] INFO: Stopping application services
[2025-12-28 12:00:30] INFO: Dropping existing database
[2025-12-28 12:00:35] INFO: Creating fresh database
[2025-12-28 12:00:40] INFO: Restoring from backup
[2025-12-28 12:03:00] INFO: Restoration complete
[2025-12-28 12:03:05] INFO: Verifying restored data
[2025-12-28 12:03:10] INFO: Verification successful: 15,432 users, 2,341 businesses
[2025-12-28 12:03:15] INFO: Restarting services
[2025-12-28 12:04:00] INFO: Services started
[2025-12-28 12:04:05] INFO: Health checks passed
[2025-12-28 12:04:10] INFO: Restore successful
```

---

## Script: health-check.sh

### Purpose
Validate health of deployed services

### Location
`/opt/toogoodtogo/deployment/scripts/health-check.sh`

### Usage
```bash
./health-check.sh [service-name]
```

### Parameters
- `service-name` (optional): Specific service to check (`bot`, `postgres`, `redis`, `nginx`). If omitted, check all services.

### Exit Codes
- `0`: All checked services healthy
- `1`: One or more services unhealthy
- `2`: Health check timeout

### Behavior

1. Determine which services to check
2. For each service:
   - Query health endpoint or run health check command
   - Parse response
   - Verify response time within SLA
3. Aggregate results
4. Report overall status

### Output

**All Healthy**:
```
[2025-12-28 10:35:00] INFO: Checking service health
[2025-12-28 10:35:01] INFO: bot: healthy (response: 45ms)
[2025-12-28 10:35:02] INFO: postgres: healthy (response: 12ms)
[2025-12-28 10:35:03] INFO: redis: healthy (response: 3ms)
[2025-12-28 10:35:04] INFO: nginx: healthy (process running)
[2025-12-28 10:35:05] INFO: All services healthy
```

**Some Unhealthy**:
```
[2025-12-28 10:35:00] INFO: Checking service health
[2025-12-28 10:35:01] INFO: bot: degraded (redis connection failed)
[2025-12-28 10:35:02] INFO: postgres: healthy (response: 15ms)
[2025-12-28 10:35:03] ERROR: redis: unhealthy (connection refused)
[2025-12-28 10:35:04] INFO: nginx: healthy (process running)
[2025-12-28 10:35:05] ERROR: Health check failed: 1 unhealthy, 1 degraded
```

### JSON Output Mode

```bash
./health-check.sh --json
```

Output:
```json
{
  "timestamp": "2025-12-28T10:35:05Z",
  "overall_status": "healthy",
  "services": {
    "bot": {
      "status": "healthy",
      "response_time_ms": 45
    },
    "postgres": {
      "status": "healthy",
      "response_time_ms": 12
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 3
    },
    "nginx": {
      "status": "healthy",
      "response_time_ms": null
    }
  }
}
```

---

## Script: setup-droplet.sh

### Purpose
Initial configuration of a fresh DigitalOcean droplet

### Location
`/opt/toogoodtogo/deployment/scripts/setup-droplet.sh`

### Usage
```bash
./setup-droplet.sh
```

### Parameters
None (interactive prompts for required information)

### Exit Codes
- `0`: Setup successful
- `1`: Setup failed
- `2`: Already configured (idempotent check)

### Behavior

1. Check if already configured (idempotent)
2. Update system packages
3. Install Docker and Docker Compose
4. Install nginx and certbot
5. Configure firewall (ufw)
6. Create application directories
7. Clone Git repository
8. Create `.env.production` from template (prompts for secrets)
9. Configure nginx with SSL (via certbot)
10. Create systemd service
11. Enable and start services
12. Run initial health check
13. Create setup completion marker

### Interactive Prompts

```
Enter Telegram Bot Token: _______________
Enter Telegram Webhook URL: https://_______________
Enter PostgreSQL Password: _______________
Enter Stripe API Key: _______________
Enter domain name for SSL: _______________
```

### Output

```
[2025-12-28 09:00:00] INFO: Starting droplet setup
[2025-12-28 09:00:05] INFO: Checking existing configuration
[2025-12-28 09:00:10] INFO: No existing configuration found
[2025-12-28 09:00:15] INFO: Updating system packages
[2025-12-28 09:05:00] INFO: Installing Docker
[2025-12-28 09:10:00] INFO: Installing nginx and certbot
[2025-12-28 09:12:00] INFO: Configuring firewall
[2025-12-28 09:12:30] INFO: Creating application directories
[2025-12-28 09:12:35] INFO: Cloning repository
[2025-12-28 09:13:00] INFO: Configuring environment variables
[Enter prompts...]
[2025-12-28 09:15:00] INFO: Configuring SSL certificates
[2025-12-28 09:17:00] INFO: Creating systemd service
[2025-12-28 09:17:05] INFO: Starting services
[2025-12-28 09:18:00] INFO: Running health checks
[2025-12-28 09:18:10] INFO: All services healthy
[2025-12-28 09:18:15] INFO: Setup complete - system ready for production
```

---

## Common Behaviors

### Logging

All scripts log to:
- **stdout**: Progress and informational messages
- **stderr**: Errors and warnings
- **File**: `/var/log/toogoodtogo/deployment.log` (persistent audit trail)

Log format:
```
[YYYY-MM-DD HH:MM:SS] LEVEL: message
```

### Error Handling

- All scripts use `set -e` (exit on error)
- Critical errors trigger cleanup and rollback
- Transient errors (network) retry up to 3 times with exponential backoff
- All errors logged with context

### Idempotency

Scripts are idempotent where possible:
- `backup.sh`: Creates new backup each run (timestamped)
- `deploy.sh`: Deploying same version twice is safe (no-op if already deployed)
- `setup-droplet.sh`: Detects existing configuration and exits safely

### Timeouts

- Health check queries: 10 seconds
- Service startup wait: 5 minutes
- Database operations: 10 minutes
- Docker pull: 15 minutes

---

## Validation

### Script Contract Tests

Each script must pass these tests:

1. **Help output available**
   ```bash
   ./deploy.sh --help
   # Prints usage information
   ```

2. **Exit code correctness**
   ```bash
   ./health-check.sh
   echo $?  # 0 if healthy, 1 if unhealthy
   ```

3. **Logging to file**
   ```bash
   ./backup.sh
   tail /var/log/toogoodtogo/deployment.log | grep "Backup complete"
   ```

4. **Error handling**
   ```bash
   ./deploy.sh invalid-tag
   # Exits with code 1, logs error
   ```

---

## Changelog

**v1.0.0** (2025-12-28):
- Initial contract definition
- Core deployment scripts specified
- Interface and behavior documented
