import re

import discord

# 🌈 Constants and utilities
from constants.celestial_constants import CELESTIAL_SERVER_ID
from utils.db.boosted_channels import upsert_boosted_channel
from utils.functions.pokemeow_reply import get_pokemeow_reply_member
from utils.logs.pretty_log import pretty_log


def extract_boosted_channel_ids(text: str) -> list[str]:
    # Find the section after "Boosted channels:"
    match = re.search(r"Boosted channels:\s*(.*)", text, re.DOTALL)
    if not match:
        return []
    section = match.group(1)
    # Find all channel IDs in the format [123456789012345678]
    ids = re.findall(r"\[(\d{17,19})\]", section)
    # Return up to 10 unique IDs
    return list(dict.fromkeys(ids))[:10]


async def my_boosted_channel_listener(
    bot: discord.Client,
    message: discord.Message,
):
    """Listener for the 'my boosted channels' command"""
    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    clan_guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not clan_guild:
        pretty_log(
            "warn",
            f"Guild {CELESTIAL_SERVER_ID} not found while processing boosted channels for user {member} ({member.id}).",
        )
        return

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    embed_description = embed.description or ""
    if not embed_description:
        return

    boosted_channel_ids = extract_boosted_channel_ids(embed_description)
    if not boosted_channel_ids:
        pretty_log(
            "info",
            f"No boosted channels found in the embed for user {member} ({member.id}).",
        )
        return

    # Check if the channel ids are in the server
    channels_in_guild = [
        channel
        for channel_id in boosted_channel_ids
        if (channel := clan_guild.get_channel(int(channel_id)))
    ]

    if not channels_in_guild:
        pretty_log(
            "info",
            f"None of the boosted channels for user {member} ({member.id}) exist in the guild.",
        )
        return

    # Register each boosted channel in the database
    for channel in channels_in_guild:
        channel_id = channel.id
        channel_name = channel.name
        await upsert_boosted_channel(
            bot=bot,
            channel_id=channel_id,
            channel_name=channel_name,
            booster_id=member.id,
            booster_name=member.name,
        )
        pretty_log(
            "info",
            f"Registered boosted channel {channel_name} ({channel_id}) for user {member} ({member.id}).",
        )
    # Add checkmark reaction to the message to indicate successful processing
    try:
        await message.add_reaction("\u2705")
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to add reaction to message {message.id} for user {member} ({member.id}): {e}",
        )
