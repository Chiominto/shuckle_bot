import re

import discord

from constants.aesthetics import *
from constants.celestial_constants import (CC_GUILD_ID,
                                           CC_SPOOKY_HOUR_CHANNEL_ID,
                                           CELESTIAL_ROLES,
                                           CELESTIAL_TEXT_CHANNELS)
from utils.db.spooky_hour_db import (fetch_spooky_hour, remove_spooky_hour,
                                     upsert_spooky_hour)
from utils.functions.cleanup_first_match import cleanup_first_match
from utils.logs.pretty_log import pretty_log


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Extract Spooky Hour Helper Functions
# 🤍💫────────────────────────────────────────────💫🤍
def extract_spooky_hour_ts(text: str):
    """
    Extracts the timestamp from the line containing '**Spooky Hour**' in the embed description.
    Returns the integer timestamp if found, else None.
    """
    for line in text.splitlines():
        if "**Spooky Hour**" in line:
            match = re.search(r"<t:(\d+):f>", line)
            if match:
                return int(match.group(1))
    return None


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Spooky Hour Embed Builder
# 🤍💫────────────────────────────────────────────💫🤍
def build_spooky_hour_embed(
    guild: discord.Guild,
    ends_on: int,
    codes_count: int = None,
    footer_text: str = None,
):
    halloween_color = 0xFFA500  # Orange color for Halloween theme
    if codes_count is None:
        codes_count = 0
    if codes_count > 0:
        code_status = (
            f"> - **{codes_count} codes** remain to be claimed (max. 1 per account)"
        )
    else:
        code_status = f"> - **All codes have been claimed!**"
    desc = f"""## Spooky Hour is active!
💝 Bonuses active:
- {Emojis.Golden} Promo item __GOLDEN DERPY CHARM__ is unlocked (team still required)
> - Check `!promo`!
- 🏆 Halloween Catch Contest is now enabled `;hween contest`
- ⚔️ Lusamine challenge is now enabled `;b npc 963`
{code_status}
> - Check `;hw` for more info!
- ⏱️ Ends on: <t:{ends_on}:f>
"""

    embed = discord.Embed(description=desc, color=halloween_color)
    embed.set_footer(
        text=footer_text or "🎃 To view the special activity, type ;hw special 🔎",
        icon_url=guild.icon.url if guild.icon else None,
    )

    return embed


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Irida Codes Extraction Function
# 🤍💫────────────────────────────────────────────💫🤍
def extract_irida_codes_count(embed: discord.Embed) -> int | None:
    """
    Extracts the number of codes remaining from the ;hw embed.
    Searches the description and all field values for a '**N codes**' pattern
    (the codes line currently lives in the Lusamine challenge field).
    Returns the integer count if found, else None.
    """
    texts = [embed.description or ""]
    texts.extend(field.value or "" for field in embed.fields)
    for text in texts:
        match = re.search(r"\*\*(\d+)\s+codes\*\*", text)
        if match:
            return int(match.group(1))
    return None

def create_cc_spooky_hour_embed(ends_on: int, footer_text: str = None, codes_count: int = None):
    """Builds an embed with information about the Spooky Hour event."""
    if codes_count is None:
        codes_count = 0
    embed = discord.Embed(
        title =ends_on,
        description = codes_count,
        color=0xFFA500,  # Orange color for Halloween theme
    )
    embed.set_footer(
        text=footer_text
    )
    return embed

# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Spooky Hour Listener Functions
# 🤍💫────────────────────────────────────────────💫🤍
async def handle_spooky_hour_hw_embed(bot: discord.Client, message: discord.Message):
    """
    Handles the Spooky Hour embed in the given message.
    Extracts the timestamp and upserts/removes from DB accordingly.
    """
    if not message.embeds:
        return

    embed = message.embeds[0]
    if not embed.description:
        return
    event_tracker_channel = message.guild.get_channel(CELESTIAL_TEXT_CHANNELS.bumps)
    spooky_hour_role = message.guild.get_role(CELESTIAL_ROLES.spooky_hour)
    if "[INACTIVE]" not in embed.description:
        ends_on = extract_spooky_hour_ts(embed.description)
        if ends_on:
            # Check for existing schedule first
            existing_spooky_hour_info = await fetch_spooky_hour(bot)
            if existing_spooky_hour_info:
                existing_ends_on = existing_spooky_hour_info["ends_on"]
                existing_message_id = existing_spooky_hour_info["message_id"]

                if existing_ends_on != ends_on:
                    # 🔄 New schedule info — update the previous embed with new details
                    footer_text = embed.footer.text if embed.footer else None
                    codes_count = extract_irida_codes_count(embed)
                    if codes_count is None:
                        codes_count = (
                            existing_spooky_hour_info.get("special_code_count") or 0
                        )
                    updated_embed = build_spooky_hour_embed(
                        message.guild, ends_on, codes_count, footer_text=footer_text
                    )

                    updated_message_id = existing_message_id
                    try:
                        previous_message = await event_tracker_channel.fetch_message(
                            existing_message_id
                        )
                        await previous_message.edit(embed=updated_embed)
                        pretty_log(
                            "success",
                            f"Updated spooky hour embed {existing_message_id} with new ends_on {ends_on}",

                        )
                    except discord.NotFound:
                        # Previous message was deleted — send a fresh one
                        await cleanup_first_match(
                            bot=bot,
                            channel=event_tracker_channel,
                            component="description",
                            phrase="Spooky Hour is active!",
                        )
                        view = SpookyHourToggleButton()
                        content = f"{spooky_hour_role.mention} is now active!"
                        new_message = await event_tracker_channel.send(
                            content=content, embed=updated_embed, view=view
                        )
                        updated_message_id = new_message.id
                        pretty_log(
                            "info",
                            f"Previous spooky hour message {existing_message_id} not found, sent new message {new_message.id}",

                        )

                    await upsert_spooky_hour(
                        bot,
                        ends_on,
                        updated_message_id,
                        special_code_count=codes_count,
                    )
                elif existing_ends_on == ends_on:
                    pretty_log(
                        "info",
                        f"Same schedule already exists with ends_on {ends_on}",

                    )
                    return
            else:
                # No existing schedule, insert new
                # Remove view from old message if exists
                await cleanup_first_match(
                    bot=bot,
                    channel=event_tracker_channel,
                    component="description",
                    phrase="Spooky Hour is active!",
                )
                footer_text = embed.footer.text if embed.footer else None
                codes_count = extract_irida_codes_count(embed)
                embed = build_spooky_hour_embed(
                    message.guild, ends_on, codes_count, footer_text=footer_text
                )
                view = SpookyHourToggleButton()
                content = f"{spooky_hour_role.mention} is now active!"
                new_message = await event_tracker_channel.send(
                    content=content, embed=embed, view=view
                )
                await upsert_spooky_hour(
                    bot, ends_on, new_message.id, special_code_count=codes_count
                )
                pretty_log(
                    "success",
                    f"Inserted new spooky_hour with ends_on {ends_on} and message_id {new_message.id}",

                )

                # Create CC info embed and send it to the CC Spooky Hour channel
                cc_guild = bot.get_guild(CC_GUILD_ID)
                cc_spooky_hour_channel = bot.get_channel(CC_SPOOKY_HOUR_CHANNEL_ID)
                if cc_spooky_hour_channel:
                    # Create embed
                    cc_embed = create_cc_spooky_hour_embed(ends_on=ends_on, footer_text=footer_text, codes_count=codes_count)
                    await cc_spooky_hour_channel.send(embed=cc_embed)
                    pretty_log(
                        "success",
                        f"Sent Spooky Hour embed to CC channel {CC_SPOOKY_HOUR_CHANNEL_ID}",

                    )
                else:
                    pretty_log(
                        "info",
                        "CC spooky hour channel not found, skipping CC embed",

                    )

                return

    elif "[INACTIVE]" in embed.description:
        # Check if there is existing schedule to remove
        existing_ends_on = await fetch_spooky_hour(bot)
        if existing_ends_on:
            await remove_spooky_hour(bot)
            content = f"{spooky_hour_role.mention} has ended."
            await event_tracker_channel.send(content=content)
            pretty_log(
                "success",
                "Removed existing spooky_hour schedule",

            )
        else:
            pretty_log(
                "info",
                "No existing spooky_hour schedule to remove",

            )
            return


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
