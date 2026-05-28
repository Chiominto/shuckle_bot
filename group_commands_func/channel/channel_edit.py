import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import DEFAULT_EMBED_COLOR
from utils.db.celestial_members_db import get_registered_personal_channel
from utils.functions.cooldown_tracker import check_cooldown, update_cooldown
from utils.functions.design_embed import design_embed, format_bulletin_desc
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log

# === Constants & Helpers ===
FLOWER_EMOJI = "❀"
DOT = "."
PLUS = "﹢"
COMMA = "﹐"
ALT_SEPARATORS = [".", "・", "﹒", "·", "ㆍ", "-", " "]
MAX_NAME_LENGTH = 100
MAX_TOPIC_LENGTH = 1024

CUSTOM_EMOJI_REGEX = r"<a?:\w+:\d+>"


def contains_custom_emoji(text: str) -> bool:
    return bool(re.search(CUSTOM_EMOJI_REGEX, text))


def is_single_default_emoji(text: str) -> bool:
    return not contains_custom_emoji(text) and len(text.strip()) <= 2


def parse_channel_name(current_name: str) -> tuple[str, str, str]:
    """Parse supported channel name formats and return (emoji, base_name, separator)."""
    if not current_name:
        raise ValueError("Channel name is empty")

    name = current_name.strip()

    # Supported modern formats: emoji<sep>name where sep can vary.
    for sep in ALT_SEPARATORS:
        if sep in name:
            left, right = name.split(sep, 1)
            if left.strip() and right.strip():
                return left.strip(), right.strip(), sep

    # Legacy format: emoji﹢name﹐...
    if PLUS in name and COMMA in name:
        start_index = name.index(PLUS) + 1
        end_index = name.index(COMMA)
        base_name = name[start_index:end_index].strip()
        if base_name:
            return name[0], base_name, PLUS

    # Fallback: treat first visible char as emoji and strip common separators.
    first_char = name[0]
    base_name = name[1:].strip().lstrip(" .・﹒·ㆍ_,-﹢﹐")
    if base_name:
        return first_char, base_name, " "

    # Final fallback
    if name:
        return name[0], name, " "

    raise ValueError("Channel name is empty after normalization")


CHANNEL_EDIT_COOLDOWN_SECONDS = 300  # 5 minutes


# 💙───────────────────────────────────────────────💙
# 🫧        Channel Edit Func
# 💙───────────────────────────────────────────────💙
async def channel_edit_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    emoji: str = None,
    topic: str = None,
):
    # 🌟 Defer response
    loader = await pretty_defer(
        interaction=interaction,
        content="Updating your channel...",
        ephemeral=False,
    )

    # 🌟 Check cooldown
    cooldown_msg = check_cooldown(
        interaction.user.id, interaction.channel.id, CHANNEL_EDIT_COOLDOWN_SECONDS
    )
    if cooldown_msg:
        await loader.error(content=cooldown_msg)
        return

    # 🌟 Validate input
    if not any([emoji, topic]):
        await loader.error(
            content="Please provide at least one field to update: emoji or topic.",
        )
        return

    if emoji and not is_single_default_emoji(emoji):
        await loader.error(
            content="Please use **one default emoji only** — no custom or combo emojis!"
        )
        return

    # 🌟 Lookup registered personal channel
    channel_id = await get_registered_personal_channel(
        bot=bot, user_id=interaction.user.id
    )
    if not channel_id:
        await loader.error(
            content="You don’t have a personal channel registered.",
        )
        pretty_log(
            "critical",
            f"{interaction.user} tried to edit channel but has no registered channel.",
        )
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            msg = "I couldn't find your channel. Please contact staff."
            await loader.error(content=msg)
            pretty_log(
                "critical",
                f"{interaction.user}'s channel ({channel_id}) not found.",
            )
            return

    # 🌟 Check permissions
    if not channel.permissions_for(channel.guild.me).manage_channels:
        await loader.error(
            content="I don’t have permission to edit your channel.",
        )
        pretty_log(
            "critical",
            f"{interaction.user}'s channel ({channel_id}) cannot be edited due to missing permissions.",
        )
        return

    old_name = channel.name
    new_name = None

    # 🌟 Build new channel name
    if emoji:
        try:
            old_emoji, old_base_name, old_sep = parse_channel_name(old_name)
        except Exception:
            await loader.error(
                content="⚠️ Failed to parse the channel name format.",
            )
            pretty_log(
                "error",
                f"{interaction.user}'s channel ({old_name}) failed name parsing.",
            )
            return

        new_raw_name = f"{emoji or old_emoji}{old_sep}{old_base_name}"
        if len(new_raw_name) > MAX_NAME_LENGTH:
            await loader.error(content="Channel name too long.")
            return
        new_name = new_raw_name.lower()

    if topic and len(topic) > MAX_TOPIC_LENGTH:
        msg = (
            f"That topic is too long ({len(topic)} characters). Max is {MAX_TOPIC_LENGTH}.",
        )
        await loader.error(content=msg)
        return

    # 🌟 Apply changes
    try:
        await asyncio.sleep(1)
        if new_name:
            await channel.edit(name=new_name)
            await asyncio.sleep(1)
        if topic:
            await channel.edit(topic=topic)
    except discord.Forbidden:
        await loader.error(content="I don't have permission to edit your channel.")
        pretty_log("critical", f"ForbiddenError editing {interaction.user}'s channel.")
        return
    except discord.HTTPException as e:
        msg = f"Failed to edit the channel: {e.text}"
        await loader.error(content=msg)
        pretty_log(
            "error", f"HTTPException editing {interaction.user}'s channel: {e.text}"
        )
        return
    except asyncio.TimeoutError:
        await loader.error(content="Channel update timed out.")
        pretty_log("error", f"TimeoutError editing {interaction.user}'s channel.")
        return

    update_cooldown(interaction.user.id, interaction.channel.id)

    # 🌟 Log change
    embed = discord.Embed(
        title=f"Channel Updated",
        description=(
            f"- **Old Name:** {old_name}\n"
            f"{f'- **New Name:** {new_name}\n' if new_name else ''}"
            f"{f'- **New Topic:** {topic}' if topic else ''}"
        ),
        timestamp=datetime.now(),
        color=DEFAULT_EMBED_COLOR,
    )
    embed.set_author(
        name=f"{interaction.user}", icon_url=interaction.user.display_avatar.url
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed = design_embed(embed=embed, user=interaction.user)

    # 🌸 Success message
    await loader.success(content=f"Channel updated: {channel.mention}", embed=embed)
    await send_server_log(bot=bot, embed=embed)

    pretty_log("ready", f"{interaction.user} updated their channel successfully.")
