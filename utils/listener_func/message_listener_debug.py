import re

import discord

from utils.listener_func.battle_frontier_ach import handle_battle_frontier_achievement
from utils.listener_func.code_use_listener import send_code_claim_to_rs
from utils.listener_func.golden_stone_listener import golden_stone_listener
from utils.logs.debug_log import debug_enabled, debug_log, enable_debug
from utils.logs.pretty_log import pretty_log
from utils.listener_func.unown_unlocks import process_unown_unlock
from utils.listener_func.promo_claim_listener import promo_claim_listener
from utils.listener_func.res_egg_listener import handle_res_egg_hatch
# enable_debug(f"{__name__}.handle_test_message")
triggers = {
    "battle_frontier_ach": "🎖️ You may continue your",
    "golden_stone": "to claim your <:golden_",
    "code_use": "<:checkedbox:752302633141665812> you used a code to claim a :gift:",
}
CODE_USE_PATTERN = re.compile(r"\byou used a code to claim\b", re.IGNORECASE)


async def handle_test_message(bot: discord.Client, message: discord.Message):
    if not message.reference or not message.reference.message_id:
        return
    replied_message = await message.channel.fetch_message(message.reference.message_id)
    if not replied_message:
        debug_log(
            f"Failed to fetch replied message with ID {message.reference.message_id} in channel {message.channel.id}"
        )
        return
    replied_message_content = getattr(replied_message, "content", "").lower()
    debug_log(f"Fetched replied message content: '{replied_message_content}'")

    replied_embed = replied_message.embeds[0] if replied_message.embeds else None
    replied_embed_author = (
        replied_embed.author.name if replied_embed and replied_embed.author else ""
    )
    replied_embed_description = (
        replied_embed.description if replied_embed and replied_embed.description else ""
    )
    replied_embed_footer = (
        replied_embed.footer.text if replied_embed and replied_embed.footer else ""
    )
    replied_embed_title = (
        replied_embed.title if replied_embed and replied_embed.title else ""
    )

    # 🌟────────────────────────────────────────────
    #   💠 Battle Frontier Achievement Handler
    # 🌟────────────────────────────────────────────
    if triggers["battle_frontier_ach"].lower() in replied_message.content.lower():
        pretty_log(
            "info",
            f"Detected Battle Frontier achievement in message ID {getattr(message, 'id', 'unknown')}",
        )
        await handle_battle_frontier_achievement(bot=bot, message=replied_message)
    # 🌟────────────────────────────────────────────
    #   💠 Golden Stone Handler
    # 🌟────────────────────────────────────────────
    if (
        replied_message
        and triggers["golden_stone"].lower() in replied_message_content.lower()
    ):
        debug_log(
            "Golden stone trigger matched. Proceeding to call golden_stone_listener."
        )
        await golden_stone_listener(bot=bot, message=replied_message)
    # ————————————————————————————————
    # 🐢 Code Claim Listener
    # ————————————————————————————————
    if replied_message and CODE_USE_PATTERN.search(replied_message_content):
        try:
            await send_code_claim_to_rs(bot=bot, message=replied_message)
            pretty_log(
                "ready",
                f"Successfully processed code claim from message ID {getattr(message, 'id', 'unknown')}",
            )
        except Exception as e:
            pretty_log(
                "critical",
                f"Failed processing code claim from message ID {getattr(message, 'id', 'unknown')}: {e}",
            )
    # 🌟────────────────────────────────────────────
    #   💠 Unown Unlock Handler
    # 🌟────────────────────────────────────────────
    if (
        replied_message_content
        and "unown ruins reward:" in replied_message_content
        and (
            "<:superrare:" in replied_message_content
            or "<:shiny:" in replied_message_content
        )
    ):
        try:
            await process_unown_unlock(bot=bot, message=replied_message)
            pretty_log(
                "ready",
                f"Successfully processed Unown unlock from message ID {getattr(message, 'id', 'unknown')}",
            )
        except Exception as e:
            pretty_log(
                "critical",
                f"Failed processing Unown unlock from message ID {getattr(message, 'id', 'unknown')}: {e}",
            )

    # 💙───────────────────────────────────────────────💙
    # 🫧 Promo Claim Processing
    # 💙───────────────────────────────────────────────💙
    if replied_embed:
        if (
            "spent" in replied_embed_description.lower()
            and "claimed a" in replied_embed_description.lower()
            and "PokeMeow Special Golden Promotionals" in replied_embed_author
        ):
            try:
                await promo_claim_listener(bot=bot, message=replied_message)
                pretty_log(
                    "ready",
                    f"Successfully processed promo claim from message ID {getattr(message, 'id', 'unknown')}",
                )
            except Exception as e:
                pretty_log(
                    "❌ ERROR",
                    f"Failed processing promo claim from message ID {getattr(message, 'id', 'unknown')}: {e}",
                )

    # 💙───────────────────────────────────────────────💙
    # 🫧 Research Lab Egg Hatch Processing
    # 💙───────────────────────────────────────────────💙
    if replied_embed and "research lab hatch" in replied_embed_author.lower():
        try:
            pretty_log(
                "ready",
                f"Processing Research Lab egg hatch from message ID {getattr(replied_message, 'id', 'unknown')}",
            )
            await handle_res_egg_hatch(bot=bot, message=replied_message)
            pretty_log(
                "ready",
                f"Successfully processed Research Lab egg hatch from message ID {getattr(replied_message, 'id', 'unknown')}",
            )
        except Exception as e:
            pretty_log(
                "critical",
                f"Failed processing Research Lab egg hatch from message ID {getattr(replied_message, 'id', 'unknown')}: {e}",
            )
