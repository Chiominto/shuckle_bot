import discord
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
)
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log

LOG_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.server_logs
RULES_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.rules


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
        info_divider = guild.get_role(CELESTIAL_ROLES.info_divider) if guild else None
        ping_divider = guild.get_role(CELESTIAL_ROLES.ping_divider) if guild else None
        # Add the roles to the member
        roles_to_add = [
            role for role in (info_divider, ping_divider) if role is not None
        ]
        if roles_to_add:
            try:
                await member.add_roles(
                    *roles_to_add,
                    reason="Assigning default divider roles on member join",
                )
                pretty_log(
                    tag="info",
                    message=(
                        f"Assigned default divider roles to new member {member} "
                        f"in guild '{guild.name}' (ID: {guild.id})"
                    ),
                    label="MemberJoin",
                )
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=(
                        f"Failed to assign default divider roles to new member {member} "
                        f"in guild '{guild.name}' (ID: {guild.id}). Error: {e}"
                    ),
                    label="MemberJoin",
                )
        title = "✨ New Member Joined"

        account_created_at = discord.utils.format_dt(member.created_at, style="f")
        content = f"Welcome {member.mention}! We are pleased to have you join us on this journey with Celestial."
        description = (
            "- Please wait for an Owner or Co‑Owner to situate you in the clan.\n"
            f"- While waiting, visit <#{RULES_CHANNEL_ID}> to get familiar with our guidelines.\n"
            "- If you have any questions, feel free to ask our helpers."
        )
        log_description = (
            f"**Member:** {member.mention}\n"
            f"**Account Created:** {account_created_at}\n"
            f"**Member Count:** {guild.member_count}"
        )

        embed = discord.Embed(
            title=title,
            description=description,
            color=DEFAULT_EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"User ID: {member.id}",
            icon_url=guild.icon.url if guild.icon else None,
        )

        general_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.general)
        if general_channel:
            try:
                await general_channel.send(content=content, embed=embed)
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=(
                        f"Failed to send welcome message for {member} "
                        f"in guild '{guild.name}' (ID: {guild.id}). Error: {e}"
                    ),
                    label="MemberJoin",
                )
        else:
            pretty_log(
                tag="warn",
                message=(
                    f"General channel (ID: {CELESTIAL_TEXT_CHANNELS.general}) not found in "
                    f"guild '{guild.name}' while handling member join event."
                ),
                label="MemberJoin",
            )
        log_embed = discord.Embed(
            title=title,
            description=log_description,
            color=DEFAULT_EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        log_embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        log_embed.set_thumbnail(url=member.display_avatar.url)
        log_embed.set_footer(
            text=f"User ID: {member.id}",
            icon_url=guild.icon.url if guild.icon else None,
        )
        if log_channel:
            try:
                await send_webhook(bot=self.bot, channel=log_channel, embed=log_embed)
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=(
                        f"Failed to send member join log webhook for {member} "
                        f"in guild '{guild.name}' (ID: {guild.id}). Error: {e}"
                    ),
                    label="MemberJoin",
                )
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
