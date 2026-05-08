import re

import discord


from utils.logs.pretty_log import pretty_log

# ————————————————————————————————
# 💸 Market Snipe Filters – No Chatting!
# ————————————————————————————————
# This module helps keep the market snipe channel clean!
# It only allows buying commands, mentions, or messages from staff.
# Everything else gets *swept away~* 🧹

# 🌸 Valid buy command patterns

# Updated: Allow optional numeric amount or 'all' after the ID, but not hybrid alphanumeric
BUY_COMMAND_PATTERNS = [
    r"^;\s*(m|market)\s*(b|buy)\s*\d+(\s*\d+|\s*all)?$",
]


# ————————————————————————————————
# ✅ Check if message is a valid buy command
# ————————————————————————————————
def is_valid_buy_command(content: str) -> bool:
    return any(
        re.match(pattern, content.strip(), re.IGNORECASE)
        for pattern in BUY_COMMAND_PATTERNS
    )


# ————————————————————————————————
# 🧸 Check if message is only mentions
# ————————————————————————————————
def is_mention_only(content: str) -> bool:
    content = content.strip()
    return bool(content) and all(
        part.startswith("<@") and part.endswith(">") for part in content.split()
    )


# ————————————————————————————————
# 🧹 Message Filter for Market Snipe
# ————————————————————————————————
async def should_delete_market_message(message: discord.Message) -> bool:
    """
    Returns True if the message was deleted.
    Also sends the user a soft reminder DM 💌
    """


    # 🛡️ Ignore bot messages and webhooks (like PokéMeow)
    if message.author.bot or message.webhook_id is not None:
        pretty_log(
            tag="debug",
            message=f"Ignored bot/webhook message from {message.author} ({message.author.id}): '{message.content}'",

            label="MARKET SNIPE",
        )
        return False

    # 🌸 Allow buy commands and mention-only messages
    if is_valid_buy_command(message.content):
        pretty_log(
            tag="debug",
            message=f"Allowed valid buy command from {message.author} ({message.author.id}): '{message.content}'",

            label="MARKET SNIPE",
        )
        return False
    if is_mention_only(message.content):
        pretty_log(
            tag="debug",
            message=f"Allowed mention-only message from {message.author} ({message.author.id}): '{message.content}'",

            label="MARKET SNIPE",
        )
        return False

    # ❌ Delete the message and softly nudge the user
    pretty_log(
        tag="info",
        message=f"Deleting message from {message.author} ({message.author.id}): '{message.content}'",

        label="MARKET SNIPE",
    )
    try:
        await message.delete()
        await message.author.send(
            "Hey there! Please avoid chatting in the market snipe channel — it's meant only for quick buying commands like `;m b 123`.\n"
            "You're free to talk elsewhere or ping someone if needed! ✨"
        )
    except discord.Forbidden:
        pretty_log(
            tag="error",
            message=f"Could not delete or DM user {message.author} ({message.author.id}) for message: '{message.content}'",

            label="MARKET SNIPE",
        )
        pass

    return True
