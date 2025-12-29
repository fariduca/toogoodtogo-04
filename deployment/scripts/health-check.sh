#!/bin/bash
# TooGoodToGo Health Check Script
# Validate health of deployed services (polling baseline)

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEPLOY_DIR="${DEPLOY_DIR:-/opt/toogoodtogo}"
readonly DEPLOYMENT_DIR="${DEPLOY_DIR}/deployment"
readonly LOG_DIR="/var/log/toogoodtogo"
readonly LOG_FILE="${LOG_DIR}/deployment.log"
readonly DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
readonly TIMEOUT="${TIMEOUT:-10}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Track results
declare -A SERVICE_STATUS
OVERALL_STATUS="healthy"

mkdir -p "$LOG_DIR" 2>/dev/null || true

# =============================================================================
# Helpers
# =============================================================================
log() {
    local level="$1"; shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        INFO)  echo -e "${GREEN}[${timestamp}]${NC} INFO: ${message}" ;;
        WARN)  echo -e "${YELLOW}[${timestamp}]${NC} WARN: ${message}" ;;
        ERROR) echo -e "${RED}[${timestamp}]${NC} ERROR: ${message}" >&2 ;;
    esac

    echo "[${timestamp}] ${level}: ${message}" >> "$LOG_FILE" 2>/dev/null || true
}

log_info() { log INFO "$@"; }
log_warn() { log WARN "$@"; }
log_error() { log ERROR "$@"; }

container_exists() {
    local name="$1"
    docker ps -a --format '{{.Names}}' | grep -qx "$name"
}

docker_compose_cmd() {
    local compose_dir
    compose_dir="${DEPLOYMENT_DIR}"
    if [[ ! -d "$compose_dir" ]]; then
        compose_dir="$(dirname "$SCRIPT_DIR")"
    fi
    (cd "$compose_dir" && docker compose -f "$DOCKER_COMPOSE_FILE" "$@")
}

show_help() {
    cat << EOF
TooGoodToGo Health Check Script

Usage: $(basename "$0") [service] [OPTIONS]

Services:
    all        Check bot, postgres, redis, nginx (nginx skipped if profile disabled)
    bot        Check bot container health endpoint
    postgres   Check postgres readiness via pg_isready
    redis      Check redis via redis-cli PING
    nginx      Check nginx container presence/process (skipped if absent)
    startup    Post-boot validation (containers + systemd)

Options:
    --json              Output results in JSON format
    --quiet, -q         Only output status (no details)
    --wait SECONDS      Wait for services to become healthy (default: no wait)
    --help, -h          Show this help message

Exit Codes:
    0 - All checked services healthy
    1 - One or more services unhealthy
    2 - Health check timeout

Examples:
    ./health-check.sh                    # Check all services
    ./health-check.sh bot                # Check only bot
    ./health-check.sh startup            # Verify services after reboot
    ./health-check.sh --json             # JSON output
    ./health-check.sh --wait 60          # Wait up to 60s for healthy
EOF
    exit 0
}

# =============================================================================
# Service Health Checks
# =============================================================================
check_bot_health() {
    local start_time
    start_time=$(date +%s%N)

    if ! container_exists "toogoodtogo_bot"; then
        SERVICE_STATUS["bot"]="unhealthy"
        SERVICE_STATUS["bot_error"]="container missing"
        SERVICE_STATUS["bot_time"]=0
        return 1
    fi

    local output
    if ! output=$(docker_compose_cmd exec -T bot python - <<'PY'
import sys, json, urllib.request, os
url = os.environ.get("HEALTH_ENDPOINT", "http://127.0.0.1:8000/health")
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        print(resp.getcode())
        print(resp.read().decode())
except Exception as e:
    print(f"ERR:{e}", file=sys.stderr)
    sys.exit(1)
PY
    ); then
        local end_time
        end_time=$(date +%s%N)
        local response_ms=$(((end_time - start_time) / 1000000))
        SERVICE_STATUS["bot"]="unhealthy"
        SERVICE_STATUS["bot_time"]="$response_ms"
        SERVICE_STATUS["bot_error"]="Connection failed"
        return 1
    fi

    local end_time
    end_time=$(date +%s%N)
    local response_ms=$(((end_time - start_time) / 1000000))

    local http_code
    http_code=$(echo "$output" | head -1)
    local body
    body=$(echo "$output" | tail -n +2)

    local status
    status=$(echo "$body" | grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)

    SERVICE_STATUS["bot_time"]="$response_ms"

    if [[ "$http_code" == "200" ]] && [[ "$status" == "healthy" ]]; then
        SERVICE_STATUS["bot"]="healthy"
        return 0
    elif [[ "$http_code" == "200" ]] && [[ "$status" == "degraded" ]]; then
        SERVICE_STATUS["bot"]="degraded"
        SERVICE_STATUS["bot_error"]="Service degraded"
        return 0
    else
        SERVICE_STATUS["bot"]="unhealthy"
        SERVICE_STATUS["bot_error"]="Status: $status, HTTP: $http_code"
        return 1
    fi
}

