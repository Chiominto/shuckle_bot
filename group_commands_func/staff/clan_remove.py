import asyncio

import discord
from discord.ext import commands

from constants.celestial_constants import CELESTIAL_ROLES, CELESTIAL_TEXT_CHANNELS
from utils.db.celestial_members_db import fetch_clan_channel_id, remove_celestial_member
from utils.functions.pretty_defer import pretty_defer
from utils.functions.webhook_func import send_webhook
from utils.listener_func.channel_boost import contact_booster_to_remove_boost
from utils.listener_func.clan_remove_listener import clan_removed_embed, get_roles
from utils.logs.pretty_log import pretty_log


async def clan_remove_func(
    bot: commands.Bot, interaction: discord.Interaction, member: discord.Member
):
    loader = await pretty_defer(
        interaction=interaction, content="Removing member from clan...", ephemeral=False
    )

    guild = interaction.guild
    if guild is None:
        await loader.error(content="This command can only be used in a server.")
        return

    # Check if they have clan role
    clan_role = guild.get_role(CELESTIAL_ROLES.celestialnova_)

    if not clan_role:
        await loader.error(content="Clan role not found.")
        return

    if clan_role not in member.roles:
        await loader.error(content=f"{member.mention} is not in the clan.")
        return

    try:
        # Get the registered channel; database errors must not be mistaken for no channel.
        clan_channel_id = await fetch_clan_channel_id(
            bot, member.id, raise_on_error=True
        )
        clan_channel = guild.get_channel(clan_channel_id) if clan_channel_id else None

        # ──────────────────────────────────────────────
        # 🎭 Gather all relevant roles in one go
        # ──────────────────────────────────────────────
        roles = get_roles(
            guild,
            CELESTIAL_ROLES.former_clan_member,
            CELESTIAL_ROLES.npc,
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
            CELESTIAL_ROLES.wish_badge,
            CELESTIAL_ROLES.solar_badge,
            CELESTIAL_ROLES.crescent_badge,
            CELESTIAL_ROLES.dream_badge,
            CELESTIAL_ROLES.prism_badge,
        )

        # 🐾 Unpack roles
        Former_Clan_Member_Role = roles[0]
        NPC_Role = roles[1]
        roles_to_remove = roles[2:]

        if Former_Clan_Member_Role is None:
            pretty_log(
                "warn",
                "⚠️ Former clan member role is missing; skipping clan removal role updates.",
            )
            await loader.error(content="Former clan member role is missing.")
            return

        if NPC_Role is None:
            pretty_log("warn", "⚠️ NPC role is missing; skipping clan removal.")
            await loader.error(content="NPC role is missing.")
            return

        pretty_log(
            "info",
            f"🧽 Removing {len(roles_to_remove)} roles and giving Stray role to {member.display_name}...",
        )

        # 🪄 Apply role changes
        try:
            await member.add_roles(Former_Clan_Member_Role, NPC_Role)
            await member.remove_roles(*filter(None, roles_to_remove))
        except discord.errors.NotFound as e:
            pretty_log(
                "info",
                f"Member {member.display_name} not found during role removal: {e}",
            )
            await loader.error(
                content=f"Member {member.display_name} not found during role removal: {e}"
            )
            return
        except Exception as e:
            pretty_log(
                "info",
                f"Unexpected error during role removal for {member.display_name}: {e}",
            )
            await loader.error(
                content=f"Unexpected error during role removal for {member.display_name}: {e}"
            )
            return

        await asyncio.sleep(1)  # ⏳ Small delay for safety

        # ──────────────────────────────────────────────
        # 🎨 Build pretty "removed" embed
        # ──────────────────────────────────────────────
        embed = clan_removed_embed(
            member=member,
            channel_name=clan_channel.name if clan_channel else "No Channel",
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
        if clan_channel:
            await contact_booster_to_remove_boost(
                bot=bot,
                channel_id=clan_channel.id,
                member=member,
                context="clan_remove",
                channel_name=clan_channel.name,
            )
            # ──────────────────────────────────────────────
            # 📦 Auto Channel Delete
            # ──────────────────────────────────────────────
            (
                await clan_channel.delete(
                    reason=f"Clan removal for {member.display_name}"
                )
                if clan_channel
                else None
            )

        removal_error = await remove_celestial_member(bot=bot, user_id=member.id)
        if removal_error:
            pretty_log("error", removal_error)
            await loader.error(content=removal_error)
            return

        await loader.success(content="", embed=embed)

    except Exception as e:
        pretty_log(
            "error",
            f"💥 Error during clan removal for {member.display_name}: {e}",
        )
        await loader.error(
            content=f"Error during clan removal for {member.display_name}: {e}"
        )
        return
