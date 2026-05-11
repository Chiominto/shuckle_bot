import re

import discord

from utils.listener_func.battle_frontier_ach import handle_battle_frontier_achievement
from utils.listener_func.code_use_listener import send_code_claim_to_rs
from utils.listener_func.golden_stone_listener import golden_stone_listener
from utils.logs.debug_log import debug_enabled, debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

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
