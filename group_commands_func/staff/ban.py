import discord
from discord.ext import commands

from utils.db.banned_members_db import upsert_banned_member
from utils.logs.pretty_log import pretty_log
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log

# 🤍────────────────────────────────────────────
#     ⚡ Co-Owner Ban Functionality
# 🤍────────────────────────────────────────────
async def ban_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    user: discord.Member | None = None,
    user_id: str | None = None,
    reason: str | None = None,
):
    """
    Main ban/preban logic.
    Handles banning (or adding to preban), logs the action, and optionally links a report message.
    Works for both members and non-members.
    """
    loader = await pretty_defer(
        interaction=interaction, content="Processing ban...", ephemeral=False
    )
    # Validate input
    if user is None and user_id is None:
        msg = "You must provide either a member or a user ID."
        await loader.error(msg)
        return

    if user_id:
        user_id = int(user_id)

    # Resolve member or fetch global user
    if user is None and user_id is not None:
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            msg = f"No user found with ID {user_id}."
            await loader.error(msg)
            return
        except discord.HTTPException:
            msg = f"Failed to fetch user with ID {user_id}."
            await loader.error(msg)
            return

    target_id = user.id
    target_name = user.name  # username#discriminator
    guild = interaction.guild
    guild_id = guild.id if guild else 0

    # 1️⃣ Add to banned_users table using DB helper
    result, error_msg = await upsert_banned_member(bot, user_id=target_id, user_name=target_name, reason=reason)
    if error_msg:
        await loader.error(f"Failed to record ban in database: {error_msg}")
        return

    # 2️⃣ Perform Discord ban
    if guild:
        try:
            # If user is a Member, ban normally
            if isinstance(user, discord.Member):
                await user.ban(reason=reason or "Ban executed by staff")
            else:
                # Non-members: ban by ID
                await guild.ban(discord.Object(id=target_id), reason=reason)
            pretty_log(
                "success",
                f"💙 Banned {target_name} ({target_id}) from guild. Reason: {reason or 'No reason provided'}",

            )
        except discord.Forbidden:
            msg = f"I don’t have permission to ban {target_name}."
            await loader.error(msg)
            return
        except discord.HTTPException as e:
            msg = f"Failed to ban {target_name}: {e}"
            await loader.error(msg)
            pretty_log(
                "error",
                f"❌ Failed to ban {target_name} ({target_id}): {e}",

            )
            return

    # 3️⃣ Log action to report channel
    # fetch target user
    target_user = await bot.fetch_user(target_id)
    target_display = (
        target_user.mention if target_user else f"{target_name} ({target_id})"
    )
    embed = discord.Embed(
        title="Server Banned",
        color=discord.Color.red(),
    )
    embed.add_field(name="Banned By", value=interaction.user.mention, inline=False)
    embed.add_field(name="User", value=target_display, inline=False)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)

    thumbnail_url = (
        target_user.display_avatar.url
        if target_user and target_user.display_avatar
        else None
    )
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    footer_text = f"User ID: {target_id}"
    embed.set_footer(
        text=footer_text, icon_url=interaction.guild.icon.url if guild else None
    )
    await send_server_log(bot, embed=embed)
    # 4️⃣ Feedback to command executor
    await loader.success(
        content=f"{target_name} has been added to the banned list.",
        embed=embed,
    )
