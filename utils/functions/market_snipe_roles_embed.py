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
EMBED_EMOJI = "🎯"
EMBED_COLOR = DEFAULT_EMBED_COLOR
from .general_roles_embed import Server_Booster_Only_Button, format_role_description


class Market_Snipe_Role_Button(Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji=EMBED_EMOJI,
            custom_id="market_snipe_role_button",
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            user = interaction.user
            view, embed = build_market_snipe_roles_embed(guild, user)
            if view and embed:
                await interaction.response.send_message(
                    embed=embed, view=view, ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while building the Market Snipe roles embed.",
                    ephemeral=True,
                )
        except Exception as e:
            pretty_log("error", f"Error in Market Snipe Role Button callback: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred.", ephemeral=True
            )


def build_market_snipe_roles_embed(guild: discord.Guild, user: discord.Member):
    try:
        view = discord.ui.View(timeout=None)

        # Get roles
        common_snipe_role = guild.get_role(CELESTIAL_ROLES.common_snipe)
        uncommon_snipe_role = guild.get_role(CELESTIAL_ROLES.uncommon_snipe)
        rare_snipe_role = guild.get_role(CELESTIAL_ROLES.rare_snipe)
        super_rare_snipe_role = guild.get_role(CELESTIAL_ROLES.superrare_snipe)
        legendary_snipe_role = guild.get_role(CELESTIAL_ROLES.legendary_snipe)
        shiny_snipe_role = guild.get_role(CELESTIAL_ROLES.shiny_snipe)
        golden_snipe_role = guild.get_role(CELESTIAL_ROLES.golden_snipe)
        mega_snipe_role = guild.get_role(CELESTIAL_ROLES.mega_snipe)
        gigantamax_snipe_role = guild.get_role(CELESTIAL_ROLES.gigantamax_snipe)
        event_exclusive_snipe_role = guild.get_role(
            CELESTIAL_ROLES.exclusive_snipe
        )
        paldean_snipe_role = guild.get_role(CELESTIAL_ROLES.paldean_snipe)

        roles = []
        if common_snipe_role:
            emoji = Emojis.Common
            view.add_item(
                Server_Booster_Only_Button(common_snipe_role, "Common Snipe", emoji)
            )
            roles.append((emoji, common_snipe_role))

        if uncommon_snipe_role:
            emoji = Emojis.Uncommon
            role = uncommon_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Uncommon Snipe", emoji))
            roles.append((emoji, role))

        if rare_snipe_role:
            emoji = Emojis.Rare
            role = rare_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Rare Snipe", emoji))
            roles.append((emoji, role))

        if super_rare_snipe_role:
            emoji = Emojis.Super_Rare
            role = super_rare_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Super Rare Snipe", emoji))
            roles.append((emoji, role))

        if legendary_snipe_role:
            emoji = Emojis.Legendary
            role = legendary_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Legendary Snipe", emoji))
            roles.append((emoji, role))

        if shiny_snipe_role:
            emoji = Emojis.Shiny
            role = shiny_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Shiny Snipe", emoji))
            roles.append((emoji, role))

        if golden_snipe_role:
            emoji = Emojis.Golden
            role = golden_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Golden Snipe", emoji))
            roles.append((emoji, role))
            
        if mega_snipe_role:
            emoji = Emojis.mega
            role = mega_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Mega Snipe", emoji))
            roles.append((emoji, role))

        if gigantamax_snipe_role:
            emoji = Emojis.gigantamax
            role = gigantamax_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Gigantamax Snipe", emoji))
            roles.append((emoji, role))

        if event_exclusive_snipe_role:
            emoji = "🍒"
            role = event_exclusive_snipe_role
            view.add_item(
                Server_Booster_Only_Button(role, "Event Exclusive Snipe", emoji)
            )
            roles.append((emoji, role))

        if paldean_snipe_role:
            emoji = "🌋"
            role = paldean_snipe_role
            view.add_item(Server_Booster_Only_Button(role, "Paldean Snipe", emoji))
            roles.append((emoji, role))

        if roles:
            desc = format_role_description(roles)
        else:
            desc = "No Market Snipe roles are currently available."

        title = f"{EMBED_EMOJI} Market Snipe Roles"
        embed = discord.Embed(
            title=title,
            description=desc,
            color=EMBED_COLOR,
        )
        return view, embed

    except Exception as e:
        pretty_log("error", f"Error building Market Snipe roles embed: {e}")
        return None, None

