# 🟪────────────────────────────────────────────
#   Battle Tower Reminders 🏰💜
# 🟪────────────────────────────────────────────

from datetime import datetime, timedelta

import discord
import pytz

from constants.aesthetics import Emojis
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
)

from utils.functions.cleanup_first_match import cleanup_first_match
from utils.logs.pretty_log import pretty_log
from utils.functions.button_func import toggle_role_button_func
from constants.aesthetics import *

# 🛠️ Scheduler placeholder (import in main scheduler file)
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# scheduler = AsyncIOScheduler(timezone="Asia/Manila")

# ─────────────────────────────────────────────
# 🐾 Constants
# ─────────────────────────────────────────────

BATTLE_WAVE_DAYS = [0, 2, 4]  # Monday=0, Wednesday=2, Friday=4
REMINDER_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.bumps
BATTLE_ROLE_MENTION = f"<@&{CELESTIAL_ROLES.battle_tower}>"

# ─────────────────────────────────────────────
# 🐾 Helper: Calculate time until next wave
# ─────────────────────────────────────────────


def next_wave_delta(now=None):
    now = now or datetime.now(pytz.timezone("Asia/Manila"))
    today_weekday = now.weekday()

    # Find next wave day strictly after today
    next_days = [
        (d - today_weekday) % 7
        for d in BATTLE_WAVE_DAYS
        if (d - today_weekday) % 7 != 0
    ]
    days_until_next = min(next_days) if next_days else 7
    next_wave = now + timedelta(days=days_until_next)
    next_wave = next_wave.replace(hour=8, minute=0, second=0, microsecond=0)

    return next_wave - now


# ─────────────────────────────────────────────
# 🐾 Send embed helper
# ─────────────────────────────────────────────
async def send_embed(
    bot,
    embed: discord.Embed,
    content,
    phrase: str,
    view=None,
):

    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if not channel:
        channel = await bot.fetch_channel(REMINDER_CHANNEL_ID)

    # get guild and icon
    guild = channel.guild
    icon_url = guild.icon.url if guild.icon else None
    embed.set_footer(
        text="Battle now using ;battle npc battletower!", icon_url=icon_url
    )

    await cleanup_first_match(
        bot=bot, channel=channel, phrase=phrase, component="title"
    )

    await channel.send(embed=embed, content=content, view=view)


# ─────────────────────────────────────────────
# 🐾 Start-of-wave reminder
# ─────────────────────────────────────────────
async def send_battle_tower_start_reminder(bot):
    delta = next_wave_delta()
    days, seconds = delta.days, delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    embed_title = "🏰 Battle Tower Wave Started!"
    embed = discord.Embed(
        title=embed_title,
        description=(
            "The Battle Tower is now open! Test your skills and reach new heights!\n\n"
            f"Next wave in: {days} days, {hours} hours, {minutes} minutes"
        ),
        color=DEFAULT_EMBED_COLOR,
    )
    embed.set_footer(text="Register now using ;battletower register!")
    content = f"{BATTLE_ROLE_MENTION} New Battle Tower Wave!"
    # Attach the persistent toggle button
    view = BattleTowerPingButton()

    await send_embed(
        bot=bot, embed=embed, content=content, view=view, phrase=embed_title
    )

# ─────────────────────────────────────────────
# 🐾 Closing reminder
# ─────────────────────────────────────────────
async def send_battle_tower_closing_reminder(bot):
    embed_title = "⏰ Battle Tower Closing Soon!"
    embed = discord.Embed(
        title=embed_title,
        description="Don’t forget to update your progress!",
        color=0xFFAA88,
    )
    embed.set_thumbnail(url=Thumbnails.BATTLE_TOWER)

    content = f"{BATTLE_ROLE_MENTION} 10 Minutes before Battle Tower Ends!"
    view = BattleTowerPingButton()
    await send_embed(
        bot=bot, embed=embed, content=content, view=view, phrase=embed_title
    )


# 🟪────────────────────────────────────────────
#   Battle Tower Role Toggle Button 🏰💜
# 🟪────────────────────────────────────────────
# Persistent button for Battle Tower ping
class BattleTowerPingButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view, never times out
        self.add_item(BattleTowerPing())


class BattleTowerPing(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Toggle Battle Ping",
            style=discord.ButtonStyle.primary,
            custom_id="battle_ping_toggle",  # Unique custom ID for persistence
        )

    async def callback(self, interaction: discord.Interaction):
        await toggle_role_button_func(
            interaction=interaction, role_id=CELESTIAL_ROLES.battle_tower, label="Battle Ping"
        )
