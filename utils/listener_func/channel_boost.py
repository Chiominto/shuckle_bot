import re
from datetime import datetime

import discord
from discord.ext import commands

from constants.aesthetics import Thumbnails
from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS, CELESTIAL_SERVER_ID
from utils.db.boosted_channels import (
    get_channel_booster_id,
    is_channel_boosted,
    remove_boosted_channel,
    upsert_boosted_channel,
)
from utils.db.celestial_members_db import fetch_clan_channel_id
from utils.functions.design_embed import design_embed, format_bulletin_desc
from utils.functions.pokemeow_reply import get_pokemeow_reply_member
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


async def contact_booster_to_remove_boost(
    bot: discord.Client,
    channel_id,
    context: str,
    member: discord.Member = None,
    channel_name: str = None,
):
    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    ex_member_channel_booster_id = await get_channel_booster_id(bot, channel_id)
    if not ex_member_channel_booster_id:
        pretty_log(
            "info",
            f"No booster found for channel {channel_id} during clan removal of {member.display_name}.",
        )
        return
    if ex_member_channel_booster_id == member.id:
        return  # Booster is the member themselves, no need to contact
    booster_member = guild.get_member(ex_member_channel_booster_id)
    if not booster_member:
        pretty_log(
            "info",
            f"Booster member {ex_member_channel_booster_id} not found in guild during clan removal of {member.display_name}.",
        )
        return

    if context == "clan_remove" and member:
        title = "Celestial Clan Leave Notification"
        desc = (
            f"Hello {booster_member.mention},\n\n"
            f"We wanted to inform you that {member.mention} | {member.display_name} is no longer part of the Celestial clan.\n\n"
            f"Whether you choose to keep or remove your boost on their channel is completely up to you"
        )
    elif context == "channel_delete":  # channel delete
        title = "Celestial Channel Deleted Notification"
        deleted_channel_name = channel_name if channel_name else "Deleted Channel"
        desc = (
            f"Hello {booster_member.mention},\n\n"
            f"We wanted to inform you that {deleted_channel_name} has been deleted.\n\n"
            f"We recommend you to remove your boost from this channel"
        )
    else:
        return
    embed = discord.Embed(
        title=title,
        description=desc,
    )
    value_str = f";channel remove_boost {channel_id}"
    embed.add_field(name="Channel Boost Remove Command", value=value_str, inline=False)
    embed = design_embed(
        embed=embed, thumbnail_url=member.display_avatar.url, user=booster_member
    )
    # Get booster member personal channel
    booster_member_channel_id = await fetch_clan_channel_id(bot, booster_member.id)
    if not booster_member_channel_id:
        booster_channel_id = CELESTIAL_TEXT_CHANNELS.iggly_haven  # Fallback channel
    else:
        booster_channel_id = booster_member_channel_id

    booster_member_channel = guild.get_channel(booster_channel_id)
    if not booster_member_channel:
        pretty_log(
            "info",
            f"Booster member channel {booster_channel_id} not found during clan removal of {member.display_name}.",
        )
        return

    content = (
        f"{booster_member.mention}"
        if booster_channel_id == CELESTIAL_TEXT_CHANNELS.iggly_haven
        else ""
    )
    await booster_member_channel.send(embed=embed, content=content)
    pretty_log(
        "info",
        f"Notified booster {booster_member.display_name} about clan removal of {member.display_name}.",
    )


