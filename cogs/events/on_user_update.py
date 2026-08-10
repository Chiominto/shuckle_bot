from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
)
from utils.cache.cache_list import celestial_members_cache
from utils.db.general_db import update_username_in_dbs
from utils.functions.channel_rename import auto_channel_rename
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


# 🟣────────────────────────────────────────────
#         🐢 Username Update Listener Cog
# 🟣────────────────────────────────────────────
class OnUserUpdateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #         🐢 User Update Event (Global Username)
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):

        # ————————————————————————————————
        # 🏷️ Username Change Check
        # ————————————————————————————————
        if before.name == after.name:
            return

        try:
            guild = self.bot.get_guild(CELESTIAL_SERVER_ID)
            if not guild:
                return
            member = guild.get_member(after.id)
            if not member:
                return
            log_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)
            if not log_channel:
                pretty_log(
                    tag="warn",
                    message=f"Server log channel not found in guild '{guild.name}'",
                    label="UsernameUpdate",
                )
                return
            title = "✏️ Guest Username Changed"
            note = ""
            clan_member = False
            if member.id in celestial_members_cache:
                title = "✏️ Clan Member Username Changed"
                note = "Kindly tell member to do `;username` to update their username in Pokemeow too."
                clan_member = True

            embed = discord.Embed(
                title=title, color=DEFAULT_EMBED_COLOR, description=note
            )
            embed.set_author(
                name=str(after),
                icon_url=after.display_avatar.url,
            )
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            embed.timestamp = datetime.now()
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(
                text=f"User ID: {after.id}",
                icon_url=guild.icon.url if guild.icon else None,
            )

            await send_webhook(self.bot, log_channel, embed=embed)
            if clan_member:
                await update_username_in_dbs(self.bot, after.id, after.name)
                celestial_members_cache[after.id]["user_name"] = after.name
                await auto_channel_rename(self.bot, after.name, member)

            pretty_log(
                tag="info",
                message=f"Username changed for {after} (ID: {after.id}): '{before.name}' → '{after.name}'",
                label="UsernameUpdate",
            )
        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Failed to log username change: {e}",
                label="UsernameUpdate",
            )


# 🟣────────────────────────────────────────────
#         🐢 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(OnUserUpdateCog(bot))
