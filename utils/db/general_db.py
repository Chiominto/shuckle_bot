import discord
from utils.logs.pretty_log import pretty_log

TABLE_NAMES = [
    "berry_reminder",
    "celestial_members",
    "ev_tracker",
    "giveaway_entries",
    "market_alerts",
    "personal_roles",
    "user_alerts",
    "watering_can",
]


async def update_username_in_dbs(bot: discord.Client, user_id: int, new_username: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            for table in TABLE_NAMES:
                await conn.execute(
                    f"UPDATE {table} SET user_name = $1 WHERE user_id = $2;",
                    new_username,
                    user_id,
                )
        pretty_log(
            tag="info",
            message=f"Updated username for user {user_id} to '{new_username}' in all relevant database tables",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update username for user {user_id} in databases: {e}",
            include_trace=True,
        )


async def remove_user_from_dbs(bot: discord.Client, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            for table in TABLE_NAMES:
                await conn.execute(
                    f"DELETE FROM {table} WHERE user_id = $1;",
                    user_id,
                )
            pretty_log(
                tag="info",
                message=f"Removed user {user_id} from all relevant database tables",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to remove user {user_id} from databases: {e}",
            include_trace=True,
        )
