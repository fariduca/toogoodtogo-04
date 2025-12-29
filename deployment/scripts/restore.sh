#!/bin/bash
# TooGoodToGo Database Restore Script
# Restore PostgreSQL database from backup
#
# Usage: ./restore.sh <backup-file>
#
# Exit Codes:
#   0 - Restore successful
#   1 - Restore failed
#   2 - Backup file not found or corrupted
#   3 - Database connection failed

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

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

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
TooGoodToGo Database Restore Script

Usage: $(basename "$0") <BACKUP-FILE> [OPTIONS]

Arguments:
    BACKUP-FILE         Path to backup file or backup ID

Options:
    --help              Show this help message
    --force             Skip confirmation prompt
    --no-restart        Don't restart services after restore

Exit Codes:
    0 - Restore successful
    1 - Restore failed
    2 - Backup file not found or corrupted
    3 - Database connection failed

Examples:
    ./restore.sh /opt/backups/postgres/toogoodtogo_manual_20251228_100000.sql.gz
    ./restore.sh toogoodtogo_manual_20251228_100000.sql.gz
    ./restore.sh --force latest

EOF
    exit 0
}

# =============================================================================
# Validation Functions
# =============================================================================
resolve_backup_file() {
    local input="$1"
    
    # If "latest", find most recent backup
    if [[ "$input" == "latest" ]]; then
        local latest
        latest=$(find "$BACKUP_DIR" -name "toogoodtogo_*.sql.gz" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [[ -z "$latest" ]]; then
            log_error "No backups found in $BACKUP_DIR"
            exit 2
        fi
        
        echo "$latest"
        return 0
    fi
    
    # If full path exists, use it
    if [[ -f "$input" ]]; then
        echo "$input"
        return 0
    fi
    
    # Try prepending backup directory
    if [[ -f "${BACKUP_DIR}/${input}" ]]; then
        echo "${BACKUP_DIR}/${input}"
        return 0
    fi
    
    log_error "Backup file not found: $input"
    exit 2
}

validate_backup_file() {
    local backup_file="$1"
    
    log_info "Validating backup file: $(basename "$backup_file")"
    
    # Check file exists
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        exit 2
    fi
    
    # Check file is readable
    if [[ ! -r "$backup_file" ]]; then
        log_error "Backup file not readable: $backup_file"
        exit 2
    fi
    
    # Verify gzip integrity
    if ! gzip -t "$backup_file" 2>/dev/null; then
        log_error "Backup file corrupted: gzip test failed"
        exit 2
    fi
    
    # Check for SQL content
    if ! zcat "$backup_file" | head -100 | grep -q "PostgreSQL database dump"; then
        log_error "Invalid backup: not a PostgreSQL dump"
        exit 2
    fi
    
    log_info "Backup validation successful"
}

confirm_restore() {
    local backup_file="$1"
    local force="$2"
    
    if [[ "$force" == "true" ]]; then
        return 0
    fi
    
    echo ""
    echo -e "${YELLOW}WARNING: This will replace the current database!${NC}"
    echo "Backup file: $(basename "$backup_file")"
    echo "Backup date: $(stat -c%y "$backup_file" | cut -d' ' -f1,2)"
    echo "Backup size: $(du -h "$backup_file" | cut -f1)"
    echo ""
    read -r -p "Are you sure you want to proceed? [y/N] " response
    
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            log_info "Restore cancelled by user"
            exit 0
            ;;
    esac
}

# =============================================================================
# Restore Operations
# =============================================================================
stop_application_services() {
    log_info "Stopping application services"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    # Stop bot service (keep postgres running)
    docker compose -f "$DOCKER_COMPOSE_FILE" stop bot nginx 2>/dev/null || true
    
    log_info "Application services stopped"
}

wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    # Source environment
    if [[ -f "${DEPLOY_DIR}/deployment/.env.production" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "${DEPLOY_DIR}/deployment/.env.production"
        set +a
    fi
    
    local db_user="${POSTGRES_USER:-toogoodtogo}"
    local retries=30
    
    while ! docker compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U "$db_user" &>/dev/null; do
        retries=$((retries - 1))
        if [[ $retries -le 0 ]]; then
            log_error "PostgreSQL failed to start"
            exit 3
        fi
        sleep 1
    done
    
    log_info "PostgreSQL is ready"
}

restore_database() {
    local backup_file="$1"
    
    log_info "Restoring database from backup"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    # Source environment
    if [[ -f "${DEPLOY_DIR}/deployment/.env.production" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "${DEPLOY_DIR}/deployment/.env.production"
        set +a
    fi
    
    local db_user="${POSTGRES_USER:-toogoodtogo}"
    local db_name="${POSTGRES_DB:-toogoodtogo}"
    
    # Restore from backup
    # The --clean flag in pg_dump handles dropping objects
    zcat "$backup_file" | docker compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
        psql -U "$db_user" -d "$db_name" --quiet --single-transaction
    
    log_info "Database restored successfully"
}

verify_restoration() {
    log_info "Verifying restored database"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    # Source environment
    if [[ -f "${DEPLOY_DIR}/deployment/.env.production" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "${DEPLOY_DIR}/deployment/.env.production"
        set +a
    fi
    
    local db_user="${POSTGRES_USER:-toogoodtogo}"
    local db_name="${POSTGRES_DB:-toogoodtogo}"
    
    # Check for key tables
    local tables
    tables=$(docker compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
        psql -U "$db_user" -d "$db_name" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    
    tables=$(echo "$tables" | tr -d ' ')
    
    if [[ "$tables" -gt 0 ]]; then
        log_info "Verification successful: $tables tables restored"
    else
        log_warn "Verification warning: no tables found in public schema"
    fi
    
    # Get row counts for key tables
    local counts
    counts=$(docker compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
        psql -U "$db_user" -d "$db_name" -t -c "
            SELECT 'users: ' || COUNT(*) FROM users
            UNION ALL
            SELECT 'businesses: ' || COUNT(*) FROM businesses
            UNION ALL
            SELECT 'offers: ' || COUNT(*) FROM offers
        " 2>/dev/null || echo "Unable to get row counts")
    
    log_info "Row counts: $counts"
}

restart_services() {
    local no_restart="$1"
    
    if [[ "$no_restart" == "true" ]]; then
        log_info "Skipping service restart (--no-restart)"
        return 0
    fi
    
    log_info "Restarting services"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_info "Services restarted"
    
    # Run health check
    if [[ -x "${SCRIPT_DIR}/health-check.sh" ]]; then
        log_info "Running health check"
        "${SCRIPT_DIR}/health-check.sh" --wait 60 || log_warn "Health check did not pass"
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    local backup_input=""
    local force=false
    local no_restart=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                ;;
            --force|-f)
                force=true
                shift
                ;;
            --no-restart)
                no_restart=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                ;;
            *)
                backup_input="$1"
                shift
                ;;
        esac
    done
    
    # Validate input
    if [[ -z "$backup_input" ]]; then
        log_error "Backup file is required"
        show_help
    fi
    
    log_info "Starting database restore"
    
    # Resolve and validate backup file
    local backup_file
    backup_file=$(resolve_backup_file "$backup_input")
    log_info "Backup file: $backup_file"
    
    validate_backup_file "$backup_file"
    
    # Confirm with user
    confirm_restore "$backup_file" "$force"
    
    # Perform restore
    stop_application_services
    wait_for_postgres
    restore_database "$backup_file"
    verify_restoration
    restart_services "$no_restart"
    
    log_info "Restore complete"
}

main "$@"
