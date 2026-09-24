import re
from urllib.parse import urlparse

import discord

from constants.celestial_constants import (CELESTIAL_TEXT_CHANNELS,
                                           DEFAULT_EMBED_COLOR)
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def extract_info(text: str | None):
    if not text:
        return None, None

    member_match = re.search(
        r"(?:^|[^\w])(?P<member>[A-Za-z0-9][A-Za-z0-9_. -]*?)\s*recovered\b",
        text,
        flags=re.IGNORECASE,
    )
    received_match = re.search(
        r"\breceived\b(?:\s*[\U0001F300-\U0001FAFF]\s*)*\s*(?P<prize>.+?)(?:!|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    member_name = member_match.group("member").strip() if member_match else None
    missing_number = received_match.group("prize").strip() if received_match else None

    if member_name:
        member_name = member_name.strip("_")
    if member_name and member_name.lower().endswith(" recovered"):
        member_name = member_name.rsplit(" recovered", 1)[0].strip()

    if missing_number:
        missing_number = re.sub(r"^[\W_]+", "", missing_number).strip()
        missing_number = missing_number.strip(" -:;,.")

    return member_name, missing_number


# 🎉────────────────────────────────────────────
#   💠 Pokémon Code Claim Handler (Patched)
# 🎉────────────────────────────────────────────
async def send_missing_number_claim_to_rs(
    bot: discord.Client, message: discord.Message
) -> str | None:
    """
    Extracts the member name and missing number from a missing number claim message and posts an embed in the rare spawn tracker channel.
    Handles shiny/golden properly and applies correct embed color.
    """

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    embed_description = embed.description if embed else ""
    embed_image_url = embed.image.url if embed and embed.image else None
    embed_color = embed.color if embed else DEFAULT_EMBED_COLOR

    try:
        member_name, prize = extract_info(embed_description)
        # Find member object in guild via user_name
        guild = message.guild
        member = discord.utils.get(guild.members, name=member_name)

        achievement_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.rare_spawns)
        if not achievement_channel:
            pretty_log(
                "critical",
                f"Acheievements channel not found in guild {guild.name} ({guild.id})",
            )
            return




        # ──────────────────────────────────────────────
        #   ✅ Build & send embed
        # ──────────────────────────────────────────────
        embed = discord.Embed(
            title="Missing Number Quest Completed",
            url=message.jump_url,
            description=f"{member.mention} has received **{prize}**!",
            color=embed_color,
        )
        if embed_image_url:
            embed.set_image(url=embed_image_url)
        embed.set_author(name=member_name, icon_url=member.avatar.url if member and member.avatar else None)

        await send_webhook(
            bot=bot,
            channel=achievement_channel,
            embed=embed,
        )

        pretty_log(
            "ready",
            f"Successfully posted Pokémon code claim for {member_name} (Message ID {message.id})",
        )

    except Exception as e:
        pretty_log(
            "critical",
            f"Unexpected error in send_missing_number_claim_to_rs (Message ID {getattr(message, 'id', 'unknown')}): {e}",
        )
