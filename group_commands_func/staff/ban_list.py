from typing import List, Optional

import discord
from discord.ext import commands
from discord.ui import Button, View
import discord
from discord.ext import commands

from utils.db.banned_members_db import upsert_banned_member, fetch_all_banned_members
from utils.logs.pretty_log import pretty_log
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log

# -------------------- Sync Guild Bans --------------------
async def sync_guild_bans_to_db(bot: discord.Client, guild: discord.Guild):
    """
    Fetches all banned members from a guild and inserts them into the banned_users table.
    Skips deleted users.
    """
    try:
        async for ban_entry in guild.bans():
            user = ban_entry.user
            if user.name.startswith("Deleted User") or user.bot:
                continue  # skip deleted users or bots if desired

            reason = ban_entry.reason
            await upsert_banned_member(bot, user_id=user.id, user_name=user.name, reason=reason)
            pretty_log(
                "info",
                f"Synchronized ban for user {user} (ID: {user.id}) in guild '{guild.name}' to database",
            )

    except discord.Forbidden:
        pretty_log(
            "error",
            f"Bot doesn't have permission to fetch bans in {guild.name}",

        )
    except discord.HTTPException as e:
        pretty_log(
            "error",
            f"Failed to fetch bans for {guild.name}: {e}",

        )


# -------------------- Chunk List --------------------
def chunk_list(data: List[dict], chunk_size: int) -> List[List[dict]]:
    """Splits a list into smaller chunks."""
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


# -------------------- Paginated View --------------------
class BannedUsersPaginator(View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0
        self.total_pages = len(embeds)
        self.message: discord.Message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PageNavButton("⬅️", self, -1))
        if self.current_page < self.total_pages - 1:
            self.add_item(PageNavButton("➡️", self, 1))

    async def send_page(self):
        """Edit the message with the current embed and update buttons."""
        try:
            embed = self.embeds[self.current_page]

            # Footer with page info
            footer_text = f"Page {self.current_page + 1}/{self.total_pages}"
            if embed.footer.text:
                embed.set_footer(
                    text=f"{embed.footer.text.split('•')[0].strip()} • {footer_text}"
                )
            else:
                embed.set_footer(text=footer_text)

            self.update_buttons()
            if self.message:
                await self.message.edit(embed=embed, view=self)
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to update banned users embed: {e}",

            )


# -------------------- Page Navigation Button --------------------
class PageNavButton(discord.ui.Button):
    def __init__(self, emoji: str, paginator: BannedUsersPaginator, direction: int):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
        self.paginator = paginator
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        # Only allow the original user to interact (optional)
        # if interaction.user.id != self.paginator.message.interaction.user.id:
        #     return await interaction.response.send_message("This menu isn't for you!", ephemeral=True)

        await interaction.response.defer()
        self.paginator.current_page += self.direction
        await self.paginator.send_page()


# -------------------- View Bans Command --------------------
async def ban_list_func(bot: commands.Bot, interaction: discord.Interaction):
    loader = await pretty_defer(
        interaction=interaction, content="Fetching banned members...", ephemeral=False
    )

    banned_users = await fetch_all_banned_members
    if not banned_users:
        await interaction.edit_original_response(
            "✅ No banned users found in this server."
        )
        return

    pages = chunk_list(banned_users, 10)
    embeds = []

    for page_num, users_chunk in enumerate(pages, start=1):
        embed = discord.Embed(
            title=f"🚫 Banned Users in {interaction.guild.name}",
            color=0xE74C3C,
            timestamp=discord.utils.utcnow(),
        )
        start_index = (page_num - 1) * 10
        for i, user in enumerate(users_chunk, start=1):
            field_lines = []
            if user.get("reason"):
                field_lines.append(f"Reason: {user['reason']}")
            embed.add_field(
                name=f"{start_index + i}. {user['user_name']} ({user['user_id']})",
                value="\n".join(field_lines) if field_lines else "—",
                inline=False,
            )
        embed.set_footer(
            text=f"Total Banned Members: {len(banned_users)} • Page {page_num}/{len(pages)}"
        )
        embeds.append(embed)

    paginator = BannedUsersPaginator(embeds)
    message = await loader.success(embed=embeds[0], content="")
    paginator.message = message  # Set the message reference for the paginator
