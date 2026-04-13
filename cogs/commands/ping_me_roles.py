import discord
from discord import app_commands
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_TEXT_CHANNELS,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID
)
from constants.aesthetics import *
from utils.logs.pretty_log import pretty_log
from utils.functions.general_roles_embed import General_Roles_Button
from utils.functions.market_snipe_roles_embed import Market_Snipe_Role_Button


EMBED_COLOR = DEFAULT_EMBED_COLOR

ROLES_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.roles_breakdown


class Main_Ping_Me_Roles_Embed_View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add General Roles Button
        self.add_item(General_Roles_Button())
        # Add Market Snipe Roles Button
        self.add_item(Market_Snipe_Role_Button())


class Ping_Me_Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Register persistent views for reboot survival
        bot.add_view(Main_Ping_Me_Roles_Embed_View())

    @app_commands.command(
        name="ping-me-roles",
        description="Sends the Ping Me Roles embed to the designated channel.",
    )
    async def ping_me_roles(self, interaction: discord.Interaction):
        """Sends the Ping Me Roles embed to the designated channel."""
        try:
            # Check if user is a staff member
            if interaction.user.id != KHY_USER_ID:
                await interaction.response.send_message(
                    "You do not have permission to use this command.", ephemeral=True
                )
                return

            guild = interaction.guild
            user = interaction.user

            channel = guild.get_channel(ROLES_CHANNEL_ID)
            if not channel:
                await interaction.response.send_message(
                    "The designated channel was not found.", ephemeral=True
                )
                return

            # Optional: delete previously sent ping me roles embeds by the bot
            async for msg in channel.history(limit=20):
                if msg.author.id == interaction.client.user.id and msg.components:
                    try:
                        await msg.delete()
                        pretty_log(
                            "info",
                            "Deleted old Ping Me Roles embed message.",
                        )
                    except:
                        pass
            title = f"{guild.name} Roles"
            desc = (
                "🐢 Role Categories\n\n" "💫 General Roles\n" "🎯 Market Snipe Roles\n"
            )
            embed = discord.Embed(
                title=title,
                description=desc,
                color=EMBED_COLOR,
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.set_image(url=Dividers.command)

            await channel.send(embed=embed, view=Main_Ping_Me_Roles_Embed_View())
            await interaction.response.send_message(
                f"Ping Me Roles embed has been sent to {channel.mention}.",
                ephemeral=True,
            )

        except Exception as e:
            pretty_log("error", f"Error in Ping Me Roles command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred.", ephemeral=True
            )
            return

    ping_me_roles.extras = {"category": "Staff"}

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping_Me_Roles(bot))
