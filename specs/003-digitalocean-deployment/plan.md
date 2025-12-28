# Implementation Plan: DigitalOcean Production Deployment

**Branch**: `003-digitalocean-deployment` | **Date**: 2025-12-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-digitalocean-deployment/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Deploy the Telegram marketplace backend application (Python 3.12+ with python-telegram-bot) to a DigitalOcean droplet along with PostgreSQL and Redis. The deployment will use Docker Compose for service orchestration, implement automatic service restarts, configure SSL/TLS for webhook endpoints, and establish monitoring and backup strategies. The deployment approach prioritizes reliability and operational simplicity for initial production use.

## Technical Context

**Language/Version**: Python 3.12+ (existing application runtime)  
**Primary Dependencies**: Docker Engine 24+, Docker Compose v2, nginx (reverse proxy), certbot (SSL/TLS)  
**Storage**: PostgreSQL 16 (persistent data), Redis 7 with RDB snapshots (cache + rate limiting)  
**Testing**: pytest (application tests), docker-compose health checks, deployment validation scripts  
**Target Platform**: DigitalOcean Droplet - Ubuntu 22.04 LTS (4GB RAM, 2 vCPUs, 80GB SSD minimum)  
**Project Type**: Infrastructure/DevOps - single droplet deployment with containerized services  
**Performance Goals**: Bot response <2s under normal load, DB queries <500ms for 95% requests, health checks <100ms  
**Constraints**: 99.5% uptime target, service restart <5 min after reboot, deployment time <15 min, zero data loss during planned maintenance  
**Scale/Scope**: Initial production deployment supporting <100 concurrent users, single-region deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Event-Driven Minimal Core
✅ **PASS** - Deployment does not modify application architecture. Existing bot core and handler modules remain unchanged.

### Principle II: Test-First & Contracted Handlers
✅ **PASS** - Application tests (unit/integration/contract) already exist and will be run in CI before deployment. Deployment itself adds infrastructure tests (health checks, service availability validation).

### Principle III: Secure & Privacy-Conscious Interaction
⚠️ **ATTENTION REQUIRED** - Deployment must implement:
- SSL/TLS for webhook endpoints (FR-015)
- Environment variable management for secrets (FR-011, no secrets in code/Git)
- Firewall configuration to restrict access (FR-016)
- Structured logging with PII scrubbing (FR-010)
- Token rotation mechanism (mentioned in constitution)

**Gate Decision**: PASS with requirements - security constraints from constitution are explicitly addressed in functional requirements.

### Technical & Security Constraints
✅ **PASS** - Deployment maintains existing constraints:
- Python 3.12+ preserved (Dockerfile already uses 3.12-slim)
- python-telegram-bot v21+ unchanged
- Environment-based configuration enforced (no secrets in code)
- PostgreSQL + Redis align with constitution recommendations
- Alembic migrations already configured

### Development Workflow & Quality Gates
✅ **PASS** - Deployment adds operational capabilities without changing development workflow:
- CI/CD pipeline will enforce existing gates (lint, type, tests, coverage)
- Semantic versioning preserved
- Health endpoint `/health` returns version, uptime, dependency status (already required by constitution)

**Overall Gate Status**: ✅ **PASS** - All constitutional requirements satisfied. Security requirements explicitly captured in functional requirements.

## Project Structure

### Documentation (this feature)

```text
specs/003-digitalocean-deployment/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Deployment Infrastructure (new for this feature)
deployment/
├── docker-compose.prod.yml      # Production Docker Compose configuration
├── nginx/
│   ├── nginx.conf               # Reverse proxy configuration
│   └── ssl/                     # SSL certificate storage (gitignored)
├── scripts/
│   ├── deploy.sh                # Main deployment script
│   ├── backup.sh                # Database backup script
│   ├── restore.sh               # Database restore script
│   ├── health-check.sh          # Deployment validation script
│   └── rollback.sh              # Rollback to previous version
├── systemd/
│   └── toogoodtogo.service      # Systemd service for auto-restart
├── monitoring/
│   ├── docker-compose.monitoring.yml  # Optional: Prometheus/Grafana setup
│   └── prometheus.yml           # Metrics configuration
└── .env.production.template     # Template for production environment variables

# Existing application code (unchanged)
src/
├── bot/
│   ├── run.py                   # Application entry point
│   ├── command_map.py
│   └── callback_map.py
├── handlers/
│   ├── discovery/
│   ├── lifecycle/
│   ├── offer_management/
│   ├── offer_posting/
│   ├── purchasing/
│   └── system/
├── models/                      # Domain models
├── services/                    # Business logic
├── storage/                     # Database repositories
├── security/                    # Auth, rate limiting
└── logging/                     # Structured logging

# Existing test structure (unchanged)
tests/
├── contract/
├── integration/
└── unit/

# CI/CD (new/modified for this feature)
.github/
└── workflows/
    ├── ci.yml                   # Existing: lint, test, build
    └── deploy.yml               # New: deployment workflow

# Docker configuration (existing, may be modified)
Dockerfile                       # Multi-stage build for app
docker-compose.yml               # Local development (unchanged)
```

**Structure Decision**: Selected infrastructure/deployment structure. This is a DevOps feature that adds deployment artifacts and scripts without modifying the existing single-project Python application structure. The `deployment/` directory contains all production deployment configuration, keeping it separate from application code and local development setup.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
