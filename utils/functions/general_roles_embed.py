import discord
from discord.ui import Button, View

from constants.aesthetics import *
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
)
from utils.logs.pretty_log import pretty_log

EMBED_COLOR = DEFAULT_EMBED_COLOR
EMBED_EMOJI = "💫"

# 🍬 Helper: Format the role list into an embed-friendly description
def format_role_description(line: list[tuple[str, discord.Role]]) -> str:
    parts = []
    for emoji, role in line:
        parts.append(f"{emoji} {role.mention}")
    return "\n".join(parts)


class ToggleRoleButton(Button):
    def __init__(self, role: discord.Role, label: str, emoji: str):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
            custom_id=f"toggle_role_{role.id}",
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        role = self.role
        try:
            if role in member.roles:
                await member.remove_roles(role)
                pretty_log(f"Removed role {role.name} from {member.display_name}")
                await interaction.response.send_message(
                    f"Removed role **{role.mention}** from you", ephemeral=True
                )
            else:
                await member.add_roles(role)
                pretty_log(f"Added role {role.name} to {member.display_name}")
                await interaction.response.send_message(
                    f"Added role **{role.mention}** to you", ephemeral=True
                )
        except Exception as e:
            pretty_log(
                f"Error toggling role {role.name} for {member.display_name}: {e}"
            )
            await interaction.response.send_message(
                "An error occurred while trying to update your roles.", ephemeral=True
            )


class Server_Booster_Only_Button(Button):
    def __init__(self, role: discord.Role, label: str, emoji: str):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
            custom_id=f"server_booster_only_{role.id}",
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        role = self.role
        SPECIAL_ROLE_IDS = [
            CELESTIAL_ROLES.server_booster,
            CELESTIAL_ROLES.top_catcher,
            CELESTIAL_ROLES.founders_,
            CELESTIAL_ROLES.elite_server_booster,
            CELESTIAL_ROLES.staff,
        ]
        try:
            if role in member.roles:
                await member.remove_roles(role)
                pretty_log(f"Removed role {role.name} from {member.display_name}")
                await interaction.response.send_message(
                    f"Removed role **{role.mention}** from you", ephemeral=True
                )
            else:
                if any(member.get_role(rid) for rid in SPECIAL_ROLE_IDS):
                    await member.add_roles(role)
                    pretty_log(f"Added role {role.name} to {member.display_name}")
                    await interaction.response.send_message(
                        f"Added role **{role.mention}** to you", ephemeral=True
                    )
                else:
                    special_roles_desc = ", ".join(
                        [f"<@&{rid}>" for rid in SPECIAL_ROLE_IDS]
                    )
                    await interaction.response.send_message(
                        f"You need to have at least one of the following roles to get **{role.mention}**: {special_roles_desc}",
                        ephemeral=True,
                    )
        except Exception as e:
            pretty_log(
                f"Error toggling role {role.name} for {member.display_name}: {e}"
            )
            await interaction.response.send_message(
                "An error occurred while trying to update your roles.", ephemeral=True
            )


class General_Roles_Button(Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji=EMBED_EMOJI,
            custom_id="general_roles_button",
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            user = interaction.user
            view, embed = build_general_roles_embed(guild, user)
            if view and embed:
                await interaction.response.send_message(
                    embed=embed,
                    view=view,
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while building the roles embed.",
                    ephemeral=True,
                )
                pretty_log(
                    "error",
                    f"Failed to build General Roles Embed for {interaction.user.display_name}",
                )
        except Exception as e:
            pretty_log(
                f"Error in General Roles Button callback for {interaction.user.display_name}: {e}"
            )
            await interaction.response.send_message(
                "An error occurred while processing your request.", ephemeral=True
            )


def build_general_roles_embed(guild: discord.Guild, user: discord.Member):
    try:
        view = discord.ui.View(timeout=None)
        clan_member_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)

        # Server Roles
        giveaway_role = guild.get_role(CELESTIAL_ROLES.giveaways)
        golden_hour_role = guild.get_role(CELESTIAL_ROLES.golden_waters)
        trade_ads_role = guild.get_role(CELESTIAL_ROLES.trade_ads)
        ee_spawn_ping = guild.get_role(CELESTIAL_ROLES.ee_ping)
        calm_waters = guild.get_role(CELESTIAL_ROLES.calm_waters)
        shiny_bonus = guild.get_role(CELESTIAL_ROLES.shiny_bonus)
        os_lotto_ping = guild.get_role(CELESTIAL_ROLES.os_lottery)
        as_spawn_ping = guild.get_role(CELESTIAL_ROLES.as_spawn_ping)
        as_rare_spawn_ping = guild.get_role(CELESTIAL_ROLES.as_rarespawn_ping)

        roles = []

        # Giveaway role (only if clan member)
        if giveaway_role and clan_member_role in user.roles:
            emoji = "🎁"
            view.add_item(
                ToggleRoleButton(role=giveaway_role, label="Giveaways", emoji=emoji)
            )
            roles.append((emoji, giveaway_role))

        if golden_hour_role:
            emoji = "🐟"
            view.add_item(
                ToggleRoleButton(
                    role=golden_hour_role, label="Golden Hour Ping", emoji=emoji
                )
            )
            roles.append((emoji, golden_hour_role))

        if calm_waters:
            emoji = "🌊"
            view.add_item(
                ToggleRoleButton(
                    role=calm_waters, label="Calm Waters Ping", emoji=emoji
                )
            )
            roles.append((emoji, calm_waters))

        if trade_ads_role:
            emoji = "📊"
            view.add_item(
                ToggleRoleButton(
                    role=trade_ads_role, label="Trade Ads Ping", emoji=emoji
                )
            )
            roles.append((emoji, trade_ads_role))

        if os_lotto_ping:
            emoji = "🎰"
            view.add_item(
                ToggleRoleButton(role=os_lotto_ping, label="OS Lotto Ping", emoji=emoji)
            )
            roles.append((emoji, os_lotto_ping))

        if shiny_bonus:
            emoji = "✨"
            view.add_item(
                ToggleRoleButton(
                    role=shiny_bonus, label="Shiny Bonus Ping", emoji=emoji
                )
            )
            roles.append((emoji, shiny_bonus))

        if ee_spawn_ping:
            emoji = Emojis.gigantamax
            view.add_item(
                ToggleRoleButton(role=ee_spawn_ping, label="EE Spawn Ping", emoji=emoji)
            )
            roles.append((emoji, ee_spawn_ping))

        if as_spawn_ping:
            emoji = Emojis.pokeball
            view.add_item(
                ToggleRoleButton(role=as_spawn_ping, label="AS Spawn Ping", emoji=emoji)
            )
            roles.append((emoji, as_spawn_ping))

        if as_rare_spawn_ping:
            emoji = Emojis.premierball
            view.add_item(
                Server_Booster_Only_Button(
                    role=as_rare_spawn_ping, label="AS Rare Spawn Hunter", emoji=emoji
                )
            )
            roles.append((emoji, as_rare_spawn_ping))

        desc = (
            format_role_description(roles)
            if roles
            else "No roles available at the moment."
        )
        embed = discord.Embed(
            title=f"{EMBED_EMOJI} General Roles", description=desc, color=EMBED_COLOR
        )

        return view, embed

    except Exception as e:
        pretty_log("error", f"Error building General Roles Embed: {e}")
        return None, None
