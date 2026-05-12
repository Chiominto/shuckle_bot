import discord

from utils.logs.pretty_log import pretty_log

# SQL SCRIPT

"""CREATE TABLE flex_messages (
    message_id BIGINT PRIMARY KEY,
    author_id BIGINT NOT NULL,
    author_name TEXT NOT NULL
);
"""


async def upsert_flex_message(bot: discord.Client, message: discord.Message):
    """Inserts or updates a flex message in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO flex_messages (message_id, author_id, author_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (message_id) DO UPDATE
                SET author_id = EXCLUDED.author_id,
                    author_name = EXCLUDED.author_name;
                """,
                message.id,
                message.author.id,
                str(message.author),
            )
    except Exception as e:
        pretty_log("error", f"Failed to upsert flex message: {e}")


async def delete_flex_message(bot: discord.Client, message_id: int):
    """Deletes a flex message from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM flex_messages WHERE message_id = $1;",
                message_id,
            )
    except Exception as e:
        pretty_log("error", f"Failed to delete flex message: {e}")


async def check_if_its_a_flex_message(bot: discord.Client, message_id: int) -> bool:
    """Checks if a message ID exists in the flex_messages table."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT 1 FROM flex_messages WHERE message_id = $1;",
                message_id,
            )
            return result is not None
    except Exception as e:
        pretty_log("error", f"Failed to check flex message: {e}")
        return False


async def get_flex_message(bot: discord.Client, message_id: int):
    """Retrieves a flex message record from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM flex_messages WHERE message_id = $1;",
                message_id,
            )
            return result
    except Exception as e:
        pretty_log("error", f"Failed to get flex message: {e}")
        return None
