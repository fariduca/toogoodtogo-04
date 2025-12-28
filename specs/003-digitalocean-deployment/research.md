# Research: DigitalOcean Production Deployment

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Date**: 2025-12-28

## Overview

This document captures research findings for deploying the Telegram marketplace backend to DigitalOcean. Research focuses on Docker Compose production deployment, SSL/TLS configuration, service orchestration, monitoring, backup strategies, and zero-downtime deployment patterns.

---

## 1. Docker Compose Production Deployment

### Decision: Use Docker Compose with Production Overrides

**Rationale**:
- Existing project already uses Docker Compose for local development
- Docker Compose v2 supports production-grade features (resource limits, health checks, restart policies)
- Simpler operational model than Kubernetes for single-server deployment
- Built-in service dependency management and networking

**Implementation Approach**:
- Create `docker-compose.prod.yml` that extends base `docker-compose.yml`
- Override development settings with production configurations:
  - Remove port exposures for PostgreSQL/Redis (internal only)
  - Add resource limits (CPU, memory)
  - Configure restart policies (`restart: unless-stopped`)
  - Use production-grade logging drivers
  - Mount persistent volumes with proper permissions

**Alternatives Considered**:
- **Kubernetes (k3s)**: Rejected - overkill for single-server deployment, adds operational complexity
- **Direct systemd services**: Rejected - manual service coordination, no built-in health checks or networking
- **Podman with systemd**: Rejected - less mature tooling, team familiarity with Docker

**Best Practices**:
- Use explicit version tags for all images (no `latest`)
- Set memory limits to prevent OOM on small droplets
- Configure health checks for all services
- Use named volumes for data persistence
- Implement proper shutdown handling with `stop_grace_period`

---

## 2. SSL/TLS Configuration for Webhook Endpoints

### Decision: nginx Reverse Proxy + Let's Encrypt with certbot

**Rationale**:
- nginx provides robust reverse proxy, load balancing, and SSL termination
- Let's Encrypt offers free, automated SSL certificates
- certbot automates certificate renewal (90-day expiration)
- Industry-standard approach with extensive documentation

**Implementation Approach**:
1. Install nginx and certbot on droplet
2. Configure nginx as reverse proxy in front of bot webhook endpoint
3. Use certbot's nginx plugin for automatic certificate provisioning
4. Set up automatic renewal via systemd timer or cron
5. Configure nginx with strong SSL settings (TLS 1.2+, secure ciphers)

**Configuration Details**:
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name bot.yourdomain.com;
    return 301 https://$host$request_uri;
}

