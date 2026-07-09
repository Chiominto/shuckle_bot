from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_ROLES, CELESTIAL_TEXT_CHANNELS
from constants.permissions import *
from utils.db.celestial_members_db import get_registered_personal_channel
from utils.functions.design_embed import design_embed
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log


# 💙────────────────────────────────────────────
#       Channel Unprivate Function (ENHANCED)
# 💙────────────────────────────────────────────
async def channel_unprivate_func(bot: commands.Bot, interaction: discord.Interaction):
    """🔓 Make your personal channel unprivate by syncing with category and preserving member permissions."""

    # Pretty Defer
    handler = await pretty_defer(
        interaction=interaction,
        content="Updating channel permissions...",
        ephemeral=True,
    )
    guild = interaction.guild
    user = interaction.user

    # Get the server constants
    clan_member_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    log_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)

    channel = interaction.channel

    # Check if its their channel
    member_channel_id = await get_registered_personal_channel(
        bot=bot, user_id=interaction.user.id
    )

    if not member_channel_id:
        msg = "You don't have a registered personal channel yet."
        await handler.error(content=msg)
        pretty_log(
            "critical",
            f"{interaction.user} tried to unprivate the channel but has no registered channel.",
        )
        return
    if interaction.channel.id != member_channel_id:
        msg = "You can only unprivate your own personal channel."
        await handler.error(content=msg)
        pretty_log(
            "critical",
            f"{interaction.user} tried to unprivate channel but is not in their personal channel.",
        )
        return

    # ✅ NEW CHECK: See if channel is already unprivate
    clan_member_overwrite = channel.overwrites_for(clan_member_role)

    # Check if Clan member role already has access (channel is not private)
    if not clan_member_overwrite.is_empty():
        msg = "🔓 Your channel is already unprivate! Clan members can see it."
        await handler.error(content=msg)
        pretty_log(
            "info",
            f"{interaction.user} tried to unprivate channel but it's already unprivate.",
        )
        return

    # Update permissions
    try:
        # ✅ STEP 1: Store custom member permissions before syncing
        custom_members = []

        for target, overwrite in channel.overwrites.items():
            # Check if it's a member (not a role) and not the channel owner
            if isinstance(target, discord.Member) and target.id != user.id:
                custom_members.append(target)
                pretty_log(
                    "info",
                    f"Found custom member in {channel.name}: {target.display_name}",
                )

        restored_count = 0

        # ✅ STEP 2: If there are no custom members, just sync with category.
        if not custom_members:
            await channel.edit(sync_permissions=True)
            pretty_log(
                "info",
                f"Synced {channel.name} with category permissions (no custom members to restore)",
            )
        else:
            # ✅ STEP 2: Sync with category permissions (removes custom overwrites)
            await channel.edit(sync_permissions=True)
            pretty_log(
                "info",
                f"Synced {channel.name} with category permissions",
            )

            # ✅ STEP 3: Re-add the channel owner's permissions
            await channel.set_permissions(
                user, overwrite=discord.PermissionOverwrite(**VIP_MEMBER_PERMISSIONS)
            )

            # ✅ STEP 4: Re-add custom members with MEMBER_PERMISSIONS
            for member in custom_members:
                try:
                    await channel.set_permissions(
                        member,
                        overwrite=discord.PermissionOverwrite(**MEMBER_PERMISSIONS),
                    )
                    restored_count += 1
                    pretty_log(
                        "info",
                        f"Restored permissions for {member.display_name} in {channel.name}",
                    )
                except Exception as e:
                    pretty_log(
                        "warn",
                        f"Failed to restore permissions for {member.display_name}: {e}",
                    )

        # Build success message
        base_msg = (
            f"Your channel {channel.mention} is now open again to other Clan members."
        )
        if restored_count > 0:
            base_msg += f"\n\n**Restored access for {restored_count} custom member(s)** who you had previously added."

        embed = discord.Embed(
            title=f"🔓 Channel Unprivate",
            description=base_msg,
        )

        embed = design_embed(user=user, embed=embed)
        await handler.success(content="", embed=embed)

        pretty_log(
            "info",
            f"{interaction.user} made their channel unprivate. Restored {restored_count} custom members.",
        )

        if log_channel:
            log_description = f"**- Member:** {interaction.user.mention}\n**- Channel:** {channel.mention}"
            if restored_count > 0:
                member_names = [
                    m.display_name for m in custom_members[:3]
                ]  # Show first 3
                if len(custom_members) > 3:
                    member_names.append(f"and {len(custom_members) - 3} more...")
                log_description += (
                    f"\n**- Restored Members:** {', '.join(member_names)}"
                )

            log_embed = discord.Embed(
                title="🔓 Channel Unprivate",
                description=log_description,
                timestamp=datetime.now(),
            )
            log_embed = design_embed(user=user, embed=log_embed)
            await send_webhook(
                bot=bot,
                channel=log_channel,
                embed=log_embed,
            )
            pretty_log(
                "info",
                f"Channel unprivate action logged in {log_channel} ({log_channel.id})",
            )
        else:
            pretty_log(
                "warn",
                f"⚠️ Log channel with ID {CELESTIAL_TEXT_CHANNELS.server_logs} not found.",
            )

    except Exception as e:
        msg = f"Failed to update permissions: `{e}`"
        await handler.error(content=msg)
        pretty_log(
            "error",
            f"Error updating {interaction.user}'s channel ({channel.id}) permissions: {e}",
        )
        return
