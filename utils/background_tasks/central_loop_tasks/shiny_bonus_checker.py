import time

import discord

from constants.celestial_constants import (
    CELESTIAL_TEXT_CHANNELS,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.db.shiny_bonus_db import delete_shiny_bonus, fetch_shiny_bonus
from utils.logs.pretty_log import pretty_log


async def check_and_handle_expired_shiny_bonus(bot):
    """Check if the shiny bonus has expired and handle its expiration."""
    shiny_bonus = await fetch_shiny_bonus(bot)
    if not shiny_bonus:
        return
    ends_on = shiny_bonus["ends_on"]
    current_time = int(time.time())
    if current_time >= ends_on:
        pretty_log(
            "info",
            "Shiny bonus has expired. Deleting bonus and notifying channels.",
        )
        await delete_shiny_bonus(bot)
        guild = bot.get_guild(CELESTIAL_SERVER_ID)
        # Notify all relevant channels
        channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.bumps)
        role = guild.get_role(CELESTIAL_ROLES.shiny_bonus)
        if channel and role:
            await channel.send(
                content=f"{role.mention} The Checklist Shiny Bonus has ended!",
            )
