import asyncio
import re
from datetime import datetime

import discord

from constants.aesthetics import Emojis
from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
)
from utils.db.celestial_members_db import (
    fetch_celestial_member,
    remove_celestial_member,
)
from utils.functions.pokemeow_reply import get_pokemeow_reply_member
from utils.functions.webhook_func import send_webhook
from utils.listener_func.channel_boost import contact_booster_to_remove_boost
from utils.logs.pretty_log import pretty_log


def get_roles(guild: discord.Guild, *role_ids: int) -> list[discord.Role | None]:
    """✨ Fetch multiple role objects by ID"""
    return [guild.get_role(rid) for rid in role_ids]


# ୨୧┈🌟 Visual Helpers ┈🌟┈୨୧
def set_member_visuals(embed: discord.Embed, member: discord.Member):
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    embed.set_thumbnail(url=member.display_avatar.url)


def clan_removed_embed(
    member: discord.Member,
    channel_name: str,
):
    desc = f""" # REMOVED FROM CLAN
- Member: {member.mention}
- Role Added: <@&{CELESTIAL_ROLES.former_clan_member}>
- Channel Deleted: {channel_name} """

    embed = discord.Embed(
        description=desc, color=DEFAULT_EMBED_COLOR, timestamp=datetime.now()
    )
    set_member_visuals(embed=embed, member=member)
    guild_icon_url = member.guild.icon.url if member.guild.icon else None
    embed.set_footer(text=f"User ID: {member.id}", icon_url=guild_icon_url)
    return embed


# 🌊────────────────────────────────────────────
#        🐾 Handle Clan Leave Command
# 🌊────────────────────────────────────────────
async def process_clan_leave_command(bot: discord.Client, message: discord.Message):
    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    replied_message = message.reference.resolved if message.reference else None
    if not replied_message:
        pretty_log(
            "warn",
            f"Leave command by {member.display_name} has no replied message to reference.",
            label="Clan Leave",
        )
        return

    await auto_clan_remove_func(
        bot=bot, member=member, message=replied_message, context="clan_leave"
    )


# 🌊────────────────────────────────────────────
#        🐾 Process Clan Kick Message
# 🌊────────────────────────────────────────────
async def process_clan_kick_message(bot: discord.Client, message: discord.Message):
    """
    Extracts the user ID from a kick message.
    Example:
    "You spent <:PokeCoin:666879070650236928> **100,000** to kick eternitystormn (ID: 1059988741122445383) from Straymons."
    -> 1059988741122445383
    Returns None if not found.
    """
    content = message.content
    if not content:
        pretty_log(
            "warn",
            f"Empty content in kick message ID {message.id}",
            label="Clan Kick",
        )
        return

    match = re.search(r"\(ID:\s*(\d+)\)", content)
    if not match:
        pretty_log(
            "warn",
            f"No user ID found in kick message ID {message.id}",
            label="Clan Kick",
        )
        return

    user_id = int(match.group(1))
    guild = message.guild
    if guild is None:
        pretty_log(
            "warn",
            f"Kick message ID {message.id} is not from a guild context.",
            label="Clan Kick",
        )
        return

    member = guild.get_member(user_id)
    if not member:
        pretty_log(
            tag="warn",
            message=(
                f"User {user_id} referenced in kick message {message.id} "
                "is no longer a member of the server."
            ),
            label="Clan Kick",
        )
        return

    replied_message = message.reference.resolved if message.reference else None
    if not replied_message:
        pretty_log(
            "warn",
            f"Kick message ID {message.id} has no replied message to reference.",
            label="Clan Kick",
        )
        return

    await auto_clan_remove_func(
        bot=bot, member=member, message=replied_message, context="clan_kick"
    )


# ──────────────────────────────────────────────
async def auto_clan_remove_func(
    bot: discord.Client, member: discord.Member, message: discord.Message, context: str
):

    guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if guild is None:
        pretty_log(
            tag="error",
            message=f"Guild {CELESTIAL_SERVER_ID} not found in bot cache during clan removal.",
            label="🛟 Clan Remove",
        )
        return

    user_id = member.id
    info = await fetch_celestial_member(bot=bot, user_id=user_id)

    if not info:
        return

    # Info
    process_message: discord.Message | None = None
    channel_id = info.get("channel_id")

    try:
        if context == "clan_kick":
            try:
                process_message = await message.reply(
                    content=f"{Emojis.loading} Processing clan removal for {member.display_name}...",
                    mention_author=False,
                )
            except Exception as e:
                pretty_log(
                    tag="warn",
                    message=f"Failed to send kick processing message for {member.display_name}: {e}",
                    label="🛟 Clan Remove",
                )

        # 🪄 Role references
        clan_member_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)


        # 🧠 Log: Role check
        pretty_log(
            tag="info",
            message=f"💭 Checking if {member.display_name} is a Clan Member...",
            label="🛟 Clan Remove",
        )

        if not clan_member_role or clan_member_role not in member.roles:
            pretty_log(
                tag="warn",
                message="❌ Member is not in Celestials.",
                label="🛟 Clan Remove",
            )
            return

        # 🗃 Get registered channel
        member_channel = guild.get_channel(channel_id) if channel_id else None
        pretty_log(
            tag="info",
            message=f"📺 Registered Channel: {member_channel.name if member_channel else 'None'}",
            label="🛟 Clan Remove",
        )
        member_channel_name = member_channel.name if member_channel else "No Channel"
        # 🧹 Begin cleanup
        cleanup_ok = await auto_clan_remove_handler(
            bot=bot,
            member=member,
            channel=member_channel,
        )
        if not cleanup_ok:
            pretty_log(
                tag="warn",
                message=f"Clan removal handler failed for {member.display_name}; skipping DB removal.",
                label="🛟 Clan Remove",
            )
            return

        await remove_celestial_member(bot=bot, user_id=user_id)

        await asyncio.sleep(1.5)  # 💤 Tiny pause for flow
        if context == "clan_leave":
            try:
                await message.reply(
                    f"💔 Goodbye, {member.display_name}! Thank you for your time in the clan. 🐾\n"
                    "We wish you all the best on your adventures ahead!",
                    mention_author=False,
                )
                await message.add_reaction("👋")
            except Exception as e:
                pretty_log(
                    tag="info",
                    message=f"Failed to send farewell message for {member.display_name}: {e}",
                    label="🛟 Clan Remove",
                )

        elif context == "clan_kick":
            if process_message and isinstance(process_message, discord.Message):
                embed = clan_removed_embed(
                    member=member,
                    channel_name=member_channel_name,
                )
                await process_message.edit(content="", embed=embed)

        pretty_log(
            tag="success",
            message=f"✅ Clan removal process completed for {member.display_name}",
            label="🛟 Clan Remove",
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"💥 Exception during clan-remove: {e}",
            label="🛟 Clan Remove",
        )


