#!/bin/bash
# TooGoodToGo Rollback Script
# Rollback to a previous application version
#
# Usage: ./rollback.sh [target-version]
#
# Exit Codes:
#   0 - Rollback successful
#   1 - Rollback failed
#   2 - Target version not found
#   3 - Backup restoration failed

set -e
set -o pipefail

# =============================================================================
# Configuration
# =============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEPLOY_DIR="${DEPLOY_DIR:-/opt/toogoodtogo}"
readonly BACKUP_DIR="${BACKUP_DIR:-/opt/backups/postgres}"
readonly LOG_DIR="/var/log/toogoodtogo"
readonly LOG_FILE="${LOG_DIR}/deployment.log"
readonly DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
readonly DEPLOYMENT_HISTORY_FILE="${DEPLOY_DIR}/deployment/.deployment_history"

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
TooGoodToGo Rollback Script

Usage: $(basename "$0") [TARGET-VERSION] [OPTIONS]

Arguments:
    TARGET-VERSION      Git tag to rollback to (e.g., v1.1.0)
                        If omitted, rollback to previous version

Options:
    --help              Show this help message
    --list              List available versions for rollback
    --force             Skip confirmation prompt
    --skip-db-restore   Don't restore database backup

Exit Codes:
    0 - Rollback successful
    1 - Rollback failed
    2 - Target version not found
    3 - Backup restoration failed

Examples:
    ./rollback.sh                       # Rollback to previous version
    ./rollback.sh v1.1.0                # Rollback to specific version
    ./rollback.sh --list                # List available versions
    ./rollback.sh v1.1.0 --force        # Skip confirmation

EOF
    exit 0
}

# =============================================================================
# Version Management
# =============================================================================
get_current_version() {
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    local version
    version=$(docker compose -f "$DOCKER_COMPOSE_FILE" exec -T bot printenv APP_VERSION 2>/dev/null || echo "unknown")
    
    echo "$version"
}

get_previous_version() {
    # Check deployment history
    if [[ -f "$DEPLOYMENT_HISTORY_FILE" ]]; then
        # Get second-to-last entry
        local previous
        previous=$(tail -2 "$DEPLOYMENT_HISTORY_FILE" | head -1 | cut -d' ' -f1)
        
        if [[ -n "$previous" ]]; then
            echo "$previous"
            return 0
        fi
    fi
    
    # Fallback: check git tags
    cd "$DEPLOY_DIR" 2>/dev/null || return 1
    
    local current
    current=$(get_current_version)
    
    local previous
    previous=$(git tag --sort=-v:refname | grep -A1 "^${current}$" | tail -1)
    
    if [[ -n "$previous" ]] && [[ "$previous" != "$current" ]]; then
        echo "$previous"
        return 0
    fi
    
    return 1
}

list_available_versions() {
    log_info "Available versions for rollback:"
    
    cd "$DEPLOY_DIR" 2>/dev/null || {
        log_error "Cannot access deploy directory"
        exit 1
    }
    
    local current
    current=$(get_current_version)
    
    echo ""
    echo "Current version: $current"
    echo ""
    echo "Available versions:"
    
    git tag --sort=-v:refname | head -10 | while read -r tag; do
        if [[ "$tag" == "$current" ]]; then
            echo "  $tag (current)"
        else
            echo "  $tag"
        fi
    done
    
    echo ""
    
    # Show deployment history
    if [[ -f "$DEPLOYMENT_HISTORY_FILE" ]]; then
        echo "Recent deployment history:"
        tail -5 "$DEPLOYMENT_HISTORY_FILE" | while read -r line; do
            echo "  $line"
        done
    fi
}

validate_target_version() {
    local target="$1"
    
    cd "$DEPLOY_DIR" 2>/dev/null || {
        log_error "Cannot access deploy directory"
        exit 2
    }
    
    # Check if tag exists
    if ! git tag | grep -q "^${target}$"; then
        log_error "Version not found: $target"
        log_info "Use --list to see available versions"
        exit 2
    fi
    
    log_info "Target version validated: $target"
}

# =============================================================================
# Rollback Operations
# =============================================================================
create_safety_backup() {
    log_info "Creating safety backup before rollback"
    
    if [[ -x "${SCRIPT_DIR}/backup.sh" ]]; then
        local backup_file
        backup_file=$("${SCRIPT_DIR}/backup.sh" pre_deployment | tail -1)
        
        if [[ -f "$backup_file" ]]; then
            log_info "Safety backup created: $backup_file"
            echo "$backup_file"
        else
            log_warn "Safety backup may have failed"
        fi
    else
        log_warn "Backup script not available"
    fi
}

