from datetime import datetime

import discord

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS
from utils.db.celestial_members_db import fetch_clan_channel_id
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


async def auto_channel_rename(
    bot: discord.Client, new_name: str, member: discord.Member
):
    """Automatically renames a clan channel based on the member's new username."""
    try:
        # Fetch the clan channel ID from the database
        clan_channel_id = await fetch_clan_channel_id(bot, member.id)
        if not clan_channel_id:
            pretty_log(
                "warn",
                f"No clan channel found for user {member.display_name} ({member.id}).",
                label="Auto Channel Rename",
            )
            return

        # Fetch the channel object
        clan_channel = bot.get_channel(clan_channel_id)
        if not clan_channel or not isinstance(clan_channel, discord.TextChannel):
            pretty_log(
                "warn",
                f"Clan channel with ID {clan_channel_id} not found or is not a text channel.",
                label="Auto Channel Rename",
            )
            return
        # Fetch old channel name before renaming
        old_name = clan_channel.name
        # Extract just the username part and preserve the emoji prefix for the rename.
        # Supports both "🌌・name" (katakana middle dot) and "🌌 · name" (spaced middle dot).
        if "・" in old_name:
            prefix, _ = old_name.split("・", 1)
            full_new_name = f"{prefix}・{new_name}"
        elif " · " in old_name:
            prefix, _ = old_name.split(" · ", 1)
            full_new_name = f"{prefix} · {new_name}"
        else:
            full_new_name = new_name

        # Rename the channel
        await clan_channel.edit(name=full_new_name)
        pretty_log(
            "info",
            f"Renamed clan channel {clan_channel.name} ({clan_channel.id}) to '{full_new_name}' for user {member.display_name} ({member.id}).",
            label="Auto Channel Rename",
        )
        desc = (
            f"**Member:** {member.mention}\n"
            f"**Channel:** {clan_channel.mention}\n"
            f"**Old Channel Name:** {old_name}\n"
            f"**New Channel Name:** {full_new_name}"
        )
        # Send success webhook log
        embed = discord.Embed(
            title="Clan Channel Renamed",
            description=desc,
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )
        embed.set_author(
            name=member.display_name,
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(
            url=member.display_avatar.url if member.display_avatar else None
        )
        embed.set_footer(
            text=f"Channel ID: {clan_channel.id}",
            icon_url=(
                member.guild.icon.url if member.guild and member.guild.icon else None
            ),
        )
        log_channel = member.guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)
        if log_channel:
            await send_webhook(bot=bot, channel=log_channel, embed=embed)
        else:
            pretty_log(
                "warn",
                f"Server log channel not found in guild '{member.guild.name}'",
                label="Auto Channel Rename",
            )

    except Exception as e:
        pretty_log(
            "error",
            f"Error renaming clan channel for user {member.display_name} ({member.id}): {e}",
            label="Auto Channel Rename",
        )
