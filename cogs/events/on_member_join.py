from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS, DEFAULT_EMBED_COLOR
from utils.cache.cache_list import celestial_members_cache
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log

LOG_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.server_logs


# 🍭──────────────────────────────
#   🎀 Cog: On Member Join
# 🍭──────────────────────────────
class OnMemberJoinCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        guild = member.guild
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        title = "✨ New Member Joined"

        account_created_at = discord.utils.format_dt(member.created_at, style="f")
        content = f"Welcome {member.mention}! We are pleased to have you join us on this journey with Celestial."
        description = """- Please wait for an Owner or Co‑Owner to situate you in the clan.
- While waiting, visit <#1490470353099817030> to get familiar with our guidelines.
- If you have any questions, feel free to ask our helpers."""
        log_description = (
            f"**Member:** {member.mention}\n"
            f"**Account Created:** {account_created_at}\n"
            f"**Member Count:** {guild.member_count}"
        )

        embed = discord.Embed(
            title=title,
            description=description,
            color=DEFAULT_EMBED_COLOR,
            timestamp=datetime.now(),
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"User ID: {member.id}",
            icon_url=guild.icon.url if guild.icon else None,
        )

        general_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.general)
        if general_channel:
            await general_channel.send(content=content, embed=embed)
        log_embed = discord.Embed(
            title=title,
            description=log_description,
            color=DEFAULT_EMBED_COLOR,
            timestamp=datetime.now(),
        )
        log_embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        log_embed.set_thumbnail(url=member.display_avatar.url)
        log_embed.set_footer(
            text=f"User ID: {member.id}",
            icon_url=guild.icon.url if guild.icon else None,
        )
        if log_channel:
            await send_webhook(bot=self.bot, channel=log_channel, embed=log_embed)
        else:
            pretty_log(
                tag="warn",
                message=(
                    f"Server log channel (ID: {LOG_CHANNEL_ID}) not found in "
                    f"guild '{guild.name}' while handling member join event."
                ),
                label="MemberJoin",
            )

        pretty_log(
            tag="info",
            message=(
                f"✨ Member joined guild '{guild.name}': {member} (ID: {member.id})"
            ),
            label="MemberJoin",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberJoinCog(bot))
