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


# 🍭──────────────────────────────
#   🎀 Slash Command: Create Custom Role
# 🍭──────────────────────────────
async def custom_role_create_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    role_name: str,
    color_type: str,
):
    """Create a custom role for the member with the specified name and color type."""
    color_type = color_type.lower()
    guild = interaction.guild

    # Check if user is a staff member
    user = interaction.user
    staff_role = guild.get_role(CELESTIAL_ROLES.staff)
    server_booster_role = guild.get_role(CELESTIAL_ROLES.server_booster)
    # Check if user has staff or booster role
    if staff_role not in user.roles and server_booster_role not in user.roles:
        await interaction.response.send_message(
            "Only staff members and server boosters can create custom roles.",
            ephemeral=True,
        )
        return
    
    # Check if member already has a custom role
    custom_role_id = await fetch_custom_role_id(bot, member)
    if custom_role_id:
        await interaction.response.send_message(
            f"{member.display_name} already has a custom role.", ephemeral=True
        )
        return

    # Open the appropriate modal based on color type
    if color_type == "solid":
        modal = CreateSolidRoleModal(bot, member, role_name)
    elif color_type == "gradient":
        modal = CreateGradientRoleModal(bot, member, role_name)
    else:
        await interaction.response.send_message(
            "Invalid color type selected.", ephemeral=True
        )
        return
    await interaction.response.send_modal(modal)


# 🍬──────────────────────────────
#     🎨 Modal: Create Solid Role
# 🍬──────────────────────────────
class CreateSolidRoleModal(discord.ui.Modal, title="🎨 Create Solid Custom Role"):
    def __init__(self, bot, member, name):
        super().__init__()
        self.bot = bot
        self.member = member
        self.name = name

        self.color_input = discord.ui.TextInput(
            label="Hex Color (e.g. #A8E6CF)", placeholder="#A8E6CF", required=True
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=False)

            # Parse color
            hex_value = self.color_input.value.strip().lstrip("#")
            role_color = discord.Color(int(hex_value, 16))
            # Create role first
            new_role = await interaction.guild.create_role(
                name=self.name,
                color=role_color,
                mentionable=False,
                reason=f"Created via /create-custom-role for {self.member.display_name} 💖",
            )
            # Fetch updated reference role position after creation
            reference_role = interaction.guild.get_role(REFERENCE_ROLE_ID)
            if reference_role is not None:
                custom_role_position = reference_role.position - 1
                await new_role.edit(position=custom_role_position)
            await self.member.add_roles(new_role)

            # Save to DB
            await upsert_role(bot=self.bot, user=self.member, role_id=new_role.id)

            # Build success embed
            embed = discord.Embed(
                title="🎀 Custom Role Created!",
                description=(
                    f"**Member:** {self.member.mention}\n"
                    f"**Role:** {new_role.mention}\n"
                    f"**Role Color:** `#{hex_value.upper()}`"
                ),
                color=role_color,
            )
            embed.set_author(
                name=self.member.display_name, icon_url=self.member.display_avatar.url
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)

            # Send followup
            await interaction.followup.send(embed=embed)

            # Log to server log channel
            log = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log:
                embed.set_footer(text=f"User ID: {self.member.id}")
                embed.timestamp = datetime.now()
                await log.send(embed=embed)

            pretty_log(
                "success",
                f"✅ Custom solid role '{new_role.name}' created for {self.member} by {interaction.user}",
            )

        except ValueError:
            pretty_log(
                "warn",
                f"❌ Invalid hex color input by {interaction.user} for {self.member}",
            )
            await interaction.followup.send("❌ Invalid hex color!", ephemeral=True)
        except Exception as e:
            pretty_log(
                "error",
                f"❌ Failed to create solid role '{self.name}' for {self.member}: {e}",
            )
            await interaction.followup.send(
                "⚠️ Failed to create the role.", ephemeral=True
            )
            # Create role
            new_role = await interaction.guild.create_role(
                name=self.name,
                color=role_color,
                mentionable=False,
                reason=f"Created via /create-custom-role for {self.member.display_name} 💖",
            )
            # Fetch updated reference role position after creation
            reference_role = interaction.guild.get_role(REFERENCE_ROLE_ID)
            if reference_role is not None:
                custom_role_position = reference_role.position - 1
                await new_role.edit(position=custom_role_position)
            await self.member.add_roles(new_role)

            # Save to DB
            await upsert_role(bot=self.bot, user=self.member, role_id=new_role.id)

            # Build success embed
            embed = discord.Embed(
                title="🎀 Custom Role Created!",
                description=(
                    f"**Member:** {self.member.mention}\n"
                    f"**Role:** {new_role.mention}\n"
                    f"**Role Color:** `#{hex_value.upper()}`"
                ),
                color=role_color,
            )
            embed.set_author(
                name=self.member.display_name, icon_url=self.member.display_avatar.url
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)

            # Send followup
            await interaction.followup.send(embed=embed)

            # Log to server log channel
            log = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log:
                embed.set_footer(text=f"User ID: {self.member.id}")
                embed.timestamp = datetime.now()
                await log.send(embed=embed)

            pretty_log(
                "success",
                f"✅ Custom solid role '{new_role.name}' created for {self.member} by {interaction.user}",
            )

        except ValueError:
            pretty_log(
                "warn",
                f"❌ Invalid hex color input by {interaction.user} for {self.member}",
            )
            await interaction.followup.send("❌ Invalid hex color!", ephemeral=True)
        except Exception as e:
            pretty_log(
                "error",
                f"❌ Failed to create solid role '{self.name}' for {self.member}: {e}",
            )
            await interaction.followup.send(
                "⚠️ Failed to create the role.", ephemeral=True
            )


