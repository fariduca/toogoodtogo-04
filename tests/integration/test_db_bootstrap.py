"""Integration test for database bootstrap and connectivity."""

import pytest
from sqlalchemy import text

from src.storage.database import get_database


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection can be established."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_database_tables_exist():
    """Test required tables exist in database."""
    db = get_database()
    await db.connect()
    
    try:
        expected_tables = ["businesses", "venues", "offers", "purchases", "customers"]
        
        async with db.session() as session:
            for table_name in expected_tables:
                result = await session.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_name = :table_name)"
                    ),
                    {"table_name": table_name}
                )
                exists = result.scalar()
                assert exists, f"Table {table_name} does not exist"
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_database_migrations_current():
    """Test all alembic migrations are applied."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            result = await session.execute(
                text("SELECT version_num FROM alembic_version")
            )
            version = result.scalar()
            assert version is not None, "No migrations applied"
            # Should have initial migration
            assert version == "001_initial_schema"
    finally:
        await db.disconnect()
