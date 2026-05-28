from datetime import datetime, timedelta

import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,

)


from utils.logs.pretty_log import pretty_log

async def send_monthly_stats_reminder(bot:discord.Client):
    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.moderator_only)

    message_content = (
        f"<@&{CELESTIAL_ROLES.co_owner}> <@&{CELESTIAL_ROLES.clan_owner_}>\n"
        f"Don't forget to check `;clan stats m`"
    )
    await channel.send(content=message_content)
    pretty_log(
        tag="info",
        message="Sent monthly stats reminder.",
    )