check_postgres_health() {
    local start_time
    start_time=$(date +%s%N)

    if docker_compose_cmd exec -T postgres pg_isready -U "${POSTGRES_USER:-toogoodtogo}" &>/dev/null; then
        local end_time
        end_time=$(date +%s%N)
        SERVICE_STATUS["postgres_time"]=$(((end_time - start_time) / 1000000))
        SERVICE_STATUS["postgres"]="healthy"
        return 0
    fi

    local end_time
    end_time=$(date +%s%N)
    SERVICE_STATUS["postgres_time"]=$(((end_time - start_time) / 1000000))
    SERVICE_STATUS["postgres"]="unhealthy"
    SERVICE_STATUS["postgres_error"]="pg_isready failed"
    return 1
}

check_redis_health() {
    local start_time
    start_time=$(date +%s%N)

    if docker_compose_cmd exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        local end_time
        end_time=$(date +%s%N)
        SERVICE_STATUS["redis_time"]=$(((end_time - start_time) / 1000000))
        SERVICE_STATUS["redis"]="healthy"
        return 0
    fi

    local end_time
    end_time=$(date +%s%N)
    SERVICE_STATUS["redis_time"]=$(((end_time - start_time) / 1000000))
    SERVICE_STATUS["redis"]="unhealthy"
    SERVICE_STATUS["redis_error"]="PING failed"
    return 1
}

check_nginx_health() {
    local start_time
    start_time=$(date +%s%N)

    if ! container_exists "toogoodtogo_nginx"; then
        SERVICE_STATUS["nginx"]="skipped"
        SERVICE_STATUS["nginx_error"]="not enabled (webhook profile off)"
        return 0
    fi

    if pgrep -x nginx &>/dev/null || docker ps --filter "name=toogoodtogo_nginx" --format "{{.Status}}" | grep -q "Up"; then
        local end_time
        end_time=$(date +%s%N)
        SERVICE_STATUS["nginx_time"]=$(((end_time - start_time) / 1000000))
        SERVICE_STATUS["nginx"]="healthy"
        return 0
    fi

    local end_time
    end_time=$(date +%s%N)
    SERVICE_STATUS["nginx_time"]=$(((end_time - start_time) / 1000000))
    SERVICE_STATUS["nginx"]="unhealthy"
    SERVICE_STATUS["nginx_error"]="Process not running"
    return 1
}

check_container_status() {
    local container_name="$1"
    local container_status

    container_status=$(docker ps --filter "name=${container_name}" --format "{{.Status}}" 2>/dev/null || echo "")

    if [[ -z "$container_status" ]]; then
        echo "not_found"
        return 1
    elif echo "$container_status" | grep -q "^Up"; then
        if echo "$container_status" | grep -q "(healthy)"; then
            echo "healthy"
            return 0
        elif echo "$container_status" | grep -q "(unhealthy)"; then
            echo "unhealthy"
            return 1
        else
            echo "running"
            return 0
        fi
    else
        echo "stopped"
        return 1
    fi
}

check_systemd_service() {
    local service_name="$1"

    if ! command -v systemctl &>/dev/null; then
        echo "systemctl_not_available"
        return 0
    fi

    local active_state
    active_state=$(systemctl is-active "$service_name" 2>/dev/null || echo "unknown")

    case "$active_state" in
        active)
            echo "active"; return 0 ;;
        inactive)
            echo "inactive"; return 1 ;;
        failed)
            echo "failed"; return 1 ;;
        *)
            echo "$active_state"; return 1 ;;
    esac
}

verify_startup() {
    log_info "Verifying services after boot"

    local all_healthy=true
    for container in toogoodtogo_bot toogoodtogo_postgres toogoodtogo_redis; do
        if ! container_exists "$container"; then
            log_error "Container $container missing"
            all_healthy=false
            continue
        fi
        local status
        status=$(check_container_status "$container")
        case "$status" in
            healthy|running)
                log_info "Container $container: $status"
                ;;
            *)
                log_error "Container $container: $status"
                all_healthy=false
                ;;
        esac
    done

    if container_exists "toogoodtogo_nginx"; then
        local status
        status=$(check_container_status "toogoodtogo_nginx")
        if [[ "$status" == "healthy" || "$status" == "running" ]]; then
            log_info "Container toogoodtogo_nginx: $status"
        else
            log_warn "Container toogoodtogo_nginx: $status"
        fi
    else
        log_info "nginx profile disabled; skipping"
    fi

    if command -v systemctl &>/dev/null; then
        local service_status
        service_status=$(check_systemd_service "toogoodtogo.service")
        if [[ "$service_status" == "active" ]]; then
            log_info "systemd toogoodtogo.service: active"
        else
            log_warn "systemd toogoodtogo.service: $service_status"
            all_healthy=false
        fi

        local timer_status
        timer_status=$(check_systemd_service "toogoodtogo-backup.timer")
        if [[ "$timer_status" == "active" ]]; then
            log_info "backup timer: active"
        elif [[ "$timer_status" != "systemctl_not_available" ]]; then
            log_warn "backup timer: $timer_status (backups may not be scheduled)"
        fi
    fi

    if [[ "$all_healthy" == "true" ]]; then
        log_info "Post-boot verification passed"
        return 0
    fi

    log_error "Post-boot verification failed"
    return 1
}

