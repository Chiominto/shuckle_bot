import re

import discord
from discord.ext import commands

from constants.celestial_constants import CC_SERVER_ID, POKEMEOW_APPLICATION_ID
from utils.logs.pretty_log import pretty_log
from utils.listener_func.clan_remove_listener import process_clan_kick_message, process_clan_leave_command
triggers = {
    "icon_unlock": "as your icon with `/battle set-icon",
    "pro_embed": "to view badge information",
    "clan_leave": "you left **celestial**",
    "clan_kick": re.compile(
        r"you spent <:pokecoin:\d+>\s+\*\*100,000\*\*\s+to kick\s+.+?\s+from celestial\.",
        re.IGNORECASE,
    ),
}


# 🟣────────────────────────────────────────────
#         🐢 Message Edit Listener Cog
# 🟣────────────────────────────────────────────
class OnMessageEditCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #         🐢 Message Listener Event
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):

        # ————————————————————————————————
        # 🏰 Guild Check — Route by server
        # ————————————————————————————————
        guild = after.guild
        if not guild:
            return  # Skip DMs

        # ————————————————————————————————
        # 🐢 Message Variables
        # ————————————————————————————————
        content = after.content
        first_embed = after.embeds[0] if after.embeds else None
        first_embed_author = (
            first_embed.author.name if first_embed and first_embed.author else ""
        )
        first_embed_description = (
            first_embed.description if first_embed and first_embed.description else ""
        )
        first_embed_footer = (
            first_embed.footer.text if first_embed and first_embed.footer else ""
        )
        first_embed_title = (
            first_embed.title if first_embed and first_embed.title else ""
        )
        content_lower = content.lower() if content else ""

        # ————————————————————————————————
        # 🏰 Ignore non-PokéMeow bot messages
        # ————————————————————————————————
        # 🚫 Ignore all bots except PokéMeow to prevent loops
        if (
            after.author.bot
            and after.author.id != POKEMEOW_APPLICATION_ID
            and not after.webhook_id
        ):
            return
        # 🪓────────────────────────────────────────────
        #        ⚔️ Handle Clan Kick Command
        # 🪓────────────────────────────────────────────
        if content and triggers["clan_kick"].search(content_lower):
            try:
                pretty_log(
                    "info",
                    f"Detected clan kick in message ID {after.id} in channel {after.channel.name}",

                )
                await process_clan_kick_message(bot=self.bot, message=after)
                pretty_log(
                    "ready",
                    f"Successfully processed clan kick in message ID {after.id}",

                )
            except Exception as e:
                pretty_log(
                    "❌ ERROR",
                    f"Failed processing clan kick in message ID {after.id}: {e}",

                )
        # 💙───────────────────────────────────────────────💙
        # 🫧 Clan Leave Processing
        # 💙───────────────────────────────────────────────💙
        if content and triggers["clan_leave"] in content_lower:
            try:
                await process_clan_leave_command(bot=self.bot, message=after)
                pretty_log(
                    "ready",
                    f"Successfully processed clan leave from message ID {after.id}",
                    
                )
            except Exception as e:
                pretty_log(
                    "❌ ERROR",
                    f"Failed processing clan leave from message ID {after.id}: {e}",

                )
# 🟣────────────────────────────────────────────
#         🐢 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(OnMessageEditCog(bot))
