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
        slash_cmd_name = "staff ban"

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
        slash_cmd_name = "staff unban"

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
        slash_cmd_name = "staff role-members"

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
        slash_cmd_name = "staff whois"

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

    # 🤍───────────────────────────────────────
    # 📌 /staff update-member
    # 🤍───────────────────────────────────────
    @staff.command(
        name="update-member",
        description="Update a member's information in the database.",
    )
    @staff_only()
    @app_commands.describe(
        member="The member to update",
        new_name="New Discord name for the member",
        new_pokemeow_name="New PokéMeow name for the member",
        new_channel="New personal channel for the member",
        new_clan_bank_donations="Updated clan bank donations",
        new_clan_treasury_donations="Updated clan treasury donation",
    )
    async def update_member(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        new_name: str | None = None,
        new_pokemeow_name: str | None = None,
        new_channel: discord.TextChannel | None = None,
        new_clan_bank_donations: str | None = None,
        new_clan_treasury_donations: str | None = None,
    ):
        slash_cmd_name = "staff update-member"

        # Call the centralized update member logic
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=update_member_func,  # your main logic lives here
            member=member,
            new_name=new_name,
            new_pokemeow_name=new_pokemeow_name,
            new_channel=new_channel,
            new_clan_bank_donations=new_clan_bank_donations,
            new_clan_treasury_donations=new_clan_treasury_donations,
        )

    update_member.extras = {"category": "Staff"}

    # 🤍───────────────────────────────────────
    # 📌 /staff clan-members
    # 🤍───────────────────────────────────────
    @staff.command(
        name="clan-members",
        description="List all members of the Celestial Clan.",
    )
    @staff_only()
    async def clan_members(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "staff clan-members"

        # Call the centralized clan members logic
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=clan_members_func,  # your main logic lives here
        )
    clan_members.extras = {"category": "Staff"}


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffGroup(bot))
