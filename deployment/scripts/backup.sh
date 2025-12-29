#!/bin/bash
# TooGoodToGo Database Backup Script
# Create compressed PostgreSQL database backups
#
# Usage: ./backup.sh [backup-type]
#
# Exit Codes:
#   0 - Backup successful
#   1 - Backup failed
#   2 - Verification failed
#   3 - Disk space insufficient

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
readonly BACKUP_RETENTION_DAYS=7
readonly MIN_DISK_SPACE_GB=2
readonly BACKUP_INDEX_FILE="${BACKUP_DIR}/backup_index.json"

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
        INFO)  echo -e "${GREEN}[$timestamp]${NC} INFO: $message" >&2 ;;
        WARN)  echo -e "${YELLOW}[$timestamp]${NC} WARN: $message" >&2 ;;
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
TooGoodToGo Database Backup Script

Usage: $(basename "$0") [BACKUP-TYPE] [OPTIONS]

Arguments:
    BACKUP-TYPE         Type of backup: scheduled, pre_deployment, manual (default: manual)

Options:
    --help              Show this help message
    --list              List available backups
    --clean             Remove backups older than retention period
    --output DIR        Override backup directory

Exit Codes:
    0 - Backup successful (outputs backup file path on last line)
    1 - Backup failed
    2 - Verification failed
    3 - Disk space insufficient

Examples:
    ./backup.sh                         # Manual backup
    ./backup.sh pre_deployment          # Pre-deployment backup
    ./backup.sh scheduled               # Scheduled backup
    ./backup.sh --list                  # List backups
    ./backup.sh --clean                 # Cleanup old backups

EOF
    exit 0
}

# =============================================================================
# Utility Functions
# =============================================================================
check_disk_space() {
    local available_gb
    available_gb=$(df -BG "$BACKUP_DIR" | tail -1 | awk '{print $4}' | tr -d 'G')
    
    if [[ "$available_gb" -lt "$MIN_DISK_SPACE_GB" ]]; then
        log_error "Insufficient disk space: ${available_gb}GB available, ${MIN_DISK_SPACE_GB}GB required"
        exit 3
    fi
    
    log_info "Disk space available: ${available_gb}GB"
}

generate_backup_filename() {
    local backup_type="$1"
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    
    echo "toogoodtogo_${backup_type}_${timestamp}.sql.gz"
}