# HTTPS webhook endpoint
server {
    listen 443 ssl http2;
    server_name bot.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/bot.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.yourdomain.com/privkey.pem;
    
    # Strong SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://localhost:8080;  # Bot application port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Alternatives Considered**:
- **Traefik**: Rejected - additional learning curve, Docker Compose integration complexity
- **Caddy**: Rejected - less familiar tooling, though automatic HTTPS is attractive
- **Application-level SSL**: Rejected - complicates application code, harder to manage certificates

**Best Practices**:
- Use certbot's `--nginx` plugin for automatic configuration
- Enable HTTP/2 for performance
- Implement rate limiting at nginx level
- Add security headers (HSTS, X-Frame-Options, etc.)
- Monitor certificate expiration (certbot renewal runs twice daily automatically)

---

## 3. Service Orchestration and Auto-Restart

### Decision: Docker Compose restart policies + systemd service wrapper

**Rationale**:
- Docker Compose handles service-level restarts (container crashes)
- systemd ensures Docker Compose itself starts on boot
- Two-layer approach provides robust failure recovery
- Aligns with modern Linux service management

**Implementation Approach**:

**Layer 1: Docker Compose restart policies**
```yaml
services:
  bot:
    restart: unless-stopped
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

**Layer 2: systemd service**
```ini
[Unit]
Description=TooGoodToGo Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/toogoodtogo
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**Alternatives Considered**:
- **Supervisor**: Rejected - redundant with Docker's built-in restart capabilities
- **Manual cron-based monitoring**: Rejected - less reliable, no proper service lifecycle management
- **Cloud provider auto-restart**: Rejected - doesn't handle individual service failures

**Best Practices**:
- Set appropriate `stop_grace_period` for graceful shutdown
- Use health checks to determine actual service readiness
- Implement exponential backoff for restart attempts
- Log restart events for debugging

---

## 4. Database Backup Strategy

### Decision: Automated pg_dump with retention policy + DigitalOcean Volumes snapshots

**Rationale**:
- `pg_dump` provides logical backups with point-in-time consistency
- Automated daily backups via cron/systemd timer
- DigitalOcean Volume snapshots provide additional block-level backup
- Dual strategy balances granular recovery with disaster recovery

**Implementation Approach**:

**Daily Automated Backups**:
```bash
#!/bin/bash
# /opt/toogoodtogo/deployment/scripts/backup.sh

BACKUP_DIR="/opt/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/toogoodtogo_$TIMESTAMP.sql.gz"

# Create backup
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml \
    exec -T postgres pg_dump -U toogoodtogo telegram_marketplace | \
    gzip > "$BACKUP_FILE"

# Verify backup
gunzip -t "$BACKUP_FILE"

# Retain last 7 daily backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

# Upload to object storage (optional)
# s3cmd put "$BACKUP_FILE" s3://my-backups/toogoodtogo/
```

**Systemd Timer**:
```ini
[Unit]
Description=Daily PostgreSQL Backup

[Timer]
OnCalendar=daily
OnCalendar=03:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Alternatives Considered**:
- **DigitalOcean Managed Database backups**: Rejected - adds cost, less control over backup timing
- **WAL archiving with continuous backup**: Rejected - overkill for initial deployment, complex setup
- **Cloud provider backup services**: Considered for future enhancement

**Best Practices**:
- Test restore procedure regularly
- Store backups off-server (DigitalOcean Spaces, S3)
- Encrypt backups containing sensitive data
- Monitor backup success/failure
- Document restore procedure in runbook

---

## 5. Monitoring and Observability

### Decision: Docker health checks + structured logging + optional Prometheus/Grafana

**Rationale**:
- Docker health checks provide basic service availability monitoring
- Structured logging (already implemented via structlog) enables log aggregation
- Prometheus/Grafana optional for metrics visualization
- Phased approach: basic monitoring first, advanced metrics later

**Implementation Approach**:

**Phase 1: Basic Monitoring (Required)**
- Docker health checks for all services
- Application health endpoint (`/health`) returning JSON status
- Structured logs written to files (rotated via Docker logging driver)
- Basic alerting via healthcheck failures

**Phase 2: Advanced Metrics (Optional)**
- Prometheus for metrics collection (app metrics, container metrics)
- Grafana for visualization
- Alert rules for critical conditions (high CPU, memory, error rate)

**Health Check Implementation**:
```yaml
services:
  bot:
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Application Health Endpoint** (to be implemented):
```python
# src/handlers/system/health.py
@app.route('/health')
def health_check():
    return {
        "status": "healthy",
        "version": VERSION,
        "uptime": get_uptime(),
        "dependencies": {
            "postgres": check_postgres_connection(),
            "redis": check_redis_connection()
        }
    }
```

**Alternatives Considered**:
- **Cloud provider monitoring**: Limited customization, vendor lock-in
- **Datadog/New Relic**: Rejected - cost prohibitive for initial deployment
- **ELK Stack**: Rejected - high resource requirements for single-droplet deployment

**Best Practices**:
- Expose health endpoints on internal port only
- Include dependency health in checks
- Implement readiness vs. liveness probes
- Set appropriate timeout values
- Log all health check failures

---

## 6. Zero-Downtime Deployment

### Decision: Blue-Green deployment pattern with Docker Compose

**Rationale**:
- Blue-Green allows testing new version before switching traffic
- Docker Compose supports multiple service instances
- nginx can switch upstream with reload (zero downtime)
- Provides instant rollback capability

**Implementation Approach**:

**Strategy 1: Rolling Update (Simpler, acceptable brief interruption)**
```bash
# Pull new images
docker compose -f docker-compose.prod.yml pull

# Recreate containers with new images
docker compose -f docker-compose.prod.yml up -d --no-deps --build bot

# Old container stops, new starts (brief gap)
```

**Strategy 2: Blue-Green with nginx (True zero-downtime)**
```bash
# 1. Start new version on different port (green)
docker compose -f docker-compose.green.yml up -d

# 2. Wait for health checks to pass
./scripts/health-check.sh green

# 3. Switch nginx upstream from blue to green
nginx -s reload

# 4. Drain and stop blue version
docker compose -f docker-compose.blue.yml down

# 5. Rename green to blue for next deployment
```

**Alternatives Considered**:
- **Load balancer with multiple instances**: Rejected - requires multiple droplets
- **Kubernetes rolling updates**: Rejected - inappropriate for single-server deployment
- **Brief maintenance window**: Acceptable fallback for P1 (basic deployment)

**Best Practices**:
- Always validate health before switching traffic
- Implement automatic rollback on health check failure
- Maintain database backward compatibility during schema changes
- Version container images with Git SHA or semantic version
- Test deployment procedure in staging environment

**Trade-off Analysis**:
- **P1 (Basic Deployment)**: Accept brief downtime (~30 seconds) during deployment for simplicity
- **P3 (Zero-Downtime)**: Implement blue-green pattern once basic deployment is stable

---

## 7. Environment Variable Management

### Decision: `.env` file + Docker Compose env_file + secrets in DigitalOcean

**Rationale**:
- Docker Compose natively supports `.env` files
- Secrets stored outside Git (`.env` in `.gitignore`)
- DigitalOcean provides secure way to manage droplet secrets
- Template file (`.env.production.template`) documents required variables

**Implementation Approach**:

**Template File** (checked into Git):
```bash
# .env.production.template
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_WEBHOOK_URL=https://bot.yourdomain.com/webhook
DATABASE_URL=postgresql://toogoodtogo:${DB_PASSWORD}@postgres:5432/telegram_marketplace
REDIS_URL=redis://redis:6379
STRIPE_API_KEY=<your-stripe-key>
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Actual File** (on droplet, not in Git):
```bash
# /opt/toogoodtogo/.env.production
TELEGRAM_BOT_TOKEN=110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
# ... actual secrets
```

**Docker Compose Usage**:
```yaml
services:
  bot:
    env_file:
      - .env.production
```

**Alternatives Considered**:
- **Docker secrets**: Requires Docker Swarm mode, unnecessary complexity
- **HashiCorp Vault**: Rejected - overkill for single-server deployment
- **Hardcoded in docker-compose.yml**: Rejected - security risk

**Best Practices**:
- Never commit actual secrets to Git
- Rotate secrets regularly (quarterly minimum)
- Use different secrets for dev/staging/production
- Document all required environment variables in template
- Validate required environment variables at application startup

---

## 8. Firewall Configuration

### Decision: DigitalOcean Cloud Firewall + ufw on droplet

**Rationale**:
- Defense in depth: cloud-level + host-level firewalls
- DigitalOcean Cloud Firewall is free and managed
- ufw provides simple interface to iptables
- Restricts attack surface to minimum required ports

**Implementation Approach**:

**DigitalOcean Cloud Firewall Rules**:
- Inbound: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Outbound: All (for package updates, external APIs)

**ufw Configuration**:
```bash
# Enable ufw
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (change port if using non-standard)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
```

**Alternatives Considered**:
- **iptables directly**: Rejected - ufw provides simpler interface
- **Cloud firewall only**: Rejected - missing host-level protection
- **fail2ban**: Considered for future enhancement (SSH brute-force protection)

**Best Practices**:
- Use DigitalOcean Cloud Firewall for primary protection
- Configure ufw as secondary layer
- Limit SSH access to specific IPs if possible
- Regularly review firewall rules
- Monitor firewall logs for suspicious activity

---

## 9. Deployment Workflow

### Decision: Git-based deployment with GitHub Actions

**Rationale**:
- Automate deployment on Git tag push
- Ensures CI tests pass before deployment
- Provides audit trail of deployments
- Integrates with existing GitHub repository

**Implementation Approach**:

**GitHub Actions Workflow**:
```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest
      
      - name: Deploy to DigitalOcean
        env:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          DROPLET_IP: ${{ secrets.DROPLET_IP }}
        run: |
          # SSH into droplet and run deployment script
          ssh -i ssh_key deploy@$DROPLET_IP '/opt/toogoodtogo/deployment/scripts/deploy.sh'
```

**Deployment Script** (on droplet):
```bash
#!/bin/bash
# /opt/toogoodtogo/deployment/scripts/deploy.sh

set -e  # Exit on error

# Pull latest code
cd /opt/toogoodtogo
git fetch --tags
git checkout $DEPLOY_TAG

# Backup database
./deployment/scripts/backup.sh

# Pull new Docker images
docker compose -f docker-compose.prod.yml pull

# Run migrations
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head

# Deploy new version
docker compose -f docker-compose.prod.yml up -d

# Validate health
./deployment/scripts/health-check.sh

# Cleanup old images
docker image prune -f
```

**Alternatives Considered**:
- **Manual deployment**: Rejected - error-prone, no audit trail
- **Jenkins/GitLab CI**: Rejected - additional infrastructure to maintain
- **Ansible/Terraform**: Considered for future scaling

**Best Practices**:
- Always run tests before deployment
- Automated database backup before deployment
- Health check validation after deployment
- Automatic rollback on deployment failure
- Tag-based deployment for version tracking

---

## 10. Redis Persistence Configuration

### Decision: RDB snapshots with 5-minute save interval

**Rationale**:
- Chosen in spec clarification (Option A)
- Balances performance with data safety
- Acceptable data loss window (max 5 minutes)
- Lower disk I/O than AOF

**Implementation Approach**:

**Redis Configuration**:
```conf
# redis.conf
save 300 10          # Save if 10 keys changed in 5 minutes
save 60 10000        # Save if 10,000 keys changed in 1 minute
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data
```

**Docker Compose Integration**:
```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server /etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./deployment/redis/redis.conf:/etc/redis/redis.conf:ro
```

**Alternatives**:
- **AOF (Append-Only File)**: Rejected - higher I/O overhead, more complex recovery
- **No persistence**: Rejected - rate limit data would be lost on restart

**Best Practices**:
- Include Redis data directory in backup strategy
- Monitor RDB save failures
- Set appropriate memory limits
- Use `maxmemory-policy allkeys-lru` for eviction

---

## Summary of Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Container Orchestration | Docker Compose v2 | Simple, already in use, production-ready |
| Reverse Proxy | nginx | Industry standard, SSL termination, performant |
| SSL/TLS | Let's Encrypt + certbot | Free, automated renewal, trusted CA |
| Auto-restart | Docker restart policies + systemd | Two-layer resilience |
| Database Backup | pg_dump + cron/systemd timer | Proven, flexible, easy restore |
| Monitoring | Docker health checks + structured logs | Simple, sufficient for initial deployment |
| Deployment | GitHub Actions + SSH deployment script | Automated, auditable, integrates with Git |
| Firewall | DigitalOcean Cloud Firewall + ufw | Defense in depth |
| Secrets Management | .env files (gitignored) | Simple, Docker Compose native |
| Redis Persistence | RDB snapshots (5-min interval) | Performance/safety balance |

## Open Questions / Future Enhancements

1. **Monitoring**: Consider adding Prometheus/Grafana once basic deployment is stable
2. **Scaling**: Plan for multi-droplet deployment if user load exceeds single-server capacity
3. **CI/CD**: Explore automated integration tests in staging environment before production
4. **Backups**: Evaluate off-site backup storage (DigitalOcean Spaces, S3)
5. **Security**: Consider fail2ban for SSH brute-force protection
6. **Database**: Evaluate DigitalOcean Managed Database for PostgreSQL if maintenance becomes burden

## References

- [Docker Compose Production Best Practices](https://docs.docker.com/compose/production/)
- [Let's Encrypt with nginx](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal)
- [systemd Service Files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [PostgreSQL Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
- [Redis Persistence](https://redis.io/docs/manual/persistence/)
- [DigitalOcean Cloud Firewalls](https://docs.digitalocean.com/products/networking/firewalls/)
- [GitHub Actions Deployment](https://docs.github.com/en/actions/deployment/about-deployments)
