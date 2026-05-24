from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_ROLES, CELESTIAL_TEXT_CHANNELS
from utils.db.temp_roles_db import delete_temp_role
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log
from utils.functions.server_booster_handler import handle_server_booster_role_remove
from utils.functions.webhook_func import send_webhook

TEMP_ROLE_IDS = [
    CELESTIAL_ROLES.coin_saver,
    CELESTIAL_ROLES.tip_jar_titan,
    CELESTIAL_ROLES.top_catcher,
]


# 🍭──────────────────────────────
#   🎀 Event: On Role Remove
# 🍭──────────────────────────────
async def handle_role_remove(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    """Handle role removal events."""
    role_id = role.id

    # ————————————————————————————————
    # 🩵 Temp Role Removed
    # ————————————————————————————————
    if role_id in TEMP_ROLE_IDS:
        user_id = member.id
        user_name = member.name
        role_name = role.name
        await delete_temp_role(bot, user_id, role_id)
        pretty_log(
            "info", f"Deleted temp role {role_name} for user {user_name} ({user_id})"
        )
    # ————————————————————————————————
    # 🩵 Server Booster Role Remove
    # ————————————————————————————————
    if role_id == CELESTIAL_ROLES.server_booster:
        await handle_server_booster_role_remove(bot, member)

    # ————————————————————————————————
    # 🩵 Role Removal Logging
    # ————————————————————————————————
    embed = discord.Embed(
        title="🗑️ Role Removed",
        description=f"**Member:** {member.mention}\n**Role:** {role.mention} ({role.name})",
        color=discord.Color.red(),
        timestamp=datetime.now(),
    )
    embed.set_thumbnail(url=role.icon.url if role.icon else member.display_avatar.url)
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    embed.set_footer(
        text=f"User ID: {member.id} | Role ID: {role.id}",
        icon_url=member.guild.icon.url if member.guild.icon else None,
    )
    role_log_channel = member.guild.get_channel(CELESTIAL_TEXT_CHANNELS.role_logs)
    await send_webhook(
        bot=bot,
        channel=role_log_channel,
        embed=embed,
    )
