import discord
from discord.ext import commands

from utils.db.banned_members_db import delete_banned_member
from utils.logs.pretty_log import pretty_log
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_server_log


# 🤍────────────────────────────────────────────
#     ⚡ Unban Functionality
# 🤍────────────────────────────────────────────
async def unban_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    user: discord.User | None = None,
    user_id: str | None = None,
    reason: str | None = None,
):
    """
    Main unban logic.
    Handles unbanning a member and removes them from the banned_users table.
    """
    loader = await pretty_defer(
        interaction=interaction, content="Processing unban...", ephemeral=True
    )

    # Validate input
    if user is None and user_id is None:
        msg = "You must provide either a member or a user ID."
        await loader.error(msg)
        return

    if user_id:
        user_id = int(user_id)

    # Resolve global user if only ID is given
    if user is None and user_id is not None:
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            msg = f"No user found with ID {user_id}."
            await loader.error(msg)
            return
        except discord.HTTPException:
            msg = f"Failed to fetch user with ID {user_id}."
            await loader.error(msg)
            return

    target_id = user.id
    target_name = user.name  # username#discriminator
    guild_id = interaction.guild.id if interaction.guild else 0

    # 1️⃣ Remove from banned_users table
    result, error_msg = await delete_banned_member(bot, user_id=target_id)
    if error_msg:
        await loader.error(f"Failed to remove ban from database: {error_msg}")
        return
    # 2️⃣ Perform Discord unban
    if interaction.guild:
        try:
            await interaction.guild.unban(
                user, reason=reason or "Unban executed by staff"
            )
        except discord.NotFound:
            msg = f"{target_name} is not banned in this guild."
            await loader.error(msg)
            return
        except discord.Forbidden:
            msg = f"I don’t have permission to unban {target_name}."
            await loader.error(msg)
            return
        except discord.HTTPException as e:
            msg = f"Failed to unban {target_name}: {e}"
            await loader.error(msg)
            return

    # 3️⃣ Log action to report channel

    embed = discord.Embed(
        title="User Unbanned",
        color=discord.Color.green(),
    )
    embed.add_field(name="User", value=f"{target_name} ({target_id})", inline=False)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    footer_text = f"Unbanned by {interaction.user} ({interaction.user.id})"
    embed.set_footer(text=footer_text)
    await send_server_log(bot, embed=embed)

    # 4️⃣ Feedback to command executor
    content = f"{target_name} has been unbanned."
    await loader.success(content=content, embed=embed)
    pretty_log(
        "success",
        f"💙 Unbanned {target_name} ({target_id}) from guild. Reason: {reason or 'No reason provided'}",
    )
