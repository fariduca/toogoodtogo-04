"""Health check endpoint for production monitoring.

Implements the health check API contract defined in:
specs/003-digitalocean-deployment/contracts/health-check-api.md

Used by Docker health checks, deployment scripts, and monitoring systems.
"""

import asyncio
import os
import resource
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger

logger = get_logger(__name__)

# Track application start time for uptime calculation
_start_time: float = time.time()

# Application version from environment or default
APP_VERSION: str = os.environ.get("APP_VERSION", "0.0.0-dev")


@dataclass
class DependencyHealth:
    """Health status for a single dependency."""

    status: str  # "healthy" or "unhealthy"
    response_time_ms: int | None = None
    error: str | None = None


@dataclass
class ResourceMetrics:
    """Resource usage metrics for monitoring."""

    memory_rss_bytes: int  # Resident set size
    memory_vms_bytes: int  # Virtual memory size
    cpu_user_seconds: float  # User CPU time
    cpu_system_seconds: float  # System CPU time
    open_fds: int | None = None  # Open file descriptors (Linux only)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        result: dict[str, Any] = {
            "memory_rss_bytes": self.memory_rss_bytes,
            "memory_vms_bytes": self.memory_vms_bytes,
            "cpu_user_seconds": round(self.cpu_user_seconds, 3),
            "cpu_system_seconds": round(self.cpu_system_seconds, 3),
        }
        if self.open_fds is not None:
            result["open_fds"] = self.open_fds
        return result


@dataclass
class HealthCheckResult:
    """Complete health check response."""

    status: str  # "healthy", "degraded", or "unhealthy"
    version: str
    uptime_seconds: int
    timestamp: str
    dependencies: dict[str, DependencyHealth] = field(default_factory=dict)
    resources: ResourceMetrics | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        result: dict[str, Any] = {
            "status": self.status,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp,
            "dependencies": {},
        }

        for name, dep in self.dependencies.items():
            dep_dict: dict[str, Any] = {"status": dep.status}
            if dep.response_time_ms is not None:
                dep_dict["response_time_ms"] = dep.response_time_ms
            if dep.error:
                dep_dict["error"] = dep.error
            result["dependencies"][name] = dep_dict

        if self.resources is not None:
            result["resources"] = self.resources.to_dict()

        if self.warnings:
            result["warnings"] = self.warnings
        if self.errors:
            result["errors"] = self.errors

        return result


def collect_resource_metrics() -> ResourceMetrics:
    """Collect current resource usage metrics.

    Returns:
        ResourceMetrics with memory and CPU usage
    """
    try:
        # Get resource usage
        usage = resource.getrusage(resource.RUSAGE_SELF)

        # Memory: maxrss is in KB on Linux, bytes on macOS
        # We'll use /proc/self/status on Linux for accurate values
        memory_rss = usage.ru_maxrss * 1024  # Convert to bytes (Linux)

        # Try to get more accurate memory from /proc on Linux
        vms_bytes = 0
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        memory_rss = int(line.split()[1]) * 1024  # KB to bytes
                    elif line.startswith("VmSize:"):
                        vms_bytes = int(line.split()[1]) * 1024  # KB to bytes
        except (FileNotFoundError, PermissionError):
            # Not on Linux or no access to /proc
            vms_bytes = memory_rss  # Fallback

        # Get open file descriptors count (Linux only)
        open_fds = None
        try:
            import os
            open_fds = len(os.listdir("/proc/self/fd"))
        except (FileNotFoundError, PermissionError):
            pass

        return ResourceMetrics(
            memory_rss_bytes=memory_rss,
            memory_vms_bytes=vms_bytes,
            cpu_user_seconds=usage.ru_utime,
            cpu_system_seconds=usage.ru_stime,
            open_fds=open_fds,
        )
    except Exception as e:
        logger.warning("Failed to collect resource metrics", error=str(e))
        return ResourceMetrics(
            memory_rss_bytes=0,
            memory_vms_bytes=0,
            cpu_user_seconds=0.0,
            cpu_system_seconds=0.0,
        )


async def check_postgres_health(session: AsyncSession) -> DependencyHealth:
    """Check PostgreSQL database health.

    Args:
        session: SQLAlchemy async session

    Returns:
        DependencyHealth with status and response time
    """
    start = time.perf_counter()
    try:
        # Simple connectivity check
        await session.execute(text("SELECT 1"))
        response_time = int((time.perf_counter() - start) * 1000)
        return DependencyHealth(status="healthy", response_time_ms=response_time)
    except Exception as e:
        logger.error("postgres_health_check_failed", error=str(e))
        return DependencyHealth(
            status="unhealthy",
            response_time_ms=None,
            error=f"Connection failed: {str(e)[:100]}",
        )


async def check_redis_health(redis_url: str) -> DependencyHealth:
    """Check Redis cache health.

    Args:
        redis_url: Redis connection URL

    Returns:
        DependencyHealth with status and response time
    """
    start = time.perf_counter()
    client = None
    try:
        client = await redis.from_url(redis_url, socket_timeout=5.0)
        await client.ping()
        response_time = int((time.perf_counter() - start) * 1000)
        return DependencyHealth(status="healthy", response_time_ms=response_time)
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return DependencyHealth(
            status="unhealthy",
            response_time_ms=None,
            error=f"Connection failed: {str(e)[:100]}",
        )
    finally:
        if client:
            await client.close()


