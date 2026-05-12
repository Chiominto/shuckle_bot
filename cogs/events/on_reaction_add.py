import discord
from discord.ext import commands

from constants.aesthetics import Emojis
from constants.celestial_constants import CELESTIAL_TEXT_CHANNELS, KHY_USER_ID
from utils.db.flex_messages_db import check_if_its_a_flex_message
from utils.functions.flex_message import new_flex_message_handler, remove_flex_message
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

TESTING = False  # Temporarily disabled to test if reactions fire at all
# enable_debug(f"{__name__}.on_reaction_add")


# 🟣────────────────────────────────────────────
#         🐢 Reaction Handler Cog
# 🟣────────────────────────────────────────────
class ReactionListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #         🐢 Raw Reaction Add Event (cached or not)
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        debug_log(
            f"[ENTRY] on_raw_reaction_add triggered: emoji={payload.emoji}, user={payload.user_id}, msg_id={payload.message_id}"
        )

        # Ignore bot reactions
        if payload.member and payload.member.bot:
            debug_log(f"[SKIP] Bot reaction, ignoring")
            return

        # Fetch the full message and call handler
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                debug_log(f"[SKIP] Guild {payload.guild_id} not found")
                return

            channel = guild.get_channel(payload.channel_id)
            if not channel:
                debug_log(f"[SKIP] Channel {payload.channel_id} not found")
                return

            message = await channel.fetch_message(payload.message_id)
            user = payload.member or await self.bot.fetch_user(payload.user_id)

            await self._handle_reaction(
                reaction_payload=payload, message=message, user=user, action="add"
            )
        except Exception as e:
            debug_log(f"[ERROR] Failed to handle raw reaction add: {e}")

    # 🟣────────────────────────────────────────────
    #         🐢 Raw Reaction Remove Event
    # 🟣────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        debug_log(
            f"[ENTRY] on_raw_reaction_remove triggered: emoji={payload.emoji}, user={payload.user_id}, msg_id={payload.message_id}"
        )

        # Fetch the full message and call handler
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                debug_log(f"[SKIP] Guild {payload.guild_id} not found")
                return

            channel = guild.get_channel(payload.channel_id)
            if not channel:
                debug_log(f"[SKIP] Channel {payload.channel_id} not found")
                return

            message = await channel.fetch_message(payload.message_id)
            user = await self.bot.fetch_user(payload.user_id)

            await self._handle_reaction(
                reaction_payload=payload, message=message, user=user, action="remove"
            )
        except Exception as e:
            debug_log(f"[ERROR] Failed to handle raw reaction remove: {e}")

    # 🟣────────────────────────────────────────────
    #         🐢 Unified Reaction Handler
    # 🟣────────────────────────────────────────────
    async def _handle_reaction(
        self,
        reaction_payload: discord.RawReactionActionEvent,
        message: discord.Message,
        user: discord.User,
        action: str,
    ):
        """
        Unified handler for both add and remove reactions.

        Args:
            reaction_payload: The raw reaction payload
            message: The message object
            user: The user who reacted
            action: Either "add" or "remove"
        """
        emoji = reaction_payload.emoji
        guild = message.guild

        # ————————————————————————————————
        # 🐢 Guild Check
        # ————————————————————————————————
        if not guild:
            debug_log(f"[SKIP] No guild found")
            return

        # ————————————————————————————————
        # 🐢 Branch logic by reaction type
        # ————————————————————————————————
        debug_log(
            f"[{action}] emoji={str(emoji)}, channel={message.channel.id}, user={user.id}, guild={guild.id}"
        )
        if str(emoji) != Emojis.alien_twerk:
            debug_log(f"[{action}] Filtered: emoji is not alien_twerk")
            return
        if message.channel.id == CELESTIAL_TEXT_CHANNELS.stellar_flex:
            debug_log(f"[{action}] Filtered: channel is stellar_flex (flex channel)")
            return
        if TESTING and user.id != KHY_USER_ID:
            debug_log(f"[{action}] Filtered: TESTING=True and user is not KHY")
            return
        debug_log(f"[{action}] Passed filters, calling {action} logic")

        if action == "add":
            await self._on_reaction_add_logic(
                message=message, user=user, emoji=emoji, guild=guild
            )
        elif action == "remove":
            await self._on_reaction_remove_logic(
                message=message, user=user, emoji=emoji, guild=guild
            )

    async def _on_reaction_add_logic(
        self,
        message: discord.Message,
        user: discord.User,
        emoji: discord.PartialEmoji,
        guild: discord.Guild,
    ):
        """Handle reaction add logic."""
        debug_log(f"Entered _on_reaction_add_logic for message {message.id}")
        # Add your specific add logic here
        # Check if message id is in flex_messages table
        if await check_if_its_a_flex_message(bot=self.bot, message_id=message.id):
            debug_log(f"Message {message.id} already a flex message, skipping.")
            pretty_log(
                "info",
                f"Message ID {message.id} is a flex message. Skipping reaction add logic.",
            )
            return
        # Process the new flex message logic
        debug_log(f"Creating new flex message for message {message.id}")
        await new_flex_message_handler(bot=self.bot, message=message)

    async def _on_reaction_remove_logic(
        self,
        message: discord.Message,
        user: discord.User,
        emoji: discord.PartialEmoji,
        guild: discord.Guild,
    ):
        """Handle reaction remove logic."""
        debug_log(
            f"Entered _on_reaction_remove_logic for message {message.id}, emoji={str(emoji)}"
        )
        # Add your specific remove logic here
        # Check if message id is in flex_messages table
        if not await check_if_its_a_flex_message(bot=self.bot, message_id=message.id):
            debug_log(f"Message {message.id} is not a flex message, skipping.")
            pretty_log(
                "info",
                f"Message ID {message.id} is not a flex message. Skipping reaction remove logic.",
            )
            return
        # Check if there aren't anymore alien twerk reactions left on the message
        if str(emoji) == Emojis.alien_twerk:
            debug_log(
                f"Removing flex message {message.id}, alien twerk reaction removed."
            )
            await remove_flex_message(bot=self.bot, message_id=message.id)
        else:
            debug_log(f"Reaction is not alien twerk: {str(emoji)}")


async def setup(bot: commands.Bot):
    pretty_log("info", "Loading ReactionListener cog...")
    await bot.add_cog(ReactionListener(bot))
    pretty_log("info", "ReactionListener cog loaded successfully!")
