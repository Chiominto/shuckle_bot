import discord
from discord.ext import commands
from datetime import datetime

from constants.celestial_constants import CELESTIAL_ROLES, CELESTIAL_SERVER_ID, KHY_USER_ID
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log


from utils.functions.dm_member import dm_member
STAFF_ROLE_IDS = {CELESTIAL_ROLES.staff}  # Staff roles allowed to make invites


# ————————————————————————————————
# 🧠 Cog for Monitoring Invite Creation
# ————————————————————————————————
class InviteMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        guild = invite.guild
        creator = invite.inviter  # User who made the invite

        # ✅ Safe creators: Wooper itself or you
        if invite.guild.id != CELESTIAL_SERVER_ID:
            return
        if not creator:  # system/vanity invite case
            return
        staff_role = guild.get_role(CELESTIAL_ROLES.staff)

        if staff_role and staff_role not in creator.roles and creator.id != KHY_USER_ID:
            return

        # ❌ Delete unauthorized invite
        try:
            await invite.delete(reason="Unauthorized invite creation")
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to delete invite {invite.code}: {e}",
            )
            return

        # 🌸 Check if creator is staff
        member = guild.get_member(creator.id)
        has_staff_role = (
            any(role.id in STAFF_ROLE_IDS for role in member.roles) if member else False
        )

        # 🐾 Build DM embed
        if member and not has_staff_role:
            # Non-staff: invite deleted, ask staff
            embed = discord.Embed(
                title="🚫 Invite Deleted!",
                description=(
                    f"Hi {creator.mention}!\n\n"
                    "I noticed you created a server invite.\n"
                    "Your invite has been deleted. 🫧\n"
                    f"If you want an invite to {guild.name}, please ask staff for an official one."
                ),
                color=0x87CEFA,  # pastel blue
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            await dm_member(bot=self.bot, member=creator, embed=embed)

        log_desc = (
            f"Invite Code: `{invite.code}`\n"
            f"Creator: {creator.mention}\n"
            f"Channel: {invite.channel.mention if invite.channel else 'N/A'}\n"
            f"Max Uses: {invite.max_uses if invite.max_uses is not None else 'Unlimited'}\n"
            f"Expires At: {invite.expires_at if invite.expires_at else 'Never'}\n"
        )
        # 📝 Log to ServerLog channel
        log_embed = discord.Embed(
            title="Unauthorized Invite Deleted",
            description=log_desc,
            color=0xFF4500,  # orange-red
        )
        log_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        log_embed.set_author(name=creator.display_name, icon_url=creator.display_avatar.url if creator.display_avatar else None)
        log_embed.set_footer(text=f"User ID: {creator.id}", icon_url=guild.icon.url if guild.icon else None)
        await send_server_log(bot=self.bot, embed=log_embed)
# ————————————————————————————————
# 🧠 Cog setup —
# ————————————————————————————————
async def setup(bot):
    await bot.add_cog(InviteMonitor(bot))
