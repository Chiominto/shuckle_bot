import re

import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from constants.paldea_galar_dict import rarity_meta
from utils.functions.design_embed import design_embed
from utils.functions.pokemeow_reply import get_pokemeow_reply_or_interaction_member
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


def extract_bold_text(message: str) -> str | None:
    match = re.search(r"\*\*([^*]+)\*\*!$", message)
    return match.group(1) if match else None


async def promo_claim_listener(bot:discord.Client,  message: discord.Message):
    member = await get_pokemeow_reply_or_interaction_member(message=message)
    if not member:
        return

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    embed_description = embed.description if embed.description else ""
    claimed_promo = extract_bold_text(embed_description)
    if not claimed_promo:
        return
    image_url = embed.image.url if embed.image else None

    pretty_log(f"Claimed promo: Golden {claimed_promo} by member: {member}")

    # Get Golden emoji and color
    golden = rarity_meta.get("golden", {})

    golden_emoji = golden.get("emoji")
    golden_color = golden.get("color")

    display_promo_name = f"{golden_emoji} {claimed_promo.title()}" if golden_emoji else f"Golden {claimed_promo.title()}"

    claim_embed = discord.Embed(
        title="Promo Claimed",
        url=message.jump_url,
        description=f"{member.mention} has claimed {display_promo_name}",
        color=golden_color if golden_color else DEFAULT_EMBED_COLOR
    )
    claim_embed.set_author(name=member.display_name, icon_url=member.avatar.url if member.avatar else None)
    if image_url:
        claim_embed.set_thumbnail(url=image_url)



    rarespawn_channel = message.guild.get_channel(CELESTIAL_TEXT_CHANNELS.rare_spawns)
    await send_webhook(
        bot=bot,
        content=None,
        embed=claim_embed,
        channel=rarespawn_channel
    )
