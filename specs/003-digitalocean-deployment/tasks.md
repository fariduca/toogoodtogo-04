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
# Tasks: DigitalOcean Production Deployment (Polling Baseline)

**Input**: Design documents from `/specs/003-digitalocean-deployment/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md)

**Tests**: Infra validation via deployment scripts + health checks. No unit tests required for this DevOps feature.

**Organization**: Grouped by user story to keep increments independently testable. Long-polling baseline (outbound-only; no public ingress, no TLS/webhook).

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no deps)
- **[Story]**: US1..US4 only for story phases

## Path Conventions
- Deployment: deployment/
- Health endpoint: src/handlers/system/
- Bot entry: src/bot/run.py
- CI/CD: .github/workflows/

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline structure and templates for polling-only deployment.

- [x] T001 Create/verify deployment folder layout for polling baseline in deployment/
- [x] T002 [P] Update env template for polling (remove webhook/TLS vars) in deployment/.env.production.template
- [x] T003 [P] Ensure secrets are gitignored in deployment/.gitignore
- [x] T004 [P] Tune Redis RDB snapshot config for production in deployment/redis/redis.conf

---

## Phase 2: Foundational (Blocking)

**Purpose**: Core compose + health plumbing with no public ingress.

- [x] T005 Define minimal services (bot/postgres/redis) with no published ports in deployment/docker-compose.prod.yml
- [x] T006 [P] Configure postgres service (volumes, auth, backups dir) in deployment/docker-compose.prod.yml
- [x] T007 [P] Configure redis service (rdb saves, maxmemory-policy, limits) in deployment/docker-compose.prod.yml
- [x] T008 [P] Configure bot service (env file, resource limits, read-only FS if possible) in deployment/docker-compose.prod.yml
- [x] T009 Harden health server binding (localhost-only or disable if unused) in src/bot/run.py and src/handlers/system/health.py

**Checkpoint**: Compose validates; services defined without ingress; health reachable container-internally.

---

## Phase 3: User Story 1 - Initial Production Deployment (P1) 🎯 MVP

**Goal**: Deploy bot+Postgres+Redis to a droplet via Docker Compose in long-polling mode.

**Independent Test**: Fresh droplet → run setup + deploy → health-check.sh succeeds → bot responds to /start.

- [x] T010 [US1] Slim droplet bootstrap (Docker/Compose, ufw deny-all inbound except SSH) in deployment/scripts/setup-droplet.sh
- [x] T011 [US1] Generate .env.production from template with required secrets only in deployment/scripts/setup-droplet.sh
- [x] T012 [P] [US1] Implement deploy script for polling (pull/build, migrations, compose up -d) in deployment/scripts/deploy.sh
- [x] T013 [US1] Add migration step (alembic upgrade head) run via bot container in deployment/scripts/deploy.sh
- [x] T014 [P] [US1] Implement internal health checker (docker exec curl localhost:8000/health) in deployment/scripts/health-check.sh
- [x] T015 [P] [US1] Implement backup script (pg_dump to host volume with rotation) in deployment/scripts/backup.sh
- [x] T016 [P] [US1] Implement restore script (select backup → drop/create → psql restore) in deployment/scripts/restore.sh
- [x] T017 [P] [US1] Implement rollback script (previous tag + optional DB restore) in deployment/scripts/rollback.sh
- [x] T018 [US1] Add deploy/run instructions for polling-only in specs/003-digitalocean-deployment/quickstart.md

**Checkpoint**: US1 complete — compose deploy works on fresh droplet; bot responds via polling.

---

## Phase 4: User Story 2 - Service Reliability & Restart (P2)

**Goal**: Recover automatically after reboot/crash with minimal manual steps.

**Independent Test**: Reboot droplet → within 5 minutes bot responds; health-check.sh passes.

- [x] T019 [US2] Systemd unit to manage compose stack (Requires=docker, restart on-failure) in deployment/systemd/toogoodtogo.service
- [x] T020 [P] [US2] Ensure compose restart policies set (restart: unless-stopped) in deployment/docker-compose.prod.yml
- [x] T021 [US2] Add reboot validation path to health-check.sh for post-boot verification in deployment/scripts/health-check.sh
- [x] T022 [P] [US2] Daily backup timer + service in deployment/systemd/toogoodtogo-backup.{timer,service}

**Checkpoint**: US2 complete — reboot leads to auto-recovery and scheduled backups run.

---

## Phase 5: User Story 3 - Low-Downtime Updates (P3)

**Goal**: Deploy updates with ≤30s interruption for single-instance polling bot.

**Independent Test**: Run deploy.sh with active users → measure downtime <30s; rollback triggers on failed health.

- [x] T023 [US3] Add pre-deploy health + draining (stop accepting updates) in deployment/scripts/deploy.sh
- [x] T024 [US3] Implement pull + recreate with stop_grace_period and health gate in deployment/scripts/deploy.sh
- [x] T025 [US3] Implement automatic rollback on failed post-deploy health in deployment/scripts/deploy.sh
- [ ] T026 [P] [US3] Optional GitHub Actions deploy workflow for manual trigger in .github/workflows/deploy.yml

**Checkpoint**: US3 complete — deploys are health-gated with rollback and short interruption.

---

## Phase 6: User Story 4 - Monitoring & Observability (P3)

**Goal**: Basic visibility; optional metrics stack remains add-on.

**Independent Test**: Logs accessible/rotated; health reports deps; optional metrics stack reachable if enabled.

- [x] T027 [US4] Configure Docker logging rotation/retention in deployment/docker-compose.prod.yml
- [x] T028 [US4] Document log access (docker logs, file locations) in specs/003-digitalocean-deployment/quickstart.md
- [x] T029 [P] [US4] Optional Prometheus/Grafana compose file guarded as opt-in in deployment/monitoring/
- [x] T030 [US4] Ensure health endpoint returns resource + dependency status for ops in src/handlers/system/health.py

**Checkpoint**: US4 complete — logs retained, health useful; metrics optional.

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: Docs, security hardening, final validation for polling baseline.

- [x] T031 [P] Normalize DEPLOY_DIR and permissions across scripts in deployment/scripts/
- [x] T032 [P] Ensure all scripts have shebang, set -euo pipefail, --help in deployment/scripts/
- [x] T033 [P] Final security review (secrets, firewall rules, no ingress) in deployment/
- [ ] T034 Validate quickstart end-to-end on fresh droplet in specs/003-digitalocean-deployment/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────┐
                             ▼
Phase 2: Foundational ───────┤ BLOCKS ALL USER STORIES
                             ▼
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
Phase 3: US1 (P1)    Phase 4: US2 (P2)    Phase 5: US3 (P3)
Initial Deploy       Reliability          Low-Downtime
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                     Phase 6: US4 (P3)
                     Monitoring
                             ▼
                     Phase 7: Polish
```

### Parallel Opportunities

- Phase 1: T002, T003, T004
- Phase 2: T006, T007, T008
- US1: T012, T014, T015, T016, T017
- US2: T020, T022
- US3: T026
- US4: T029
- Polish: T031, T032, T033

### Implementation Strategy
- MVP = US1 (polling deployment) after Setup + Foundational.
- Then US2 (reliability) → US3 (low-downtime) → US4 (monitoring) → Polish.
- Validate after each phase with health-check.sh and bot interaction.
| US3 (Zero-Downtime) | US1 | US1 complete (needs deploy.sh) |