# =============================================================================
# Output Formatting
# =============================================================================
output_text() {
    local quiet="$1"

    for service in bot postgres redis nginx; do
        local status="${SERVICE_STATUS[$service]:-skipped}"
        local time="${SERVICE_STATUS[${service}_time]:-0}"
        local error="${SERVICE_STATUS[${service}_error]:-}"

        if [[ "$status" == "skipped" ]]; then
            continue
        fi

        if [[ "$quiet" == "true" ]]; then
            echo "$service: $status"
        else
            case "$status" in
                healthy)
                    log_info "$service: healthy (response: ${time}ms)"
                    ;;
                degraded)
                    log_warn "$service: degraded (${error})"
                    ;;
                unhealthy)
                    log_error "$service: unhealthy (${error})"
                    ;;
            esac
        fi
    done

    if [[ "$quiet" != "true" ]]; then
        if [[ "$OVERALL_STATUS" == "healthy" ]]; then
            log_info "All services healthy"
        else
            log_error "One or more services unhealthy"
        fi
    fi
}

output_json() {
    local json="{"
    json+="\"status\":\"${OVERALL_STATUS}\","
    json+="\"timestamp\":\"$(date -Iseconds)\","
    json+="\"services\":{"

    local first=true
    for service in bot postgres redis nginx; do
        local status="${SERVICE_STATUS[$service]:-skipped}"

        if [[ "$status" == "skipped" ]]; then
            continue
        fi

        if [[ "$first" != "true" ]]; then
            json+=","
        fi
        first=false

        local time="${SERVICE_STATUS[${service}_time]:-0}"
        local error="${SERVICE_STATUS[${service}_error]:-}"

        json+="\"${service}\":{"
        json+="\"status\":\"${status}\""
        json+=",\"response_time_ms\":${time}"
        if [[ -n "$error" ]]; then
            json+=",\"error\":\"${error}\""
        fi
        json+='}'
    done

    json+='}}'
    echo "$json"
}

# =============================================================================
# Main
# =============================================================================
main() {
    local service="all"
    local json_output=false
    local quiet=false
    local wait_seconds=0

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help ;;
            --json)
                json_output=true; shift ;;
            --quiet|-q)
                quiet=true; shift ;;
            --wait)
                wait_seconds="$2"; shift 2 ;;
            -*)
                log_error "Unknown option: $1"; show_help ;;
            *)
                service="$1"; shift ;;
        esac
    done

    local start_time
    start_time=$(date +%s)

    while true; do
        OVERALL_STATUS="healthy"
        SERVICE_STATUS=()

        if [[ "$json_output" != "true" && "$quiet" != "true" ]]; then
            log_info "Checking service health"
        fi

        case "$service" in
            all)
                check_bot_health || OVERALL_STATUS="unhealthy"
                check_postgres_health || OVERALL_STATUS="unhealthy"
                check_redis_health || OVERALL_STATUS="unhealthy"
                check_nginx_health || true
                ;;
            bot)
                check_bot_health || OVERALL_STATUS="unhealthy" ;;
            postgres)
                check_postgres_health || OVERALL_STATUS="unhealthy" ;;
            redis)
                check_redis_health || OVERALL_STATUS="unhealthy" ;;
            nginx)
                check_nginx_health || OVERALL_STATUS="unhealthy" ;;
            startup)
                verify_startup || OVERALL_STATUS="unhealthy" ;;
            *)
                log_error "Unknown service: $service"; exit 1 ;;
        esac

        if [[ "$wait_seconds" -gt 0 ]]; then
            local elapsed
            elapsed=$(($(date +%s) - start_time))

            if [[ "$OVERALL_STATUS" == "healthy" ]]; then
                break
            elif [[ $elapsed -ge $wait_seconds ]]; then
                log_error "Timeout waiting for healthy services"
                OVERALL_STATUS="timeout"
                break
            else
                sleep 5
                continue
            fi
        else
            break
        fi
    done

    if [[ "$json_output" == "true" ]]; then
        output_json
    else
        output_text "$quiet"
    fi

    case "$OVERALL_STATUS" in
        healthy) exit 0 ;;
        timeout) exit 2 ;;
        *) exit 1 ;;
    esac
}

main "$@"
