"""Unit tests for health check endpoint.

Tests the health check API contract defined in:
specs/003-digitalocean-deployment/contracts/health-check-api.md
"""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.system.health import (
    APP_VERSION,
    DependencyHealth,
    HealthCheckResult,
    check_postgres_health,
    check_redis_health,
    get_http_status_code,
    perform_health_check,
    reset_start_time,
)


class TestDependencyHealth:
    """Tests for DependencyHealth dataclass."""

    def test_healthy_dependency(self):
        """Test creating a healthy dependency status."""
        dep = DependencyHealth(status="healthy", response_time_ms=15)

        assert dep.status == "healthy"
        assert dep.response_time_ms == 15
        assert dep.error is None

    def test_unhealthy_dependency(self):
        """Test creating an unhealthy dependency status."""
        dep = DependencyHealth(
            status="unhealthy",
            response_time_ms=None,
            error="Connection refused",
        )

        assert dep.status == "unhealthy"
        assert dep.response_time_ms is None
        assert dep.error == "Connection refused"


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_healthy_result_to_dict(self):
        """Test converting healthy result to dictionary."""
        result = HealthCheckResult(
            status="healthy",
            version="1.2.0",
            uptime_seconds=3600,
            timestamp="2025-12-28T10:30:00Z",
            dependencies={
                "postgres": DependencyHealth(status="healthy", response_time_ms=15),
                "redis": DependencyHealth(status="healthy", response_time_ms=3),
            },
        )

        data = result.to_dict()

        assert data["status"] == "healthy"
        assert data["version"] == "1.2.0"
        assert data["uptime_seconds"] == 3600
        assert data["timestamp"] == "2025-12-28T10:30:00Z"
        assert data["dependencies"]["postgres"]["status"] == "healthy"
        assert data["dependencies"]["postgres"]["response_time_ms"] == 15
        assert data["dependencies"]["redis"]["status"] == "healthy"
        assert "warnings" not in data
        assert "errors" not in data

    def test_degraded_result_to_dict(self):
        """Test converting degraded result to dictionary."""
        result = HealthCheckResult(
            status="degraded",
            version="1.2.0",
            uptime_seconds=3600,
            timestamp="2025-12-28T10:30:00Z",
            dependencies={
                "postgres": DependencyHealth(status="healthy", response_time_ms=15),
                "redis": DependencyHealth(
                    status="unhealthy",
                    error="Connection timeout",
                ),
            },
            warnings=["Redis unavailable"],
        )

        data = result.to_dict()

        assert data["status"] == "degraded"
        assert data["dependencies"]["redis"]["status"] == "unhealthy"
        assert data["dependencies"]["redis"]["error"] == "Connection timeout"
        assert "response_time_ms" not in data["dependencies"]["redis"]
        assert data["warnings"] == ["Redis unavailable"]

    def test_unhealthy_result_to_dict(self):
        """Test converting unhealthy result to dictionary."""
        result = HealthCheckResult(
            status="unhealthy",
            version="1.2.0",
            uptime_seconds=120,
            timestamp="2025-12-28T10:30:00Z",
            dependencies={
                "postgres": DependencyHealth(
                    status="unhealthy", error="Connection refused"
                ),
                "redis": DependencyHealth(status="unhealthy", error="ECONNREFUSED"),
            },
            errors=["Critical: postgres connection failed", "Critical: redis connection failed"],
        )

        data = result.to_dict()

        assert data["status"] == "unhealthy"
        assert data["errors"] == [
            "Critical: postgres connection failed",
            "Critical: redis connection failed",
        ]


class TestCheckPostgresHealth:
    """Tests for PostgreSQL health check."""

    @pytest.mark.asyncio
    async def test_postgres_healthy(self):
        """Test PostgreSQL health check when database is responsive."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        result = await check_postgres_health(mock_session)

        assert result.status == "healthy"
        assert result.response_time_ms is not None
        assert result.response_time_ms >= 0
        assert result.error is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_postgres_unhealthy_connection_error(self):
        """Test PostgreSQL health check when connection fails."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Connection refused"))

        result = await check_postgres_health(mock_session)

        assert result.status == "unhealthy"
        assert result.response_time_ms is None
        assert "Connection failed" in result.error


class TestCheckRedisHealth:
    """Tests for Redis health check."""

    @pytest.mark.asyncio
    async def test_redis_healthy(self):
        """Test Redis health check when cache is responsive."""
        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis.from_url = AsyncMock(return_value=mock_client)

            result = await check_redis_health("redis://localhost:6379")

            assert result.status == "healthy"
            assert result.response_time_ms is not None
            assert result.response_time_ms >= 0
            assert result.error is None

    @pytest.mark.asyncio
    async def test_redis_unhealthy_connection_error(self):
        """Test Redis health check when connection fails."""
        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_redis.from_url = AsyncMock(side_effect=Exception("ECONNREFUSED"))

            result = await check_redis_health("redis://localhost:6379")

            assert result.status == "unhealthy"
            assert result.response_time_ms is None
            assert "Connection failed" in result.error


