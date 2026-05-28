from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_startup_migrations(engine: AsyncEngine) -> None:
    """Apply lightweight schema migrations needed for local SQLite deployments."""

    async with engine.begin() as connection:
        tables_result = await connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {row[0] for row in tables_result.fetchall()}

        if "conversion_history" in tables:
            columns_result = await connection.execute(text("PRAGMA table_info(conversion_history)"))
            columns = {row[1] for row in columns_result.fetchall()}
            if "user_id" not in columns:
                await connection.execute(text("ALTER TABLE conversion_history ADD COLUMN user_id INTEGER"))

