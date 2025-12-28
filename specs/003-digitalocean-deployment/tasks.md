# Tasks: DigitalOcean Production Deployment

**Input**: Design documents from `/specs/003-digitalocean-deployment/`  
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: Infrastructure validation through deployment scripts and health checks. No unit tests required for this DevOps feature.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation of each deployment capability.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Includes exact file paths in descriptions

## Path Conventions

- **Deployment infrastructure**: `deployment/` at repository root
- **Application health endpoint**: `src/handlers/system/`
- **CI/CD workflows**: `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and deployment directory structure

- [x] T001 Create deployment directory structure per plan in deployment/
- [x] T002 [P] Create environment template file in deployment/.env.production.template
- [x] T003 [P] Create .gitignore entries for deployment secrets in deployment/.gitignore
- [x] T004 [P] Create Redis configuration file with RDB persistence in deployment/redis/redis.conf

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be fully validated

**⚠️ CRITICAL**: These components are required by all deployment user stories

- [x] T005 Create production Docker Compose file in deployment/docker-compose.prod.yml
- [x] T006 [P] Configure PostgreSQL service with production settings in deployment/docker-compose.prod.yml
- [x] T007 [P] Configure Redis service with RDB snapshots in deployment/docker-compose.prod.yml
- [x] T008 [P] Configure bot service with resource limits in deployment/docker-compose.prod.yml
- [x] T009 Implement health check endpoint (GET /health) in src/handlers/system/health.py
- [x] T009a [P] Write unit tests for health endpoint in tests/unit/handlers/test_health.py
- [x] T010 Register health endpoint in bot application in src/bot/run.py
- [x] T011 [P] Create nginx reverse proxy configuration in deployment/nginx/nginx.conf
- [x] T012 [P] Create nginx SSL template configuration in deployment/nginx/ssl.conf.template

**Checkpoint**: Foundation ready - core Docker Compose and health check infrastructure complete

---

## Phase 3: User Story 1 - Initial Production Deployment (Priority: P1) 🎯 MVP

**Goal**: Deploy backend, PostgreSQL, and Redis to a DigitalOcean droplet with all services accessible and healthy

**Independent Test**: Deploy to fresh droplet → Run health-check.sh → Verify bot responds to /start command

### Implementation for User Story 1

- [x] T013 [US1] Create droplet setup script in deployment/scripts/setup-droplet.sh
- [x] T014 [US1] Implement Docker and Docker Compose installation in deployment/scripts/setup-droplet.sh
- [x] T015 [US1] Implement nginx and certbot installation in deployment/scripts/setup-droplet.sh
- [x] T016 [US1] Implement firewall (ufw) configuration in deployment/scripts/setup-droplet.sh
- [x] T017 [US1] Implement environment variable prompts and .env.production creation in deployment/scripts/setup-droplet.sh
- [x] T018 [US1] Implement SSL certificate provisioning via certbot in deployment/scripts/setup-droplet.sh
- [x] T019 [P] [US1] Create deployment script in deployment/scripts/deploy.sh
- [x] T020 [US1] Implement pre-deployment backup call in deployment/scripts/deploy.sh
- [x] T021 [US1] Implement Git tag checkout and image pull in deployment/scripts/deploy.sh
- [x] T022 [US1] Implement database migration execution in deployment/scripts/deploy.sh
- [x] T023 [US1] Implement service startup and health validation in deployment/scripts/deploy.sh
- [x] T024 [P] [US1] Create health check validation script in deployment/scripts/health-check.sh
- [x] T025 [US1] Implement multi-service health checking in deployment/scripts/health-check.sh
- [x] T026 [US1] Implement JSON output mode for health-check.sh in deployment/scripts/health-check.sh
- [x] T027 [P] [US1] Create backup script in deployment/scripts/backup.sh
- [x] T028 [US1] Implement pg_dump execution via Docker in deployment/scripts/backup.sh
- [x] T029 [US1] Implement backup verification and rotation in deployment/scripts/backup.sh
- [x] T030 [US1] Implement backup metadata index in deployment/scripts/backup.sh
- [x] T031 [P] [US1] Create restore script in deployment/scripts/restore.sh
- [x] T032 [US1] Implement backup validation and database restoration in deployment/scripts/restore.sh
- [x] T033 [P] [US1] Create rollback script in deployment/scripts/rollback.sh
- [x] T034 [US1] Implement version rollback with backup restoration in deployment/scripts/rollback.sh
- [x] T035 [US1] Create deployment logging infrastructure in /var/log/toogoodtogo/

**Checkpoint**: User Story 1 complete - can deploy to fresh droplet, all services start, bot responds to commands

---

## Phase 4: User Story 2 - Service Reliability and Restart (Priority: P2)

**Goal**: All services automatically restart after system reboot or service crashes

**Independent Test**: Reboot droplet → Wait 5 minutes → Verify all services running → Verify bot responds

### Implementation for User Story 2

- [x] T036 [US2] Create systemd service unit for Docker Compose in deployment/systemd/toogoodtogo.service
- [x] T037 [US2] Configure service dependencies (Requires=docker.service) in deployment/systemd/toogoodtogo.service
- [x] T038 [US2] Configure restart policy and start command in deployment/systemd/toogoodtogo.service
- [x] T039 [US2] Add systemd service installation to setup-droplet.sh in deployment/scripts/setup-droplet.sh
- [x] T040 [US2] Configure Docker restart policies (restart: unless-stopped) in deployment/docker-compose.prod.yml
- [x] T041 [US2] Configure deploy.restart_policy for services in deployment/docker-compose.prod.yml
- [x] T042 [US2] Add service startup verification after reboot to health-check.sh in deployment/scripts/health-check.sh
- [x] T043 [P] [US2] Create and enable systemd timer for daily automated backups (FR-017) in deployment/systemd/toogoodtogo-backup.timer
- [x] T044 [P] [US2] Create systemd service for backup timer execution in deployment/systemd/toogoodtogo-backup.service

**Checkpoint**: User Story 2 complete - droplet reboot results in automatic service recovery within 5 minutes

---

## Phase 5: User Story 3 - Zero-Downtime Updates (Priority: P3)

**Goal**: Deploy application updates with minimal or no service interruption

**Independent Test**: Deploy new version during active bot usage → Measure downtime → Verify < 30 seconds

### Implementation for User Story 3

- [x] T045 [US3] Implement graceful shutdown with stop_grace_period in deployment/docker-compose.prod.yml
- [x] T046 [US3] Implement rolling update strategy in deploy.sh in deployment/scripts/deploy.sh
- [x] T047 [US3] Add pre-deployment health check validation in deployment/scripts/deploy.sh
- [x] T048 [US3] Implement automatic rollback on health check failure in deployment/scripts/deploy.sh
- [x] T049 [P] [US3] Create GitHub Actions deployment workflow in .github/workflows/deploy.yml
- [x] T050 [US3] Implement SSH deployment step in GitHub Actions in .github/workflows/deploy.yml
- [x] T051 [US3] Add deployment status notification to GitHub Actions in .github/workflows/deploy.yml
- [x] T052 [US3] Implement deployment lock to prevent concurrent deploys in deployment/scripts/deploy.sh

**Checkpoint**: User Story 3 complete - deployments complete with < 30 second interruption and automatic rollback on failure

---

## Phase 6: User Story 4 - Monitoring and Observability (Priority: P3)

**Goal**: Operations team can monitor service health, resource usage, and access application logs

**Independent Test**: Check logs accessible → Verify health endpoint returns correct data → Confirm log rotation

### Implementation for User Story 4

- [x] T053 [US4] Configure Docker logging driver with rotation in deployment/docker-compose.prod.yml
- [x] T054 [US4] Configure log retention (7 days) in deployment/docker-compose.prod.yml
- [x] T055 [P] [US4] Create Prometheus configuration in deployment/monitoring/prometheus.yml
- [x] T056 [P] [US4] Create monitoring Docker Compose file in deployment/monitoring/docker-compose.monitoring.yml
- [x] T057 [US4] Configure Prometheus service with bot scraping in deployment/monitoring/docker-compose.monitoring.yml
- [x] T058 [US4] Configure Grafana service with Prometheus datasource in deployment/monitoring/docker-compose.monitoring.yml
- [x] T059 [P] [US4] Create Grafana dashboard JSON for service health in deployment/monitoring/dashboards/service-health.json
- [x] T060 [US4] Add resource usage metrics to health endpoint in src/handlers/system/health.py
- [x] T061 [US4] Document log access procedures in quickstart.md

**Checkpoint**: User Story 4 complete - logs accessible for 7 days, optional Prometheus/Grafana available

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, security hardening, and final validation

**Analysis Issues to Address** (from `/speckit.analyze`):
- A2 (MEDIUM): Add uptime measurement methodology to monitoring docs or health endpoint
- A3 (MEDIUM): Standardize `DEPLOY_DIR=/opt/toogoodtogo` path convention across all scripts
- A4 (MEDIUM): Document deployment lock as MVP limitation or backport T052 if needed
- A5 (MEDIUM): Document edge case handling (disk space, Redis memory, network loss, missing env vars) in RUNTIME_GUIDE.md
- A6 (MEDIUM): Clarify US3 scenario 3 refers to single-instance validation, not multi-instance
- A7 (LOW): Document Docker internal network isolation for FR-014 in quickstart.md
- A8 (LOW): Add optional load testing task for SC-004 performance validation
- A9 (LOW): Review docker-compose.prod.yml modifications for merge safety
- A10 (LOW): Add comment in contracts clarifying repo vs installed paths

- [x] T062 [P] Update quickstart.md with actual file paths and final commands in specs/003-digitalocean-deployment/quickstart.md
- [x] T063 [P] Create operational runbook (RUNTIME_GUIDE.md) in docs/RUNTIME_GUIDE.md
- [x] T064 [P] Create fail2ban configuration for SSH protection in deployment/fail2ban/jail.local
- [x] T065 Add fail2ban installation to setup-droplet.sh in deployment/scripts/setup-droplet.sh
- [x] T066 Implement secret rotation documentation in docs/RUNTIME_GUIDE.md
- [x] T067 Run complete quickstart.md validation end-to-end
- [x] T068 Verify all scripts are executable (chmod +x) in deployment/scripts/
- [x] T069 Add script help output (--help flag) to all deployment scripts
- [x] T070 Final security review of all deployment files

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ─────────────────┐
                                ▼
Phase 2: Foundational ──────────┤ BLOCKS ALL USER STORIES
                                ▼
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
Phase 3: US1 (P1)       Phase 4: US2 (P2)       Phase 5: US3 (P3)
Initial Deployment      Service Reliability     Zero-Downtime
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                        Phase 6: US4 (P3)
                        Monitoring
                                │
                                ▼
                        Phase 7: Polish
```

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US1 (Initial Deployment) | Phase 2 (Foundational) | Foundational complete |
| US2 (Service Reliability) | US1 | US1 complete (needs working deployment) |
| US3 (Zero-Downtime) | US1 | US1 complete (needs deploy.sh) |
| US4 (Monitoring) | US1 | US1 complete (needs health endpoint) |

