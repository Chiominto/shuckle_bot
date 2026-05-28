from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.permissions import MEMBER_PERMISSIONS
from utils.db.celestial_members_db import get_registered_personal_channel
from utils.functions.cooldown_tracker import check_cooldown, update_cooldown
from utils.functions.design_embed import design_embed, format_bulletin_desc
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log
from utils.functions.pretty_defer import pretty_defer

async def channel_invite_func(
    bot: commands.Bot, interaction: discord.Interaction, member: discord.Member
):
    # 🕒 Cooldown check
    cooldown_result = check_cooldown(
        user_id=interaction.user.id, channel_id=interaction.channel.id, seconds=15
    )
    if cooldown_result:
        await interaction.response.send_message(
            f"⏳ Please wait {cooldown_result} seconds before using this command again.",
            ephemeral=True,
        )
        return
    loader = await pretty_defer(interaction=interaction, content="Inviting member to your channel...", ephemeral=False)
    command_user = interaction.user
    # 🏠 Get personal channel
    channel_id = await get_registered_personal_channel(
        bot=bot, user_id=interaction.user.id
    )
    if not channel_id:
        await loader.error(content="You don't have a registered personal channel yet.")
        pretty_log(
            "critical",
            f"{interaction.user} tried to invite {member} but has no registered channel.",
        )
        return

    # 🛰️ Fetch channel
    channel = bot.get_channel(channel_id)
    if not channel:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            await loader.error(content="❌ Your personal channel could not be found.")
            pretty_log(
                "critical",
                f"{interaction.user} channel ({channel_id}) not found when inviting {member}.",
            )
            return
        except discord.Forbidden:
            await loader.error(content="❌ I don’t have permission to access your channel.")
            pretty_log(
                "critical",
                f"{interaction.user} channel ({channel_id}) forbidden when inviting {member}.",
            )
            return

        except Exception as e:
            await loader.error(content=f"⚠️ Failed to retrieve your channel: `{e}`")
            pretty_log(
                "error",
                f"Error fetching {interaction.user}'s channel ({channel_id}) for {member}: {e}",
            )
            return

    if not isinstance(channel, discord.TextChannel):
        await loader.error(content="❌ Your personal channel is invalid.")
        pretty_log(
            "critical",
            f"{interaction.user}'s channel ({channel_id}) is not a TextChannel.",
        )
        return

    # 🔍 Check if already invited
    current_perms = channel.overwrites_for(member)
    if current_perms.read_messages:
        await loader.error(content=f"{member.mention} is already added to your channel {channel.mention}!")
        return

    # 🔐 Update permissions
    NEW_MEMBER_PERMISSION = MEMBER_PERMISSIONS
    try:
        await channel.set_permissions(
            member, overwrite=discord.PermissionOverwrite(**NEW_MEMBER_PERMISSION)
        )
    except discord.Forbidden:
        await loader.error(content="❌ I don’t have permission to edit channel permissions.")
        pretty_log(
            "critical",
            f"Forbidden: {interaction.user} could not add {member} to {channel.name}.",
        )
        return
    except Exception as e:
        await loader.error(content=f"⚠️ Failed to update permissions: `{e}`")
        pretty_log(
            "error",
            f"Error adding {member} to {channel.name} by {interaction.user}: {e}",
        )
        return

    # ✅ Confirmation embed
    confirm_embed = discord.Embed(
        title="👥 Member Added!",
        description=f"You have successfully added {member.mention} to your channel {channel.mention}!",
        color=discord.Color.blurple(),
        timestamp=datetime.now(),
    )
    confirm_embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    confirm_embed.set_thumbnail(url=member.display_avatar.url)
    await loader.success(content=f"{member.mention} has been added to your channel {channel.mention}!", embed=confirm_embed)
    # 📝 Log to server
    desc = format_bulletin_desc(
        "Channel Owner",
        interaction.user.mention,
        "Member Added",
        member.mention,
        "Channel",
        channel.mention,
    )
    log_embed = discord.Embed(
        title="👥 Member Added!",
        description=desc,
    )
    log_embed = design_embed(
        embed=log_embed,
        user=interaction.user,
        thumbnail_url=member.display_avatar.url,
        color="blue",
    )

    await send_server_log(bot=bot, embed=log_embed)

    # ⏱️ Update cooldown
    update_cooldown(interaction.user.id, interaction.channel.id)

    # 🌟 Pretty log success
    pretty_log(
        "ready",
        f"{interaction.user} successfully added {member} to {channel.name}",
    )
