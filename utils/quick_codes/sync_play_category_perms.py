import discord
from discord.ext import commands

from constants.aesthetics import Emojis
from utils.logs.pretty_log import pretty_log

SOURCE_CATEGORY_ID = 1490117523864158431


# 🍭──────────────────────────────
#   🎀 Sync Play Category Perms
# 🍭──────────────────────────────
async def sync_play_category_perms(
    bot: discord.Client,
    message: discord.Message,
):
    """Copies permission overwrites from the source category to the category this command is run in."""
    processing_msg = await message.reply(
        f"{Emojis.loading} Syncing category permissions..."
    )

    try:
        target_category = message.channel.category
        if target_category is None:
            await processing_msg.edit(
                content=f"{Emojis.error} This channel is not in a category."
            )
            return

        source_category = message.guild.get_channel(SOURCE_CATEGORY_ID)
        if source_category is None or not isinstance(
            source_category, discord.CategoryChannel
        ):
            await processing_msg.edit(
                content=f"{Emojis.error} Source category `{SOURCE_CATEGORY_ID}` not found."
            )
            return

        if target_category.id == source_category.id:
            await processing_msg.edit(
                content=f"{Emojis.error} The target and source categories are the same."
            )
            return

        # Copy all permission overwrites from source to target
        for target, overwrite in source_category.overwrites.items():
            await target_category.set_permissions(target, overwrite=overwrite)

        # Remove any overwrites in target that don't exist in source
        for target in list(target_category.overwrites.keys()):
            if target not in source_category.overwrites:
                await target_category.set_permissions(target, overwrite=None)

        pretty_log(
            "info",
            f"Synced perms from category '{source_category.name}' ({source_category.id}) "
            f"to '{target_category.name}' ({target_category.id})",
        )
        await processing_msg.edit(
            content=f"{Emojis.check} Copied permissions from **{source_category.name}** to **{target_category.name}**."
        )

    except Exception as e:
        pretty_log("error", f"Error syncing category perms: {e}")
        await processing_msg.edit(
            content=f"{Emojis.error} Error syncing category permissions: `{e}`"
        )
