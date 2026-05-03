import discord
from discord.ext import commands
from utils.listener_func.ee_spawn_listener import (
    check_cc_bump_reminder,
    check_ee_near_spawn_alert,
    extract_boss_from_wb_command_embed,
    extract_boss_from_wb_spawn_command,
)
from constants.celestial_constants import CC_SERVER_ID, POKEMEOW_APPLICATION_ID, CC_BUMP_CHANNEL_ID, CELESTIAL_TEXT_CHANNELS, KHY_USER_ID
from utils.listener_func.icon_unlock_listener import icon_unlock_listener
from utils.listener_func.wb_rs import handle_wb_rewards
from utils.logs.pretty_log import pretty_log
from utils.listener_func.shiny_bonus_listener import (
    handle_pokemeow_global_bonus,
    read_shiny_bonus_timestamp_from_cc_channel,
)
from utils.quick_codes.sync_donation_roles import sync_donation_roles
from utils.listener_func.code_use_listener import send_code_claim_to_rs
from utils.listener_func.clan_invite_listener import clan_invite_listener
triggers = {
    "icon_unlock": "as your icon with `/battle set-icon",
    "global_bonus": "Global bonuses",
    "wb_spawn": "spawned a world boss using 1x <:boss_coin:1249165805095092356>",
    "wb_command": "a world boss has spawned! register now!",
    "ee_vote_checker": "there is no active world boss",
    "code_use": "<:checkedbox:752302633141665812> you used a code to claim a :gift:",
}
from utils.listener_func.donation_listener import give_command_listener, clan_donate_listener
CLAN_BANK_USER_NAMES = ["burgersbank"]
CC_SHINY_BONUS_CHANNEL_ID = 1457171231445876746
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
        # 🐢 Khy Quick Codes
        # ————————————————————————————————
        if message.author.id == KHY_USER_ID and message.content.startswith("!sync_donation_roles"):
            pretty_log(
                "info",
                f"Detected sync donation roles command from {message.author.display_name}.",
                label="Sync Donation Roles Command",
            )
            await sync_donation_roles(bot=self.bot, message=message)

        # ————————————————————————————————
        # 🐢 CC Bump Reminder Listener
        # ————————————————————————————————
        if guild.id == CC_SERVER_ID:
            if message.channel.id == CC_BUMP_CHANNEL_ID:
                pretty_log(
                    "info",
                    f"Detected message in CC bump channel: Message ID {message.id}",
                    label="CC Bump Reminder Listener",
                )
                await check_cc_bump_reminder(self.bot, message)
            if message.channel.id == CC_SHINY_BONUS_CHANNEL_ID:
                pretty_log(
                    "info",
                    f"Detected message in CC shiny bonus channel: Message ID {message.id}",
                    label="CC Shiny Bonus Listener",
                )
                await read_shiny_bonus_timestamp_from_cc_channel(
                    bot=self.bot, message=message
                )

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
        # 🐢 Clan Invite Handler
        # ————————————————————————————————
        if (
            ":tada: Welcome," in message.content
            and "You have successfully joined" in message.content
            and "Celestial" in message.content
        ):
            pretty_log(
                message=f"Detected clan invite message edit for member '{message.author.display_name}'.",
                tag="info",
                label="Clan Invite Command",
            )
            await clan_invite_listener(self.bot, message)
        # ————————————————————————————————
        # 🐢 Icon Unlock Handler
        # ————————————————————————————————
        if triggers["icon_unlock"].lower() in first_embed_description.lower():
            pretty_log(
                tag="info",
                message=f"Detected icon unlock message in {message.channel.name}",
            )
            await icon_unlock_listener(self.bot, message)
        # ————————————————————————————————
        # 🐢 World Boss Rewards Handler
        # ————————————————————————————————
        if first_embed:
            if (
                "Here are your rewards" in first_embed_title
                and "Boss id:" in first_embed_title
            ):
                pretty_log(
                    tag="info",
                    message=f"Detected world boss rewards message in {message.channel.name}",
                )
                await handle_wb_rewards(self.bot, message)
        # ————————————————————————————————
        # 🐢 Shiny Bonus Lisetner
        # ————————————————————————————————
        if first_embed:
            if triggers["global_bonus"] in first_embed_title:
                pretty_log(
                    "info",
                    f"Detected global bonus embed from PokéMeow bot: Message ID {message.id}",
                    label="Shiny Bonus Listener",
                )
                await handle_pokemeow_global_bonus(bot=self.bot, message=message)

        # ————————————————————————————————
        # 🐢 EE Near Spawn Alert Checker
        # ————————————————————————————————
        if message.embeds:
            embed_title = (
                message.embeds[0].title if message.embeds[0].title else ""
            )
            if triggers["ee_vote_checker"] in embed_title.lower():
                pretty_log(
                    "info",
                    f"Detected EE vote checker embed from PokéMeow bot: Message ID {message.id}",
                    label="EE Near Spawn Alert Checker",
                )
                await check_ee_near_spawn_alert(bot=self.bot, message=message)

        # ————————————————————————————————
        # 🐢 World Boss Command Embed Listener
        # ————————————————————————————————
        if message.embeds:
            embed_title = (
                message.embeds[0].title if message.embeds[0].title else ""
            )
            if triggers["wb_command"] in embed_title.lower():
                pretty_log(
                    "info",
                    f"Detected world boss command embed from PokéMeow bot: Message ID {message.id}",
                    label="World Boss Command Embed Listener",
                )
                await extract_boss_from_wb_command_embed(
                    bot=self.bot, message=message
                )
        # ————————————————————————————————
        # 🐢 World Boss Spawn Listener
        # ————————————————————————————————
        if message.content:
            if triggers["wb_spawn"] in message.content.lower():
                pretty_log(
                    "info",
                    f"Detected world boss spawn message from PokéMeow bot: Message ID {message.id}",
                    label="World Boss Spawn Listener",
                )
                await extract_boss_from_wb_spawn_command(
                    bot=self.bot, message=message
                )

        # ————————————————————————————————
        # 🐢 Code Claim Listener
        # ————————————————————————————————
        if triggers["code_use"].lower() in content:
            try:
                await send_code_claim_to_rs(bot=self.bot, message=message)
                pretty_log(
                    "ready",
                    f"Successfully processed code claim from message ID {getattr(message, 'id', 'unknown')}",

                )
            except Exception as e:
                pretty_log(
                    "critical",
                    f"Failed processing code claim from message ID {getattr(message, 'id', 'unknown')}: {e}",

                )

        # ————————————————————————————————
        # 🐢 Clan Donations
        # ————————————————————————————————
        if (
            content
                and "You successfully donated" in content
                and "Celestial" in content
            ):
            pretty_log(
                    "info",
                    f"Detected clan donation message: {content}",
                    label="DONATION_LISTENER",
                )
            await clan_donate_listener(self.bot, message)
        if (
            message.channel.id == CELESTIAL_TEXT_CHANNELS.donations
        ):
            # Clan Bank Donation
            if (
                content
                and "gave" in content
                and "PokeCoins" in content
                and any(name in content for name in CLAN_BANK_USER_NAMES)
            ):
                pretty_log(
                    "info",
                    f"Detected clan bank donation message: {content}",
                    label="DONATION_LISTENER",
                )
                await give_command_listener(self.bot, message)
# 🟣────────────────────────────────────────────
#         🐢 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
