import json
import re

import asyncpg
import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    HANA_USER_ID
)
from utils.cache.cache_list import celestial_members_cache
from utils.cache.celestial_members_cache import load_celestial_members_cache
from utils.db.general_db import TABLE_NAMES
from utils.logs.pretty_log import pretty_log

# Add authorized Discord user IDs here to enable !db_cleanup.
MANUAL_CLEANUP_USER_IDS: set[int] = set([HANA_USER_ID])
PAGE_SIZE = 15
DELETE_BATCH_SIZE = 500


async def setup_member_cleanup(bot: discord.Client):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS member_cleanup_reviews (
                id BIGSERIAL PRIMARY KEY,
                message_id BIGINT,
                candidates JSONB NOT NULL,
                tables TEXT[] NOT NULL,
                skipped TEXT[] NOT NULL,
                page INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        reviews = await conn.fetch(
            "SELECT id, message_id FROM member_cleanup_reviews "
            "WHERE status = 'pending' AND message_id IS NOT NULL"
        )
    for review in reviews:
        bot.add_view(CleanupReview(bot, review["id"]), message_id=review["message_id"])


async def _member_ids(guild: discord.Guild) -> set[int]:
    members = {member.id async for member in guild.fetch_members(limit=None)}
    if not members:
        raise RuntimeError("The server member list was empty; cleanup was stopped.")
    return members


def _table_name(table: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", table):
        raise ValueError(f"Invalid table name in TABLE_NAMES: {table!r}")
    return f'"{table}"'


async def _build_preview(bot: discord.Client, member_ids: set[int]):
    candidates: dict[str, str] = {}
    tables = []
    skipped = []
    async with bot.pg_pool.acquire() as conn:
        for table in dict.fromkeys(TABLE_NAMES):
            name = _table_name(table)
            columns = await conn.fetch(
                """
                SELECT attname FROM pg_attribute
                WHERE attrelid = to_regclass($1) AND attnum > 0 AND NOT attisdropped
                """,
                table,
            )
            column_names = {row["attname"] for row in columns}
            if "user_id" not in column_names:
                skipped.append(table)
                continue
            tables.append(table)
            name_column = "user_name" if "user_name" in column_names else "NULL AS user_name"
            rows = await conn.fetch(
                f"SELECT DISTINCT user_id, {name_column} FROM {name} WHERE user_id IS NOT NULL"
            )
            for row in rows:
                user_id = row["user_id"]
                if not isinstance(user_id, int):
                    raise ValueError(f"Non-integer user_id in table {table!r}.")
                if user_id not in member_ids:
                    key = str(user_id)
                    username = row["user_name"]
                    if key not in candidates or (not candidates[key] and username):
                        candidates[key] = str(username) if username else ""
    if not tables:
        raise RuntimeError("No listed database tables with a user_id column were found.")
    return candidates, tables, skipped


def _review_embed(review) -> discord.Embed:
    candidates = json.loads(review["candidates"])
    entries = sorted(candidates.items(), key=lambda item: int(item[0]))
    pages = max(1, (len(entries) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(review["page"], pages - 1)
    lines = []
    for user_id, name in entries[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        safe_name = discord.utils.escape_mentions(
            discord.utils.escape_markdown(name[:100].replace("\n", " "))
        )
        lines.append(f"`{user_id}` — {safe_name or 'Unknown name'}")
    embed = discord.Embed(
        title="Database cleanup review",
        description=(
            "Owner: review the list, use **Remove** to exclude a username or ID, "
            "then choose **Continue** or **Cancel**.\n\n"
            + ("\n".join(lines) or "No stale user IDs found.")
        ),
        color=discord.Color.orange(),
    )
    embed.add_field(name="Candidates", value=str(len(entries)))
    embed.add_field(name="Page", value=f"{page + 1}/{pages}")
    if review["skipped"]:
        embed.add_field(
            name="Skipped tables (missing table or user_id)",
            value=", ".join(review["skipped"])[:1024],
            inline=False,
        )
    embed.set_footer(text="Continue permanently deletes rows without a backup.")
    return embed


async def _clear_missing_pending_reviews(bot: discord.Client, channel: discord.TextChannel):
    async with bot.pg_pool.acquire() as conn:
        reviews = await conn.fetch(
            "SELECT id, message_id FROM member_cleanup_reviews WHERE status = 'pending'"
        )

    active_review_ids = []
    for review in reviews:
        message_id = review["message_id"]
        if message_id is not None:
            try:
                await channel.fetch_message(message_id)
            except discord.NotFound:
                pass
            else:
                active_review_ids.append(review["id"])
                continue

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE member_cleanup_reviews
                SET status = 'cancelled', candidates = '{}'::jsonb
                WHERE id = $1 AND status = 'pending'
                """,
                review["id"],
            )
        pretty_log(
            "warn",
            f"Cancelled cleanup review {review['id']} because its preview message is missing.",
        )

    if active_review_ids:
        raise RuntimeError(
            f"Cleanup review {active_review_ids[0]} is still active. "
            "Use its Cancel button before starting another preview."
        )


async def create_member_cleanup_preview(bot: discord.Client):
    await bot.wait_until_ready()
    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if guild is None:
        raise RuntimeError("Celestial server is unavailable; cleanup preview was not created.")
    channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.commands)
    if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Commands channel is unavailable; cleanup preview was not created.")
    await _clear_missing_pending_reviews(bot, channel)
    member_ids = await _member_ids(guild)
    candidates, tables, skipped = await _build_preview(bot, member_ids)
    async with bot.pg_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT pg_advisory_xact_lock($1)", CELESTIAL_SERVER_ID)
            pending = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM member_cleanup_reviews WHERE status = 'pending')"
            )
            if pending:
                raise RuntimeError(
                    "A cleanup review is already pending. Use its Cancel button first."
                )
            review = await conn.fetchrow(
                """
                INSERT INTO member_cleanup_reviews (candidates, tables, skipped)
                VALUES ($1::jsonb, $2::text[], $3::text[])
                RETURNING *
                """,
                json.dumps(candidates),
                tables,
                skipped,
            )
            view = CleanupReview(bot, review["id"])
            owner_role = guild.get_role(CELESTIAL_ROLES.clan_owner_)
            if owner_role is None:
                raise RuntimeError("Clan owner role is unavailable; cleanup review was not sent.")
            message = await channel.send(
                content=owner_role.mention,
                embed=_review_embed(review),
                view=view,
                allowed_mentions=discord.AllowedMentions(roles=[owner_role]),
            )
            await conn.execute(
                "UPDATE member_cleanup_reviews SET message_id = $1 WHERE id = $2",
                message.id,
                review["id"],
            )


class RemoveCandidateModal(discord.ui.Modal, title="Remove from cleanup list"):
    candidate = discord.ui.TextInput(label="Username or user ID", max_length=100)

    def __init__(self, view: "CleanupReview"):
        super().__init__()
        self.review_view = view

    async def on_submit(self, interaction: discord.Interaction):
        if not await self.review_view.interaction_check(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        query = self.candidate.value.strip().casefold()
        async with self.review_view.bot.pg_pool.acquire() as conn:
            async with conn.transaction():
                review = await conn.fetchrow(
                    "SELECT * FROM member_cleanup_reviews WHERE id = $1 FOR UPDATE",
                    self.review_view.review_id,
                )
                if not review or review["status"] != "pending":
                    await interaction.followup.send("This review is no longer active.", ephemeral=True)
                    return
                candidates = json.loads(review["candidates"])
                matches = [
                    user_id for user_id, name in candidates.items()
                    if user_id == query or (name and name.casefold() == query)
                ]
                if len(matches) != 1:
                    await interaction.followup.send(
                        "No unique match. Use the user ID shown in the preview.", ephemeral=True
                    )
                    return
                del candidates[matches[0]]
                review = await conn.fetchrow(
                    """
                    UPDATE member_cleanup_reviews SET candidates = $1::jsonb
                    WHERE id = $2 RETURNING *
                    """,
                    json.dumps(candidates),
                    self.review_view.review_id,
                )
        await interaction.message.edit(embed=_review_embed(review), view=self.review_view)
        await interaction.followup.send("Removed from this cleanup list.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await _report_review_error(interaction, error)


async def _report_review_error(interaction: discord.Interaction, error: Exception):
    pretty_log("error", f"Cleanup review failed: {error}", include_trace=True)
    if interaction.response.is_done():
        await interaction.followup.send("Cleanup review failed; check the bot logs.", ephemeral=True)
    else:
        await interaction.response.send_message(
            "Cleanup review failed; check the bot logs.", ephemeral=True
        )


class CleanupReview(discord.ui.View):
    def __init__(self, bot: discord.Client, review_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.review_id = review_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        authorized = (
            interaction.guild_id == CELESTIAL_SERVER_ID
            and isinstance(interaction.user, discord.Member)
            and any(role.id == CELESTIAL_ROLES.clan_owner_ for role in interaction.user.roles)
        )
        if not authorized:
            await interaction.response.send_message(
                "Only a clan owner can review this cleanup.", ephemeral=True
            )
        return authorized

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item
    ):
        await _report_review_error(interaction, error)

    async def _change_page(self, interaction: discord.Interaction, delta: int):
        async with self.bot.pg_pool.acquire() as conn:
            review = await conn.fetchrow(
                """
                UPDATE member_cleanup_reviews
                SET page = LEAST(
                    GREATEST(0, page + $1),
                    GREATEST(0, (SELECT count(*) FROM jsonb_object_keys(candidates)) - 1) / 15
                )
                WHERE id = $2 AND status = 'pending' RETURNING *
                """,
                delta,
                self.review_id,
            )
        if not review:
            await interaction.response.send_message("This review is no longer active.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=_review_embed(review), view=self)

    @discord.ui.button(label="Previous", custom_id="cleanup:previous")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._change_page(interaction, -1)

    @discord.ui.button(label="Next", custom_id="cleanup:next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._change_page(interaction, 1)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.secondary, custom_id="cleanup:remove")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveCandidateModal(self))

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.danger, custom_id="cleanup:continue")
    async def proceed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            guild = self.bot.get_guild(CELESTIAL_SERVER_ID)
            if guild is None:
                raise RuntimeError("Celestial server is unavailable.")
            current_members = await _member_ids(guild)
            async with self.bot.pg_pool.acquire() as conn:
                async with conn.transaction():
                    review = await conn.fetchrow(
                        "SELECT * FROM member_cleanup_reviews WHERE id = $1 FOR UPDATE",
                        self.review_id,
                    )
                    if not review or review["status"] != "pending":
                        await interaction.followup.send("This review is no longer active.", ephemeral=True)
                        return
                    candidate_ids = {
                        int(user_id) for user_id in json.loads(review["candidates"])
                    }
                    stale_ids = sorted(candidate_ids - current_members)
                    for table in review["tables"]:
                        for offset in range(0, len(stale_ids), DELETE_BATCH_SIZE):
                            await conn.execute(
                                f"DELETE FROM {_table_name(table)} WHERE user_id = ANY($1::bigint[])",
                                stale_ids[offset : offset + DELETE_BATCH_SIZE],
                            )
                    await conn.execute(
                        "UPDATE member_cleanup_reviews "
                        "SET status = 'completed', candidates = '{}'::jsonb WHERE id = $1",
                        self.review_id,
                    )
        except (asyncpg.PostgresError, discord.HTTPException, RuntimeError, ValueError) as e:
            pretty_log("error", f"Database cleanup failed: {e}", include_trace=True)
            await interaction.followup.send(
                f"Cleanup failed; no deletion was committed. Check the bot logs: {e}",
                ephemeral=True,
            )
            return

        for user_id in stale_ids:
            celestial_members_cache.pop(user_id, None)
        try:
            cache_refreshed = await load_celestial_members_cache(self.bot)
        except (asyncpg.PostgresError, RuntimeError) as e:
            pretty_log("error", f"Cleanup completed but cache refresh failed: {e}", include_trace=True)
            cache_refreshed = False
        result = f"Cleanup completed for {len(stale_ids)} user IDs."
        if not cache_refreshed:
            result += " Celestial member cache refresh failed; check the logs."
        self.stop()
        try:
            await interaction.message.edit(content=result, view=None)
        except discord.HTTPException as e:
            pretty_log("error", f"Cleanup completed but review update failed: {e}", include_trace=True)
        await interaction.followup.send(result, ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cleanup:cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE member_cleanup_reviews SET status = 'cancelled', candidates = '{}'::jsonb "
                "WHERE id = $1 AND status = 'pending'",
                self.review_id,
            )
        if result == "UPDATE 0":
            await interaction.response.send_message("This review is no longer active.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(content="Cleanup cancelled; no rows deleted.", view=None)


async def scheduled_member_cleanup_preview(bot: discord.Client):
    try:
        await create_member_cleanup_preview(bot)
    except (asyncpg.PostgresError, discord.HTTPException, RuntimeError, ValueError) as e:
        pretty_log("error", f"Monthly database cleanup preview failed: {e}", include_trace=True)