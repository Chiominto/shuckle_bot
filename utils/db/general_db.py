import asyncpg
import discord

from utils.logs.pretty_log import pretty_log

TABLE_NAMES = [
    "berry_reminder",
    "celestial_members",
    "custom_roles",
    "ev_tracker",
    "giveaway_entries",
    "market_alerts",
    "user_alerts",
    "watering_can",
    "factions",
    "pokemeow_timer",
    "server_cooldowns",
    "server_currency",
    "snipe_ga_wins",
    "special_battle_timers",
    "temp_roles",
    "user_alerts",
    "user_wb_ping",
    "utilities",
    "watering_can",
    "weekly_goal_tracker"

]


async def update_username_in_dbs(bot: discord.Client, user_id: int, new_username: str):
    async with bot.pg_pool.acquire() as conn:
        for table in TABLE_NAMES:
            try:
                await conn.execute(
                    f"UPDATE {table} SET user_name = $1 WHERE user_id = $2;",
                    new_username,
                    user_id,
                )
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=f"Failed to update username for user {user_id} in table '{table}': {e}",
                    include_trace=True,
                )
    pretty_log(
        tag="info",
        message=f"Updated username for user {user_id} to '{new_username}' in all relevant database tables",
    )


async def remove_user_from_dbs(bot: discord.Client, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            failed_tables = []
            for table in TABLE_NAMES:
                try:
                    await conn.execute(
                        f"DELETE FROM {table} WHERE user_id = $1;",
                        user_id,
                    )
                except asyncpg.PostgresError as e:
                    failed_tables.append(table)
                    pretty_log(
                        tag="error",
                        message=f"Failed to remove user {user_id} from table '{table}': {e}",
                        include_trace=True,
                    )
            if not failed_tables:
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
