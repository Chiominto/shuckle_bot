import discord
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.logs.pretty_log import pretty_log

CC_MH_REPORT_CHANNEL_ID = 1502156762466357338


async def send_long_message(channel: discord.TextChannel, content: str):
    """Send a message, splitting it into chunks if it exceeds Discord's 2000-character limit."""
    MAX_LEN = 2000
    if len(content) <= MAX_LEN:
        await channel.send(content)
        return

    lines = content.split("\n")
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > MAX_LEN:
            await channel.send(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await channel.send(chunk)


async def relay_meowsummit_reports(bot: commands.Bot, message: discord.Message):
    """Relay messages from MeowSummit reports category to Straymons reports channel."""

    # Prepare report content (text only)
    final_msg = message.content or ""

    # Send to Straymons report channel
    guild = bot.get_guild(CELESTIAL_SERVER_ID)

    target_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.summit_reports)
    if target_channel:
        try:
            # 📤 Send text + attachments in a single message
            if message.attachments:
                files = [
                    await attachment.to_file() for attachment in message.attachments
                ]
                await target_channel.send(content=final_msg or None, files=files)
            elif final_msg:
                await target_channel.send(content=final_msg)
            else:
                pretty_log(
                    "warning",
                    "⚠️ Skipping empty report relay (no text and no attachments).",
                )

        except Exception as e:
            pretty_log(
                "error",
                f"❌ Failed to send report relay: {e}",
            )
