import discord
from utils.logs.pretty_log import pretty_log


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Spooky Hour DB Functions
# 🤍💫────────────────────────────────────────────💫🤍
async def upsert_spooky_hour(
    bot: discord.Client,
    ends_on: int,
    message_id: int = None,
    special_code_count: int = None,
    zero_code_announced: bool = False,
):
    """
    Upserts the spooky_hour row with the given ends_on, optional message_id, special_code_count, and zero_code_announced.
    """
    query = """
        INSERT INTO spooky_hour (id, ends_on, message_id, special_code_count, zero_code_announced)
        VALUES (1, $1, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE SET
            ends_on = EXCLUDED.ends_on,
            message_id = EXCLUDED.message_id,
            special_code_count = EXCLUDED.special_code_count,
            zero_code_announced = EXCLUDED.zero_code_announced
    """
    params = (ends_on, message_id, special_code_count, zero_code_announced)
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, *params)
        pretty_log(
            "success",
            f"Upserted spooky_hour with ends_on {ends_on}"
            + (f", message_id {message_id}" if message_id else "")
            + (
                f", special_code_count {special_code_count}"
                if special_code_count is not None
                else ""
            )
            + f", zero_code_announced {zero_code_announced}",

        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert spooky_hour: {e}",
            
        )


async def remove_spooky_hour(bot: discord.Client):
    """
    Removes the row from spooky_hour table.
    """
    query = "DELETE FROM spooky_hour"
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query)
        pretty_log(
            "success",
            "Removed spooky_hour row",

        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove spooky_hour row: {e}",

        )


async def reset_spooky_hour(bot: discord.Client):
    """
    Resets event-specific spooky_hour columns, but does NOT touch special_code_count or zero_code_announced.
    """
    query = """
        UPDATE spooky_hour
        SET ends_on = NULL,
            message_id = NULL
        WHERE id = 1
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query)
        pretty_log(
            "success",
            "Reset spooky_hour event columns (kept special_code_count and zero_code_announced)",

        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to reset spooky_hour event columns: {e}",

        )


async def update_spooky_hour_event(
    bot: discord.Client,
    ends_on: int = None,
    message_id: int = None,
):
    """
    Updates event-specific columns in the spooky_hour table (ends_on, message_id).
    Does NOT touch special_code_count or zero_code_announced.
    """
    query = """
        UPDATE spooky_hour
        SET ends_on = $1,
            message_id = $2
        WHERE id = 1
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, ends_on, message_id)
        pretty_log(
            "success",
            f"Updated spooky_hour event columns: ends_on={ends_on}, message_id={message_id}",

        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update spooky_hour event columns: {e}",

        )


async def fetch_spooky_hour(bot: discord.Client):
    """
    Fetches the spooky_hour row.
    Returns a dict with ends_on, message_id, special_code_count, and zero_code_announced, or None if not found.
    """
    query = "SELECT ends_on, message_id, special_code_count, zero_code_announced FROM spooky_hour LIMIT 1"
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query)
        if row:
            return {
                "ends_on": row["ends_on"],
                "message_id": row["message_id"],
                "special_code_count": row["special_code_count"],
                "zero_code_announced": row["zero_code_announced"],
            }
        return None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch spooky_hour row: {e}",

        )
        return None


async def update_zero_code_announced(bot: discord.Client, announced: bool):
    """
    Updates the zero_code_announced column in the spooky_hour table.
    """
    query = "UPDATE spooky_hour SET zero_code_announced = $1 WHERE id = 1"
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, announced)
        pretty_log(
            "success",
            f"Updated zero_code_announced to {announced}",

        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update zero_code_announced: {e}",

        )


async def update_code_count(bot: discord.Client, special_code_count: int):
    """
    Updates the special_code_count column in the spooky_hour table.
    """
    query = "UPDATE spooky_hour SET special_code_count = $1 WHERE id = 1"
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, special_code_count)
        pretty_log(
            "success",
            f"Updated special_code_count to {special_code_count}",

        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update special_code_count: {e}",

        )
