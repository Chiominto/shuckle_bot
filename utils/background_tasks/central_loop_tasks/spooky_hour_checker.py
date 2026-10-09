from datetime import datetime

import discord

from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS, CELESTIAL_ROLES

from utils.db.spooky_hour_db import fetch_spooky_hour, remove_spooky_hour
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log



# 🕒────────────────────────────────────────────
#     ✨ Spooky Hour Checker
#     Checks if Spooky Hour has ended
# 🕒────────────────────────────────────────────
async def check_and_handle_spooky_hour_expiry(bot: discord.Client):
    """Checks if Spooky Hour has ended and removes the schedule if so."""
    now = int(datetime.now().timestamp())

    # Fetch current Spooky Hour schedule
    spooky_hour_info = await fetch_spooky_hour(bot)
    if not spooky_hour_info:
        return  # No Spooky Hour scheduled

    ends_on = spooky_hour_info["ends_on"]

    if now >= ends_on:
        try:
            # Reset Spooky Hour schedule from DB
            await remove_spooky_hour(bot)
            event_tracker_channel = bot.get_channel(CELESTIAL_TEXT_CHANNELS.bumps)
            if not event_tracker_channel:
                return
            guild = event_tracker_channel.guild
            if not guild:
                return
            spooky_hour_role = guild.get_role(CELESTIAL_ROLES.spooky_hour)
            if not spooky_hour_role:
                return

            content = f"{spooky_hour_role.mention} has ended."
            await event_tracker_channel.send(content=content)


            # Log successful removal
            pretty_log(
                "info",
                f"Spooky Hour ended automatically at {now}, schedule removed.",
                
            )

        except Exception as e:
            # Log any errors during removal
            pretty_log(
                "error",
                f"Failed to remove Spooky Hour schedule: {type(e).__name__}: {e}",

            )