async def perform_health_check(
    db_session: AsyncSession | None = None,
    redis_url: str | None = None,
    include_resources: bool = True,
) -> HealthCheckResult:
    """Perform comprehensive health check of all dependencies.

    Args:
        db_session: Optional database session for PostgreSQL check
        redis_url: Optional Redis URL for Redis check
        include_resources: Whether to include resource metrics (default True)

    Returns:
        HealthCheckResult with overall status and dependency details
    """
    uptime = int(time.time() - _start_time)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    result = HealthCheckResult(
        status="healthy",
        version=APP_VERSION,
        uptime_seconds=uptime,
        timestamp=timestamp,
    )

    # Collect resource metrics if requested
    if include_resources:
        result.resources = collect_resource_metrics()

    # Check PostgreSQL if session provided
    if db_session is not None:
        result.dependencies["postgres"] = await check_postgres_health(db_session)
    else:
        result.dependencies["postgres"] = DependencyHealth(
            status="unhealthy",
            error="Database session not available",
        )
        result.warnings.append("Database check skipped - no session available")

    # Check Redis if URL provided
    if redis_url:
        result.dependencies["redis"] = await check_redis_health(redis_url)
    else:
        result.dependencies["redis"] = DependencyHealth(
            status="unhealthy",
            error="Redis URL not configured",
        )
        result.warnings.append("Redis check skipped - URL not configured")

    # Determine overall status
    unhealthy_deps = [
        name for name, dep in result.dependencies.items() if dep.status == "unhealthy"
    ]

    if len(unhealthy_deps) == len(result.dependencies):
        # All dependencies unhealthy
        result.status = "unhealthy"
        result.errors = [f"Critical: {dep} connection failed" for dep in unhealthy_deps]
    elif unhealthy_deps:
        # Some dependencies unhealthy
        result.status = "degraded"
        for dep in unhealthy_deps:
            result.warnings.append(f"{dep.capitalize()} unavailable")
    else:
        # All healthy
        result.status = "healthy"

    return result


def get_http_status_code(health_status: str) -> int:
    """Get HTTP status code for health status.

    Args:
        health_status: "healthy", "degraded", or "unhealthy"

    Returns:
        HTTP status code (200 or 503)
    """
    if health_status == "unhealthy":
        return 503
    return 200


# HTTP server for health endpoint
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health check endpoint."""

    # Class-level references to resources (set during server startup)
    db = None
    redis_url: str | None = None
    loop: asyncio.AbstractEventLoop | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use structured logging."""
        logger.debug("health_http_request", message=format % args)

    def do_GET(self) -> None:
        """Handle GET requests to /health endpoint."""
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')
            return

        async def run_check() -> HealthCheckResult:
            session = None
            try:
                if self.db is not None:
                    async with self.db.session() as session:
                        return await perform_health_check(session, self.redis_url)
                return await perform_health_check(None, self.redis_url)
            except Exception as e:
                logger.error("health_check_error", error=str(e))
                return HealthCheckResult(
                    status="unhealthy",
                    version=APP_VERSION,
                    uptime_seconds=int(time.time() - _start_time),
                    timestamp=datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    errors=[f"Health check failed: {str(e)}"],
                )

        loop = self.loop
        if loop is None or loop.is_closed():
            logger.error(
                "health_check_error",
                error="Event loop unavailable for health check",
            )
            result = HealthCheckResult(
                status="unhealthy",
                version=APP_VERSION,
                uptime_seconds=int(time.time() - _start_time),
                timestamp=datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                errors=["Health check loop unavailable"],
            )
        else:
            future = asyncio.run_coroutine_threadsafe(run_check(), loop)
            try:
                result = future.result(timeout=10)
            except Exception as e:
                future.cancel()
                logger.error("health_check_error", error=str(e))
                result = HealthCheckResult(
                    status="unhealthy",
                    version=APP_VERSION,
                    uptime_seconds=int(time.time() - _start_time),
                    timestamp=datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    errors=[f"Health check error: {str(e)}"],
                )

        # Send response
        import json

        status_code = get_http_status_code(result.status)
        response_body = json.dumps(result.to_dict())

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(response_body.encode("utf-8"))


def start_health_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    db: Any = None,
    redis_url: str | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> HTTPServer:
    """Start HTTP server for health check endpoint.

    Args:
        host: Host to bind to
        port: Port to listen on
        db: Database instance for health checks
        redis_url: Redis URL for health checks
        loop: Event loop used to execute async health checks

    Returns:
        Running HTTPServer instance
    """
    HealthCheckHandler.db = db
    HealthCheckHandler.redis_url = redis_url
    HealthCheckHandler.loop = loop or asyncio.get_event_loop()

    server = HTTPServer((host, port), HealthCheckHandler)
    logger.info("health_server_started", host=host, port=port)
    return server


def reset_start_time() -> None:
    """Reset start time for testing purposes."""
    global _start_time
    _start_time = time.time()
