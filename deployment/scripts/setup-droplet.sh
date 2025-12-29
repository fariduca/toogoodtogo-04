#!/bin/bash
# TooGoodToGo Droplet Setup Script
# Initial server configuration for production deployment
#
# Usage: ./setup-droplet.sh [--non-interactive]
#
# Exit Codes:
#   0 - Setup successful
#   1 - Setup failed
#   2 - Already configured
#
# This script is idempotent - safe to run multiple times

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
readonly DEPLOY_DIR="/opt/toogoodtogo"
readonly LOG_DIR="/var/log/toogoodtogo"
readonly BACKUP_DIR="/opt/backups/postgres"
readonly LOG_FILE="${LOG_DIR}/deployment.log"
readonly SETUP_MARKER="${DEPLOY_DIR}/.setup-complete"
readonly SCRIPT_NAME=$(basename "$0")

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# =============================================================================
# Logging Functions
# =============================================================================
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Console output with color
    case "$level" in
        INFO)  echo -e "${GREEN}[$timestamp]${NC} INFO: $message" ;;
        WARN)  echo -e "${YELLOW}[$timestamp]${NC} WARN: $message" ;;
        ERROR) echo -e "${RED}[$timestamp]${NC} ERROR: $message" >&2 ;;
    esac
    
    # File output (if log directory exists)
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
TooGoodToGo Droplet Setup Script

Usage: $SCRIPT_NAME [OPTIONS]

Options:
    --help              Show this help message
    --non-interactive   Run without prompts (requires environment variables)

Environment Variables (for non-interactive mode):
    TELEGRAM_BOT_TOKEN      Telegram bot API token (required)
    POSTGRES_PASSWORD       PostgreSQL password (required)
    SECRET_KEY              Application secret key (required)
    STRIPE_API_KEY          Stripe API key (optional)
    GIT_REPO_URL            Git repository URL (default: current directory)

Examples:
    # Interactive setup
    sudo ./setup-droplet.sh

    # Non-interactive setup
    export TELEGRAM_BOT_TOKEN="your-token"
    export POSTGRES_PASSWORD="secure-password"
    export SECRET_KEY="random-secret-key"
    sudo -E ./setup-droplet.sh --non-interactive

EOF
    exit 0
}

# =============================================================================
# Validation Functions
# =============================================================================
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_already_configured() {
    if [[ -f "$SETUP_MARKER" ]]; then
        log_warn "Droplet already configured (marker: $SETUP_MARKER)"
        log_info "To reconfigure, remove the marker file: rm $SETUP_MARKER"
        exit 2
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine OS version"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]] || [[ "${VERSION_ID%%.*}" -lt 22 ]]; then
        log_warn "This script is designed for Ubuntu 22.04+. Current: $PRETTY_NAME"
    fi
}

# =============================================================================
# Installation Functions
# =============================================================================
update_system() {
    log_info "Updating system packages..."
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
    log_info "System packages updated"
}

install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker already installed: $(docker --version)"
        return 0
    fi
    
    log_info "Installing Docker..."
    
    # Install prerequisites
    apt-get install -y -qq \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Add repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Enable and start Docker
    systemctl enable docker
    systemctl start docker
    
    log_info "Docker installed: $(docker --version)"
}

configure_firewall() {
    log_info "Configuring firewall (ufw)..."
    
    # Install ufw if not present
    apt-get install -y -qq ufw
    
    # Reset to defaults
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH only (polling mode has no inbound HTTP/S)
    ufw allow OpenSSH
    
    # Enable firewall
    echo "y" | ufw enable
    
    log_info "Firewall configured: SSH, HTTP, HTTPS allowed"
}

