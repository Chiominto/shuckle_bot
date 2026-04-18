import re
from urllib.parse import urlparse

import discord

from constants.celestial_constants import (
    CELESTIAL_TEXT_CHANNELS,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from constants.aesthetics import Emojis
from constants.paldea_galar_dict import rarity_meta

from utils.functions.pokemeow_reply import get_pokemeow_reply_member
from utils.logs.pretty_log import pretty_log
from utils.functions.design_embed import design_embed, format_bulletin_desc
from utils.functions.webhook_func import send_webhook


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def extract_prize(text):
    """
    Extracts the prize name (e.g., 'Shiny Quaxly') from a message like:
    'You claimed a code for a <:Shiny:667126233217105931> <:912:1194246013934911488> Shiny Quaxly!'
    Returns the string between the last emoji and the exclamation mark.
    """
    match = re.search(r"(?:<:[^>]+> )+([^\!]+)!", text)
    if match:
        return match.group(1).strip()
    return None



# 🎉────────────────────────────────────────────
#   💠 Pokémon Code Claim Handler (Patched)
# 🎉────────────────────────────────────────────
async def send_code_claim_to_rs(
    bot: discord.Client, message: discord.Message
) -> str | None:
    """
    Extracts the Pokémon name from a code claim message and posts an embed in the rare spawn tracker channel.
    Handles shiny/golden properly and applies correct embed color.
    """
    try:
        member = await get_pokemeow_reply_member(message=message)
        if not member:
            pretty_log(
                "critical",
                f"Failed to fetch member from message ID {message.id}",

            )
            return

        guild = member.guild

        achievement_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.rare_spawns)
        if not achievement_channel:
            pretty_log(
                "critical",
                f"Acheievements channel not found in guild {guild.name} ({guild.id})",

            )
            return

        content = (
            message.content if isinstance(message, discord.Message) else str(message)
        )
        raw_pokemon_name = re.search(r"\*\*(.*?)\*\*", content)
        if not raw_pokemon_name:
            pretty_log(
                "critical",
                f"Failed to extract Pokémon name from message ID {message.id}",

            )
            return

        clean_pokemon_name = raw_pokemon_name.group(1).strip()
        pokemon_name_lower = clean_pokemon_name.lower()

        # ──────────────────────────────────────────────
        #   ✅ Rarity Detection (before replacements)
        # ──────────────────────────────────────────────
        rarity_key = "default"
        if "golden" in pokemon_name_lower:
            rarity_key = "golden"
        elif "shiny" in pokemon_name_lower:
            rarity_key = "shiny"

        rarity_info = rarity_meta.get(rarity_key, rarity_meta["unknown"])
        color = rarity_info["color"]
        display_name = clean_pokemon_name

        # ──────────────────────────────────────────────
        #   ✅ Replace keyword with emoji (case-insensitive)
        # ──────────────────────────────────────────────
        if rarity_key in ("golden", "shiny"):
            display_name = re.sub(
                rarity_key,
                rarity_info["emoji"],
                display_name,
                flags=re.IGNORECASE,
            ).strip()


        # ──────────────────────────────────────────────
        #   ✅ Build & send embed
        # ──────────────────────────────────────────────
        footer_text = "Code claimed successfully!"
        embed = discord.Embed(
            title="Code Claimed",
            url=message.jump_url,
            description=f"{member.mention} has claimed a code for **{display_name}**!",
        )
        embed = design_embed(
            user=member,
            embed=embed,
            pokemon_name=pokemon_name_lower,
            override_color=color,
            footer_text=footer_text,
        )
        embed.color = color
        await send_webhook(
            bot=bot,
            channel_id=achievement_channel.id,
            embed=embed,
        )

        pretty_log(
            "ready",
            f"Successfully posted Pokémon code claim for {display_name} (Message ID {message.id})",

        )

    except Exception as e:
        pretty_log(
            "critical",
            f"Unexpected error in send_code_claim_to_rs (Message ID {getattr(message, 'id', 'unknown')}): {e}",

        )
