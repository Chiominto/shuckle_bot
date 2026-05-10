import asyncio

import discord

from constants.aesthetics import Emojis
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
    clan_bank_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.donations)
    donated_role = guild.get_role(CELESTIAL_ROLES.tip_jar_titan)
    not_donated_role = guild.get_role(CELESTIAL_ROLES.coin_saver)
    celestial_nova_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    if not clan_bank_channel:
        pretty_log(
            "error",
            "Donation channel not found in guild",
            label="DonationRoleReset",
        )
        return
    if not celestial_nova_role:
        pretty_log(
            "error",
            "Celestial Nova role not found in guild",
            label="DonationRoleReset",
        )
        return
    if not donated_role or not not_donated_role:
        pretty_log(
            "error",
            "One or more donation roles not found in guild",
            label="DonationRoleReset",
        )

        return
    sent_message = None
    overwrite_bank_channel = clan_bank_channel.overwrites_for(celestial_nova_role)
    original_send_messages = overwrite_bank_channel.send_messages
    try:
        overwrite_bank_channel.send_messages = False
        await clan_bank_channel.set_permissions(
            celestial_nova_role, overwrite=overwrite_bank_channel
        )
        msg_clan_bank_close = f"{Emojis.loading} Closing donation channel while we reset donated roles. Please wait..."
        sent_message = await clan_bank_channel.send(msg_clan_bank_close)
        celestial_members_ids, _ = await fetch_all_celestial_member_ids(bot)
        for member_id in celestial_members_ids:
            member = guild.get_member(member_id)
            if not member:
                try:
                    member = await guild.fetch_member(member_id)
                except discord.NotFound:
                    pretty_log(
                        "warning",
                        f"Member not found in guild for ID {member_id}; skipping",
                    )
                    continue
                except discord.Forbidden:
                    pretty_log(
                        "error",
                        f"Missing permissions to fetch member {member_id}; skipping",
                    )
                    continue
                except discord.HTTPException as e:
                    pretty_log(
                        "error",
                        f"HTTP error fetching member {member_id}; skipping: {e}",
                    )
                    continue
            if donated_role in member.roles:
                try:
                    await member.remove_roles(
                        donated_role, reason="Scheduled donation role reset"
                    )
                    pretty_log(
                        "info", f"Removed donated role from {member.name} ({member.id})"
                    )
                    await asyncio.sleep(0.5)
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
                    await asyncio.sleep(0.5)
                except Exception as e:
                    pretty_log(
                        "error",
                        f"Error adding not donated role to {member.name} ({member.id}): {e}",
                    )
    finally:
        overwrite_bank = clan_bank_channel.overwrites_for(celestial_nova_role)
        overwrite_bank.send_messages = original_send_messages
        try:
            await clan_bank_channel.set_permissions(
                celestial_nova_role, overwrite=overwrite_bank
            )
        except Exception as e:
            pretty_log("error", f"Error restoring donation channel permissions: {e}")
        if sent_message:
            try:
                await sent_message.delete()
            except Exception as e:
                pretty_log("warning", f"Error deleting status message: {e}")
    content = f"<@&{CELESTIAL_ROLES.coin_saver}>, it's that time again drop your weekly <:PokeCoin:1255459577080840223> 100k coins and keep the stars in our system shining bright."
    try:
        await clan_bank_channel.send(content)
        pretty_log("info", "Sent donation reminder message in clan bank channel")
    except Exception as e:
        pretty_log("error", f"Error sending donation reminder message: {e}")
