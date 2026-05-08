from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.db.custom_roles_db_func import (
    fetch_custom_role_id,
    update_gradient_role,
    upsert_role,
)
from utils.logs.pretty_log import pretty_log

LOG_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.server_logs
REFERENCE_ROLE_ID = CELESTIAL_ROLES.personal_role_divider

from utils.functions.webhook_func import send_webhook


# 🍭──────────────────────────────
#   🎀 Slash Command: Edit Custom Role
# 🍭──────────────────────────────
async def custom_role_edit_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    new_role_name: str = None,
    color_type: str = None,
):
    """Edit a member's custom role with a new name and/or color type."""
    color_type = color_type.lower() if color_type else None
    if not new_role_name and not color_type:
        await interaction.response.send_message(
            "You must provide at least a new role name or a color type to edit.",
            ephemeral=True,
        )
        return

    # Check if user has a custom role
    user = interaction.user
    guild = interaction.guild
    custom_role_id = await fetch_custom_role_id(bot, user)
    if not custom_role_id:
        await interaction.response.send_message(
            "You don't have a custom role to edit.", ephemeral=True
        )
        return
    custom_role = guild.get_role(custom_role_id)
    if not custom_role:
        await interaction.response.send_message(
            "Your custom role was not found in the server. Please contact a staff member.",
            ephemeral=True,
        )
        return

    # Check if custom role is below the position variable, if below move above
    custom_role_position = custom_role.position
    top_grinder_role = guild.get_role(CELESTIAL_ROLES.top_catcher)
    top_grinder_role_position = top_grinder_role.position
    reference_role = guild.get_role(REFERENCE_ROLE_ID)
    reference_position = reference_role.position

    if custom_role_position < top_grinder_role_position:
        new_position = reference_position - 1
        try:
            await custom_role.edit(
                position=new_position,
                reason="Ensuring custom role is below reference role",
            )
            pretty_log(
                "info",
                f"Moved role {custom_role.name} ({custom_role.id}) below reference role.",
                label="CUSTOM ROLE",
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Could not move role position: {e}",
            )

    # Check if they have inputted a color type
    if color_type and color_type == "solid":
        modal = SolidColorModal(bot, custom_role, new_role_name)
        await interaction.response.send_modal(modal)
    elif color_type and color_type == "gradient":
        modal = GradientColorModal(bot, custom_role, new_role_name)
        await interaction.response.send_modal(modal)

    # Check if user only has inputted a new role name
    if new_role_name and not color_type:
        old_name = custom_role.name
        try:
            await custom_role.edit(
                name=new_role_name, reason="Updated via edit command"
            )
            pretty_log(
                "info",
                f"Role name updated: {old_name} ({custom_role.id}) ➜ {new_role_name}",
                label="CUSTOM ROLE",
            )
            await interaction.response.send_message(
                f"✅ Your role name has been updated from `{old_name}` to `{new_role_name}`.",
                ephemeral=True,
            )

            # Log the change
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(
                    title="🎀 Custom Role Name Updated",
                    description=(
                        f"**Member:** {interaction.user.mention}\n"
                        f"**Role:** {custom_role.mention}\n"
                        f"**Old Name:** `{old_name}`\n"
                        f"**New Name:** `{new_role_name}`"
                    ),
                    color=custom_role.color,
                    timestamp=datetime.now(),
                )
                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url,
                )
                embed.set_thumbnail(
                    url=(
                        custom_role.icon.url
                        if custom_role.icon
                        else interaction.user.display_avatar.url
                    )
                )
                embed.set_footer(text=f"User ID: {interaction.user.id}")
                await send_webhook(
                    bot=bot,
                    channel=log_channel,
                    embed=embed,
                )

        except Exception as e:
            pretty_log(
                "error",
                f"Could not edit role name: {e}",
            )
            await interaction.response.send_message(
                "⚠️ Failed to update role name.", ephemeral=True
            )


