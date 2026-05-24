from datetime import datetime

import discord
from discord.ext import commands
from constants.celestial_constants import CELESTIAL_ROLES, CELESTIAL_TEXT_CHANNELS

from utils.logs.pretty_log import pretty_log
from utils.db.temp_roles_db import upsert_temp_role
from .on_role_remove import TEMP_ROLE_IDS
from utils.functions.webhook_func import send_webhook
from utils.functions.webhook_func import send_server_log
from utils.functions.server_booster_handler import handle_server_booster_role_add

# 🍭──────────────────────────────
#   🎀 Event: On Role Add
# 🍭──────────────────────────────
async def handle_role_add(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    """Handle role addition events."""
    role_id = role.id

    # ————————————————————————————————
    # 🩵 Temp Role Add
    # ————————————————————————————————
    if role_id in TEMP_ROLE_IDS:
        user_id = member.id
        user_name = member.name
        role_name = role.name
        await upsert_temp_role(bot, user_id, user_name, role_id, role_name)
        pretty_log(
            "info",
            f"Upserted temp role {role_name} for user {user_name} ({user_id})"
        )
    # ————————————————————————————————
    # 🩵 Server Booster Role Add
    # ————————————————————————————————
    if role_id == CELESTIAL_ROLES.server_booster:
        await handle_server_booster_role_add(bot, member)

    # ————————————————————————————————
    # 🩵 Role Add Logging
    # ————————————————————————————————
    embed = discord.Embed(
        title="✅ Role Added",
        description=f"**Member:** {member.mention}\n**Role:** {role.mention} ({role.name})",
        color=discord.Color.green(),
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