# ─────────────────────────────────────────────
# 💫 Channel Boost Listener
# ─────────────────────────────────────────────
async def boost_channel_listener(bot: commands.Bot, message: discord.Message):
    """
    Extract the first channel ID from a message content in the format <#123456789012345678>.
    Posts an embed to the server log channel when a channel is boosted.
    Includes 3-hour cooldown per user per channel to prevent spam abuse.
    """
    try:
        content = message.content
        if not content:
            return

        guild = message.guild
        if not guild:
            pretty_log(
                "warn",
                f"Cannot process boost message {message.id}: message has no guild context.",
            )
            return

        match = re.search(r"<#(\d+)>", content)
        if not match:
            pretty_log(
                "warn",
                f"No channel mention found in boost message {message.id}.",
            )
            return

        boosted_channel_id = int(match.group(1))
        boosted_channel = guild.get_channel(boosted_channel_id)
        if not boosted_channel:
            pretty_log(
                "info",
                f"Boosted channel {boosted_channel_id} not found in guild {guild.name} ({guild.id}).",
            )
            return

        member = await get_pokemeow_reply_member(message=message)
        if not member:
            return
        # Check if channel is already boosted
        if await is_channel_boosted(bot=bot, channel_id=boosted_channel_id):
            pretty_log(
                "info",
                f"Channel {boosted_channel_id} is already boosted. No action taken (Message ID {message.id}).",
            )
            return
        # Upsert boosted channel record
        await upsert_boosted_channel(
            bot=bot,
            channel_id=boosted_channel_id,
            channel_name=boosted_channel.name,
            booster_id=member.id,
            booster_name=member.name,
        )
        pretty_log(
            "info",
            f"Channel {boosted_channel_id} marked as boosted by {member} ({member.id}).",
        )

        # Check if the boosted channel is their registered personal channel
        registered_channel_id = await fetch_clan_channel_id(bot=bot, user_id=member.id)
        if registered_channel_id == boosted_channel_id:
            pretty_log(
                "info",
                f"User {member} ({member.id}) boosted their own registered personal channel {boosted_channel_id}. No reward given.",
            )
            return

        server_log = guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)
        if not server_log:
            pretty_log(
                "warn",
                f"Server log channel not found in guild {guild.name} ({guild.id}).",
            )
            return

        desc = format_bulletin_desc(
            "Channel", f"<#{boosted_channel_id}>", "Boosted By", member.mention
        )

        embed = discord.Embed(title="💫 Channel Boosted", description=desc)

        footer_text = "💫 Newly Boosted Channel"
        embed = design_embed(
            user=member,
            embed=embed,
            thumbnail_url=Thumbnails.BLUE_SPARKLE,
            footer_text=footer_text,
        )

        await send_webhook(
            bot=bot,
            channel=server_log,
            embed=embed,
        )

        pretty_log(
            "success",
            f"Logged boosted channel: {boosted_channel.name} ({boosted_channel_id}) boosted by {member} (Message ID {message.id}).",
        )

        return

    except Exception as e:
        pretty_log(
            "critical",
            f"Unexpected error in boost_channel_listener (Message ID {getattr(message, 'id', 'unknown')}): {e}",
        )
        return


# ─────────────────────────────────────────────
# 💠 Remove Boosted Channel Listener
# ─────────────────────────────────────────────
async def remove_boosted_channel_listener(bot, message: discord.Message):
    try:
        content = message.content
        if not content:
            return

        guild = message.guild
        if not guild:
            pretty_log(
                "warn",
                f"Cannot process unboost message {message.id}: message has no guild context.",
            )
            return

        match = re.search(r"<#(\d+)>", content)
        if not match:
            pretty_log(
                "warn", f"No channel mention found in unboost message {message.id}."
            )
            return

        unboosted_channel_id = int(match.group(1))
        member = await get_pokemeow_reply_member(message=message)
        if not member:
            return

        # Keep the cooldown active when someone unboosts to prevent immediate re-boost abuse
        # This means they can't boost again for rewards until the 3-hour cooldown expires

        unboosted_channel = guild.get_channel(unboosted_channel_id)
        if not unboosted_channel:
            pretty_log(
                "warn",
                f"Unboosted channel {unboosted_channel_id} not found in guild {guild.name} ({guild.id}).",
            )
            return
        server_log = guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)
        if not server_log:
            pretty_log(
                "warn",
                f"Server log channel not found in guild {guild.name} ({guild.id}) during unboost logging.",
            )
            return

        unboosted_channel_name = unboosted_channel.name
        # Get booster ID
        booster_id = await get_channel_booster_id(
            bot=bot, channel_id=unboosted_channel_id
        )
        if not booster_id:
            pretty_log(
                "info",
                f"No booster ID found for channel {unboosted_channel_id} when attempting to remove boost (Message ID {message.id}).",
            )
            return

        # Remove the boosted channel record
        if booster_id == member.id:
            await remove_boosted_channel(bot, channel_id=unboosted_channel_id)
            desc = format_bulletin_desc("Channel", f"<#{unboosted_channel_id}>")
            embed = discord.Embed(
                title="😢 Unboosted Channel",
                description=desc,
                color=discord.Color.red(),
                timestamp=datetime.now(),
            )

            footer_text = "😢 Unboosted Channel"
            guild_icon_url = guild.icon.url if guild.icon else None
            if guild_icon_url:
                embed.set_thumbnail(url=guild_icon_url)
            embed.set_footer(text=footer_text, icon_url=guild_icon_url)

            await send_webhook(
                bot=bot,
                channel=server_log,
                embed=embed,
            )
            pretty_log(
                "ready",
                f"Logged Removed boosted channel: {unboosted_channel_name} ({unboosted_channel_id}), "
                f"boost removed by {member.display_name} (Message ID {message.id}).",
            )
        else:
            pretty_log(
                "info",
                f"User {member} ({member.id}) attempted to remove boost for channel {unboosted_channel_id} but is not the booster (Booster ID: {booster_id}). No action taken (Message ID {message.id}).",
            )
            return

    except Exception as e:
        pretty_log(
            "critical",
            f"Unexpected error in remove_boosted_channel_listener "
            f"(Message ID {getattr(message, 'id', 'unknown')}): {e}",
        )
