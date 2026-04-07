import discord
from discord.ext import commands

from constants.shellshuckle_constants import CC_SERVER_ID, POKEMEOW_APPLICATION_ID
from utils.listener_func.icon_unlock_listener import icon_unlock_listener
from utils.logs.pretty_log import pretty_log

triggers = {
    "icon_unlock": "as your icon with `/battle set-icon",
}


# 🟣────────────────────────────────────────────
#         🐢 Message Create Listener Cog
# 🟣────────────────────────────────────────────
class MessageCreateListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #         🐢 Message Listener Event
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        # ————————————————————————————————
        # 🏰 Guild Check — Route by server
        # ————————————————————————————————
        guild = message.guild
        if not guild:
            return  # Skip DMs

        # ————————————————————————————————
        # 🐢 Message Variables
        # ————————————————————————————————
        content = message.content
        first_embed = message.embeds[0] if message.embeds else None
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

        # ————————————————————————————————
        # 🏰 Ignore non-PokéMeow bot messages
        # ————————————————————————————————
        # 🚫 Ignore all bots except PokéMeow to prevent loops
        if (
            message.author.bot
            and message.author.id != POKEMEOW_APPLICATION_ID
            and not message.webhook_id
        ):
            return

        # ————————————————————————————————
        # 🐢 Icon Unlock Handler
        # ————————————————————————————————
        if triggers["icon_unlock"].lower() in first_embed_description.lower():
            pretty_log(
                tag="info",
                message=f"Detected icon unlock message in {message.channel.name}",
            )
            await icon_unlock_listener(self.bot, message)


# 🟣────────────────────────────────────────────
#         🐢 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))

