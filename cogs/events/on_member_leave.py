from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS
from utils.logs.pretty_log import pretty_log
from utils.cache.cache_list import celestial_members_cache
from utils.functions.webhook_func import send_webhook

LOG_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.server_logs


# 🍭──────────────────────────────
#   🎀 Cog: On Member Leave
# 🍭──────────────────────────────
class OnMemberLeaveCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        clan_joined_at = ""
        title = "👋 Guest Left"

        if member.id in celestial_members_cache:
            title = "👋 Clan Member Left"
            member_info = celestial_members_cache.get(member.id)
            clan_joined_at_unix_seconds = member_info.get("date_joined")
            if clan_joined_at_unix_seconds:
                clan_joined_at = f"**Joined Clan at:** <t:{clan_joined_at_unix_seconds}:f>\n"

        description = (
            f"**Member:** {member.mention}\n"
            f"{clan_joined_at}"
            f"**Joined at:** {discord.utils.format_dt(member.joined_at, style='f') if member.joined_at else 'Unknown'}"
        )
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.orange(),
            timestamp=datetime.now(),
        )
        embed.set_author(name=member.name, icon_url=member.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text=f"User ID: {member.id}", icon_url=guild.icon.url if guild.icon else None)

        if log_channel:
            await send_webhook(bot=self.bot, channel=log_channel, embed=embed)
        else:
            pretty_log(
                tag="warn",
                message=(
                    f"Server log channel (ID: {LOG_CHANNEL_ID}) not found in "
                    f"guild '{guild.name}' while handling member leave event."
                ),
                label="MemberLeave",
            )

        pretty_log(
            tag="info",
            message=(
                f"👋 Member left guild '{guild.name}': {member} (ID: {member.id})"
            ),
            label="MemberLeave",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberLeaveCog(bot))
