import discord
from discord.ext import commands

from utils.logs.pretty_log import pretty_log
from utils.db.banned_members_db import upsert_banned_member


# 🟣────────────────────────────────────────────
#         🐢 Guild Ban Listener Cog
# 🟣────────────────────────────────────────────
class GuildBanListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_ban(self, guild: discord.Guild, user: discord.User):
        # Try to fetch the ban reason
        reason = None
        try:
            ban_entry = await guild.fetch_ban(user)
            reason = ban_entry.reason
        except Exception as e:
            reason = None

        # Log the ban event with reason if available
        msg = f"User {user} (ID: {user.id}) was banned from guild '{guild.name}' (ID: {guild.id})"
        if reason:
            msg += f" | Reason: {reason}"
        else:
            msg += " | Reason: Not provided"
        await upsert_banned_member(bot=self.bot, user_id=user.id, user_name=user.name, reason=reason)
        pretty_log(
            tag="info",
            message=msg,
            label="GuildBan",
            bot=self.bot,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildBanListener(bot))
