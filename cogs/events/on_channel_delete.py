import discord
from discord.ext import commands
from utils.listener_func.channel_boost import contact_booster_to_remove_boost

from constants.celestial_constants import CELESTIAL_SERVER_ID
from utils.db.boosted_channels import is_channel_boosted
from utils.logs.pretty_log import pretty_log


class OnChannelDeleteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):

        # Only care for text channels
        if not isinstance(channel, discord.TextChannel):
            return

        # Only process in clan guild
        if channel.guild.id != CELESTIAL_SERVER_ID:
            return

        # Check if the deleted channel was boosted
        if await is_channel_boosted(self.bot, channel.id):
            try:
                await contact_booster_to_remove_boost(
                    bot=self.bot,
                    channel_id=channel.id,
                    context="channel_delete",
                    channel_name=channel.name,
                )
                pretty_log(
                    "info",
                    f"Channel {channel.name} (ID: {channel.id}) was boosted. Contacted booster to remove boost after deletion.",
                )
            except Exception as e:
                pretty_log(
                    "critical",
                    message=(
                        f"Error while contacting booster to remove boost for channel {channel.name} (ID: {channel.id}) after deletion: {e}"
                    ),
                )


async def setup(bot):
    await bot.add_cog(OnChannelDeleteCog(bot))
