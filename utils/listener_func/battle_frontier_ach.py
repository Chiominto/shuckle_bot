# Extracts the earned symbol after the medal emoji (🎖️), handling both bold (**...**) and non-bold cases.
import re
import traceback
from datetime import datetime

import discord

from constants.aesthetics import *
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.functions.webhook_func import send_webhook
from utils.logs.debug_log import debug_enabled, debug_log, enable_debug
from utils.logs.pretty_log import pretty_log


class BF_THUMBNAIL:
    pyramid = "https://media.discordapp.net/attachments/1484878359929557174/1486167767206989824/pyramid_king_brandon.png?ex=69c48517&is=69c33397&hm=d59282848784745787111102bbb128899becff3f10bc91214b19f77df7fcbd5c&=&format=webp&quality=lossless"
    dome = "https://media.discordapp.net/attachments/1484878359929557174/1485446324156629214/dome_ace_tucker.png?ex=69c1e531&is=69c093b1&hm=e83315d20a2a120ffd7288e016147c23c988976b63baae1cf8d0cf8d7c93c95a&=&format=webp&quality=lossless"
    pike = "https://media.discordapp.net/attachments/1484878359929557174/1485419725700989058/pike_queen_lucy.png?ex=69c1cc6c&is=69c07aec&hm=f3f6eaaf7d4fd3577e06620a470ccc5971a5108e9e2ee354f1f7747d294b318d&=&format=webp&quality=lossless"
    tower = "https://media.discordapp.net/attachments/1484878359929557174/1485249092425879582/salon_maiden_anabel.png?ex=69c12d82&is=69bfdc02&hm=d353d8e85b614898a2b112a6dd6f42b9f5cd00225278d02d62110149e5adf7cd&=&format=webp&quality=lossless"
    palace = "https://media.discordapp.net/attachments/1484878359929557174/1484901318631096430/palace_maven_spenser.png?ex=69bfe99e&is=69be981e&hm=2d9de5f1f6b3ffe341e86d42309c0bbafe1c1cd90ada9a37fb87860105bf389f&=&format=webp&quality=lossless"
    arena = "https://media.discordapp.net/attachments/1484878359929557174/1485101559300886618/arena_tycoon_greta.png?ex=69c0a41b&is=69bf529b&hm=40841088b674957363aa438db2b2621d6612ba02d8062c00ef54b6bc043a1df1&=&format=webp&quality=lossless"
    factory = "https://cdn.discordapp.com/attachments/1050645885844987904/1497204507845726218/factory_head_noland.png?ex=69ecabdb&is=69eb5a5b&hm=b31116f8dcbe417012f36c23575baede32887110444a4b49dfe95d9f948aa60b"


class BF_AUTHOR_IMAGE_URL:
    pyramid = "https://media.discordapp.net/attachments/1484878359929557174/1486167766296956948/1480698196924698804.png?ex=69c48517&is=69c33397&hm=0d21b7029fe7328cb036cff34b9012aaa9e3f9e9f7c748fe7e894f80e69cd092&=&format=webp&quality=lossless"
    dome = "https://media.discordapp.net/attachments/1484878359929557174/1485446323871154256/1480698207313985677.png?ex=69c1e531&is=69c093b1&hm=96fa5099362fe49fa5c229962bd6670f35492ee6f405f5c77ce59e4d638d18bf&=&format=webp&quality=lossless"
    pike = "https://media.discordapp.net/attachments/1484878359929557174/1485419726078345319/1480698198640168991.png?ex=69c1cc6c&is=69c07aec&hm=1426b6cc4894e7ef88a82ae567698b780a8110bdfaca3cef24be7a7161aaf9f3&=&format=webp&quality=lossless"
    tower = "https://media.discordapp.net/attachments/1484878359929557174/1485249092102656093/1480696620835410183.png?ex=69c12d82&is=69bfdc02&hm=1d1f59c2b8595f5b6e5dbd7864b04e2cf45744d1e566d6093aa9e26acd7ba91c&=&format=webp&quality=lossless"
    palace = "https://media.discordapp.net/attachments/1484878359929557174/1484878389830619357/1480698205636136990.png?ex=69bfd443&is=69be82c3&hm=bd2f3a8439fb04edffd9c911c9f57a783b01107be02acb796eb3528859938289&=&format=webp&quality=lossless"
    arena = "https://media.discordapp.net/attachments/1484878359929557174/1485101868735660253/1480698203694301204.png?ex=69c0a465&is=69bf52e5&hm=425669e7bd62595e460a075cf2fb30dbda449b4f4434eb2947dd14b9e46d7f42&=&format=webp&quality=lossless"
    factory = "https://media.discordapp.net/attachments/1484878359929557174/1497205774370209812/1480698201630834738.png?ex=69ecad09&is=69eb5b89&hm=dd542980389fa5d3a139f8a1bc32dbb7f62e87a1d25b6a916594abea1640fafb&=&format=webp&quality=lossless&width=90&height=68"