### Within Each User Story

1. Create script files first (skeleton with --help)
2. Implement core functionality
3. Add error handling and logging
4. Validate against contract specifications

### Parallel Opportunities per Phase

**Phase 1 (Setup)**:
```
T002 (.env template) ──┐
T003 (.gitignore)    ──┼── All parallel
T004 (redis.conf)    ──┘
```

**Phase 2 (Foundational)**:
```
T006 (PostgreSQL)  ──┐
T007 (Redis)       ──┼── Parallel (all docker-compose services)
T008 (Bot)         ──┘

T011 (nginx.conf)  ──┬── Parallel (nginx configs)
T012 (ssl.conf)    ──┘
```

**Phase 3 (US1 - Initial Deployment)**:
```
T019 (deploy.sh)      ──┐
T024 (health-check.sh)──┤
T027 (backup.sh)      ──┼── All scripts can be created in parallel
T031 (restore.sh)     ──┤
T033 (rollback.sh)    ──┘
```

**Phase 4 (US2 - Reliability)**:
```
T043 (backup.timer)   ──┬── Parallel (systemd timers)
T044 (backup.service) ──┘
```

**Phase 6 (US4 - Monitoring)**:
```
T055 (prometheus.yml)              ──┐
T056 (docker-compose.monitoring)   ──┼── Parallel (monitoring setup)
T059 (grafana dashboard)           ──┘
```

