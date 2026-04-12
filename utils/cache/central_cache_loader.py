import discord

from utils.logs.pretty_log import pretty_log

from .pokemon_cache import load_pokemon_cache
from .celestial_members_cache import load_celestial_members_cache


from .webhook_url_cache import load_webhook_url_cache


async def load_all_cache(bot: discord.Client):
    """
    Loads all caches used by the bot.
    """
    try:

        # Load Celestial Members Cache
        await load_celestial_members_cache(bot)
        # Load Pokemon Cache
        await load_pokemon_cache(bot)
        # Load Webhook URL Cache
        await load_webhook_url_cache(bot)


    except Exception as e:
        pretty_log(
            message=f"❌ Error loading caches: {e}",
            tag="cache",
        )
        return
    pretty_log(
        message="✅ All caches loaded successfully.",
        tag="cache",
    )