enable_debug(f"{__name__}.handle_battle_frontier_achievement")
TESTING = False
symbol_map = {
    "gold knowledge symbol": {
        "emoji": Emojis.gold_knowledge_symbol,
        "npc_name": "Factory Head Noland",
        "npc_emoji": Emojis.factory_head_noland,
        "challenge": "Battle Factory",
        "reward": "Blunder Policy",
        "reward_emoji": Emojis.blunder_policy,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.factory,
        "thumbnail_url": BF_THUMBNAIL.factory,
        "footer_text": "Defeated Round 6, Battle 7 of Battle Factory",
    },
    "gold guts symbol": {
        "emoji": Emojis.gold_guts_symbol,
        "npc_name": "Arena Tycoon Greta",
        "npc_emoji": Emojis.arena_tycoon_greta,
        "challenge": "Battle Arena",
        "reward": "Adrenaline Orb",
        "reward_emoji": Emojis.adrenaline_orb,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.arena,
        "thumbnail_url": BF_THUMBNAIL.arena,
        "round_info": "Defeated Round 8, Battle 7 of Battle Arena",
    },
    "gold tactics symbol": {
        "emoji": Emojis.gold_tactics_symbol,
        "npc_name": "Dome Ace Tucker",
        "npc_emoji": Emojis.dome_ace_tucker,
        "challenge": "Battle Dome",
        "reward": "Scope Lens",
        "reward_emoji": Emojis.scope_lens,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.dome,
        "thumbnail_url": BF_THUMBNAIL.dome,
        "footer_text": "Defeated Round 10, Battle 4 of Battle Dome",
    },
    "gold luck symbol": {
        "emoji": Emojis.gold_luck_symbol,
        "npc_name": "Pike Queen Lucy",
        "npc_emoji": Emojis.pike_queen_lucy,
        "challenge": "Battle Pike",
        "reward": "Black Sludge",
        "reward_emoji": Emojis.black_sludge,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.pike,
        "thumbnail_url": BF_THUMBNAIL.pike,
        "footer_text": "Defeated Round 10, Room 7 of Battle Pike",
    },
    "gold spirits symbol": {
        "emoji": Emojis.gold_ability_symbol,
        "npc_name": "Palace Maven Spenser",
        "npc_emoji": Emojis.palace_maven_spenser,
        "challenge": "Battle Palace",
        "reward": "Throat Spray",
        "reward_emoji": Emojis.throat_spray,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.palace,
        "thumbnail_url": BF_THUMBNAIL.palace,
        "footer_text": "Defeated Round 6, Battle 7 of Battle Palace",
    },
    "gold brave symbol": {
        "emoji": Emojis.gold_brave_symbol,
        "npc_name": "Pyramid King Brandon",
        "npc_emoji": Emojis.pyramid_king_brandon,
        "challenge": "Battle Pyramid",
        "reward": "Weakness Policy",
        "reward_emoji": Emojis.weakness_policy,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.pyramid,
        "thumbnail_url": BF_THUMBNAIL.pyramid,
        "footer_text": "Defeated Round 10, Battle 7 of Battle Pyramid",
    },
    "gold ability symbol": {
        "emoji": Emojis.gold_ability_symbol,
        "npc_name": "Salon Maiden Anabel",
        "npc_emoji": Emojis.salon_maiden_anabel,
        "challenge": "Battle Tower",
        "reward": "Shell Bell",
        "reward_emoji": Emojis.shell_bell,
        "footer_image_url": BF_AUTHOR_IMAGE_URL.tower,
        "thumbnail_url": BF_THUMBNAIL.tower,
        "footer_text": "Defeated Round 10, Battle 7 of Battle Tower",
    },
}


# Extracts the username before 'won the battle!' in a message line.
def extract_winner_name(text):
    # Handles cases like: <emoji> **username** won the battle!
    # and also without emoji or bold
    match = re.search(
        r"(?:<:[^>]+>\s*)?\*\*(?P<name1>[\w.]+)\*\* won the battle!|(?:<:[^>]+>\s*)?(?P<name2>[\w.]+) won the battle!",
        text,
    )
    if match:
        # Prefer bolded username if present
        if match.group("name1"):
            return match.group("name1")
        elif match.group("name2"):
            return match.group("name2")
    return None


