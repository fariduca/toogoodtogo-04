# Quickstart Guide: DigitalOcean Production Deployment

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)  
**Version**: 1.0.0  
**Date**: 2025-12-28

## Overview

This guide walks you through deploying the TooGoodToGo Telegram marketplace bot to a DigitalOcean droplet for the first time **using long polling**. No public HTTP/S ingress or TLS is required for this baseline; all traffic is outbound to Telegram plus private DB/Redis networking.

**Time Required**: ~45 minutes  
**Skill Level**: Intermediate (familiarity with Linux, Docker, and command line required)

---

## Prerequisites

### 1. DigitalOcean Account & Droplet

- [ ] DigitalOcean account created
- [ ] Droplet provisioned with these specifications:
  - **OS**: Ubuntu 22.04 LTS
  - **Size**: At least 4GB RAM, 2 vCPUs, 80GB SSD
  - **Region**: Choose based on user location
  - **SSH Key**: Added to droplet during creation

### 2. Domain Name (optional, webhook-only)

- Only needed if you later switch to webhook + HTTPS. For polling you can skip this entirely.

### 3. Telegram Bot Created

- [ ] Bot created via [@BotFather](https://t.me/botfather)
- [ ] Bot token saved securely (format: `110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`)
- [ ] Bot username noted (e.g., `@YourMarketplaceBot`)

### 4. Stripe Account (for payments)

- [ ] Stripe account created
- [ ] API keys obtained (publishable and secret key)
- [ ] Test mode vs. live mode decided

### 5. Local Development Machine

- [ ] SSH client installed
- [ ] Git installed (to push code)
- [ ] SSH key pair generated and added to DigitalOcean

---

## Step 1: Initial Droplet Access

### 1.1 SSH into Droplet

```bash
ssh root@<droplet-ip-address>
```

**Expected**: Successfully connected to droplet as root user

### 1.2 Update System Packages

```bash
apt update && apt upgrade -y
```

**Expected**: All packages updated (may take 5-10 minutes)

---

## Step 2: Run Automated Setup Script

### 2.1 Clone Repository

```bash
# Create application directory
mkdir -p /opt/toogoodtogo

# Clone repository (replace with your fork if applicable)
git clone https://github.com/yourusername/toogoodtogo.git /opt/toogoodtogo

# Navigate to deployment scripts
cd /opt/toogoodtogo/deployment/scripts
```

### 2.2 Run Setup Script (polling baseline)

```bash
chmod +x setup-droplet.sh
./setup-droplet.sh
```

**What this does**:
- Installs Docker and Docker Compose
- Configures firewall (ufw) to allow only SSH inbound (no HTTP/S needed for polling)
- Creates directory structure
- Sets up environment configuration for long polling (no TLS/webhook)

**Interactive Prompts** (have these ready):

```
Enter Telegram Bot Token: <paste-your-token>
Enter PostgreSQL Password: <create-strong-password>
Enter Secret Key (optional auto-generate): <leave blank to auto-generate>
Enter Stripe API Key (optional): <press enter to skip if not used>
```

**Expected Output**:
```
[2025-12-28 09:18:15] INFO: Setup complete - system ready for production
```

**Time**: 10-15 minutes

---

## Step 3: Verify Installation

### 3.1 Check Docker Installation

```bash
docker --version
docker compose version
```

**Expected**:
```
Docker version 24.0.7
Docker Compose version v2.23.0
```

### 3.2 Check Firewall Status

```bash
ufw status
```

**Expected**:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
```

### 3.3 Check SSL Certificate

```bash
certbot certificates
```

**Expected**:
```
Found the following certs:
  Certificate Name: bot.yourdomain.com
    Domains: bot.yourdomain.com
    Expiry Date: 2026-03-28 (VALID: 89 days)
```

---

## Step 4: Deploy Application

### 4.1 Checkout Stable Release

```bash
cd /opt/toogoodtogo

# List available tags
git fetch --tags
git tag

# Checkout latest stable release (e.g., v1.0.0)
git checkout v1.0.0
```

### 4.2 Review Configuration

```bash
# Check environment file
cat /opt/toogoodtogo/deployment/.env.production

# Verify all required variables are set
```

**Required Variables (polling)**:
- `TELEGRAM_BOT_TOKEN`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (DATABASE_URL derived)
- `REDIS_URL`
- `SECRET_KEY`
- `ENVIRONMENT=production`

### 4.3 Start Services (no ingress)

```bash
cd /opt/toogoodtogo/deployment

# Start core services (bot, postgres, redis). Nginx profile is disabled by default.
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

**Expected Output**:
```
[+] Running 3/3
 ✔ Container toogoodtogo_postgres  Started
 ✔ Container toogoodtogo_redis     Started
 ✔ Container toogoodtogo_bot       Started
```

**Time**: 3-5 minutes for initial image pull and service startup

### 4.4 Run Database Migrations

```bash
# Run Alembic migrations
docker compose -f docker-compose.prod.yml exec bot alembic upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add offers table
```

---

## Step 5: Verify Deployment

### 5.1 Check Service Health

```bash
cd /opt/toogoodtogo/deployment/scripts
./health-check.sh
```

**Expected Output**:
```
[2025-12-28 10:35:05] INFO: All services healthy
```

### 5.2 Check Docker Container Status

```bash
docker ps
```

**Expected**: All containers showing "healthy" status

### 5.3 Test Telegram Bot

1. Open Telegram
2. Search for your bot (`@YourMarketplaceBot`)
3. Send `/start` command
4. **Expected**: Bot responds with welcome message

### 5.4 Verify Bot Interaction (polling)

1. Open Telegram
2. Search for your bot (`@YourMarketplaceBot`)
3. Send `/start` command
4. **Expected**: Bot responds with welcome message

---

## Step 6: Enable Auto-Restart

### 6.1 Create Systemd Service

```bash
# Copy systemd service file
cp /opt/toogoodtogo/deployment/systemd/toogoodtogo.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service (start on boot)
systemctl enable toogoodtogo

# Start service
systemctl start toogoodtogo

# Check status
systemctl status toogoodtogo
```

**Expected**:
```
● toogoodtogo.service - TooGoodToGo Telegram Bot
   Loaded: loaded (/etc/systemd/system/toogoodtogo.service; enabled)
   Active: active (exited) since Sat 2025-12-28 10:40:00 UTC
```

### 6.2 Test Auto-Restart

```bash
# Reboot droplet
reboot

# Wait 2-3 minutes, then SSH back in
ssh root@<droplet-ip-address>

# Check services restarted automatically
docker ps
```

**Expected**: All containers running after reboot

---

## Step 7: Configure Automated Backups

### 7.1 Create Backup Directory

```bash
mkdir -p /opt/backups/postgres
chown -R root:root /opt/backups
chmod 750 /opt/backups
```

### 7.2 Test Manual Backup

```bash
cd /opt/toogoodtogo/deployment/scripts
./backup.sh manual
```

**Expected**:
```
[2025-12-28 11:00:55] INFO: Backup complete: /opt/backups/postgres/toogoodtogo_20251228_110055.sql.gz
```

### 7.3 Schedule Daily Backups

```bash
# Create systemd timer for backups
cp /opt/toogoodtogo/deployment/systemd/toogoodtogo-backup.timer /etc/systemd/system/
cp /opt/toogoodtogo/deployment/systemd/toogoodtogo-backup.service /etc/systemd/system/

# Enable timer
systemctl enable toogoodtogo-backup.timer
systemctl start toogoodtogo-backup.timer

# Verify timer is active
systemctl list-timers --all | grep toogoodtogo
```

**Expected**:
```
Sat 2025-12-29 03:00:00 UTC  12h left  - - toogoodtogo-backup.timer
```

---

## Step 8: Configure Monitoring (Optional)

### 8.1 View Application Logs

Docker container logs are stored with rotation (7-day retention by default):

```bash
# View recent logs (last 100 lines)
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs --tail=100

# Follow logs in real-time
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs -f

# View logs for a specific service
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs bot --tail=50
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs postgres --tail=50
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs redis --tail=50
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs nginx --tail=50

# View logs with timestamps
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs -t --tail=50

# View logs since a specific time
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs --since="2025-01-01T00:00:00"

# Search for errors in logs
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs bot 2>&1 | grep -i error
```

**Log File Locations** (JSON format, managed by Docker):
```bash
# Find actual log files on disk
docker inspect --format='{{.LogPath}}' toogoodtogo_bot
docker inspect --format='{{.LogPath}}' toogoodtogo_postgres

# Log files are typically at:
# /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

**Log Retention Configuration** (in docker-compose.prod.yml):
- Bot: 20MB max size, 5 files (100MB total)
- PostgreSQL: 5MB max size, 3 files (15MB total)
- Redis: 5MB max size, 2 files (10MB total)
- nginx: 10MB max size, 3 files (30MB total) - webhook profile only
- nginx: 20MB max size, 5 files (100MB total)

### 8.2 View Deployment Logs

```bash
# View deployment audit log
tail -f /var/log/toogoodtogo/deployment.log

# View last 50 deployment log entries
tail -50 /var/log/toogoodtogo/deployment.log

# Search for specific deployment actions
grep "deploy" /var/log/toogoodtogo/deployment.log
grep "backup" /var/log/toogoodtogo/deployment.log
grep "ERROR" /var/log/toogoodtogo/deployment.log
```

### 8.3 View Systemd Service Logs

```bash
# View systemd service logs
journalctl -u toogoodtogo.service -f

# View logs since last boot
journalctl -u toogoodtogo.service -b

# View logs from last hour
journalctl -u toogoodtogo.service --since "1 hour ago"

# View backup timer logs
journalctl -u toogoodtogo-backup.timer
journalctl -u toogoodtogo-backup.service
```

### 8.4 Setup Prometheus/Grafana (Advanced - Optional)

```bash
cd /opt/toogoodtogo

# Start monitoring stack
docker compose -f deployment/monitoring/docker-compose.monitoring.yml up -d

# Access Grafana at http://<droplet-ip>:3000
# Default credentials: admin/admin
```

---

## Step 9: Security Hardening

### 9.1 Change Default Passwords

```bash
# Update PostgreSQL password
# 1. Edit .env.production with new password
# 2. Update postgres container
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml restart postgres
```

### 9.2 Configure fail2ban (SSH Protection)

```bash
apt install fail2ban -y

# Copy jail configuration
cp /opt/toogoodtogo/deployment/fail2ban/jail.local /etc/fail2ban/

# Restart fail2ban
systemctl restart fail2ban

# Check status
fail2ban-client status sshd
```

### 9.3 Restrict SSH Access (Optional but Recommended)

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Set these values:
# PermitRootLogin no
# PasswordAuthentication no
# AllowUsers yourusername

# Restart SSH
systemctl restart sshd
```

**Warning**: Ensure you have sudo access with your user before disabling root login!

---

## Step 10: Test Deployment Workflow

### 10.1 Create Test Deployment

```bash
# Assume new version v1.0.1 is tagged in Git
cd /opt/toogoodtogo/deployment/scripts

# Deploy new version
./deploy.sh v1.0.1
```

**Expected**:
```
[2025-12-28 14:30:15] INFO: Deployment successful: v1.0.1
```

### 10.2 Test Rollback

```bash
# Rollback to previous version
./rollback.sh v1.0.0
```

**Expected**:
```
[2025-12-28 14:35:05] INFO: Rollback successful: v1.0.0
```

---

## Troubleshooting

### Issue: Bot Not Responding

**Symptoms**: Telegram bot doesn't respond to messages

**Checks**:
```bash
# 1. Check bot container is running
docker ps | grep bot

# 2. Check bot logs for errors
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs bot

# 3. Verify webhook is configured
curl https://bot.yourdomain.com/webhook

# 4. Test database connection
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml exec bot python -c "from src.storage.database import init_db; init_db()"
```

**Solution**: Check that:
- Telegram bot token is correct
- Webhook URL is accessible from internet
- SSL certificate is valid
- Database migrations have run

---

### Issue: SSL Certificate Failed

**Symptoms**: certbot fails to obtain certificate

**Checks**:
```bash
# Check DNS resolution
dig bot.yourdomain.com

# Check port 80 is accessible
curl http://bot.yourdomain.com
```

**Solution**:
- Ensure DNS A record points to droplet IP
- Ensure firewall allows port 80 (HTTP)
- Wait for DNS propagation (up to 24 hours)

---

### Issue: High Memory Usage

**Symptoms**: Droplet running out of memory

**Checks**:
```bash
# Check memory usage
free -h

# Check per-container memory
docker stats
```

**Solution**:
- Add memory limits to docker-compose.prod.yml
- Upgrade droplet size
- Optimize application (reduce workers)

---

### Issue: Database Backup Fails

**Symptoms**: Backup script exits with error

**Checks**:
```bash
# Check disk space
df -h /opt/backups

# Check PostgreSQL is running
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml ps postgres

# Test backup manually
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml exec postgres pg_dump -U toogoodtogo telegram_marketplace
```

**Solution**:
- Free up disk space
- Check PostgreSQL credentials
- Verify backup directory permissions

---

## Next Steps

### Production Readiness Checklist

- [ ] All services passing health checks
- [ ] SSL certificate configured and auto-renewing
- [ ] Automated daily backups running
- [ ] Service auto-restart on boot verified
- [ ] Deployment and rollback tested
- [ ] Bot responds to Telegram commands
- [ ] Monitoring configured
- [ ] Security hardening applied
- [ ] Documentation reviewed by team
- [ ] Disaster recovery plan documented

### Ongoing Maintenance

**Daily**:
- Monitor application logs for errors
- Check health status

**Weekly**:
- Review resource usage (CPU, memory, disk)
- Test backup restoration (restore to staging)

**Monthly**:
- Review and update dependencies
- Rotate secrets (bot token, API keys)
- Review firewall rules

**Quarterly**:
- Update system packages
- Review SSL certificate expiration
- Performance testing

---

## Additional Resources

### Documentation

- [spec.md](spec.md) - Feature specification
- [plan.md](plan.md) - Implementation plan
- [research.md](research.md) - Technology decisions
- [contracts/health-check-api.md](contracts/health-check-api.md) - Health check API
- [contracts/deployment-scripts.md](contracts/deployment-scripts.md) - Script interfaces

### External Resources

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [DigitalOcean Tutorials](https://docs.digitalocean.com/products/droplets/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [PostgreSQL Backup Guide](https://www.postgresql.org/docs/current/backup.html)
- [nginx Configuration Guide](https://nginx.org/en/docs/)

### Support

- GitHub Issues: `https://github.com/yourusername/toogoodtogo/issues`
- Team Chat: [Your team communication channel]
- On-call: [Emergency contact information]

---

## Appendix A: Complete Command Reference

```bash
# Service Management
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml up -d       # Start services
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml down        # Stop services
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml restart     # Restart services
docker compose -f /opt/toogoodtogo/docker-compose.prod.yml logs -f     # View logs

# Deployment
cd /opt/toogoodtogo/deployment/scripts
./deploy.sh v1.0.0                    # Deploy version
./rollback.sh v0.9.0                  # Rollback to version
./health-check.sh                     # Check service health
./backup.sh                           # Create backup
./restore.sh <backup-file>            # Restore from backup

# System
systemctl status toogoodtogo          # Check service status
systemctl restart toogoodtogo         # Restart service
journalctl -u toogoodtogo -f          # View systemd logs

# SSL Certificate
certbot certificates                  # Check certificate status
certbot renew                         # Manually renew certificate
certbot renew --dry-run               # Test renewal process

# Firewall
ufw status                            # Check firewall rules
ufw allow <port>                      # Allow port
ufw deny <port>                       # Deny port
```

---

**Version**: 1.0.0  
**Last Updated**: 2025-12-28  
**Maintained By**: DevOps Team