**Phase 7 (Polish)**:
```
T062 (quickstart.md)   ──┐
T063 (RUNTIME_GUIDE)   ──┼── All docs parallel
T064 (fail2ban config) ──┘
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks) - ~30 min
2. Complete Phase 2: Foundational (8 tasks) - ~2 hours
3. Complete Phase 3: User Story 1 (23 tasks) - ~1 day
4. **STOP and VALIDATE**: Deploy to test droplet
5. If successful → production-ready MVP

### Incremental Delivery

| Phase | Duration | Outcome |
|-------|----------|---------|
| Setup + Foundational | 3-4 hours | Docker Compose ready, health endpoint working |
| US1: Initial Deployment | 1-2 days | **MVP: Can deploy to production** |
| US2: Service Reliability | 4-6 hours | Auto-restart on reboot |
| US3: Zero-Downtime | 4-6 hours | CI/CD with rollback |
| US4: Monitoring | 4-6 hours | Prometheus/Grafana optional |
| Polish | 2-4 hours | Docs, security hardening |

**Total Estimated Effort**: 3-5 days for complete feature

### Validation Checkpoints

After each phase, validate:

1. **Setup**: All files created, correct structure
2. **Foundational**: `docker compose -f deployment/docker-compose.prod.yml config` validates
3. **US1**: Fresh droplet deployment succeeds, bot responds
4. **US2**: Droplet reboot → services auto-recover
5. **US3**: `git tag && git push` triggers deployment, rollback works
6. **US4**: Logs accessible, Grafana shows metrics (if deployed)
7. **Polish**: Complete walkthrough of quickstart.md succeeds

---

## File Summary

### New Files to Create

| Path | Created In |
|------|------------|
| `deployment/.env.production.template` | T002 |
| `deployment/.gitignore` | T003 |
| `deployment/redis/redis.conf` | T004 |
| `deployment/docker-compose.prod.yml` | T005-T008 |
| `deployment/nginx/nginx.conf` | T011 |
| `deployment/nginx/ssl.conf.template` | T012 |
| `deployment/scripts/setup-droplet.sh` | T013-T018 |
| `deployment/scripts/deploy.sh` | T019-T023 |
| `deployment/scripts/health-check.sh` | T024-T026 |
| `deployment/scripts/backup.sh` | T027-T030 |
| `deployment/scripts/restore.sh` | T031-T032 |
| `deployment/scripts/rollback.sh` | T033-T034 |
| `deployment/systemd/toogoodtogo.service` | T036-T038 |
| `deployment/systemd/toogoodtogo-backup.timer` | T043 |
| `deployment/systemd/toogoodtogo-backup.service` | T044 |
| `.github/workflows/deploy.yml` | T049-T051 |
| `deployment/monitoring/prometheus.yml` | T055 |
| `deployment/monitoring/docker-compose.monitoring.yml` | T056-T058 |
| `deployment/monitoring/dashboards/service-health.json` | T059 |
| `deployment/fail2ban/jail.local` | T064 |
| `docs/RUNTIME_GUIDE.md` | T063 |

### Modified Files

| Path | Modified In |
|------|-------------|
| `src/handlers/system/health.py` | T009, T060 |
| `src/bot/run.py` | T010 |
| `specs/003-digitalocean-deployment/quickstart.md` | T062 |

---

## Notes

- All scripts must include shebang (`#!/bin/bash`) and `set -e`
- All scripts must implement `--help` flag for documentation
- Scripts must log to `/var/log/toogoodtogo/deployment.log`
- Exit codes must follow contract specifications
- Health endpoint must match contract in `contracts/health-check-api.md`
- Deployment scripts must match contract in `contracts/deployment-scripts.md`