def extract_earned_symbol(text):
    # Try to match bolded symbol name first
    match = re.search(r"🎖️ Earned [^*\n]*\*\*(.+?)\*\*", text)
    if match:
        return match.group(1).strip()
    # Fallback: match non-bold symbol name
    match = re.search(r"🎖️ Earned [^\n]* ([A-Za-z ]+?) from", text)
    if match:
        return match.group(1).strip()
    return None


async def get_member_by_username(guild, username):
    # Case-insensitive search for member by username (name#discriminator or just name)
    for member in guild.members:
        if member.name == username or member.display_name == username:
            return member
    return None


async def handle_battle_frontier_achievement(
    bot: discord.Client, message: discord.Message
):
    content = message.content
    debug_log(f"Raw message content: {content}")
    winner_name = extract_winner_name(content)
    debug_log(f"Extracted winner name: '{winner_name}'")
    earned_symbol = extract_earned_symbol(content)
    debug_log(f"Extracted earned symbol: '{earned_symbol}'")
    guild = message.guild
    debug_log(f"Guild: {guild.name} (ID: {guild.id})")
    debug_log(f"Message ID: {getattr(message, 'id', 'unknown')}")
    if not winner_name or not earned_symbol:
        debug_log(
            f"Could not extract winner name or earned symbol from message ID {getattr(message, 'id', 'unknown')}. Winner name: '{winner_name}', Earned symbol: '{earned_symbol}'",
        )
        return  # Not a battle achievement message, ignore

    # Get the member object for the winner
    debug_log(
        f"Attempting to find member object for winner: '{winner_name}'",
    )
    member: discord.Member = await get_member_by_username(guild, winner_name)
    if not member:
        pretty_log(
            message=f"Could not find member with username '{winner_name}' in guild '{guild.name}'",
            tag="warn",
        )
        debug_log(f"Member not found for username: '{winner_name}'")
        return  # Member not found, ignore

    debug_log(f"Found member: {member.display_name} (ID: {member.id})")
    symbol_info = symbol_map.get(earned_symbol.lower())
    if not symbol_info:
        pretty_log(
            message=f"Unrecognized earned symbol: '{earned_symbol}' in message: '{content}'",
            tag="warning",
        )
        debug_log(f"Symbol info not found for: '{earned_symbol.lower()}'")
        return  # Symbol not in our map, ignore
    # Create and send the embed announcement
    debug_log(f"Preparing embed for symbol: '{earned_symbol}'")
    try:
        symbol_emoji = symbol_info["emoji"]
        npc_name = symbol_info["npc_name"]
        npc_emoji = symbol_info["npc_emoji"]
        challenge = symbol_info["challenge"]
        reward = symbol_info["reward"]
        reward_emoji = symbol_info["reward_emoji"]
        footer_image_url = symbol_info["footer_image_url"]
        footer_text = symbol_info.get("footer_text", "")
        thumbnail_url = symbol_info["thumbnail_url"]
        desc = (
            f"{member.mention} has earned the {symbol_emoji} **{earned_symbol}** by defeating {npc_emoji} **{npc_name}**!\n\n"
            f"**🎁 Extra Reward:** {reward_emoji} **{reward}**\n"
        )
        debug_log(f"Embed description: {desc}")
        embed = discord.Embed(
            title=f"{challenge} Completed!",
            url=message.jump_url,
            description=desc,
            timestamp=datetime.now(),
            color=0xB4CBF0,
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(text=footer_text, icon_url=footer_image_url)
        debug_log(f"Embed prepared. Checking for Battle Unlocks channel...")
        battle_unlocks_channel = guild.get_channel(
            CELESTIAL_TEXT_CHANNELS.battle_unlocks
        )
        if not battle_unlocks_channel:
            pretty_log(
                message=f"Could not find Battle Unlocks channel in guild '{guild.name}'",
                tag="error",
            )
            debug_log(
                f"Battle Unlocks channel not found in guild '{guild.name}'",
            )
            return  # Channel not found, ignore
        if not TESTING:
            debug_log(
                f"Sending Battle Frontier embed via webhook to channel '{battle_unlocks_channel.name}' ({battle_unlocks_channel.id})",
            )
            await send_webhook(
                bot=bot,
                channel=battle_unlocks_channel,
                embed=embed,
            )
            debug_log("Battle Frontier embed webhook send completed")
        else:
            debug_log(
                f"TESTING mode: sending embed to current channel instead.",
            )
            await message.channel.send(embed=embed)
        pretty_log(
            message=f"Announced Battle Frontier achievement for member '{member.display_name}' - earned symbol: '{earned_symbol}'",
            tag="info",
        )
    except Exception as e:
        pretty_log(
            message=f"Failed to announce Battle Frontier achievement for '{winner_name}' ({earned_symbol}): {e}",
            tag="critical",
        )
        debug_log(f"Battle Frontier announcement exception: {traceback.format_exc()}")
