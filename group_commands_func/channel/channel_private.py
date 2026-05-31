from datetime import datetime

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_ROLES
from constants.permissions import MEMBER_PERMISSIONS
from utils.db.celestial_members_db import get_registered_personal_channel
from utils.functions.design_embed import design_embed
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log


# Channel Private Function
async def channel_private_func(bot: commands.Bot, interaction: discord.Interaction):
    """Make your personal channel private to only you and staff."""

    handler = await pretty_defer(
        interaction=interaction,
        content="Updating channel permissions...",
        ephemeral=True,
    )
    guild = interaction.guild
    user = interaction.user
    channel = interaction.channel

    member_channel_id = await get_registered_personal_channel(
        bot=bot, user_id=interaction.user.id
    )

    if not member_channel_id:
        msg = "You don't have a registered personal channel yet."
        await handler.error(content=msg)
        pretty_log(
            "critical",
            f"{interaction.user} tried to make channel private but has no registered channel.",
        )
        return

    if interaction.channel.id != member_channel_id:
        msg = "You can only make your own personal channel private."
        await handler.error(content=msg)
        pretty_log(
            "critical",
            f"{interaction.user} tried to make channel private but is not in their personal channel.",
        )
        return

    clan_member_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    if not clan_member_role:
        msg = "Clan member role not found. Please contact staff."
        await handler.error(content=msg)
        pretty_log(
            "error",
            f"Clan member role not found when {interaction.user} tried to make channel private.",
        )
        return

    clan_member_overwrite = channel.overwrites_for(clan_member_role)
    if clan_member_overwrite.is_empty():
        msg = "Your channel is already private. Other Clan members can't see it."
        await handler.error(content=msg)
        pretty_log(
            "info",
            f"{interaction.user} tried to make channel private but it's already private.",
        )
        return

    try:
        await channel.set_permissions(clan_member_role, overwrite=None)
        await channel.set_permissions(
            user,
            overwrite=discord.PermissionOverwrite(**MEMBER_PERMISSIONS),
        )

        embed = discord.Embed(
            title="Channel Made Private",
            description=(
                f"Your channel {channel.mention} is now private to only you, "
                "the staff, and the people you've added here."
            ),
        )
        footer_text = "Other Clan members can't see this channel now."
        embed = design_embed(user=user, embed=embed, footer_text=footer_text)
        await handler.success(content="", embed=embed)

        pretty_log(
            "info",
            f"{interaction.user} made their channel private.",
        )

        log_embed = discord.Embed(
            title="Channel Made Private",
            description=(
                f"**- Member:** {interaction.user.mention}\n"
                f"- **Channel:** {channel.mention}"
            ),
            timestamp=datetime.now(),
        )
        log_embed = design_embed(user=user, embed=log_embed)
        await send_server_log(bot=bot, embed=log_embed)

    except Exception as e:
        msg = f"Failed to update permissions: `{e}`"
        await handler.error(content=msg)
        pretty_log(
            "error",
            f"Error updating {interaction.user}'s channel ({channel.id}) permissions: {e}",
        )
        return
