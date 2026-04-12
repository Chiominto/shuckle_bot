import discord
from utils.logs.pretty_log import pretty_log


# SQL SCRIPT
"""CREATE TABLE personal_roles (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    role_id BIGINT
);
"""

async def upsert_personal_role(bot: discord.Client, user_id: int, user_name: str, role_id: int):
    """Inserts or updates a personal role in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO personal_roles (user_id, user_name, role_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    role_id = EXCLUDED.role_id;
                """,
                user_id,
                user_name,
                role_id,
            )
            return True, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert personal role for {user_id} - {user_name}: {e}",
            include_trace=True,
        )
        return False, str(e)

async def fetch_personal_role(bot: discord.Client, user_id: int):
    """Fetches a personal role for a user from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT user_id, user_name, role_id FROM personal_roles WHERE user_id = $1;", user_id)
            return row, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch personal role for user {user_id}: {e}",
            include_trace=True,
        )
        return None, str(e)

async def fetch_personal_role_id(bot: discord.Client, user_id: int):
    """Fetches just the role ID of a user's personal role from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT role_id FROM personal_roles WHERE user_id = $1;", user_id)
            return row["role_id"] if row else None, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch personal role ID for user {user_id}: {e}",
            include_trace=True,
        )
        return None, str(e)

async def fetch_personal_role_by_role_id(bot: discord.Client, role_id: int):
    """Fetches a personal role by role ID from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT user_id, user_name, role_id FROM personal_roles WHERE role_id = $1;", role_id)
            return row, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch personal role for role ID {role_id}: {e}",
            include_trace=True,
        )
        return None, str(e)

async def delete_personal_role(bot: discord.Client, user_id: int):
    """Deletes a personal role for a user from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM personal_roles WHERE user_id = $1;", user_id)
            return True, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete personal role for user {user_id}: {e}",
            include_trace=True,
        )
        return False, str(e)