# 🍓──────────────────────────────
#    🌈 Modal: Create Gradient Role
# 🍓──────────────────────────────
class CreateGradientRoleModal(discord.ui.Modal, title="🌈 Create Gradient Custom Role"):
    def __init__(self, bot, member, name):
        super().__init__()
        self.bot = bot
        self.member = member
        self.name = name

        self.start_color = discord.ui.TextInput(
            label="Start Color (Hex)", placeholder="#A8E6CF", required=True
        )
        self.end_color = discord.ui.TextInput(
            label="End Color (Hex)", placeholder="#CBF1F5", required=True
        )
        self.add_item(self.start_color)
        self.add_item(self.end_color)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=False)

            # 1. Create base role (solid color)
            new_role = await interaction.guild.create_role(
                name=self.name,
                color=discord.Color.default(),
                mentionable=False,
                reason=f"Created via /create-custom-role (gradient) for {self.member.display_name} 💖",
            )

            # Fetch updated reference role position after creation
            reference_role = interaction.guild.get_role(REFERENCE_ROLE_ID)
            if reference_role is not None:
                custom_role_position = reference_role.position - 1
                await new_role.edit(position=custom_role_position)
            await self.member.add_roles(new_role)

            # 2. Save to DB
            await upsert_role(bot=self.bot, user=self.member, role_id=new_role.id)

            # 3. Patch with gradient via helper
            success = await update_gradient_role(
                self.bot,
                interaction.guild.id,
                new_role.id,
                primarycolor=self.start_color.value,
                secondarycolor=self.end_color.value,
                name=self.name,
            )

            if not success:
                await interaction.followup.send(
                    "⚠️ Role was created, but gradient colors failed to apply.",
                    ephemeral=True,
                )
                return

            # 4. Success embed
            embed = discord.Embed(
                title="🌈 Custom Gradient Role Created!",
                description=(
                    f"**Member:** {self.member.mention}\n"
                    f"**Role:** {new_role.mention}\n"
                    f"**Gradient Colors:** `{self.start_color.value}` ➜ `{self.end_color.value}`"
                ),
                color=new_role.color,
            )
            embed.set_author(
                name=self.member.display_name, icon_url=self.member.display_avatar.url
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)

            # Send followup
            await interaction.followup.send(embed=embed)

            # Log to server log channel
            log = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log:
                embed.set_footer(text=f"User ID: {self.member.id}")
                embed.timestamp = datetime.now()
                await log.send(embed=embed)

            pretty_log(
                "success",
                f"✅ Custom gradient role '{new_role.name}' created for {self.member} by {interaction.user}",
            )

        except Exception as e:
            pretty_log(
                "error",
                f"❌ Failed to create gradient role '{self.name}' for {self.member}: {e}",
            )
            await interaction.followup.send(
                "⚠️ Failed to create the gradient role.", ephemeral=True
            )
