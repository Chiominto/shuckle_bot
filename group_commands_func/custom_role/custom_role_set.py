from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_TEXT_CHANNELS,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.db.custom_roles_db_func import (
    fetch_custom_role_id,
    get_role_by_id,
    remove_role,
    remove_role_by_role_id,
    update_gradient_role,
    upsert_role,
)
from utils.logs.pretty_log import pretty_log

LOG_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.server_logs
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_webhook




# 🍭──────────────────────────────
#   🎀 Slash Command: Set Custom Role
# 🍭──────────────────────────────
async def custom_role_set_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    role: discord.Role,
):
    """Set a member's custom role to the specified role."""
    guild = interaction.guild

    # Check if user is a staff member
    user = interaction.user
    # Initialize loader
    loader = await pretty_defer(
        interaction=interaction,
        content="Setting the custom role...",
        ephemeral=False,
    )
    # Check if member has a custom role
    custom_role_id = await fetch_custom_role_id(bot, member)
    if custom_role_id:
        custom_role = guild.get_role(custom_role_id)
        if custom_role_id and custom_role:
            msg = f"{member.display_name} already has a custom role: {custom_role.mention}."
            await loader.error(content=msg)
            return
        if custom_role_id and not custom_role:
            # Delete the old role from the database
            await remove_role(bot, member)
            pretty_log(
                "success",
                f"Removed non-existent role from database for user {member.display_name}.",
            )

    # Check if the inputted role already belongs to another user
    user_id_with_role = await get_role_by_id(bot, role.id)
    if user_id_with_role:
        user_with_role = guild.get_member(user_id_with_role["user_id"])
        if user_with_role:
            pretty_log(
                "info",
                f"Role {role.name} is already assigned to {user_with_role.display_name}.",
            )
        else:
            # The role is in the database but the user is not found in the guild
            await remove_role_by_role_id(bot, role_id=role.id)
            # Log the cleanup action
            pretty_log(
                "success",
                f"Removed role {role.name} from database as it was assigned to a non-existent user.",
            )

    # Check if role position is 90 or higher
    reference_role = guild.get_role(CELESTIAL_ROLES.personal_role_divider)
    position = reference_role.position if reference_role else 54
    if role.position < position:
        # Move the role to position 90
        try:
            await role.edit(
                position=position, reason="Moving custom role to position 90."
            )
            pretty_log("success", f"Moved role {role.name} to position {position}.")
        except discord.Forbidden:
            msg = "I don't have permission to move that role."
            await loader.error(content=msg)
            return
        except discord.HTTPException as e:
            msg = f"Failed to move role due to an error: {e}"
            await loader.error(content=msg)
            return

    # Assign the role to the member
    try:
        await member.add_roles(role, reason="Custom role assigned by staff.")
        pretty_log("success", f"Assigned role {role.name} to {member.display_name}.")
        await upsert_role(bot, member, role.id)
        # Build confirmation embed
        embed = discord.Embed(
            title="✅ Custom Role Assigned!",
            description=f"**Member:** {member.mention}\n**Role:** {role.mention}\n**Assigned by:** {user.mention}",
            color=role.color,
            timestamp=datetime.now(),
        )
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        await loader.success(embed=embed, content="")

        # Send a log embed to your server log channel
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await send_webhook(
                bot=bot,
                channel=log_channel,
                embed=embed,
            )
    except discord.Forbidden:

        msg = "I don't have permission to assign that role."
        await loader.error(content=msg)
        return
    except discord.HTTPException as e:
        msg = f"Failed to assign role due to an error: {e}"
        await loader.error(content=msg)
        return
