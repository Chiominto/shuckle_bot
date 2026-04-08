# ──────────────────────────────
# 💙 Reusable Discord Button Helpers
# ──────────────────────────────
import discord
from utils.logs.pretty_log import pretty_log


# -------------------- User check helper --------------------
async def check_user(
    interaction: discord.Interaction, user_id: int, label: str = "Button"
):
    """
    Check if the interaction user is the allowed user.

    Parameters:
    - interaction: discord.Interaction
    - user_id: int, the ID of the user allowed to press
    - label: str, label for logging

    Returns:
    - bool: True if allowed, False if not
    """
    if interaction.user.id != user_id:
        try:
            await interaction.response.send_message(
                "This button isn't for you!", ephemeral=True
            )
            pretty_log(
                label=f"🦭 {label}",
                message=f"💙 Unauthorized button press by {interaction.user} (ID: {interaction.user.id})",
                
            )
        except Exception as e:
            pretty_log(
                label=f"🦭 {label}",
                message=f"❌ Failed to send ephemeral in check_user: {e}",

            )
        return False
    return True


# -------------------- Role toggle helper --------------------
async def toggle_role(
    interaction: discord.Interaction, role_id: int, label: str = "Role Toggle"
):
    """
    Toggles a role for the interaction user. Adds it if missing, removes if present.

    Parameters:
    - interaction: discord.Interaction
    - role_id: int, the Discord role ID to toggle
    - label: str, label for logging

    Usage inside a discord.ui.Button callback:
    await toggle_role(interaction, self.hunter_role_id, label="Hunter Role")
    """
    try:
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(
                f"{label} not found.", ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"{label} removed!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"{label} added!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(
            f"⚠️ Something went wrong: {e}", ephemeral=True
        )
        pretty_log(
            label=f"🦭 {label}",
            message=f"❌ Error toggling role: {e}",

        )

async def toggle_role_button_func(
    interaction: discord.Interaction, role_id: int, label: str = "Role Toggle"
):
    """
    Toggles a role for the interaction user. Adds it if missing, removes if present.

    Parameters:
    - interaction: discord.Interaction
    - role_id: int, the Discord role ID to toggle
    - label: str, label for logging

    Usage inside a discord.ui.Button callback:
    await toggle_role(interaction, self.hunter_role_id, label="Hunter Role")
    """
    try:
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(
                f"{label} not found.", ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"{role.mention} removed!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"{role.mention} added!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(
            f"⚠️ Something went wrong: {e}", ephemeral=True
        )
        pretty_log(
            label=f"🦭 {label}",
            message=f"❌ Error toggling role: {e}",

        )
