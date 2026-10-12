import re

import discord

from constants.aesthetics import *
from constants.celestial_constants import (CC_GUILD_ID,
                                           CC_SPOOKY_HOUR_CHANNEL_ID,
                                           CELESTIAL_ROLES,
                                           CELESTIAL_TEXT_CHANNELS,
                                           CELESTIAL_SERVER_ID)
from utils.db.spooky_hour_db import (fetch_spooky_hour, remove_spooky_hour,
                                     upsert_spooky_hour)
from utils.functions.cleanup_first_match import cleanup_first_match
from utils.logs.pretty_log import pretty_log

from .spooky_hour_listener import (SpookyHourToggleButton,
                                   build_spooky_hour_embed)


async def handle_cc_spooky_hour_message(bot, message: discord.Message):
    if not message.embeds:
        return

    cc_embed = message.embeds[0]
    try:
        cc_ends_on = int(cc_embed.title.strip())
        cc_codes_count = int(cc_embed.description.strip())
    except (AttributeError, ValueError):
        pretty_log("warn", f"Ignoring invalid CC Spooky Hour embed in message {message.id}")
        return

    cc_footer_text = (
        cc_embed.footer.text.strip()
        if cc_embed.footer and cc_embed.footer.text
        else None
    )
    celestial_guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not celestial_guild:
        pretty_log("warn", f"Celestial guild {CELESTIAL_SERVER_ID} is not available in cache")
        return

    bumps_channel = celestial_guild.get_channel(CELESTIAL_TEXT_CHANNELS.bumps)
    if not bumps_channel:
        pretty_log("warn", "Celestial spooky hour announcement channel was not found")
        return

    spooky_hour_role = celestial_guild.get_role(CELESTIAL_ROLES.spooky_hour)
    if not spooky_hour_role:
        pretty_log("warn", "Celestial Spooky Hour role was not found")
        return

    existing_spooky_hour_info = await fetch_spooky_hour(bot)
    if existing_spooky_hour_info:
        existing_ends_on = existing_spooky_hour_info["ends_on"]
        existing_message_id = existing_spooky_hour_info["message_id"]
        existing_codes_count = existing_spooky_hour_info["special_code_count"]

        if (
            existing_ends_on == cc_ends_on
            and existing_codes_count == cc_codes_count
        ):
            return

        new_embed = build_spooky_hour_embed(
            celestial_guild, cc_ends_on, cc_codes_count, cc_footer_text
        )
        updated_message_id = existing_message_id
        existing_message = None
        if existing_message_id:
            try:
                existing_message = await bumps_channel.fetch_message(existing_message_id)
            except discord.NotFound:
                pass

        if existing_message:
            await existing_message.edit(embed=new_embed)
        else:
            await cleanup_first_match(
                bot=bot,
                channel=bumps_channel,
                component="description",
                phrase="Spooky Hour is active!",
            )
            new_message = await bumps_channel.send(
                embed=new_embed,
                content=f"{spooky_hour_role.mention} is now active!",
                view=SpookyHourToggleButton(),
            )
            updated_message_id = new_message.id

        zero_code_announced = (
            existing_spooky_hour_info["zero_code_announced"]
            if existing_ends_on == cc_ends_on
            else False
        )
        await upsert_spooky_hour(
            bot,
            cc_ends_on,
            updated_message_id,
            special_code_count=cc_codes_count,
            zero_code_announced=zero_code_announced,
        )
        pretty_log(
            "success",
            f"Updated spooky hour message with ends_on {cc_ends_on} and {cc_codes_count} codes",
        )
        await message.add_reaction("👻")
        return

    await cleanup_first_match(
        bot=bot,
        channel=bumps_channel,
        component="description",
        phrase="Spooky Hour is active!",
    )

    new_embed = build_spooky_hour_embed(
        celestial_guild, cc_ends_on, cc_codes_count, cc_footer_text
    )
    content = f"{spooky_hour_role.mention} is now active!"
    view = SpookyHourToggleButton()
    new_message = await bumps_channel.send(embed=new_embed, content=content, view=view)
    await upsert_spooky_hour(
        bot,
        cc_ends_on,
        new_message.id,
        special_code_count=cc_codes_count,
        zero_code_announced=False,
    )
    pretty_log("success", f"Created new spooky hour message with ends_on {cc_ends_on}")
    await message.add_reaction("✅")


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Spooky Hour Role Toggle Button
# 🤍💫────────────────────────────────────────────💫🤍
class SpookyHourToggleButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Toggle Spooky Hour Role",
        style=discord.ButtonStyle.secondary,
        emoji="👻",
        custom_id="toggle_spooky_hour_role_button",
    )
    async def toggle_role(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:

            role = interaction.guild.get_role(CELESTIAL_ROLES.spooky_hour)
            if not role:
                await interaction.response.send_message(
                    "Spooky Hour role not found.", ephemeral=True
                )
                return

            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(
                    f"{role.mention} role removed!", ephemeral=True
                )
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(
                    f"{role.mention} role added!", ephemeral=True
                )
        except Exception as e:
            pretty_log(
                "error",
                f"Error toggling Spooky Hour role: {e}",

                include_trace=True,
            )
            await interaction.response.send_message(
                "An error occurred while toggling the Spooky Hour role.",
                ephemeral=True,
            )
