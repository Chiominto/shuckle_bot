import discord
from discord.ext import commands

from constants.celestial_constants import (
    CELESTIAL_TEXT_CHANNELS,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.db.custom_roles_db_func import is_custom_role, remove_role_by_role_id
from utils.logs.pretty_log import pretty_log


class OnRoleDeleteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if role.guild.id != CELESTIAL_SERVER_ID:
            return

        role_id = role.id
        role_name = role.name
        # Check if the deleted role is a custom role
        if await is_custom_role(self.bot, role_id):
            # Remove the custom role from the database
            await remove_role_by_role_id(self.bot, role_id)
            pretty_log(
                message=f"Custom role  {role_name} deleted from database after role deletion.",
                tag="info",
                label="Role Delete Event",
            )


async def setup(bot):
    await bot.add_cog(OnRoleDeleteCog(bot))