class TestPerformHealthCheck:
    """Tests for comprehensive health check."""

    @pytest.mark.asyncio
    async def test_all_healthy(self):
        """Test health check when all dependencies are healthy."""
        reset_start_time()

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis.from_url = AsyncMock(return_value=mock_client)

            result = await perform_health_check(
                db_session=mock_session,
                redis_url="redis://localhost:6379",
            )

            assert result.status == "healthy"
            assert result.version == APP_VERSION
            assert result.uptime_seconds >= 0
            assert result.dependencies["postgres"].status == "healthy"
            assert result.dependencies["redis"].status == "healthy"
            assert result.warnings == []
            assert result.errors == []

    @pytest.mark.asyncio
    async def test_redis_unhealthy_degraded(self):
        """Test health check returns degraded when Redis is down."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_redis.from_url = AsyncMock(side_effect=Exception("Connection refused"))

            result = await perform_health_check(
                db_session=mock_session,
                redis_url="redis://localhost:6379",
            )

            assert result.status == "degraded"
            assert result.dependencies["postgres"].status == "healthy"
            assert result.dependencies["redis"].status == "unhealthy"
            assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_all_unhealthy(self):
        """Test health check returns unhealthy when all dependencies are down."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_redis.from_url = AsyncMock(side_effect=Exception("ECONNREFUSED"))

            result = await perform_health_check(
                db_session=mock_session,
                redis_url="redis://localhost:6379",
            )

            assert result.status == "unhealthy"
            assert result.dependencies["postgres"].status == "unhealthy"
            assert result.dependencies["redis"].status == "unhealthy"
            assert len(result.errors) == 2

    @pytest.mark.asyncio
    async def test_no_session_provided(self):
        """Test health check when no database session is provided."""
        result = await perform_health_check(db_session=None, redis_url=None)

        assert result.status == "unhealthy"
        assert result.dependencies["postgres"].status == "unhealthy"
        assert result.dependencies["redis"].status == "unhealthy"

    @pytest.mark.asyncio
    async def test_timestamp_format(self):
        """Test that timestamp is in ISO 8601 format with Z suffix."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis.from_url = AsyncMock(return_value=mock_client)

            result = await perform_health_check(
                db_session=mock_session,
                redis_url="redis://localhost:6379",
            )

            # Verify timestamp format
            assert result.timestamp.endswith("Z")
            # Verify it can be parsed as ISO 8601
            datetime.fromisoformat(result.timestamp.replace("Z", "+00:00"))


class TestGetHttpStatusCode:
    """Tests for HTTP status code determination."""

    def test_healthy_returns_200(self):
        """Test healthy status returns 200 OK."""
        assert get_http_status_code("healthy") == 200

    def test_degraded_returns_200(self):
        """Test degraded status returns 200 OK (service still operational)."""
        assert get_http_status_code("degraded") == 200

    def test_unhealthy_returns_503(self):
        """Test unhealthy status returns 503 Service Unavailable."""
        assert get_http_status_code("unhealthy") == 503


class TestContractCompliance:
    """Tests verifying compliance with health-check-api.md contract."""

    @pytest.mark.asyncio
    async def test_response_contains_required_fields(self):
        """Verify response contains all required fields per contract."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis.from_url = AsyncMock(return_value=mock_client)

            result = await perform_health_check(
                db_session=mock_session,
                redis_url="redis://localhost:6379",
            )

            data = result.to_dict()

            # Required top-level fields
            assert "status" in data
            assert "version" in data
            assert "uptime_seconds" in data
            assert "timestamp" in data
            assert "dependencies" in data

            # Status must be valid value
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

            # Dependencies must include postgres and redis
            assert "postgres" in data["dependencies"]
            assert "redis" in data["dependencies"]

            # Each dependency must have status
            for dep_name, dep_data in data["dependencies"].items():
                assert "status" in dep_data
                assert dep_data["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_healthy_dependency_includes_response_time(self):
        """Verify healthy dependencies include response_time_ms per contract."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        with patch("src.handlers.system.health.redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis.from_url = AsyncMock(return_value=mock_client)

            result = await perform_health_check(
                db_session=mock_session,
                redis_url="redis://localhost:6379",
            )

            data = result.to_dict()

            # Healthy dependencies must include response_time_ms
            assert "response_time_ms" in data["dependencies"]["postgres"]
            assert "response_time_ms" in data["dependencies"]["redis"]
            assert isinstance(data["dependencies"]["postgres"]["response_time_ms"], int)
            assert isinstance(data["dependencies"]["redis"]["response_time_ms"], int)