find_backup_for_version() {
    local target_version="$1"
    
    # Look for pre-deployment backup from when this version was deployed
    # Format: toogoodtogo_pre_deployment_YYYYMMDD_HHMMSS.sql.gz
    
    local backup
    backup=$(find "$BACKUP_DIR" -name "toogoodtogo_*.sql.gz" -printf '%T@ %p\n' 2>/dev/null | sort -rn | while read -r timestamp file; do
        # Check if deployment history has this version with a timestamp
        if [[ -f "$DEPLOYMENT_HISTORY_FILE" ]]; then
            local deploy_timestamp
            deploy_timestamp=$(grep "^${target_version} " "$DEPLOYMENT_HISTORY_FILE" | cut -d' ' -f2)
            
            if [[ -n "$deploy_timestamp" ]]; then
                # Find backup closest to (but before) this deployment
                local backup_date
                backup_date=$(basename "$file" | sed 's/.*_\([0-9]\{8\}_[0-9]\{6\}\)\.sql\.gz/\1/')
                echo "$file"
                break
            fi
        fi
    done)
    
    if [[ -n "$backup" ]]; then
        echo "$backup"
    fi
}

stop_services() {
    log_info "Stopping current services"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    docker compose -f "$DOCKER_COMPOSE_FILE" stop
    
    log_info "Services stopped"
}

checkout_version() {
    local target="$1"
    
    log_info "Checking out version $target"
    
    cd "$DEPLOY_DIR"
    
    git fetch --all --tags --prune
    git checkout "tags/$target" --force
    
    log_info "Checked out $target"
}

restore_backup() {
    local skip_restore="$1"
    local backup_file="$2"
    
    if [[ "$skip_restore" == "true" ]]; then
        log_warn "Skipping database restore (--skip-db-restore)"
        return 0
    fi
    
    if [[ -n "$backup_file" ]] && [[ -f "$backup_file" ]]; then
        log_info "Restoring database from backup: $(basename "$backup_file")"
        
        if [[ -x "${SCRIPT_DIR}/restore.sh" ]]; then
            "${SCRIPT_DIR}/restore.sh" "$backup_file" --force --no-restart || {
                log_error "Database restore failed"
                exit 3
            }
        fi
    else
        log_warn "No backup available for database restore"
        log_info "Database will remain at current state"
    fi
}

start_services() {
    local target="$1"
    
    log_info "Starting services with version $target"
    
    cd "${DEPLOY_DIR}/deployment"
    
    export APP_VERSION="$target"
    
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_info "Services started"
}

validate_rollback() {
    log_info "Validating rollback"
    
    if [[ -x "${SCRIPT_DIR}/health-check.sh" ]]; then
        if "${SCRIPT_DIR}/health-check.sh" --wait 120; then
            log_info "Rollback validation successful"
            return 0
        else
            log_error "Rollback validation failed - services not healthy"
            return 1
        fi
    else
        log_warn "Health check script not available"
        return 0
    fi
}

record_rollback() {
    local from_version="$1"
    local to_version="$2"
    
    local timestamp
    timestamp=$(date -Iseconds)
    
    echo "$to_version $timestamp ROLLBACK_FROM:$from_version" >> "$DEPLOYMENT_HISTORY_FILE"
    
    log_info "Rollback recorded in deployment history"
}

confirm_rollback() {
    local current="$1"
    local target="$2"
    local force="$3"
    
    if [[ "$force" == "true" ]]; then
        return 0
    fi
    
    echo ""
    echo -e "${YELLOW}ROLLBACK CONFIRMATION${NC}"
    echo "Current version: $current"
    echo "Target version:  $target"
    echo ""
    read -r -p "Proceed with rollback? [y/N] " response
    
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            log_info "Rollback cancelled"
            exit 0
            ;;
    esac
}

# =============================================================================
# Main
# =============================================================================
main() {
    local target_version=""
    local force=false
    local list_only=false
    local skip_db_restore=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                ;;
            --list|-l)
                list_only=true
                shift
                ;;
            --force|-f)
                force=true
                shift
                ;;
            --skip-db-restore)
                skip_db_restore=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                ;;
            *)
                target_version="$1"
                shift
                ;;
        esac
    done
    
    # Handle list mode
    if [[ "$list_only" == "true" ]]; then
        list_available_versions
        exit 0
    fi
    
    # Get current version
    local current_version
    current_version=$(get_current_version)
    log_info "Current version: $current_version"
    
    # Determine target version
    if [[ -z "$target_version" ]]; then
        target_version=$(get_previous_version) || {
            log_error "Cannot determine previous version"
            log_info "Please specify a target version: ./rollback.sh v1.0.0"
            exit 2
        }
        log_info "Rolling back to previous version: $target_version"
    fi
    
    # Validate target
    validate_target_version "$target_version"
    
    # Confirm rollback
    confirm_rollback "$current_version" "$target_version" "$force"
    
    log_info "Starting rollback from $current_version to $target_version"
    
    # Create safety backup
    create_safety_backup
    
    # Find backup for target version
    local backup_file
    backup_file=$(find_backup_for_version "$target_version")
    
    # Perform rollback
    stop_services
    checkout_version "$target_version"
    restore_backup "$skip_db_restore" "$backup_file"
    start_services "$target_version"
    
    # Validate
    if validate_rollback; then
        record_rollback "$current_version" "$target_version"
        log_info "Rollback successful: $target_version"
    else
        log_error "Rollback completed but validation failed"
        exit 1
    fi
}

main "$@"