install_fail2ban() {
    log_info "Installing and configuring fail2ban..."
    
    # Install fail2ban
    apt-get install -y -qq fail2ban
    
    # Copy custom jail configuration if available
    local jail_src="${DEPLOY_DIR}/deployment/fail2ban/jail.local"
    local jail_dest="/etc/fail2ban/jail.local"
    
    if [[ -f "$jail_src" ]]; then
        cp "$jail_src" "$jail_dest"
        chmod 644 "$jail_dest"
        log_info "Custom fail2ban configuration installed"
    else
        # Create basic SSH protection if custom config not available
        cat > "$jail_dest" << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h
EOF
        chmod 644 "$jail_dest"
        log_info "Basic fail2ban configuration created"
    fi
    
    # Enable and start fail2ban
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    log_info "fail2ban installed and started"
}

create_directories() {
    log_info "Creating application directories..."
    
    # Create main directories
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "${DEPLOY_DIR}/deployment/nginx/ssl"
    mkdir -p "${DEPLOY_DIR}/deployment/scripts"
    
    # Set permissions
    chmod 755 "$DEPLOY_DIR"
    chmod 755 "$LOG_DIR"
    chmod 700 "$BACKUP_DIR"
    
    # Initialize log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    log_info "Directories created"
}

# =============================================================================
# Environment Configuration
# =============================================================================
prompt_for_value() {
    local var_name="$1"
    local prompt="$2"
    local is_secret="${3:-false}"
    local default="${4:-}"
    
    # Check if already set in environment
    if [[ -n "${!var_name:-}" ]]; then
        echo "${!var_name}"
        return 0
    fi
    
    # Interactive prompt
    if [[ "$is_secret" == "true" ]]; then
        read -r -s -p "$prompt: " value
        echo
    else
        if [[ -n "$default" ]]; then
            read -r -p "$prompt [$default]: " value
            value="${value:-$default}"
        else
            read -r -p "$prompt: " value
        fi
    fi
    
    echo "$value"
}

create_env_file() {
    local non_interactive="$1"
    
    log_info "Configuring environment variables..."
    
    local env_file="${DEPLOY_DIR}/deployment/.env.production"
    
    if [[ "$non_interactive" == "true" ]]; then
        # Validate required variables
        local required_vars=("TELEGRAM_BOT_TOKEN" "POSTGRES_PASSWORD" "SECRET_KEY")
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                log_error "Required environment variable not set: $var"
                exit 1
            fi
        done
    else
        # Interactive prompts
        TELEGRAM_BOT_TOKEN=$(prompt_for_value "TELEGRAM_BOT_TOKEN" "Enter Telegram Bot Token" true)
        POSTGRES_PASSWORD=$(prompt_for_value "POSTGRES_PASSWORD" "Enter PostgreSQL Password" true)
        SECRET_KEY=$(prompt_for_value "SECRET_KEY" "Enter Secret Key (or press enter to generate)" true)
        
        # Generate secret key if not provided
        if [[ -z "$SECRET_KEY" ]]; then
            SECRET_KEY=$(openssl rand -hex 32)
            log_info "Generated secret key"
        fi
        
        STRIPE_API_KEY=$(prompt_for_value "STRIPE_API_KEY" "Enter Stripe API Key (optional, press enter to skip)" true)
    fi
    
    # Set defaults
    POSTGRES_USER="${POSTGRES_USER:-toogoodtogo}"
    POSTGRES_DB="${POSTGRES_DB:-toogoodtogo}"
    
    # Write environment file
    cat > "$env_file" << EOF
# TooGoodToGo Production Environment
# Generated: $(date -Iseconds)

# Telegram Configuration
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

# Database Configuration
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}
DATABASE_URL=postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@postgres:5432/\${POSTGRES_DB}

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=${SECRET_KEY}

# Stripe (Optional)
STRIPE_API_KEY=${STRIPE_API_KEY:-}
STRIPE_WEBHOOK_SECRET=

# Monitoring
SENTRY_DSN=
LOG_LEVEL=INFO

# Deployment
DEPLOY_DIR=${DEPLOY_DIR}
BACKUP_DIR=${BACKUP_DIR}
DOCKER_COMPOSE_FILE=docker-compose.prod.yml
HEALTH_CHECK_TIMEOUT=120
APP_VERSION=latest

# SSL (optional, webhook mode only)
DOMAIN=
SSL_EMAIL=
EOF

    # Secure the file
    chmod 600 "$env_file"
    
    log_info "Environment file created: $env_file"
}

