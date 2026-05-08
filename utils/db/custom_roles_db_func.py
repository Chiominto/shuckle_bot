import discord

from utils.logs.pretty_log import pretty_log

# SQL Script to create the custom_roles table
"""CREATE TABLE custom_roles (
    user_id   BIGINT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    role_id   BIGINT NOT NULL
);"""


# Fetch one custom role entry for a user
async def fetch_user_role(bot, user: discord.Member):
    """
    Fetch a single custom_roles row for a user.
    Returns None if not found.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM custom_roles
            WHERE user_id = $1;
            """,
            user_id,
        )

# Check if role id is in database
async def is_custom_role(bot, role_id: int):
    """
    Check if a role_id exists in custom_roles.
    Returns True if exists, False otherwise.
    """
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 1 FROM custom_roles
            WHERE role_id = $1;
            """,
            role_id,
        )
        return row is not None

# Fetch all custom roles
async def fetch_all_roles(bot):
    """
    Fetch all custom_roles rows.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT * FROM custom_roles;
            """
        )
async def fetch_all_user_ids_with_roles(bot):
    """
    Fetch all user_ids from custom_roles.
    """
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id FROM custom_roles;
            """
        )
        return [row["user_id"] for row in rows]

# Update role_id for a user
async def update_role(bot, user: discord.Member, role_id: int):
    """
    Update the role_id for a user in custom_roles.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE custom_roles
            SET role_id = $1
            WHERE user_id = $2;
            """,
            role_id,
            user_id,
        )


# Upsert custom role (insert or update)
async def upsert_role(bot, user: discord.Member, role_id: int):
    """
    Insert or update a custom_roles row for a user.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO custom_roles (user_id, user_name, role_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET user_name = $2, role_id = $3;
            """,
            user_id,
            user_name,
            role_id,
        )


# Add custom role (insert new row)
async def add_role(bot, user: discord.Member, role_id: int):
    """
    Add a new custom_roles row for a user.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO custom_roles (user_id, user_name, role_id)
            VALUES ($1, $2, $3);
            """,
            user_id,
            user_name,
            role_id,
        )


# Remove custom role (delete row)
async def remove_role(bot, user: discord.Member):
    """
    Remove a custom_roles row for a user.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM custom_roles
            WHERE user_id = $1;
            """,
            user_id,
        )
async def remove_role_by_user_id(bot, user_id: int):
    """
    Remove a custom_roles row for a user by user_id.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM custom_roles
            WHERE user_id = $1;
            """,
            user_id,
        )

# Remove custom role by role_id
async def remove_role_by_role_id(bot, role_id: int):
    """
    Remove a custom_roles row by role_id.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM custom_roles
            WHERE role_id = $1;
            """,
            role_id,
        )


# Reset custom roles (clear table)
async def reset_roles(bot):
    """
    Delete all rows from custom_roles table.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            TRUNCATE TABLE custom_roles;
            """
        )


# Get custom role by role_id
async def get_role_by_id(bot, role_id: int):
    """
    Get the user with the given role_id.
    Returns None if not found.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM custom_roles
            WHERE role_id = $1;
            """,
            role_id,
        )


# Fetch custom role_id for a user
async def fetch_custom_role_id(bot, user: discord.Member):
    """
    Fetch the custom role_id for a user.
    Returns None if not found.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT role_id FROM custom_roles
            WHERE user_id = $1;
            """,
            user_id,
        )
        return row["role_id"] if row else None

async def fetch_custom_role_id_by_user_id(bot, user_id: int):
    """
    Fetch the custom role_id for a user by user_id.
    Returns None if not found.
    """
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT role_id FROM custom_roles
            WHERE user_id = $1;
            """,
            user_id,
        )
        return row["role_id"] if row else None

# 🌸────────────────────────────────────────────
#         ✨ Helper: Update Gradient Role ✨
# 🌸────────────────────────────────────────────
async def update_gradient_role(
    bot,
    guild_id: int,
    role_id: int,
    primarycolor: str,
    secondarycolor: str,
    name: str = None,
):
    payload = {
        "colors": {
            "primary_color": int(primarycolor.lstrip("#"), 16),
            "secondary_color": int(secondarycolor.lstrip("#"), 16),
            "tertiary_color": None,
        }
    }
    if name:
        payload["name"] = name

    url = f"/guilds/{guild_id}/roles/{role_id}"

    try:
        await bot.http.request(discord.http.Route("PATCH", url), json=payload)
        return True
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update gradient role: {e}",
        )
        return False
