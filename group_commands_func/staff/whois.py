from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
)
from utils.db.personal_roles_db import fetch_personal_role_id
from utils.functions.pokemon_func import format_price_w_coin
from utils.functions.pretty_defer import pretty_defer
from utils.logs.pretty_log import pretty_log


async def whois_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    user: discord.Member | None = None,
    user_id: str | None = None,
):
    """
    Main whois logic.
    Fetches and displays information about a member or user, including personal role info if applicable.
    Works for both members and non-members.
    """
    loader = await pretty_defer(
        interaction=interaction, content="Fetching user info...", ephemeral=True
    )
    guild = interaction.guild
    celestial_guild = bot.get_guild(CELESTIAL_SERVER_ID)
    # Validate input
    if user is None and user_id is None:
        msg = "You must provide either a member or a user ID."
        await loader.error(msg)
        return

    if user_id:
        user_id = int(user_id)

    # Resolve member
    user = guild.get_member(user_id) if user_id else user
    if not user:
        await loader.error("Member not found in this server.")
        return

    personal_role_id, error_msg = await fetch_personal_role_id(bot, user_id=user.id)
    server_joined_unix = int(user.joined_at.timestamp()) if user.joined_at else None
    server_joined_ts = (
        f"<t:{server_joined_unix}:f>" if server_joined_unix else "Unknown"
    )
    account_created_unix = int(user.created_at.timestamp()) if user.created_at else None
    account_created_ts = (
        f"<t:{account_created_unix}:f>" if account_created_unix else "Unknown"
    )
    celestial_member = False
    personal_role_str = (
        f"**Personal Role:** <@&{personal_role_id}>" if personal_role_id else ""
    )

    from utils.cache.celestial_members_cache import fetch_celestial_member_cache

    user_celestial_info = fetch_celestial_member_cache(user.id)
    if user_celestial_info:
        celestial_member = True
        channel_id = user_celestial_info.get("channel_id")
        if channel_id:
            member_channel = celestial_guild.get_channel(channel_id)
        else:
            member_channel = "N/A"
        actual_perks = user_celestial_info.get("actual_perks") or "N/A"
        clan_bank_donations = user_celestial_info.get("clan_bank_donations") or 0
        clan_treasury_donations = (
            user_celestial_info.get("clan_treasury_donations") or 0
        )
        clan_bank_donations_str = (
            f"**Clan Bank Donations:** {format_price_w_coin(clan_bank_donations)}\n"
        )
        clan_treasury_donations_str = f"**Clan Treasury Donations:** {format_price_w_coin(clan_treasury_donations)}\n"
        total_donations = clan_bank_donations + clan_treasury_donations
        total_donations_str = (
            f"**Total Donations:** {format_price_w_coin(total_donations)}\n"
        )
        clan_joined_date_unix = user_celestial_info.get("date_joined")
        if clan_joined_date_unix:
            clan_joined_date = f"<t:{clan_joined_date_unix}:f>"
        else:
            clan_joined_date = "N/A"
        clan_joined_date_str = f"**Clan Joined Date:** {clan_joined_date}\n"

        desc = (
            f"**User:**{user.mention}\n"
            f"**Account Created:** {account_created_ts}\n"
            f"**Server Joined:** {server_joined_ts}\n"
            f"{personal_role_str}\n"
        )
        title = f"Community Member Info"
        if celestial_member:
            title = f"Celestial Member Info"
            desc = (
                f"**User:**{user.mention}\n"
                f"{personal_role_str}\n"
                f"**Member Channel:** {member_channel.mention if isinstance(member_channel, discord.TextChannel) else member_channel}\n"
                f"**Perks:** {actual_perks}\n"
                f"{clan_bank_donations_str}"
                f"{clan_treasury_donations_str}"
                f"{total_donations_str}"
                f"{clan_joined_date_str}"
                f"**Account Created:** {account_created_ts}\n"
                f"**Server Joined:** {server_joined_ts}\n"
            )
        color = DEFAULT_EMBED_COLOR
        if personal_role_id:
            personal_role = celestial_guild.get_role(personal_role_id)
            if personal_role and personal_role.color.value != 0:
                color = personal_role.color.value
        embed = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.now())
        embed.set_footer(
            text=f"User ID: {user.id}",
            icon_url=(
                interaction.guild.icon.url
                if interaction.guild and interaction.guild.icon
                else None
            ),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        await loader.success(embed=embed, content="")

