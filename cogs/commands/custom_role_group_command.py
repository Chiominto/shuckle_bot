from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from group_commands_func.custom_role import *
from utils.functions.command_safe import run_command_safe
from utils.logs.pretty_log import pretty_log

from utils.functions.role_checks import owner_and_co_owner_only, staff_only

# 🍭──────────────────────────────
#   🎀 Custom Role Group Command
# 🍭──────────────────────────────
class CustomRoleGroupCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Register the group command
    custom_role_group = app_commands.Group(
        name="custom-role", description="Commands related to custom roles"
    )

    # 🎀────────────────────────────────────────────
    #          🌸 /custom-role create 🌸
    # 🎀────────────────────────────────────────────
    @custom_role_group.command(
        name="create",
        description="Create a custom role for a member",
    )
    @app_commands.describe(
        member="The member to create the custom role for",
        role_name="The name of the custom role",
        color_type="The color type of the custom role",
    )
    @staff_only()
    async def custom_role_create(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role_name: str,
        color_type: Literal["Solid", "Gradient"],
    ):
        slash_cmd_name = "/custom-role create"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=custom_role_create_func,
            member=member,
            role_name=role_name,
            color_type=color_type,
        )
    custom_role_create.extras = {"category": "Staff"}
    # 🎀────────────────────────────────────────────
    #          🌸 /custom-role edit 🌸
    # 🎀────────────────────────────────────────────
    @custom_role_group.command(
        name="edit",
        description="Edit a member's custom role",
    )
    @app_commands.describe(
        new_role_name="The new name of the custom role",
        color_type="The color type of the custom role",
    )
    async def custom_role_edit(
        self,
        interaction: discord.Interaction,
        new_role_name: str = None,
        color_type: Literal["Solid", "Gradient"] = None,
    ):
        slash_cmd_name = "/custom-role edit"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=custom_role_edit_func,
            new_role_name=new_role_name,
            color_type=color_type,
        )

    custom_role_edit.extras = {"category": "Public"}

    # 🎀────────────────────────────────────────────
    #          🌸 /custom-role edit-icon 🌸
    # 🎀────────────────────────────────────────────
    @custom_role_group.command(
        name="edit-icon",
        description="Edit a member's custom role's icon",
    )
    async def custom_role_edit_icon(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "/custom-role edit-icon"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=custom_role_edit_icon_func,
        )
    custom_role_edit_icon.extras = {"category": "Public"}


    #          🌸 /custom-role set 🌸
    # 🎀────────────────────────────────────────────
    @custom_role_group.command(
        name="set",
        description="Sets a member's custom role to a specified role",
    )
    @app_commands.describe(
        member="The member to set the custom role for",
        role="The role to set as the custom role",
    )
    @staff_only()
    async def custom_role_set(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
    ):
        slash_cmd_name = "/custom-role set"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=custom_role_set_func,
            member=member,
            role=role,
        )
    custom_role_set.extras = {"category": "Staff"}

# 🎀────────────────────────────────────────────
#           🌸 Cog Setup Function 🌸
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CustomRoleGroupCommand(bot)
    await bot.add_cog(cog)