# 🌸────────────────────────────────────────────
#           🎨 Modal: Solid Color Input
# 🌸────────────────────────────────────────────
class SolidColorModal(discord.ui.Modal, title="🎨 Enter Solid Color"):
    def __init__(self, bot, role, name):
        super().__init__()
        self.bot = bot
        self.role = role
        self.name = name

        self.color_input = discord.ui.TextInput(
            label="Hex Color (e.g. #D8B4F8)", placeholder="#D8B4F8", required=True
        )
        self.add_item(self.color_input)

    #
    async def on_submit(self, interaction: discord.Interaction):
        pretty_log(
            "info",
            f"Solid color submitted: {self.color_input.value}",
        )

        updates = {}
        changes = [
            f"**Member:** {interaction.user.mention}",
            f"**Role:** {self.role.mention}",
        ]

        if self.name and self.name != self.role.name:
            updates["name"] = self.name
            changes.append(f"**Role Name:** `{self.role.name}` 🔷➜ `{self.name}`")

        try:
            hex_value = self.color_input.value.strip().lstrip("#")
            old_color = str(self.role.color)
            new_color = f"#{hex_value.upper()}"
            updates["color"] = discord.Color(int(hex_value, 16))
            changes.append(f"**Role Color:** `{old_color}` 🔷➜ `{new_color}`")
        except ValueError:
            return await interaction.response.send_message(
                "❌ Invalid hex color format!", ephemeral=True
            )

        try:
            await self.role.edit(**updates, reason="Updated via solid modal")
            pretty_log(
                "info",
                f"Role updated: {self.role.name} ({self.role.id})",
                label="CUSTOM ROLE",
            )
            # Send confirmation message
            embed = discord.Embed(
                title="🎀 Your Custom Role Was Updated! 💖",
                description="\n".join(changes),
                color=self.role.color,
            )
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            thumbnail_url = (
                self.role.icon.url
                if self.role.icon
                else interaction.user.display_avatar.url
            )
            embed.set_thumbnail(url=thumbnail_url)
            await interaction.response.send_message(embed=embed)

            # Log the change
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = embed.copy()
                log_embed.title = "🎀 Custom Role Updated"
                log_embed.set_footer(text=f"User ID: {interaction.user.id}")
                log_embed.timestamp = datetime.now()
                await send_webhook(
                    bot=self.bot,
                    channel=log_channel,
                    embed=log_embed,
                )

        except Exception as e:
            pretty_log(
                "error",
                f"Could not edit role: {e}",
            )
            return await interaction.response.send_message(
                "⚠️ Failed to update role.", ephemeral=True
            )


# 🌸────────────────────────────────────────────
#         🌈 Modal: Gradient Color Input
# 🌸────────────────────────────────────────────
class GradientColorModal(discord.ui.Modal, title="🌈 Enter Gradient Colors"):
    def __init__(self, bot, role, name):
        super().__init__()
        self.bot = bot
        self.role = role
        self.name = name

        self.start_color = discord.ui.TextInput(
            label="Start Color (Hex)", placeholder="#D8B4F8", required=True
        )
        self.end_color = discord.ui.TextInput(
            label="End Color (Hex)", placeholder="#F9C2D7", required=True
        )
        self.add_item(self.start_color)
        self.add_item(self.end_color)

    async def on_submit(self, interaction: discord.Interaction):
        pretty_log(
            "info",
            f"Gradient chosen: {self.start_color.value} → {self.end_color.value}",
        )

        changes = [
            f"**Member:** {interaction.user.mention}",
            f"**Role:** {self.role.mention}",
        ]

        if self.name and self.name != self.role.name:
            changes.append(f"**Role Name:** `{self.role.name}` 🔷➜ `{self.name}`")

        changes.append(
            f"**Role Color:** `{self.start_color.value}` & `{self.end_color.value}` 💖"
        )

        try:
            success = await update_gradient_role(
                self.bot,
                interaction.guild.id,
                self.role.id,
                primarycolor=self.start_color.value,
                secondarycolor=self.end_color.value,
                name=self.name if self.name and self.name != self.role.name else None,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to update gradient role via API: {e}",
            )
            return await interaction.response.send_message(
                "⚠️ Failed to update role gradient via API.", ephemeral=True
            )

        embed = discord.Embed(
            title="🎀 Your Custom Role Was Updated!",
            description="\n".join(changes),
            color=self.role.color,
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.set_thumbnail(
            url=(
                self.role.icon.url
                if self.role.icon
                else interaction.user.display_avatar.url
            )
        )
        await interaction.response.send_message(embed=embed)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = embed.copy()
            log_embed.title = "🎀 Custom Role Updated"
            log_embed.set_footer(text=f"User ID: {interaction.user.id}")
            log_embed.timestamp = datetime.now()
            await send_webhook(
                bot=self.bot,
                channel=log_channel,
                embed=log_embed,
            )