# =============================================================================
# Backup Operations
# =============================================================================
create_backup() {
    local backup_type="$1"
    local backup_filename
    backup_filename=$(generate_backup_filename "$backup_type")
    local backup_path="${BACKUP_DIR}/${backup_filename}"
    
    log_info "Creating $backup_type backup: $backup_filename"
    
    # Ensure backup directory exists
    mkdir -p "$BACKUP_DIR"
    
    cd "${DEPLOY_DIR}/deployment" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    
    # Source environment for database credentials
    if [[ -f "${DEPLOY_DIR}/deployment/.env.production" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "${DEPLOY_DIR}/deployment/.env.production"
        set +a
    fi
    
    local db_user="${POSTGRES_USER:-toogoodtogo}"
    local db_name="${POSTGRES_DB:-toogoodtogo}"
    
    # Run pg_dump via Docker
    docker compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
        pg_dump -U "$db_user" -d "$db_name" --clean --if-exists --no-owner --no-acl \
        | gzip > "$backup_path"
    
    # Check if backup was created
    if [[ ! -f "$backup_path" ]] || [[ ! -s "$backup_path" ]]; then
        log_error "Backup file was not created or is empty"
        exit 1
    fi
    
    local backup_size
    backup_size=$(du -h "$backup_path" | cut -f1)
    log_info "Backup created: $backup_path (size: $backup_size)"
    
    # Verify backup
    verify_backup "$backup_path"
    
    # Update backup index
    update_backup_index "$backup_path" "$backup_type"
    
    # Output backup path (for scripting)
    echo "$backup_path"
}

verify_backup() {
    local backup_path="$1"
    
    log_info "Verifying backup integrity"
    
    # Test gzip integrity
    if ! gzip -t "$backup_path" 2>/dev/null; then
        log_error "Backup verification failed: gzip test failed"
        exit 2
    fi
    
    # Check for SQL content
    if ! zcat "$backup_path" | head -100 | grep -q "PostgreSQL database dump"; then
        log_error "Backup verification failed: not a valid PostgreSQL dump"
        exit 2
    fi
    
    log_info "Backup verification successful"
}

update_backup_index() {
    local backup_path="$1"
    local backup_type="$2"
    local timestamp
    timestamp=$(date -Iseconds)
    
    # Get backup size
    local size
    size=$(stat -c%s "$backup_path")
    
    # Create or update index
    local entry
    entry=$(cat << EOF
{
    "file": "$(basename "$backup_path")",
    "path": "$backup_path",
    "type": "$backup_type",
    "timestamp": "$timestamp",
    "size_bytes": $size
}
EOF
)
    
    # Append to index file (simple JSON lines format)
    echo "$entry" >> "${BACKUP_INDEX_FILE}.tmp"
    
    # Ensure we maintain a valid JSON structure
    if [[ -f "$BACKUP_INDEX_FILE" ]]; then
        # Merge existing entries
        cat "$BACKUP_INDEX_FILE" "${BACKUP_INDEX_FILE}.tmp" > "${BACKUP_INDEX_FILE}.new"
        mv "${BACKUP_INDEX_FILE}.new" "$BACKUP_INDEX_FILE"
        rm -f "${BACKUP_INDEX_FILE}.tmp"
    else
        mv "${BACKUP_INDEX_FILE}.tmp" "$BACKUP_INDEX_FILE"
    fi
    
    log_info "Backup index updated"
}

list_backups() {
    log_info "Available backups:"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warn "No backup directory found"
        exit 0
    fi
    
    local count=0
    while IFS= read -r -d '' file; do
        local size
        size=$(du -h "$file" | cut -f1)
        local date
        date=$(stat -c%y "$file" | cut -d' ' -f1)
        
        echo "  $(basename "$file") - $size - $date"
        count=$((count + 1))
    done < <(find "$BACKUP_DIR" -name "toogoodtogo_*.sql.gz" -print0 | sort -z)
    
    log_info "Total backups: $count"
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $BACKUP_RETENTION_DAYS days"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warn "No backup directory found"
        exit 0
    fi
    
    local count=0
    while IFS= read -r -d '' file; do
        log_info "Removing old backup: $(basename "$file")"
        rm -f "$file"
        count=$((count + 1))
    done < <(find "$BACKUP_DIR" -name "toogoodtogo_*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS" -print0)
    
    log_info "Removed $count old backups"
}

# =============================================================================
# Main
# =============================================================================
main() {
    local backup_type="manual"
    local list_only=false
    local clean_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                ;;
            --list)
                list_only=true
                shift
                ;;
            --clean)
                clean_only=true
                shift
                ;;
            --output)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                ;;
            *)
                backup_type="$1"
                shift
                ;;
        esac
    done
    
    # Handle list/clean modes
    if [[ "$list_only" == "true" ]]; then
        list_backups
        exit 0
    fi
    
    if [[ "$clean_only" == "true" ]]; then
        cleanup_old_backups
        exit 0
    fi
    
    # Validate backup type
    case "$backup_type" in
        scheduled|pre_deployment|manual)
            ;;
        *)
            log_error "Invalid backup type: $backup_type"
            log_error "Valid types: scheduled, pre_deployment, manual"
            exit 1
            ;;
    esac
    
    log_info "Starting $backup_type backup"
    
    # Pre-checks
    check_disk_space
    
    # Create backup
    create_backup "$backup_type"
    
    # Cleanup old backups (for scheduled backups)
    if [[ "$backup_type" == "scheduled" ]]; then
        cleanup_old_backups
    fi
    
    log_info "Backup complete"
}

main "$@"
