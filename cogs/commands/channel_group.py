import discord
from discord import app_commands
from discord.ext import commands

from group_commands_func.channel import *
from utils.functions.command_safe import run_command_safe


class ChannelGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ⚡ Top-level Staff group
    channel = app_commands.Group(
        name="channel",
        description="Channel Command Group",
    )

    # 🤍───────────────────────────────────────
    # 📌 /channel invite
    # 🤍───────────────────────────────────────
    @channel.command(name="invite", description="Adds a user to your private channel")
    @app_commands.describe(member="The member to add in your channel")
    async def channel_invite_func(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        slash_cmd_name = "channel invite"

        await run_command_safe(
            bot=self.bot,
            command_func=channel_invite_func,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            member=member,
        )

    channel_invite_func.extras = {"category": "Public"}

    # 🤍───────────────────────────────────────
    # 📌 /channel remove
    # 🤍───────────────────────────────────────
    @channel.command(
        name="remove", description="Removes a user from your private channel"
    )
    @app_commands.describe(member="The member to remove from your channel")
    async def channel_remove_func(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        slash_cmd_name = "channel remove"

        await run_command_safe(
            bot=self.bot,
            command_func=channel_remove_func,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            member=member,
        )

    channel_remove_func.extras = {"category": "Public"}

    # 🤍───────────────────────────────────────
    # 📌 /channel edit
    # 🤍───────────────────────────────────────
    @channel.command(
        name="edit", description="Edits the emoji or topic of your private channel"
    )
    @app_commands.describe(
        emoji="New custom emoji for your channel (must be a single default emoji)",
        topic="New topic for your channel",
    )
    async def channel_edit_func(
        self,
        interaction: discord.Interaction,
        emoji: str = None,
        topic: str = None,
    ):
        slash_cmd_name = "channel edit"

        await run_command_safe(
            bot=self.bot,
            command_func=channel_edit_func,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            emoji=emoji,
            topic=topic,
        )

    channel_edit_func.extras = {"category": "Public"}

    # 🤍───────────────────────────────────────
    # 📌 /channel private
    # 🤍───────────────────────────────────────
    @channel.command(
        name="private",
        description="Make your personal channel private to only you and staff.",
    )
    async def channel_private_func(self, interaction: discord.Interaction):
        slash_cmd_name = "channel private"

        await run_command_safe(
            bot=self.bot,
            command_func=channel_private_func,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
        )

    channel_private_func.extras = {"category": "Public"}

    # 🤍───────────────────────────────────────
    # 📌 /channel unprivate
    # 🤍───────────────────────────────────────
    @channel.command(
        name="unprivate",
        description="Make your personal channel visible to all Clan members again.",
    )
    async def channel_unprivate_func(self, interaction: discord.Interaction):
        slash_cmd_name = "channel unprivate"

        await run_command_safe(
            bot=self.bot,
            command_func=channel_unprivate_func,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
        )

    channel_unprivate_func.extras = {"category": "Public"}


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelGroup(bot))
