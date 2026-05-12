import re

import discord
from discord.ext import commands

from constants.celestial_constants import (
    CC_BUMP_CHANNEL_ID,
    CC_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    KHY_USER_ID,
    POKEMEOW_APPLICATION_ID,
)
from utils.listener_func.battle_frontier_ach import handle_battle_frontier_achievement
from utils.listener_func.clan_invite_listener import clan_invite_listener
from utils.listener_func.code_use_listener import send_code_claim_to_rs
from utils.listener_func.ee_spawn_listener import (
    check_cc_bump_reminder,
    check_ee_near_spawn_alert,
    extract_boss_from_wb_command_embed,
    extract_boss_from_wb_spawn_command,
)
from utils.listener_func.golden_stone_listener import golden_stone_listener
from utils.listener_func.icon_unlock_listener import icon_unlock_listener
from utils.listener_func.shiny_bonus_listener import (
    handle_pokemeow_global_bonus,
    read_shiny_bonus_timestamp_from_cc_channel,
)
from utils.listener_func.wb_rs import handle_wb_rewards
from utils.logs.pretty_log import pretty_log
from utils.quick_codes.sync_donation_roles import sync_donation_roles
from utils.listener_func.incense_listener import (
    incense_command_handler,
    incense_depleted_handler,
    incense_use_handler,
    server_has_incense_handler,
)

CC_MH_REPORT_CHANNEL_ID = 1502156762466357338
triggers = {
    "icon_unlock": "as your icon with `/battle set-icon",
    "global_bonus": "Global bonuses",
    "wb_spawn": "spawned a world boss using 1x <:boss_coin:1249165805095092356>",
    "wb_command": "a world boss has spawned! register now!",
    "ee_vote_checker": "there is no active world boss",
    "code_use": "<:checkedbox:752302633141665812> you used a code to claim a :gift:",
    "golden_stone": "to claim your <:golden_",
    "battle_frontier_ach": "🎖️ you may continue your",
    "incense_command": "Incense charges are shared & used by every player in this server",
    "has_incense": "<:incense:1202436296874922065> An `;incense` is currently active in this server!",
    "incense_depleted": "your server's incense has run out!",
    "incense_use": "Incense. Your server has received the following benefits",
}
from utils.listener_func.donation_listener import (
    clan_donate_listener,
    give_command_listener,
)
from utils.listener_func.market_snipe_filter import should_delete_market_message
from utils.listener_func.message_listener_debug import handle_test_message
from utils.listener_func.ms_reports import relay_meowsummit_reports

CLAN_BANK_USER_NAMES = ["burgersbank"]
CC_SHINY_BONUS_CHANNEL_ID = 1457171231445876746
CODE_USE_PATTERN = re.compile(r"\byou used a code to claim\b", re.IGNORECASE)


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
            return  # Skip

        # ————————————————————————————————
        # 🐢 Market Snipe Filter
        # ————————————————————————————————
        if (
            message.channel.id == CELESTIAL_TEXT_CHANNELS.market_snipe
            and not message.author.bot
            and not message.webhook_id
        ):
            await should_delete_market_message(message)

        # ————————————————————————————————
        # 🐢 Khy Quick Codes
        # ————————————————————————————————
        if message.author.id == KHY_USER_ID and message.content.startswith(
            "!sync_donation_roles"
        ):
            pretty_log(
                "info",
                f"Detected sync donation roles command from {message.author.display_name}.",
                label="Sync Donation Roles Command",
            )
            await sync_donation_roles(bot=self.bot, message=message)
        if (
            message.content
            and message.content.lower().startswith("stest")
            and message.author.id == KHY_USER_ID
        ):
            pretty_log(
                "debug",
                f"Received test command from {message.author}, invoking test handler",
            )
            await handle_test_message(self.bot, message)
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
            if message.channel.id == CC_MH_REPORT_CHANNEL_ID:
                pretty_log(
                    "info",
                    f"Detected message in MeowSummit reports channel: Message ID {message.id}",
                    label="MeowSummit Report Relay",
                )
                await relay_meowsummit_reports(bot=self.bot, message=message)

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
            embed_title = message.embeds[0].title if message.embeds[0].title else ""
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
            embed_title = message.embeds[0].title if message.embeds[0].title else ""
            if triggers["wb_command"] in embed_title.lower():
                pretty_log(
                    "info",
                    f"Detected world boss command embed from PokéMeow bot: Message ID {message.id}",
                    label="World Boss Command Embed Listener",
                )
                await extract_boss_from_wb_command_embed(bot=self.bot, message=message)
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
                await extract_boss_from_wb_spawn_command(bot=self.bot, message=message)

        # ————————————————————————————————
        # 🐢 Code Claim Listener
        # ————————————————————————————————
        if content and CODE_USE_PATTERN.search(content):
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
        if content and "You successfully donated" in content and "Celestial" in content:
            pretty_log(
                "info",
                f"Detected clan donation message: {content}",
                label="DONATION_LISTENER",
            )
            await clan_donate_listener(self.bot, message)
        if message.channel.id == CELESTIAL_TEXT_CHANNELS.donations:
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
        # ————————————————————————————————
        # 🐢 Golden Stone Listener
        # ————————————————————————————————
        if content and triggers["golden_stone"] in content.lower():
            try:
                await golden_stone_listener(bot=self.bot, message=message)
                pretty_log(
                    "ready",
                    f"Successfully processed golden stone claim from message ID {getattr(message, 'id', 'unknown')}",
                )
            except Exception as e:
                pretty_log(
                    "critical",
                    f"Failed processing golden stone claim from message ID {getattr(message, 'id', 'unknown')}: {e}",
                )
        # ————————————————————————————————
        # 🐢 Battle Frontier Listener
        # ————————————————————————————————
        if content and triggers["battle_frontier_ach"] in content.lower():
            try:
                pretty_log(
                    "info",
                    f"Detected Battle Frontier achievement in message ID {getattr(message, 'id', 'unknown')}",
                )
                await handle_battle_frontier_achievement(bot=self.bot, message=message)
                pretty_log(
                    "ready",
                    f"Successfully processed Battle Frontier achievement from message ID {getattr(message, 'id', 'unknown')}",
                )
            except Exception as e:
                pretty_log(
                    "critical",
                    f"Failed processing Battle Frontier achievement from message ID {getattr(message, 'id', 'unknown')}: {e}",
                )
        # ————————————————————————————————
        # 🩵 Incense Listeners
        # ————————————————————————————————
        if first_embed:
            # Incense Command Handler
            if triggers["incense_command"] in first_embed_footer:
                pretty_log(
                    "info",
                    f"Detected incense command embed from PokéMeow bot: Message ID {message.id}",
                    label="Incense Command Handler",
                )
                await incense_command_handler(bot=self.bot, message=message)
        if message.content and triggers["incense_use"] in message.content:
            pretty_log(
                "info",
                f"Detected incense use message from PokéMeow bot: Message ID {message.id}",
                label="Incense Use Handler",
            )
            await incense_use_handler(bot=self.bot, message=message)

        if message.content and triggers["has_incense"] in message.content:
            await server_has_incense_handler(bot=self.bot, message=message)

        if message.content and triggers["incense_depleted"] in message.content:
            pretty_log(
                "info",
                f"Detected incense depleted message from PokéMeow bot: Message ID {message.id}",
                label="Incense Depleted Handler",
            )
            await incense_depleted_handler(bot=self.bot, message=message)

# 🟣────────────────────────────────────────────
#         🐢 Setup Function
# 🟣────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
