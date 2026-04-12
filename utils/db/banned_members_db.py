import discord
from utils.logs.pretty_log import pretty_log
import time
# SQL SCRIPT
"""CREATE TABLE banned_members (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    reason TEXT,
    banned_at BIGINT
);
"""

async def upsert_banned_member(
    bot: discord.Client, user_id: int, user_name: str, reason: str
):
    """Inserts or updates a banned member in the database."""
    timestamp = int(time.time())
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO banned_members (user_id, user_name, reason, banned_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    reason = EXCLUDED.reason,
                    banned_at = EXCLUDED.banned_at;
                """,
                user_id,
                user_name,
                reason,
                timestamp,
            )
            
            return True, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert banned member {user_id} - {user_name}: {e}",
            include_trace=True,
        )
        return False, str(e)

async def fetch_all_banned_members(bot: discord.Client):
    """Fetches all banned members from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, user_name, reason, banned_at FROM banned_members;")
            return rows, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch banned members: {e}",
            include_trace=True,
        )
        return None, str(e)

async def delete_banned_member(bot: discord.Client, user_id: int):
    """Deletes a banned member from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM banned_members WHERE user_id = $1;", user_id)
            return True, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete banned member {user_id}: {e}",
            include_trace=True,
        )
        return False, str(e)

async def fetch_banned_member(bot: discord.Client, user_id: int):
    """Fetches a single banned member from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT user_id, user_name, reason, banned_at FROM banned_members WHERE user_id = $1;", user_id)
            return row, None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch banned member {user_id}: {e}",
            include_trace=True,
        )
        return None, str(e)