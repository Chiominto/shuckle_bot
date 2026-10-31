import re

import discord

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
    CELESTIAL_EMOJIS
)
from constants.aesthetics import Emojis
from constants.paldea_galar_dict import rarity_meta
from utils.functions.design_embed import design_embed
from utils.functions.pokemeow_reply import get_pokemeow_reply_or_interaction_member
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log

RARE_EGG_EXCLUSIVES = [
    "chingling",
    "mimejr",
    "happiny",
    "chatot",
    "munchlax",
    "riolu",
    "audino",
    "zorua",
    "emolga",
    "ferroseed",
    "golett",
    "pawniard",
    "pancham",
    "spritzee",
    "swirlix",
    "noibat",
    "crabrawler",
    "rockruff",
    "type-null",
    "yamper",
    "nickit",
]
SUPER_RARE_EGG_EXCLUSIVE = ["carbink", "mimikyu"]


def extract_hatch_info(message: str) -> dict | None:
    match = re.search(
        r"\*\*(.+?)\*\* hatched in \*\*(.+?)\*\*!.*?" r"\*\*(.+?)\*\*",
        message,
        re.DOTALL,
    )

    if not match:
        return None

    return {
        "egg_type": match.group(1),
        "incubator_num": match.group(2),
        "hatched_mon": match.group(3),
    }


async def handle_res_egg_hatch(bot: discord.Client, message: discord.Message):

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    hatch_info = extract_hatch_info(embed.description)
    if not hatch_info:
        return
    embed_color = embed.color
    embed_image_url = embed.image.url if embed.image else None
    embed_author_text = embed.author.name if embed.author else None
    embed_author_icon_url = embed.author.icon_url if embed.author else None


    egg_type = hatch_info["egg_type"]
    hatched_mon = hatch_info["hatched_mon"]
    incubator_num = hatch_info["incubator_num"]

    if (
        hatched_mon.lower() not in RARE_EGG_EXCLUSIVES
        and hatched_mon.lower() not in SUPER_RARE_EGG_EXCLUSIVE
        and "shiny" not in hatched_mon.lower()
        and "golden" not in hatched_mon.lower()
    ):
        return

    if hatched_mon.lower() in RARE_EGG_EXCLUSIVES:
        display_name = f"{Emojis.Rare} {hatched_mon}"
    elif hatched_mon.lower() in SUPER_RARE_EGG_EXCLUSIVE:
        display_name = f"{Emojis.SuperRare} {hatched_mon}"
    elif "shiny" in hatched_mon.lower():
        # Remove Shiny from the name for display
        clean_name = hatched_mon.lower().replace("shiny", "").strip()
        display_name = f"{Emojis.Shiny} {clean_name}"
    elif "golden" in hatched_mon.lower():
        # Remove Golden from the name for display
        clean_name = hatched_mon.lower().replace("golden", "").strip()
        display_name = f"{Emojis.Golden} {clean_name}"
    else:
        display_name = hatched_mon

    rarespawn_channel = message.guild.get_channel(CELESTIAL_TEXT_CHANNELS.rare_spawns)

    rs_embed = discord.Embed(
        title=f"**{egg_type.title()}** hatched in **{incubator_num.title()}**",
        url=message.jump_url,
        description=f"{display_name}",
        color=embed_color
    )

    if embed_image_url:
        rs_embed.set_image(url=embed_image_url)
    if embed_author_text:
        rs_embed.set_author(name=embed_author_text, icon_url=embed_author_icon_url)

    await send_webhook(
        bot=bot,
        channel=rarespawn_channel,
        embed=rs_embed
    )