# ──────────────────────────────────────────────
# 🧹 Handler: Remove a member from the clan
# ──────────────────────────────────────────────
async def auto_clan_remove_handler(
    bot: discord.Client,
    member: discord.Member,
    channel: discord.TextChannel | None,
) -> bool:
    guild = member.guild
    pretty_log(
        "info",
        f"📤 Starting clan removal for {member.display_name}",
    )

    try:

        # ──────────────────────────────────────────────
        # 🎭 Gather all relevant roles in one go
        # ──────────────────────────────────────────────
        roles = get_roles(
            guild,
            CELESTIAL_ROLES.former_clan_member,
            CELESTIAL_ROLES.celestialnova_,
            CELESTIAL_ROLES.top_catcher,
            CELESTIAL_ROLES.nebula,
            CELESTIAL_ROLES.comet,
            CELESTIAL_ROLES.supernova,
            CELESTIAL_ROLES.golden_fry_disciple,
            CELESTIAL_ROLES.patreon_auctions_ping,
            CELESTIAL_ROLES.incense_ping,
            CELESTIAL_ROLES.ee_ping,
            CELESTIAL_ROLES.out_of_orbit,
            CELESTIAL_ROLES.grounded,
            CELESTIAL_ROLES.coin_saver,
            CELESTIAL_ROLES.tip_jar_titan,
            CELESTIAL_ROLES.os_lottery,
            CELESTIAL_ROLES.shiny_bonus,
            CELESTIAL_ROLES.giveaways,
            CELESTIAL_ROLES.battle_tower,
        )

        # 🐾 Unpack roles
        Former_Clan_Member_Role = roles[0]
        roles_to_remove = roles[1:]

        if Former_Clan_Member_Role is None:
            pretty_log(
                "warn",
                "⚠️ Former clan member role is missing; skipping clan removal role updates.",
            )
            return False

        pretty_log(
            "info",
            f"🧽 Removing {len(roles_to_remove)} roles and giving Stray role to {member.display_name}...",
        )

        # 🪄 Apply role changes
        try:
            await member.add_roles(Former_Clan_Member_Role)
            await member.remove_roles(*filter(None, roles_to_remove))
        except discord.errors.NotFound as e:
            pretty_log(
                "info",
                f"Member {member.display_name} not found during role removal: {e}",
            )
            return False
        except Exception as e:
            pretty_log(
                "info",
                f"Unexpected error during role removal for {member.display_name}: {e}",
            )
            return False

        await asyncio.sleep(1)  # ⏳ Small delay for safety

        # ──────────────────────────────────────────────
        # 🎨 Build pretty "removed" embed
        # ──────────────────────────────────────────────
        embed = clan_removed_embed(
            member=member, channel_name=channel.name if channel else "No Channel"
        )

        # ──────────────────────────────────────────────
        # 📋 Log to staff report channel
        # ──────────────────────────────────────────────
        log_channel = guild.get_channel(CELESTIAL_TEXT_CHANNELS.server_logs)
        if log_channel:
            await send_webhook(
                bot=bot,
                channel=log_channel,
                embed=embed,
            )
            pretty_log(
                "success",
                f"✅ Clan removal completed and logged for {member.display_name} in #{log_channel.name}",
            )
        else:
            pretty_log(
                "warn",
                f"⚠️ Reports channel not found, removal logged only to interaction for {member.display_name}",
            )
        # Contact booster to remove their boost
        if channel:
            await contact_booster_to_remove_boost(
                bot=bot,
                channel_id=channel.id,
                member=member,
                context="clan_remove",
                channel_name=channel.name,
            )
            # ──────────────────────────────────────────────
            # 📦 Auto Channel Delete
            # ──────────────────────────────────────────────
            (
                await channel.delete(reason=f"Clan removal for {member.display_name}")
                if channel
                else None
            )

        return True

    except Exception as e:
        pretty_log(
            "error",
            f"💥 Error during clan removal for {member.display_name}: {e}",
        )
        return False
