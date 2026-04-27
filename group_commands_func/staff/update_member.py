from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import DEFAULT_EMBED_COLOR
from utils.db.celestial_members_db import (
    fetch_celestial_member,
    update_member_info,
    upsert_celestial_member_id_and_name_only,
)
from utils.functions.parsers import parse_compact_number
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log, send_webhook
from utils.logs.pretty_log import pretty_log


async def update_member_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    new_name: str = None,
    new_pokemeow_name: str = None,
    new_channel: discord.TextChannel = None,
    new_clan_bank_donations: str = None,
    new_clan_treasury_donations: str = None,
):
    # Defer the interaction to buy time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Updating info for {member.name}...",
        ephemeral=False,
    )

    # Check if user has put atleast one field to update
    if not any(
        [
            new_name,
            new_pokemeow_name,
            new_channel,
            new_clan_bank_donations,
            new_clan_treasury_donations,
        ]
    ):
        await loader.error("Please provide at least one field to update.")
        return

    # Verify inputted fields
    if new_clan_bank_donations is not None:
        new_clan_bank_donations = parse_compact_number(new_clan_bank_donations)
        if new_clan_bank_donations is None:
            await loader.error(
                "Invalid format for Clan Bank Donations. Please enter a valid number (e.g., 1.5k, 2M)."
            )
            return
    if new_clan_treasury_donations is not None:
        new_clan_treasury_donations = parse_compact_number(new_clan_treasury_donations)
        if new_clan_treasury_donations is None:
            await loader.error(
                "Invalid format for Clan Treasury Donations. Please enter a valid number (e.g., 1.5k, 2M)."
            )
            return

    # Check if member is in database
    member_info = await fetch_celestial_member(bot, member.id)
    if not member_info:
        # Upsert first before updating if member is not in database
        await upsert_celestial_member_id_and_name_only(bot, member.id, member.name)
        pretty_log(
            tag="info",
            message=f"Member {member.id} - {member.name} was not in the database, upserted with ID and name only before updating.",
        )

    # Update the member info in the database
    try:
        await update_member_info(
            bot=bot,
            user_id=member.id,
            new_name=new_name,
            new_pokemeow_name=new_pokemeow_name,
            new_channel_id=new_channel.id if new_channel else None,
            new_clan_bank_donation=new_clan_bank_donations,
            new_clan_treasury_donation=new_clan_treasury_donations,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update member info for {member.id}: {e}",
            include_trace=True,
        )
        await loader.error(
            "An error occurred while updating the member info. Please try again later."
        )
        return

    # Log the successful update
    new_name_str = f"**Name:** {new_name}\n" if new_name else ""
    new_pokemeow_name_str = (
        f"**Pokémeow Name:** {new_pokemeow_name}\n" if new_pokemeow_name else ""
    )
    new_channel_str = f"**Channel:** {new_channel.mention}\n" if new_channel else ""
    new_clan_bank_donations_str = (
        f"**Clan Bank Donations:** {new_clan_bank_donations}\n"
        if new_clan_bank_donations is not None
        else ""
    )
    new_clan_treasury_donations_str = (
        f"**Clan Treasury Donations:** {new_clan_treasury_donations}\n"
        if new_clan_treasury_donations is not None
        else ""
    )

    desc = (
        f"**Member:** {member.mention}\n"
        f"**Updated Fields:**\n"
        f"{new_name_str}"
        f"{new_pokemeow_name_str}"
        f"{new_channel_str}"
        f"{new_clan_bank_donations_str}"
        f"{new_clan_treasury_donations_str}"
    )
    embed = discord.Embed(
        title="Member Info Updated",
        description=desc,
        color=DEFAULT_EMBED_COLOR,
        timestamp=datetime.now(),
    )

    embed.set_author(
        name=interaction.user.name, icon_url=interaction.user.display_avatar.url
    )
    embed.set_thumbnail(
        url=member.display_avatar.url if member.display_avatar else None
    )
    embed.set_footer(
        text=f"User ID: {member.id}",
        icon_url=(
            interaction.guild.icon.url
            if interaction.guild and interaction.guild.icon
            else None
        ),
    )
    await loader.success(content="", embed=embed)
    await send_server_log(bot=bot, embed=embed)
