#!/bin/bash
# TooGoodToGo Deployment Script
# Deploy new application version to production
#
# Usage: ./deploy.sh <git-tag>
#
# Exit Codes:
#   0 - Deployment successful
#   1 - Deployment failed
#   2 - Backup failed
#   3 - Migration failed

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEPLOY_DIR="${DEPLOY_DIR:-/opt/toogoodtogo}"
readonly BACKUP_DIR="${BACKUP_DIR:-/opt/backups/postgres}"
readonly LOG_DIR="/var/log/toogoodtogo"
readonly LOG_FILE="${LOG_DIR}/deployment.log"
readonly DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
readonly HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-120}"
readonly DEPLOYMENT_LOCK_FILE="/tmp/toogoodtogo-deploy.lock"
readonly DRAIN_WAIT="${DRAIN_WAIT:-5}"
readonly STOP_TIMEOUT="${STOP_TIMEOUT:-30}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Track deployment state for rollback
PREVIOUS_VERSION=""
PREVIOUS_IMAGE=""
BACKUP_FILE=""
DEPLOYMENT_STARTED=false
ROLLBACK_ATTEMPTED=false

# =============================================================================
# Logging Functions
# =============================================================================
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        INFO)  echo -e "${GREEN}[$timestamp]${NC} INFO: $message" ;;
        WARN)  echo -e "${YELLOW}[$timestamp]${NC} WARN: $message" ;;
        ERROR) echo -e "${RED}[$timestamp]${NC} ERROR: $message" >&2 ;;
    esac
    
    if [[ -d "$LOG_DIR" ]]; then
        echo "[$timestamp] $level: $message" >> "$LOG_FILE"
    fi
}

log_info() { log INFO "$@"; }
log_warn() { log WARN "$@"; }
log_error() { log ERROR "$@"; }

# =============================================================================
# Help and Usage
# =============================================================================
show_help() {
    cat << EOF
TooGoodToGo Deployment Script

Usage: $(basename "$0") <git-tag> [OPTIONS]

Arguments:
    git-tag             Git tag to deploy (e.g., v1.2.0)

Options:
    --help              Show this help message
    --skip-backup       Skip pre-deployment backup (not recommended)
    --skip-migration    Skip database migrations
    --force             Force deployment even if same version

Exit Codes:
    0 - Deployment successful
    1 - Deployment failed
    2 - Backup failed
    3 - Migration failed

Examples:
    ./deploy.sh v1.2.0
    ./deploy.sh v1.2.0 --skip-backup
    ./deploy.sh v1.2.0 --force

EOF
    exit 0
}

# =============================================================================
# Cleanup and Rollback
# =============================================================================
cleanup() {
    local exit_code=$?
    
    # Remove lock file
    rm -f "$DEPLOYMENT_LOCK_FILE"
    
    if [[ $exit_code -ne 0 ]] && [[ "$DEPLOYMENT_STARTED" == "true" ]]; then
        log_error "Deployment failed - initiating rollback"
        rollback
    fi
    
    exit $exit_code
}

rollback() {
    if [[ "$ROLLBACK_ATTEMPTED" == "true" ]]; then
        log_warn "Rollback already attempted, skipping"
        return 1
    fi
    ROLLBACK_ATTEMPTED=true

    if [[ -z "$PREVIOUS_VERSION" || "$PREVIOUS_VERSION" == "none" ]]; then
        log_warn "No previous version available for rollback"
        return 1
    fi

    log_info "Rolling back to $PREVIOUS_VERSION"

    cd "${DEPLOY_DIR}/deployment"

    # Restore database from backup if we have one
    if [[ -n "$BACKUP_FILE" ]] && [[ -f "$BACKUP_FILE" ]]; then
        log_info "Restoring database from backup: $BACKUP_FILE"
        "${SCRIPT_DIR}/restore.sh" "$BACKUP_FILE" || log_warn "Database restore failed"
    fi

    # Restore to previous version
    if [[ -n "$PREVIOUS_IMAGE" ]]; then
        log_info "Restoring previous image: $PREVIOUS_IMAGE"
        export APP_VERSION="$PREVIOUS_VERSION"
        docker compose -f "$DOCKER_COMPOSE_FILE" up -d --no-build || true
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" up -d --pull never || true
    fi

    # Verify rollback succeeded
    sleep 10
    if [[ -x "${SCRIPT_DIR}/health-check.sh" ]]; then
        if "${SCRIPT_DIR}/health-check.sh" --wait 60 &>/dev/null; then
            log_info "Rollback successful"
            return 0
        else
            log_error "Rollback health check failed"
            return 1
        fi
    fi

    log_info "Rollback complete (unverified)"
    return 0
}

