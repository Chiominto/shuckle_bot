import traceback
from datetime import datetime

import discord
from discord.ext import commands

CC_ERROR_LOGS_CHANNEL_ID = 1444997181244444672
# -------------------- 🧩 Global Bot Reference --------------------
from typing import Optional

BOT_INSTANCE: Optional[commands.Bot] = None


def set_bot(bot: commands.Bot):
    """Set the global bot instance for automatic logging."""
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# -------------------- 🧩 Log Tags --------------------
TAGS = {
    "info": "🐢 INFO",  # Shuckle (default/info)
    "db": "🍯 DB",  # Honey jar (Shuckle makes berry juice)
    "cmd": "🥚 CMD",  # Egg (Shuckle's shell)
    "ready": "🍓 READY",  # Berry (Shuckle stores berries)
    "error": "🟥 ERROR",  # Red square (Shuckle's shell color)
    "warn": "🟡 WARN",  # Yellow circle (Shuckle's limbs)
    "critical": "💥 CRITICAL",  # Explosion (Shuckle under attack)
    "skip": "🐚 SKIP",  # Shell (Shuckle hides)
    "sent": "📦 SENT",  # Box (Shuckle stores things)
    "debug": "🐞 DEBUG",  # Bug (Shuckle is a bug type)
    "success": "🌟 SUCCESS",  # Star (Shuckle wins)
    "cache": "🥒 CACHE",  # Pickle (Shuckle is the mold Pokémon)
    "schedule": "⏳ SCHEDULE",  # Hourglass (slow, patient Shuckle)
}

# -------------------- 🎨 Shuckle ANSI Colors --------------------
COLOR_SHUCKLE_RED = "\033[38;2;232;53;53m"  # Shuckle shell red
COLOR_SHUCKLE_YELLOW = "\033[38;2;255;221;51m"  # Shuckle limbs yellow
COLOR_SHUCKLE_WHITE = "\033[38;2;255;255;255m"  # White (shell spots)
COLOR_RESET = "\033[0m"

MAIN_COLORS = {
    "red": COLOR_SHUCKLE_RED,  # For errors/critical
    "yellow": COLOR_SHUCKLE_YELLOW,  # For warnings
    "white": COLOR_SHUCKLE_WHITE,  # For info/default
    "reset": COLOR_RESET,
}
# -------------------- ⚠️ Critical Logs Channel --------------------
CRITICAL_LOG_CHANNEL_ID = (
    1444997181244444672  # CC Error Logs
)
CRITICAL_LOG_CHANNEL_LIST = [
    1410202143570530375,  # Ghouldengo Bot Logs
    CC_ERROR_LOGS_CHANNEL_ID,
    1375702774771093697,
]


# -------------------- 🌟 Pretty Log --------------------
def pretty_log(
    tag: str = "info",
    message: str = "",
    *,
    label: str = None,
    bot: commands.Bot = None,
    include_trace: bool = True,
):
    """
    Prints a colored log for Shuckle-themed bots with timestamp and emoji.
    Sends critical/error/warn messages to Discord if bot is set.
    """
    prefix = TAGS.get(tag) if tag else ""
    prefix_part = f"[{prefix}] " if prefix else ""
    label_str = f"[{label}] " if label else ""

    # Choose color based on tag
    color = MAIN_COLORS["white"]  # info/default (was blue, now shuckle white)
    if tag in ("warn",):
        color = MAIN_COLORS["yellow"]
    elif tag in ("error",):
        color = MAIN_COLORS["red"]
    elif tag in ("critical",):
        color = MAIN_COLORS["yellow"]

    now = datetime.now().strftime("%H:%M:%S")
    log_message = f"{color}[{now}] {prefix_part}{label_str}{message}{COLOR_RESET}"
    print(log_message)

    # Optionally print traceback
    if include_trace and tag in ("error", "critical"):
        traceback.print_exc()

    # Send to all Discord channels in the list if bot available
    bot_to_use = bot or BOT_INSTANCE
    if bot_to_use and tag in ("critical", "error", "warn"):
        for channel_id in CRITICAL_LOG_CHANNEL_LIST:
            try:
                channel = bot_to_use.get_channel(channel_id)
                if channel:
                    full_message = f"{prefix_part}{label_str}{message}"
                    if include_trace and tag in ("error", "critical"):
                        full_message += f"\n```py\n{traceback.format_exc()}```"
                    if len(full_message) > 2000:
                        full_message = full_message[:1997] + "..."
                    bot_to_use.loop.create_task(channel.send(full_message))
            except Exception:
                print(
                    f"{COLOR_SHUCKLE_RED}[❌ ERROR] Failed to send log to Discord channel {channel_id}{COLOR_RESET}"
                )
                traceback.print_exc()


# -------------------- 🌸 UI Error Logger --------------------
def log_ui_error(
    *,
    error: Exception,
    interaction: discord.Interaction = None,
    label: str = "UI",
    bot: commands.Bot = None,
    include_trace: bool = True,
):
    """Logs UI errors with automatic Discord reporting."""
    location_info = ""
    if interaction:
        user = interaction.user
        location_info = f"User: {user} ({user.id}) | Channel: {interaction.channel} ({interaction.channel_id})"

    error_message = f"UI error occurred. {location_info}".strip()
    now = datetime.now().strftime("%H:%M:%S")

    print(
        f"{COLOR_SHUCKLE_RED}[{now}] [💥 CRITICAL] {label} error: {error_message}{COLOR_RESET}"
    )
    if include_trace:
        traceback.print_exception(type(error), error, error.__traceback__)

    bot_to_use = bot or BOT_INSTANCE

    pretty_log(
        "error",
        error_message,
        label=label,
        bot=bot_to_use,
        include_trace=include_trace,
    )

    if bot_to_use:
        for channel_id in CRITICAL_LOG_CHANNEL_LIST:
            try:
                channel = bot_to_use.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title=f"⚠️ UI Error Logged [{label}]",
                        description=f"{location_info or '*No interaction data*'}",
                        color=0x88DFFF,  # Ghouldengo cyan
                    )
                    if include_trace:
                        trace_text = "".join(
                            traceback.format_exception(
                                type(error), error, error.__traceback__
                            )
                        )
                        if len(trace_text) > 1000:
                            trace_text = trace_text[:1000] + "..."
                        embed.add_field(
                            name="Traceback",
                            value=f"```py\n{trace_text}```",
                            inline=False,
                        )
                    bot_to_use.loop.create_task(channel.send(embed=embed))
            except Exception:
                print(
                    f"{COLOR_SHUCKLE_RED}[❌ ERROR] Failed to send UI error to bot channel {channel_id}{COLOR_RESET}"
                )
                traceback.print_exc()