# =============================================================================
# SSL Configuration
# =============================================================================
# =============================================================================
# Systemd Service Installation
# =============================================================================
create_systemd_service() {
    log_info "Installing systemd services..."
    
    local systemd_src="${DEPLOY_DIR}/deployment/systemd"
    local systemd_dest="/etc/systemd/system"
    
    # Install main service
    if [[ -f "${systemd_src}/toogoodtogo.service" ]]; then
        cp "${systemd_src}/toogoodtogo.service" "${systemd_dest}/"
        chmod 644 "${systemd_dest}/toogoodtogo.service"
        log_info "Installed toogoodtogo.service"
    else
        log_error "toogoodtogo.service not found in ${systemd_src}"
        return 1
    fi
    
    # Install backup service
    if [[ -f "${systemd_src}/toogoodtogo-backup.service" ]]; then
        cp "${systemd_src}/toogoodtogo-backup.service" "${systemd_dest}/"
        chmod 644 "${systemd_dest}/toogoodtogo-backup.service"
        log_info "Installed toogoodtogo-backup.service"
    else
        log_warn "toogoodtogo-backup.service not found, skipping"
    fi
    
    # Install backup timer
    if [[ -f "${systemd_src}/toogoodtogo-backup.timer" ]]; then
        cp "${systemd_src}/toogoodtogo-backup.timer" "${systemd_dest}/"
        chmod 644 "${systemd_dest}/toogoodtogo-backup.timer"
        log_info "Installed toogoodtogo-backup.timer"
    else
        log_warn "toogoodtogo-backup.timer not found, skipping"
    fi
    
    # Reload systemd daemon
    systemctl daemon-reload
    log_info "Systemd daemon reloaded"
    
    # Enable services
    systemctl enable toogoodtogo.service
    log_info "Enabled toogoodtogo.service"
    
    # Enable backup timer (enables scheduled backups)
    if [[ -f "${systemd_dest}/toogoodtogo-backup.timer" ]]; then
        systemctl enable toogoodtogo-backup.timer
        systemctl start toogoodtogo-backup.timer
        log_info "Enabled and started toogoodtogo-backup.timer (daily backups at 3:00 AM)"
    fi
    
    log_info "Systemd services installed and enabled"
}

# =============================================================================
# Final Validation
# =============================================================================
run_health_check() {
    log_info "Running initial health check..."
    
    local health_script="${DEPLOY_DIR}/deployment/scripts/health-check.sh"
    
    if [[ -x "$health_script" ]]; then
        if "$health_script"; then
            log_info "All services healthy"
            return 0
        else
            log_warn "Some services may not be healthy yet"
            return 0
        fi
    else
        log_warn "Health check script not available yet"
        return 0
    fi
}

mark_setup_complete() {
    echo "Setup completed: $(date -Iseconds)" > "$SETUP_MARKER"
    chmod 644 "$SETUP_MARKER"
    log_info "Setup marked as complete"
}

# =============================================================================
# Main
# =============================================================================
main() {
    local non_interactive=false
    local skip_ssl=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                ;;
            --non-interactive)
                non_interactive=true
                shift
                ;;
            --skip-ssl)
                skip_ssl=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
    
    log_info "Starting droplet setup"
    
    # Pre-flight checks
    check_root
    check_os
    check_already_configured
    
    # Create directories first (for logging)
    create_directories
    
    # System setup
    update_system
    install_docker
    configure_firewall
    install_fail2ban
    
    # Environment configuration
    create_env_file "$non_interactive" "$skip_ssl"
    
    # SSL configuration
    # Service configuration (placeholder)
    create_systemd_service
    
    # Final validation
    run_health_check
    
    # Mark complete
    mark_setup_complete
    
    log_info "Setup complete - system ready for deployment"
    log_info "Next steps:"
    log_info "  1. Copy deployment files to $DEPLOY_DIR/deployment/"
    log_info "  2. Run: cd $DEPLOY_DIR/deployment && ./scripts/deploy.sh <version>"
}

main "$@"
