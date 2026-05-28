# 🌸 channel_remove.py — Remove someone from personal channel 💫
from datetime import datetime

import discord
from discord.ext import commands

from utils.db.celestial_members_db import get_registered_personal_channel
from utils.functions.cooldown_tracker import check_cooldown, update_cooldown
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log


async def channel_remove_func(
    bot: commands.Bot, interaction: discord.Interaction, member: discord.Member
):
    # ─────────────────────────────────────────────
    # 🌟 Initialize Loader
    # ─────────────────────────────────────────────
    loader = await pretty_defer(
        interaction=interaction, content="Processing Removal...", ephemeral=False
    )
    # Check if they are tryin to remove themselves from their channel
    if member.id == interaction.user.id:
        await loader.error(content="You cannot remove yourself from your own channel!")
        return

    # ─────────────────────────────────────────────
    #  🌟 Step 1: Check cooldown
    # ─────────────────────────────────────────────
    cooldown_msg = check_cooldown(
        interaction.user.id, interaction.channel.id, seconds=15
    )
    if cooldown_msg:
        await loader.error(content=cooldown_msg)
        return

    # ─────────────────────────────────────────────
    #  🌟 Step 2: Fetch personal channel
    # ─────────────────────────────────────────────
    channel_id = await get_registered_personal_channel(
        bot=bot, user_id=interaction.user.id
    )
    if not channel_id:
        await loader.error(
            content="📭 You don't have a registered personal channel yet."
        )
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            await loader.error(content="Your personal channel could not be found.")
            pretty_log(
                "critical",
                f"{interaction.user}'s channel ({channel_id}) not found during remove command.",
            )
            return
        except discord.Forbidden:
            await loader.error(
                content="I don't have permission to access your personal channel.",
            )
            pretty_log(
                "critical",
                f"Forbidden fetching {interaction.user}'s channel ({channel_id}) during remove command.",
            )
            return
        except discord.HTTPException as e:
            await loader.error(content="Failed to fetch your personal channel.")
            pretty_log(
                "error",
                f"HTTPException fetching {interaction.user}'s channel ({channel_id}) during remove command: {e}",
            )
            return

    if not isinstance(channel, discord.TextChannel):
        await loader.error(content="Your personal channel is invalid.")
        return

    # ─────────────────────────────────────────────
    #  🌟 Step 3: Check member’s permissions
    # ─────────────────────────────────────────────
    overwrite = channel.overwrites_for(member)
    if overwrite.is_empty():
        await loader.error(content=f"{member.display_name} is not in your channel.")
        return

    # ─────────────────────────────────────────────
    #  🌟 Step 4: Remove member permissions
    # ─────────────────────────────────────────────
    try:
        await channel.set_permissions(member, overwrite=None)
    except Exception as e:
        await loader.error(
            content="There was an error removing the member from your channel."
        )
        pretty_log(
            "❌ ERROR",
            f"Failed to remove {member} from {channel.name}: {e}",
        )
        return

    # 🌸 Success log
    pretty_log(
        "💙 CHANNEL",
        f"Removed {member} from {channel.name}",
    )

    # ─────────────────────────────────────────────
    #  🌟 Step 5: Confirmation embed for user
    # ─────────────────────────────────────────────
    confirm_embed = discord.Embed(
        title="👋 Member Removed!",
        description=f"You have successfully removed {member.mention} from your channel {channel.mention}.",
        color=discord.Color.red(),
        timestamp=datetime.now(),
    )
    confirm_embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    confirm_embed.set_thumbnail(url=member.display_avatar.url)
    await loader.success(embed=confirm_embed, content="")

    # ─────────────────────────────────────────────
    #  🌟 Step 6: Staff log embed
    # ─────────────────────────────────────────────
    log_embed = discord.Embed(
        title="👋 Member Removed!",
        description=f"{interaction.user.mention} removed {member.mention} from their channel {channel.mention}.",
        color=discord.Color.red(),
        timestamp=datetime.now(),
    )
    log_embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    log_embed.set_thumbnail(url=member.display_avatar.url)
    await send_server_log(bot=bot, embed=log_embed)

    # ─────────────────────────────────────────────
    #  🌟 Step 7: Update cooldown
    # ─────────────────────────────────────────────
    update_cooldown(interaction.user.id, interaction.channel.id)
