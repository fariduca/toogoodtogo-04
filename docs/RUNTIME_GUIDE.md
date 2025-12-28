# TooGoodToGo Runtime Operations Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-04  
**For**: Production Operations Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Daily Operations](#daily-operations)
4. [Service Management](#service-management)
5. [Deployment Operations](#deployment-operations)
6. [Backup & Recovery](#backup--recovery)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Troubleshooting](#troubleshooting)
9. [Secret Rotation](#secret-rotation)
10. [Emergency Procedures](#emergency-procedures)

---

## Overview

This guide provides operational procedures for maintaining the TooGoodToGo Telegram marketplace bot in production. It covers routine operations, troubleshooting, and emergency procedures.

### System Components

| Component | Container | Port | Purpose |
|-----------|-----------|------|---------|
| Bot | toogoodtogo_bot | 8000 | Telegram webhook handler |
| PostgreSQL | toogoodtogo_postgres | 5432 | Persistent data storage |
| Redis | toogoodtogo_redis | 6379 | Rate limiting, ephemeral data |
| nginx | toogoodtogo_nginx | 80/443 | Reverse proxy, SSL termination |

### Critical Paths

- **Webhook**: Internet → nginx → bot (port 8000)
- **Database**: bot → PostgreSQL (internal)
- **Cache**: bot → Redis (internal)

---

## Architecture

### Network Topology

```
Internet
    │
    ▼ (HTTPS:443)
┌───────────────┐
│    nginx      │ ──────────────────────┐
│  (SSL/proxy)  │                       │
└───────────────┘                       │
    │                                   │
    ▼ (HTTP:8000 internal)              │
┌───────────────┐                       │
│     Bot       │◄──────────────────────┘
│  (Python app) │     (internal network)
└───────────────┘
    │           │
    ▼           ▼
┌─────────┐ ┌─────────┐
│PostgreSQL│ │  Redis  │
│ (5432)  │ │ (6379)  │
└─────────┘ └─────────┘
```

### File System Layout

```
/opt/toogoodtogo/                    # Application root
├── deployment/
│   ├── docker-compose.prod.yml      # Main compose file
│   ├── .env.production              # Environment secrets
│   ├── nginx/                       # nginx configuration
│   ├── redis/                       # Redis configuration
│   ├── systemd/                     # systemd services
│   ├── scripts/                     # Operational scripts
│   └── monitoring/                  # Prometheus/Grafana
└── src/                             # Application source

/opt/backups/postgres/               # Database backups
/var/log/toogoodtogo/                # Deployment logs
```

---

## Daily Operations

### Morning Checklist

```bash
# 1. Verify all services healthy
/opt/toogoodtogo/deployment/scripts/health-check.sh

# 2. Check disk space
df -h /opt/toogoodtogo /opt/backups /var/lib/docker

# 3. Verify backup ran successfully (timer runs at 3:00 AM)
systemctl status toogoodtogo-backup.timer
ls -la /opt/backups/postgres/ | tail -5

# 4. Check for any errors in logs
docker compose -f /opt/toogoodtogo/deployment/docker-compose.prod.yml logs --since "12 hours ago" | grep -i error | tail -20
```

### Weekly Checklist

```bash
# 1. Review disk usage trends
du -sh /opt/backups/postgres/*

# 2. Check SSL certificate expiry
certbot certificates

# 3. Review system updates
apt update && apt list --upgradable

# 4. Test backup restoration (on staging if available)
# /opt/toogoodtogo/deployment/scripts/restore.sh --dry-run <latest-backup>
```

---

## Service Management

### Starting Services

```bash
# Start via systemd (recommended - auto-restart on failure)
systemctl start toogoodtogo

# Or start directly via Docker Compose
cd /opt/toogoodtogo/deployment
docker compose -f docker-compose.prod.yml up -d
```

### Stopping Services

```bash
# Stop via systemd
systemctl stop toogoodtogo

# Or stop via Docker Compose (graceful 30-second shutdown)
docker compose -f docker-compose.prod.yml down
```

### Restarting Services

```bash
# Restart entire stack
systemctl restart toogoodtogo

# Restart specific service
docker compose -f docker-compose.prod.yml restart bot
docker compose -f docker-compose.prod.yml restart nginx
```

### Viewing Service Status

```bash
# Overall status
systemctl status toogoodtogo
docker compose -f docker-compose.prod.yml ps

# Detailed container status
docker inspect toogoodtogo_bot | jq '.[0].State'
```

---

## Deployment Operations

### Standard Deployment

```bash
# 1. SSH to production server
ssh deploy@<server-ip>

# 2. Deploy new version (creates backup automatically)
cd /opt/toogoodtogo/deployment/scripts
./deploy.sh v1.2.3

# 3. Monitor logs during deployment
docker compose -f docker-compose.prod.yml logs -f bot
```

### Rollback Procedure

```bash
# Automatic rollback (recommended)
./rollback.sh v1.2.2

# Manual rollback (if automatic fails)
git checkout tags/v1.2.2 --force
docker compose -f docker-compose.prod.yml up -d --build
```

### Skip Options

```bash
# Skip pre-deployment backup (not recommended)
./deploy.sh v1.2.3 --skip-backup

# Skip database migrations
./deploy.sh v1.2.3 --skip-migration
```

---

## Backup & Recovery

### Backup Locations

```bash
# Automatic daily backups (3:00 AM via systemd timer)
/opt/backups/postgres/

# Backup naming convention
toogoodtogo_YYYYMMDD_HHMMSS.sql.gz          # Scheduled
toogoodtogo_YYYYMMDD_HHMMSS_pre_deployment.sql.gz  # Pre-deploy
```

### Manual Backup

```bash
# Create immediate backup
/opt/toogoodtogo/deployment/scripts/backup.sh manual

# Verify backup
gunzip -t /opt/backups/postgres/latest-backup.sql.gz
```

### Restore Procedure

```bash
# 1. Stop the application
systemctl stop toogoodtogo

# 2. Restore from backup
/opt/toogoodtogo/deployment/scripts/restore.sh /opt/backups/postgres/backup-file.sql.gz

# 3. Restart application
systemctl start toogoodtogo

# 4. Verify health
/opt/toogoodtogo/deployment/scripts/health-check.sh
```

### Backup Retention

- **Daily backups**: Kept for 7 days
- **Pre-deployment backups**: Kept until cleanup
- **Recommended**: Copy critical backups to off-site storage

---

## Monitoring & Alerting

### Health Check Endpoint

```bash
# Local health check
curl -s http://127.0.0.1:8000/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "version": "v1.2.3",
#   "uptime_seconds": 86400,
#   "dependencies": {
#     "postgres": {"status": "healthy", "response_time_ms": 5},
#     "redis": {"status": "healthy", "response_time_ms": 2}
#   }
# }
```

### Prometheus/Grafana (Optional)

```bash
# Start monitoring stack
docker compose -f monitoring/docker-compose.monitoring.yml up -d

# Access:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Log Monitoring

```bash
# Real-time log following
docker compose -f docker-compose.prod.yml logs -f

# Error pattern search
docker compose -f docker-compose.prod.yml logs | grep -E "(ERROR|CRITICAL)"

# Deployment audit log
tail -f /var/log/toogoodtogo/deployment.log
```

---

## Troubleshooting

### Common Issues

#### 1. Health Check Failing

```bash
# Check which dependency is unhealthy
curl -s http://127.0.0.1:8000/health | jq

# If PostgreSQL unhealthy:
docker compose exec postgres pg_isready -U toogoodtogo
docker compose logs postgres --tail=50

# If Redis unhealthy:
docker compose exec redis redis-cli ping
docker compose logs redis --tail=50
```

#### 2. Bot Not Responding

```bash
# Check container status
docker ps -a | grep toogoodtogo_bot

# View bot logs
docker compose logs bot --tail=100

# Check for OOM or resource issues
docker stats toogoodtogo_bot --no-stream
```

#### 3. SSL Certificate Issues

```bash
# Check certificate status
certbot certificates

# Renew certificate
certbot renew

# If renewal fails, check nginx
systemctl status nginx
cat /var/log/letsencrypt/letsencrypt.log
```

#### 4. Disk Space Issues

```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -f

# Remove old backups (keep last 7)
ls -t /opt/backups/postgres/*.sql.gz | tail -n +8 | xargs rm -f
```

#### 5. Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection from bot container
docker compose exec bot python -c "from src.storage.database import engine; print('OK')"

# Check PostgreSQL logs
docker compose logs postgres --since "1 hour ago"
```

---

## Secret Rotation

### Rotating Database Password

```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)
echo "New password: $NEW_PASSWORD"

# 2. Update PostgreSQL user password
docker compose exec postgres psql -U toogoodtogo -c \
  "ALTER USER toogoodtogo PASSWORD '$NEW_PASSWORD';"

# 3. Update .env.production
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASSWORD/" \
  /opt/toogoodtogo/deployment/.env.production

# 4. Restart application
systemctl restart toogoodtogo

# 5. Verify connection
/opt/toogoodtogo/deployment/scripts/health-check.sh
```

### Rotating Telegram Bot Token

⚠️ **Warning**: This requires creating a new bot or regenerating the token via BotFather.

```bash
# 1. Get new token from @BotFather (/token command)

# 2. Update .env.production
nano /opt/toogoodtogo/deployment/.env.production
# Change TELEGRAM_BOT_TOKEN=<new-token>

# 3. Update webhook URL with new bot
# (via @BotFather or Telegram API)

# 4. Restart application
systemctl restart toogoodtogo
```

### Rotating Stripe API Key

```bash
# 1. Get new API key from Stripe Dashboard

# 2. Update .env.production
nano /opt/toogoodtogo/deployment/.env.production
# Change STRIPE_API_KEY=<new-key>

# 3. Restart application
systemctl restart toogoodtogo

# 4. Test a payment flow
```

### Rotating SECRET_KEY

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update .env.production
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" \
  /opt/toogoodtogo/deployment/.env.production

# 3. Restart application (note: may invalidate sessions)
systemctl restart toogoodtogo
```

---

## Emergency Procedures

### Complete Service Outage

```bash
# 1. Check systemd service
systemctl status toogoodtogo

# 2. Check Docker
docker ps -a
docker compose -f docker-compose.prod.yml ps

# 3. Attempt restart
systemctl restart toogoodtogo

# 4. If restart fails, check logs
journalctl -u toogoodtogo --since "10 minutes ago"
docker compose logs --since "10 minutes ago"

# 5. Manual start
docker compose -f docker-compose.prod.yml up -d
```

### Database Corruption

```bash
# 1. Stop application
systemctl stop toogoodtogo

# 2. Check PostgreSQL integrity
docker compose up postgres
docker compose exec postgres pg_isready

# 3. If corrupted, restore from backup
./restore.sh /opt/backups/postgres/<latest-backup>.sql.gz

# 4. Restart application
systemctl start toogoodtogo
```

### Rollback After Failed Deployment

```bash
# 1. Automatic rollback should trigger on health check failure
# Check if rollback occurred:
cat /var/log/toogoodtogo/deployment.log | tail -50

# 2. If automatic rollback failed:
./rollback.sh <previous-version>

# 3. Verify health
./health-check.sh
```

### Server Compromise Suspected

```bash
# 1. Take server offline (if possible)
# Via DigitalOcean console: Power Off

# 2. If must stay online, block incoming traffic
ufw default deny incoming

# 3. Rotate ALL secrets immediately (from secure workstation)
# - Telegram Bot Token (via BotFather)
# - Database password
# - Stripe API keys
# - SECRET_KEY

# 4. Review access logs
cat /var/log/auth.log | tail -100

# 5. Contact security team
```

---

## Edge Case Handling

### Disk Space Exhaustion

```bash
# Symptoms: Containers fail to start, backups fail
# Check: df -h

# Immediate mitigation:
docker system prune -f
rm /opt/backups/postgres/*.sql.gz.old 2>/dev/null

# Long-term: Resize droplet or add volume
```

### Redis Memory Exhaustion

```bash
# Symptoms: Rate limiting fails, degraded health status
# Check: docker compose exec redis redis-cli info memory

# Immediate mitigation:
docker compose exec redis redis-cli flushdb

# Long-term: Increase maxmemory in redis.conf
```

### Network Connectivity Loss

```bash
# Symptoms: Health checks pass but webhooks fail
# Check: 
curl -I https://api.telegram.org
ping google.com

# Resolution:
# - Check DigitalOcean network status
# - Verify firewall rules: ufw status
# - Check nginx: systemctl status nginx
```

### Missing Environment Variables

```bash
# Symptoms: Bot fails to start
# Check:
docker compose logs bot | head -50

# Resolution:
# Verify all required vars in .env.production:
cat .env.production | grep -E "^[A-Z]"

# Required minimum:
# - TELEGRAM_BOT_TOKEN
# - POSTGRES_PASSWORD
# - SECRET_KEY
```

---

## Contact Information

| Role | Contact | When to Contact |
|------|---------|-----------------|
| On-Call Engineer | [phone/slack] | P1/P2 incidents |
| DevOps Lead | [email] | Architecture questions |
| Security Team | [email] | Security incidents |
| DigitalOcean Support | [support portal] | Infrastructure issues |

---

**Document Version**: 1.0.0  
**Last Reviewed**: 2025-01-04  
**Next Review**: 2025-04-04
