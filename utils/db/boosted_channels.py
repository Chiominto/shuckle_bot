import discord

from utils.logs.pretty_log import pretty_log

# Insert / upsert a channel
async def upsert_boosted_channel(
    bot, channel_id: int, channel_name: str, booster_id: int, booster_name: str
):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO boosted_channels (channel_id, channel_name, boosted_by_id, boosted_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (channel_id) DO UPDATE
            SET channel_name = EXCLUDED.channel_name,
                boosted_by_id = EXCLUDED.boosted_by_id,
                boosted_by = EXCLUDED.boosted_by
        """,
            channel_id,
            channel_name,
            booster_id,
            booster_name,
        )


async def clear_channel_boost_info(bot: discord.Client, channel_id: int):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE boosted_channels
            SET boosted_by_id = NULL, boosted_by = NULL
            WHERE channel_id = $1
        """,
            channel_id,
        )


async def get_channel_booster_id(bot: discord.Client, channel_id: int) -> int | None:
    async with bot.pg_pool.acquire() as conn:
        boosted_by_id = await conn.fetchval(
            "SELECT boosted_by_id FROM boosted_channels WHERE channel_id = $1",
            channel_id,
        )
        return boosted_by_id


async def remove_boosted_channel(bot: discord.Client, channel_id: int):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM boosted_channels WHERE channel_id = $1",
            channel_id,
        )
        pretty_log(
            "info",
            f"Removed boosted channel record for channel {channel_id}.",
            
        )


async def is_channel_boosted(bot: discord.Client, channel_id: int) -> bool:
    async with bot.pg_pool.acquire() as conn:
        boosted_by_id = await conn.fetchval(
            "SELECT boosted_by_id FROM boosted_channels WHERE channel_id = $1",
            channel_id,
        )
        pretty_log(
            "info",
            f"Checked if channel {channel_id} is boosted: {'Yes' if boosted_by_id else 'No'}.",

        )
        return boosted_by_id is not None
