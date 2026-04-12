import discord
from discord.ext import commands

from utils.db.banned_members_db import delete_banned_member
from utils.logs.pretty_log import pretty_log


# 🟣────────────────────────────────────────────
#         🐢 Guild Unban Listener Cog
# 🟣────────────────────────────────────────────
class GuildUnbanListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_unban(self, guild: discord.Guild, user: discord.User):
        # Remove from banned members DB
        await delete_banned_member(bot=self.bot, user_id=user.id)

        # Log the unban event
        msg = f"User {user} (ID: {user.id}) was unbanned from guild '{guild.name}' (ID: {guild.id})"
        pretty_log(
            tag="success",
            message=msg,
            label="GuildUnban",
            bot=self.bot,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildUnbanListener(bot))
