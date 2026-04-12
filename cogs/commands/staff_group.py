import discord
from discord import app_commands
from discord.ext import commands

from group_commands_func.staff import *

from utils.functions.command_safe import run_command_safe
from utils.functions.role_checks import owner_and_co_owner_only, staff_only

class StaffGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ⚡ Top-level Staff group
    staff = app_commands.Group(
        name="staff",
        description="Staff Command Group",
    )

    # 🤍───────────────────────────────────────
    # 📌 /staff ban
    # 🤍───────────────────────────────────────
    @staff.command(
        name="ban",
        description="Preemptively bans a member from joining.",
    )
    @app_commands.describe(
        user="The user to ban (optional if using user ID)",
        user_id="The Discord user ID to ban (optional if using member)",
        reason="Optional reason for ban",
    )
    @owner_and_co_owner_only()
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
        user_id: str | None = None,
        reason: str | None = None,
    ):
        slash_cmd_name = "co-owner ban"

        # Call the centralized preban logic
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=ban_func,  # your main logic lives here
            user=user,
            user_id=user_id,
            reason=reason,
        )

    ban.extras = {"category": "Staff"}

    # 🤍───────────────────────────────────────
    # 📌 /staff unban
    # 🤍───────────────────────────────────────
    @staff.command(
        name="unban",
        description="Unbans a user by ID or member.",
    )
    @app_commands.describe(
        user="The user to unban (optional if using user ID)",
        user_id="The Discord user ID to unban (optional if using member)",
        reason="Optional reason for unban",
    )
    @owner_and_co_owner_only()
    async def unban(
        self,
        interaction: discord.Interaction,
        user: discord.User | None = None,
        user_id: str | None = None,
        reason: str | None = None,
    ):
        slash_cmd_name = "co-owner unban"

        # Call the centralized unban logic
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=unban_func,  # your main logic lives here
            user=user,
            user_id=user_id,
            reason=reason,
        )
    unban.extras = {"category": "Staff"}

    # 🤍───────────────────────────────────────
    # 📌 /staff role-members
    # 🤍───────────────────────────────────────
    @staff.command(
        name="role-members",
        description="List members with a specific role.",
    )
    @staff_only()
    @app_commands.describe(
        role="The role to check members for",
    )
    async def role_members(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ):
        slash_cmd_name = "role-members"

        # Call the centralized role members logic
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=role_members_func,  # your main logic lives here
            role=role,
        )
    role_members.extras = {"category": "Staff"}

    # 🤍───────────────────────────────────────
    # 📌 /staff whois
    # 🤍───────────────────────────────────────
    @staff.command(
        name="whois",
        description="Fetch information about a member or user.",
    )
    @staff_only()
    @app_commands.describe(
        user="The member to fetch info about (optional if using user ID)",
        user_id="The Discord user ID to fetch info about (optional if using member)",
    )
    async def whois(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
        user_id: str | None = None,
    ):
        slash_cmd_name = "whois"

        # Call the centralized whois logic
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=whois_func,  # your main logic lives here
            user=user,
            user_id=user_id,
        )
    whois.extras = {"category": "Staff"}

async def setup(bot: commands.Bot):
    await bot.add_cog(StaffGroup(bot))