import re

import discord

from constants.aesthetics import Emojis
from constants.celestial_constants import (
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
)
from utils.db.flex_messages_db import (
    delete_flex_message,
    get_flex_message,
    upsert_flex_message,
)
from utils.logs.pretty_log import pretty_log

processing_flex_message_ids = set()
EMOJI_MAP = {
    "PokeCoin": Emojis.pokecoin,
    "Shiny": Emojis.Shiny,
    "Golden": Emojis.Golden,
    "Legendary": Emojis.Legendary,
    "Common": Emojis.Common,
    "Uncommon": Emojis.Uncommon,
    "Rare": Emojis.Rare,
    "Superrare": Emojis.Super_Rare,
    "Mega": Emojis.mega,
    "ShinyMega": Emojis.shinymega,
    "gigantamax": Emojis.gigantamax,
    "shinygigantamax": Emojis.shinygigantamax,
}


CUSTOM_EMOJI_PATTERN = re.compile(r"<a?:([A-Za-z0-9_]+):\d+>")


def _canonical_emoji_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


CANONICAL_EMOJI_MAP = {
    _canonical_emoji_name(name): emoji for name, emoji in EMOJI_MAP.items()
}


def replace_mapped_emojis(text: str) -> str:
    """Replaces custom emoji tags in text using EMOJI_MAP values."""
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        emoji_name = match.group(1)
        mapped = CANONICAL_EMOJI_MAP.get(_canonical_emoji_name(emoji_name))
        return mapped if mapped else match.group(0)

    return CUSTOM_EMOJI_PATTERN.sub(_replace, text)


async def new_flex_message_handler(bot: discord.Client, message: discord.Message):
    """Handles the logic for when a new flex message is created."""
    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not guild:
        pretty_log("critical", f"Guild with ID {CELESTIAL_SERVER_ID} not found.")
        return
    member = guild.get_member(message.author.id)
    flex_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.stellar_flex)
    if not flex_channel and not member:
        pretty_log(
            "critical",
            f"Flex channel or member not found in guild {CELESTIAL_SERVER_ID}.",
        )
        return
    # Don't process if the message is in the stellar flex channel to avoid recursion
    if message.channel.id == CELESTIAL_TEXT_CHANNELS.stellar_flex:
        return

    # Add to processing message IDS to prevent race conditions with reactions
    if message.id in processing_flex_message_ids:
        return
    processing_flex_message_ids.add(message.id)
    try:
        old_embed_title = message.embeds[0].title if message.embeds else ""
        color = message.embeds[0].color if message.embeds else DEFAULT_EMBED_COLOR
        message_content = replace_mapped_emojis(message.content)
        embed_description = replace_mapped_emojis(
            message.embeds[0].description if message.embeds else ""
        )
        final_embed_description = embed_description
        if embed_description:
            final_embed_description = embed_description
        elif message_content:
            final_embed_description = message_content
        jump_url = message.jump_url
        channel_jump_text = f"[{message.channel.name}]({jump_url})" if jump_url else ""
        jump_url_text = f"[Jump to original message]({jump_url})" if jump_url else ""
        if final_embed_description and jump_url_text:
            embed_description = f"{final_embed_description}\n\n{jump_url_text}"

        # Create the flex message embed
        embed = discord.Embed(
            title=old_embed_title,
            description=embed_description,
            color=color,
        )
        embed.set_author(
            name=str(message.author),
            icon_url=(
                message.author.display_avatar.url
                if message.author.display_avatar
                else None
            ),
        )
        embed.set_image(
            url=(
                message.embeds[0].image.url
                if message.embeds and message.embeds[0].image
                else None
            )
        )
        embed.set_thumbnail(
            url=(
                message.embeds[0].thumbnail.url
                if message.embeds and message.embeds[0].thumbnail
                else None
            )
        )

        # Preserve and replace emojis in original embed fields
        if message.embeds and message.embeds[0].fields:
            for field in message.embeds[0].fields:
                field_name = replace_mapped_emojis(field.name)
                field_value = replace_mapped_emojis(field.value)
                embed.add_field(name=field_name, value=field_value, inline=field.inline)

        # Update flex_content logic
        if embed_description and message_content:
            flex_content = (
                f"{Emojis.alien_twerk} | {channel_jump_text}\n\n{message_content}"
            )
        else:
            flex_content = f"{Emojis.alien_twerk} | {channel_jump_text}"

        # Add original footer to the embed
        if message.embeds and message.embeds[0].footer:
            embed.set_footer(
                text=message.embeds[0].footer.text,
                icon_url=message.embeds[0].footer.icon_url,
            )

        await flex_channel.send(content=flex_content, embed=embed)
        await upsert_flex_message(bot=bot, message=message)
    except Exception as e:
        pretty_log("error", f"Error processing flex message: {e}")
    finally:
        processing_flex_message_ids.discard(message.id)


async def remove_flex_message(bot: discord.Client, message_id: int):
    """Handles the logic for when a flex message is deleted."""
    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not guild:
        pretty_log("critical", f"Guild with ID {CELESTIAL_SERVER_ID} not found.")
        return

    flex_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.stellar_flex)
    if not flex_channel:
        pretty_log(
            "critical",
            f"Flex channel with ID {CELESTIAL_TEXT_CHANNELS.stellar_flex} not found.",
        )
        return

    try:
        # Find the copied flex message using the original message id in jump URL text.
        target = f"/{message_id}"
        flex_message = None

        async for msg in flex_channel.history(limit=200):
            if target in (msg.content or ""):
                flex_message = msg
                break

            if msg.embeds:
                description = msg.embeds[0].description or ""
                if target in description:
                    flex_message = msg
                    break

        if flex_message:
            await flex_message.delete()
        else:
            pretty_log(
                "warning",
                f"Could not find copied flex message for original message ID {message_id}.",
            )

        await delete_flex_message(bot=bot, message_id=message_id)
    except discord.NotFound:
        # Message doesn't exist in channel anymore, safe to remove from DB.
        await delete_flex_message(bot=bot, message_id=message_id)
    except discord.Forbidden as e:
        pretty_log(
            "error",
            f"Missing permissions to delete flex message {message_id}: {e}",
        )
    except discord.HTTPException as e:
        pretty_log("error", f"Failed to delete flex message {message_id}: {e}")
