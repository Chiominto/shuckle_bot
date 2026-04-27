import re
from datetime import datetime

import discord
from constants.celestial_constants import (
    CELESTIAL_TEXT_CHANNELS,
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
    CELESTIAL_BANK_USER_ID,
    CELESTIAL_EMOJIS
)
from constants.aesthetics import Thumbnails
from utils.functions.webhook_func import send_server_log
from utils.logs.pretty_log import pretty_log
from utils.db.celestial_members_db import(
    update_clan_bank_donation,
    update_clan_treasury_donation,
    fetch_clan_bank_donation,
    fetch_clan_treasury_donation,
    fetch_donation_record
)
from utils.functions.pokemeow_reply import get_pokemeow_reply_member
from utils.functions.pokemon_func import format_price_w_coin
from utils.functions.design_embed import design_embed
MIN_DONATION_AMOUNT = 100_000
CLAN_BANK_IDS = [CELESTIAL_BANK_USER_ID]

def extract_pokecoins_amount_from_donate(text: str) -> int:
    """
    Extracts the donated PokeCoins amount from a message like:
    'You successfully donated <...> **50,000** to ...'
    """
    match = re.search(
        r"donated.*?\*\*(?P<amount>[\d,]+)\*\*",
        text,
        re.IGNORECASE,
    )

    if match:
        amount = int(match.group("amount").replace(",", ""))
        pretty_log(
            "info",
            f"[EXTRACT] Extracted amount {amount} from donation message: {text}",
        )
        return amount

    pretty_log(
        "info",
        f"[EXTRACT] Could not extract amount from donation message: {text}",
    )
    return 0


def extract_any_pokecoins_amount(text: str) -> int:
    """
    Extracts the PokeCoins amount immediately preceding 'PokeCoins'
    and returns it as an int.
    """
    match = re.search(
        r"([\d,]+)\s*PokeCoins?",
        text,
        re.IGNORECASE,
    )

    if match:
        amount = int(match.group(1).replace(",", ""))
        pretty_log(
            "info",
            f"[EXTRACT] Extracted PokeCoins amount: {amount} from message: {text}",
        )
        return amount

    pretty_log(
        "info",
        f"[EXTRACT] Could not extract PokeCoins amount from message: {text}",
    )
    return 0


async def clan_donate_listener(bot: discord.Client, message: discord.Message):
    # Get replied message
    if not message.reference:
        return
    replied_message = (
        message.reference.resolved.content if message.reference.resolved else None
    )
    if not replied_message:
        return

    # Get member
    member = await get_pokemeow_reply_member(message)
    if not member:
        pretty_log(
            "info",
            f"Could not get member from PokéMeow reply for message {message.id}. Ignoring.",
        )
        return
    # Extract donation amount from message content
    content = message.content
    amount = extract_pokecoins_amount_from_donate(content)
    if amount < MIN_DONATION_AMOUNT:
        pretty_log(
            "info",
            f"Extracted amount {amount} is less than minimum donation amount. Ignoring.",
        )
        return
    await process_donation(
        bot, member, amount, context="clan treasury", message=message, replied_message=replied_message
    )


async def give_command_listener(bot: discord.Client, message: discord.Message):

    # Get replied message
    if not message.reference:
        return
    replied_message = (
        message.reference.resolved.content if message.reference.resolved else None
    )
    if not replied_message:
        return

    # Get member
    member = await get_pokemeow_reply_member(message)
    if not member:
        pretty_log(
            "info",
            f"Could not get member from PokéMeow reply for message {message.id}. Ignoring.",
        )
        return

    # Check if any of the clan bank ids are mentioned in the replied message
    if not any(str(clan_bank_id) in replied_message for clan_bank_id in CLAN_BANK_IDS):
        pretty_log(
            "info",
            f"Message {message.id} does not mention any of the clan bank ids. Ignoring.",
        )
        return
    # Extract amount from the message content using regex
    amount = extract_any_pokecoins_amount(message.content)
    if (
        amount < MIN_DONATION_AMOUNT and member.id != KHY_USER_ID
    ):  # Kyra's donations can be any amount for testing
        pretty_log(
            "info",
            f"Extracted amount {amount} is less than minimum donation amount. Ignoring.",
        )
        return
    await process_donation(bot, member, amount, context="clan bank", message=message, replied_message=replied_message)


async def process_donation(
    bot: discord.Client,
    member: discord.Member,
    amount: int,
    context: str,
    message: discord.Message,
    replied_message: discord.Message
):

    # Fetch donation record
    donation_record = await fetch_donation_record(bot, member.id)
    clan_treasury_donations = donation_record["clan_treasury_donation"] if donation_record else 0
    clan_bank_donations = donation_record["clan_bank_donation"] if donation_record else 0

    # Get roles
    not_donated_role = member.guild.get_role(CELESTIAL_ROLES.coin_saver)
    donated_role = member.guild.get_role(CELESTIAL_ROLES.tip_jar_titan)

    # Update roles
    if not_donated_role in member.roles:
        try:
            await member.remove_roles(not_donated_role, reason="Made a donation")
            pretty_log(
                "info",
                f"Removed role {not_donated_role.name} from member {member.id} for making a donation.",
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to remove role {not_donated_role.name} from member {member.id}: {e}",
                include_trace=True,
            )
    if donated_role not in member.roles:
        try:
            await member.add_roles(donated_role, reason="Made a donation")
            pretty_log(
                "info",
                f"Added role {donated_role.name} to member {member.id} for making a donation.",
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to add role {donated_role.name} to member {member.id}: {e}",
                include_trace=True,
            )
            

    # Log the donation
    if context == "clan bank":
        title = "Clan Bank Donation"
        thumbnail_url = Thumbnails.bank
        new_total = clan_bank_donations + amount
        await update_clan_bank_donation(bot, member.id, new_total)
    else:
        title = "Clan Treasury Donation"
        thumbnail_url = Thumbnails.treasury
        new_total = clan_treasury_donations + amount
        await update_clan_treasury_donation(bot, member.id, new_total)

    amount_formatted = format_price_w_coin(amount)
    embed = discord.Embed(
        title=title,
        url=message.jump_url,
        description=(
            f"- **Member:** {member.mention}\n"
            f"- **Amount:** {amount_formatted}\n"
            f"- **New Total {context.title()} Donations:** {format_price_w_coin(new_total)}"
        ),
        color=DEFAULT_EMBED_COLOR,
        timestamp=datetime.now(),
    )
    embed = design_embed(embed=embed, user=member, thumbnail_url=thumbnail_url)
    await send_server_log(
        bot=bot,
        embed=embed,
    )

    # Add reaction to the message to acknowledge the donation
    try:
        await replied_message.add_reaction("✅")
        await replied_message.add_reaction(CELESTIAL_EMOJIS.snorlax_coin)
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to add reaction to message {message.id}: {e}",
            include_trace=True,
        )
