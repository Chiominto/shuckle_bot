import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
)
from utils.db.celestial_members_db import fetch_all_celestial_member_ids
from utils.logs.pretty_log import pretty_log


async def reset_donation_roles(bot: discord.Client):
    """Reset donation roles for all members."""
    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not guild:
        pretty_log(
            "error",
            "Guild not found for donation role reset",
            label="DonationRoleReset",
        )
        return
    donated_role = guild.get_role(CELESTIAL_ROLES.tip_jar_titan)
    not_donated_role = guild.get_role(CELESTIAL_ROLES.coin_saver)
    if not donated_role or not not_donated_role:
        pretty_log(
            "error",
            "One or more donation roles not found in guild",
            label="DonationRoleReset",
        )
        return
    celestial_members_ids, _ = await fetch_all_celestial_member_ids(bot)
    for member_id in celestial_members_ids:
        member = guild.get_member(member_id)
        if not member:
            continue
        if donated_role in member.roles:
            try:
                await member.remove_roles(
                    donated_role, reason="Scheduled donation role reset"
                )
                pretty_log(
                    "info", f"Removed donated role from {member.name} ({member.id})"
                )
            except Exception as e:
                pretty_log(
                    "error",
                    f"Error removing donated role from {member.name} ({member.id}): {e}",
                )
        if not_donated_role not in member.roles:
            try:
                await member.add_roles(
                    not_donated_role, reason="Scheduled donation role reset"
                )
                pretty_log(
                    "info", f"Added not donated role to {member.name} ({member.id})"
                )
            except Exception as e:
                pretty_log(
                    "error",
                    f"Error adding not donated role to {member.name} ({member.id}): {e}",
                )

    clan_bank_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.clan_bank)
    if clan_bank_channel:
        content = f"<@&{CELESTIAL_ROLES.coin_saver}> , it's that time again drop your weekly <:PokeCoin:1255459577080840223> 100k coins and keep the stars in our system shining bright."
        try:
            await clan_bank_channel.send(content)
            pretty_log("info", "Sent donation reminder message in clan bank channel")
        except Exception as e:
            pretty_log("error", f"Error sending donation reminder message: {e}")
