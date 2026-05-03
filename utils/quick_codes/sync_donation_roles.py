from datetime import datetime

import discord
from discord.ext import commands
from constants.celestial_constants import CELESTIAL_ROLES
from constants.aesthetics import Emojis
from utils.logs.pretty_log import pretty_log
from utils.db.temp_roles_db import upsert_temp_role
from utils.db.temp_roles_db import upsert_temp_role

# 🍭──────────────────────────────
#   🎀 Sync donation Roles
# 🍭──────────────────────────────
async def sync_donation_roles(
    bot: discord.Client,
    message: discord.Message,
):
    """Sync donated and not donated roles."""
    processing_msg = await message.reply(f"{Emojis.loading} Syncing donation roles...")
    donated_role = message.guild.get_role(CELESTIAL_ROLES.tip_jar_titan)
    not_donated_role = message.guild.get_role(CELESTIAL_ROLES.coin_saver)

    try:
        # Find guild members who have either of the roles
        for member in message.guild.members:
            if donated_role in member.roles:
                await upsert_temp_role(bot, member.id, member.name, donated_role.id, donated_role.name)
                pretty_log(
                    "info",
                    f"Upserted temp role {donated_role.name} for user {member.name} ({member.id})"
                )
            if not_donated_role in member.roles:
                await upsert_temp_role(bot, member.id, member.name, not_donated_role.id, not_donated_role.name)
                pretty_log(
                    "info",
                    f"Upserted temp role {not_donated_role.name} for user {member.name} ({member.id})"
                )
        await processing_msg.edit(content=f"{Emojis.success} Successfully synced donation roles.")
        
    except Exception as e:
        pretty_log("error", f"Error syncing donation roles: {e}")
        await processing_msg.edit(content=f"{Emojis.error} Error syncing donation roles.")
        return


