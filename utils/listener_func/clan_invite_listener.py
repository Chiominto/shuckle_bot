import re
from datetime import datetime

import discord

from constants.aesthetics import *
from constants.celestial_constants import (
    CELESTIAL_CATEGORIES,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.db.celestial_members_db import fetch_clan_channel_id, upsert_celestial_member
from utils.functions.webhook_func import send_server_log, send_webhook
from utils.logs.debug_log import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

CLAN_CATEGORY_ID = 1490117523864158431

enable_debug(f"{__name__}.clan_invite_listener")


async def clan_invite_listener(bot: discord.Client, message: discord.Message):
    debug_log("Auto Clan Invite triggered")
    user_mention_pattern = r"<@(\d+)>"
    debug_log(f"Searching for user mention in message: {message.content}")
    match = re.search(user_mention_pattern, message.content)
    pokemeow_name = "N/A"

    if not match:
        debug_log("No user mention found in the message content.")
        return

    user_id = match.group(1)
    debug_log(f"Extracted User ID: {user_id}")
    try:
        user = await bot.fetch_user(int(user_id))
        pokemeow_name = user.name
        debug_log(f"Fetched user: {user.name}#{user.discriminator}")

        replied_message = message.reference.resolved if message.reference else None
        if not replied_message:
            debug_log("No replied message found")
        if replied_message and replied_message.content:
            debug_log(f"Found replied message: {replied_message.content}")
            match = re.search(
                r"has invited \\*\\*(.*?)\\*\\* to join", replied_message.content
            )
            if match:
                pokemeow_name = match.group(1)
                debug_log(
                    f"Extracted pokemeow_name from replied message: {pokemeow_name}"
                )
    except Exception as e:
        debug_log(f"Error fetching user with ID {user_id}: {e}")
        return

    guild = message.guild
    member = guild.get_member(user.id)
    if not member:
        debug_log(
            f"User {user.name}#{user.discriminator} is not a member of the guild."
        )
        return
    debug_log(f"Member found: {member.name} (ID: {member.id})")

    processing_msg = None
    if replied_message:
        processing_msg = await replied_message.reply(
            content=f"{Emojis.loading} Processing clan invite for **{user.name}**..."
        )

    new_member_channel = None
    # Check if member already has a clan channel
    debug_log(f"Fetching clan channel ID for member {member.id}")
    existing_channel_id = await fetch_clan_channel_id(bot=bot, user_id=member.id)
    existing_channel = None
    debug_log(f"Existing channel ID result: {existing_channel_id}")
    if existing_channel_id:
        debug_log(f"Looking up channel object for ID {existing_channel_id}")
        existing_channel = guild.get_channel(existing_channel_id)
        if existing_channel:
            new_member_channel = existing_channel
            debug_log(
                f"Member {member.name} already has a clan channel: {existing_channel.name}"
            )
        else:
            debug_log(
                f"Channel ID {existing_channel_id} exists in DB but channel not found in guild"
            )
    # Make channel first
    if not existing_channel:
        debug_log(
            f"No usable existing channel found. Creating new channel for {member.name}"
        )
        try:
            new_member_channel = await guild.create_text_channel(
                name=f"🌌・{member.name}",
                category=guild.get_channel(CLAN_CATEGORY_ID),
            )
            debug_log(
                f"Successfully created new channel: {new_member_channel.name} (ID: {new_member_channel.id})"
            )
        except Exception as e:
            debug_log(f"Error creating channel for {member.name}: {e}")
            pretty_log(
                message=f"❌ Failed to create channel for **{member.name}**. Error: {e}",
                tag="error",
            )
            if processing_msg:
                await processing_msg.edit(
                    content=f"{Emojis.error} Failed to create channel for **{member.name}**."
                )
            return

    # Upsert member to DB
    try:
        await upsert_celestial_member(
            bot=bot,
            user_id=member.id,
            pokemeow_name=pokemeow_name,
            user_name=member.name,
            channel_id=new_member_channel.id,
        )
        debug_log(
            f"Upserted member {member.name} to database with channel ID {new_member_channel.id}"
        )
        pretty_log(
            message=f"✅ Successfully processed clan invite for **{member.name}**.",
            tag="success",
        )
    except Exception as e:
        debug_log(f"Error upserting member {member.name} to DB: {e}")
        pretty_log(
            message=f"❌ Failed to upsert member **{member.name}** to database. Error: {e}",
            tag="error",
        )
        if processing_msg:
            await processing_msg.edit(
                content=f"{Emojis.error} Failed to save member **{member.name}** to database."
            )
        return

    # Add roles to member
    clan_member_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)
    coin_saver_role = guild.get_role(CELESTIAL_ROLES.coin_saver)
    drifting_star_role = guild.get_role(CELESTIAL_ROLES.driftingstar)
    adventurer_role = guild.get_role(CELESTIAL_ROLES.adventurer)
    try:
        debug_log(
            f"Attempting to add roles to {member.name}. Clan role ID: {clan_member_role.id if clan_member_role else 'None'}, Coin saver role ID: {coin_saver_role.id if coin_saver_role else 'None'}"
        )
        await member.add_roles(clan_member_role, coin_saver_role)
        debug_log(f"Added roles to {member.name} successfully.")
        if drifting_star_role and adventurer_role:
            # Remove both roles from member if they have them cuz its guest roles
            if drifting_star_role in member.roles:
                await member.remove_roles(drifting_star_role)
                debug_log(f"Removed drifting star role from {member.name}")
            if adventurer_role in member.roles:
                await member.remove_roles(adventurer_role)
                debug_log(f"Removed adventurer role from {member.name}")

    except Exception as e:
        debug_log(f"Error adding roles to {member.name}: {e}")
        pretty_log(
            message=f"⚠️ Failed to assign roles to **{member.name}**. Error: {e}",
        )
        if processing_msg:
            await processing_msg.edit(
                content=f"{Emojis.error} Failed to assign roles to **{member.name}**."
            )
    clan_instructions = """1. Do `;clan` to be registered properly
2. Head over to <#1490470353099817030> for the server rules and role breakdowns
3. <#1493874658347450441>  for helpful tips and information on Celestial
4. All clan/weekly donations are in <#1492032552654077992>
5. `!h` for vast knowledge on PokéMeow provided by Khy
6. Any additional questions or concerns please reach out to Burger or Fries."""

    instructions_embed = discord.Embed(
        title=f"Welcome to the Celestial Clan, {member.name}! 🌌",
        description=clan_instructions,
        color=DEFAULT_EMBED_COLOR,
        timestamp=datetime.now(),
    )
    instructions_embed.set_thumbnail(
        url=member.display_avatar.url if member.display_avatar else None
    )
    debug_log(f"Sending instructions embed to channel {new_member_channel.name}")
    instruction_msg = await new_member_channel.send(embed=instructions_embed)
    await instruction_msg.pin()
    debug_log(f"Instructions message pinned in {new_member_channel.name}")

    invite_success_message = f"""Welcome to Celestial {member.mention} <a:sparkles:1492709079108288574>
Where legends rise and stars align.
Glad to have you with us—let’s shine together!

Please head over to your own personal channel ([{new_member_channel.name}]({new_member_channel.jump_url})) with additional tips and suggestions"""

    invite_success_embed = discord.Embed(
        description=invite_success_message,
        color=DEFAULT_EMBED_COLOR,
        timestamp=datetime.now(),
    )
    invite_success_embed.set_thumbnail(
        url=member.display_avatar.url if member.display_avatar else None
    )
    if processing_msg:
        await processing_msg.delete()
        debug_log("Deleted processing message")
    debug_log(f"Sending final invite success message")
    await message.reply(content=member.mention, embed=invite_success_embed)
    debug_log(f"Clan invite listener completed successfully for {member.name}")

    # Make log embed
    log_embed_description = (
        f"**Member:** {member.mention}\n"
        f"**PokéMeow Name:** {pokemeow_name}\n"
        f"**Channel:** {new_member_channel.mention}\n"
        f"**Account Created:** {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"**Joined Server:** {member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"**Joined Clan:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    log_embed = discord.Embed(
        title="New Clan Member Added",
        description=log_embed_description,
        color=DEFAULT_EMBED_COLOR,
        timestamp=datetime.now(),
    )
    log_embed.set_thumbnail(
        url=member.display_avatar.url if member.display_avatar else None
    )
    log_embed.set_footer(
        text=f"User ID: {member.id}", icon_url=guild.icon.url if guild.icon else None
    )
    log_embed.set_author(
        name=member.display_name,
        icon_url=member.display_avatar.url if member.display_avatar else None,
    )

    await send_server_log(
        bot=bot,
        embed=log_embed,
    )