trap cleanup EXIT

# =============================================================================
# Validation Functions
# =============================================================================
validate_git_tag() {
    local tag="$1"
    
    if [[ -z "$tag" ]]; then
        log_error "Git tag is required"
        show_help
    fi
    
    # Validate tag format (semver with optional v prefix)
    if [[ ! "$tag" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        log_warn "Tag '$tag' does not follow semantic versioning"
    fi
}

check_deployment_lock() {
    if [[ -f "$DEPLOYMENT_LOCK_FILE" ]]; then
        local lock_pid
        lock_pid=$(cat "$DEPLOYMENT_LOCK_FILE")
        
        if kill -0 "$lock_pid" 2>/dev/null; then
            log_error "Another deployment is in progress (PID: $lock_pid)"
            exit 1
        else
            log_warn "Stale lock file found, removing"
            rm -f "$DEPLOYMENT_LOCK_FILE"
        fi
    fi
    
    echo $$ > "$DEPLOYMENT_LOCK_FILE"
}

get_current_version() {
    cd "${DEPLOY_DIR}/deployment"
    
    if docker compose -f "$DOCKER_COMPOSE_FILE" ps -q bot &>/dev/null; then
        PREVIOUS_VERSION=$(docker compose -f "$DOCKER_COMPOSE_FILE" exec -T bot printenv APP_VERSION 2>/dev/null || echo "unknown")
        PREVIOUS_IMAGE=$(docker compose -f "$DOCKER_COMPOSE_FILE" images bot --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || echo "")
    else
        PREVIOUS_VERSION="none"
        PREVIOUS_IMAGE=""
    fi
    
    log_info "Current version: $PREVIOUS_VERSION"
    if [[ -n "$PREVIOUS_IMAGE" ]]; then
        log_info "Current image: $PREVIOUS_IMAGE"
    fi
}

# =============================================================================
# Deployment Steps
# =============================================================================
create_backup() {
    local skip_backup="$1"
    
    if [[ "$skip_backup" == "true" ]]; then
        log_warn "Skipping pre-deployment backup (--skip-backup)"
        return 0
    fi
    
    log_info "Creating pre-deployment backup"
    
    if [[ -x "${SCRIPT_DIR}/backup.sh" ]]; then
        BACKUP_FILE=$("${SCRIPT_DIR}/backup.sh" pre_deployment | tail -1)
        if [[ -f "$BACKUP_FILE" ]]; then
            log_info "Backup created: $BACKUP_FILE"
        else
            log_error "Backup creation failed"
            exit 2
        fi
    else
        log_warn "Backup script not available, skipping backup"
    fi
}

pre_deploy_health_check() {
    log_info "Running pre-deployment health check"

    if [[ -x "${SCRIPT_DIR}/health-check.sh" ]]; then
        if ! "${SCRIPT_DIR}/health-check.sh" --quiet; then
            log_warn "Pre-deployment health check failed - services may already be unhealthy"
            return 1
        fi
        log_info "Pre-deployment health check passed"
    else
        log_warn "Health check script not available"
    fi
    return 0
}

drain_services() {
    log_info "Draining services (waiting ${DRAIN_WAIT}s for in-flight requests)"

    # For polling bot there is no external ingress to drain,
    # but we give time for any pending update processing
    sleep "$DRAIN_WAIT"

    log_info "Drain complete"
}

fetch_and_checkout() {
    local tag="$1"
    
    log_info "Checking out tag $tag"
    
    cd "$DEPLOY_DIR"
    
    # Fetch latest from remote
    git fetch --all --tags --prune
    
    # Checkout the tag
    git checkout "tags/$tag" --force
    
    log_info "Checked out $tag"
}

pull_docker_images() {
    local tag="$1"
    
    log_info "Pulling Docker images for $tag"
    
    cd "${DEPLOY_DIR}/deployment"
    
    # Set version for docker compose
    export APP_VERSION="$tag"
    
    # Build/pull images
    docker compose -f "$DOCKER_COMPOSE_FILE" build --pull
    docker compose -f "$DOCKER_COMPOSE_FILE" pull --ignore-buildable
    
    log_info "Docker images ready"
}

run_migrations() {
    local skip_migration="$1"
    
    if [[ "$skip_migration" == "true" ]]; then
        log_warn "Skipping database migrations (--skip-migration)"
        return 0
    fi
    
    log_info "Running database migrations"
    
    cd "${DEPLOY_DIR}/deployment"
    
    # Ensure database is running
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d postgres
    
    # Wait for postgres to be ready
    local retries=30
    while ! docker compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-toogoodtogo}" &>/dev/null; do
        retries=$((retries - 1))
        if [[ $retries -le 0 ]]; then
            log_error "PostgreSQL failed to start"
            exit 3
        fi
        sleep 1
    done
    
    # Run Alembic migrations
    docker compose -f "$DOCKER_COMPOSE_FILE" run --rm bot alembic upgrade head || {
        log_error "Migration failed"
        exit 3
    }
    
    log_info "Migrations applied successfully"
}

deploy_services() {
    log_info "Deploying services with controlled recreate"

    cd "${DEPLOY_DIR}/deployment"

    # Stop bot gracefully with timeout
    log_info "Stopping bot container (timeout: ${STOP_TIMEOUT}s)"
    docker compose -f "$DOCKER_COMPOSE_FILE" stop --timeout "$STOP_TIMEOUT" bot || true

    # Recreate with new image
    log_info "Starting services with new version"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans

    log_info "Services deployed"
}

wait_for_health() {
    local timeout="${HEALTH_CHECK_TIMEOUT}"
    
    log_info "Waiting for services to become healthy (timeout: ${timeout}s)"
    
    local start_time
    start_time=$(date +%s)
    
    while true; do
        local elapsed
        elapsed=$(($(date +%s) - start_time))
        
        if [[ $elapsed -ge $timeout ]]; then
            log_error "Health check timeout after ${timeout}s"
            return 1
        fi
        
        # Check if health-check.sh exists and is executable
        if [[ -x "${SCRIPT_DIR}/health-check.sh" ]]; then
            if "${SCRIPT_DIR}/health-check.sh" &>/dev/null; then
                log_info "All services healthy"
                return 0
            fi
        else
            # Fallback: check Docker health status
            cd "${DEPLOY_DIR}/deployment"
            local unhealthy
            unhealthy=$(docker compose -f "$DOCKER_COMPOSE_FILE" ps --format json | grep -c '"Health": "unhealthy"' || true)
            local starting
            starting=$(docker compose -f "$DOCKER_COMPOSE_FILE" ps --format json | grep -c '"Health": "starting"' || true)
            
            if [[ "$unhealthy" -eq 0 ]] && [[ "$starting" -eq 0 ]]; then
                log_info "All services healthy (Docker health check)"
                return 0
            fi
        fi
        
        sleep 5
    done
}

# =============================================================================
# Main
# =============================================================================
main() {
    local git_tag=""
    local skip_backup=false
    local skip_migration=false
    local force=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                ;;
            --skip-backup)
                skip_backup=true
                shift
                ;;
            --skip-migration)
                skip_migration=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                ;;
            *)
                git_tag="$1"
                shift
                ;;
        esac
    done
    
    # Validate inputs
    validate_git_tag "$git_tag"
    
    log_info "Starting deployment of $git_tag"
    
    # Pre-deployment checks
    check_deployment_lock
    get_current_version
    
    # Check if already deployed
    if [[ "$PREVIOUS_VERSION" == "$git_tag" ]] && [[ "$force" != "true" ]]; then
        log_info "Version $git_tag already deployed. Use --force to redeploy."
        exit 0
    fi
    
    # Pre-deployment backup
    create_backup "$skip_backup"
    
    DEPLOYMENT_STARTED=true

    # Pre-deploy health check and drain
    pre_deploy_health_check || true
    drain_services
    
    # Deployment steps
    fetch_and_checkout "$git_tag"
    pull_docker_images "$git_tag"
    run_migrations "$skip_migration"
    deploy_services
    
    # Validation with health gate
    if wait_for_health; then
        log_info "Deployment successful: $git_tag"
    else
        log_error "Deployment validation failed - triggering rollback"
        exit 1
    fi
}

main "$@"
