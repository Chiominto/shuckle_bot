import discord

from constants.celestial_constants import (CELESTIAL_SERVER_ID,
                                           CELESTIAL_TEXT_CHANNELS)
from utils.cache.celestial_members_cache import fetch_channel_id_cache
from utils.logs.pretty_log import pretty_log


async def dm_member(
    bot:discord.Client,
    member: discord.Member,
    content: str = None,
    embed: discord.Embed = None,
):
    """DMs a member with fallback to their celestial channel, or public channel if all else fails."""

    # Prevent sending empty messages
    if content is None and embed is None:
        pretty_log(
            tag="warn",
            message=f"Attempted to DM member {member} (ID: {member.id}) with no content or embed. Aborting.",
        )
        return

    celestial_guild = bot.get_guild(CELESTIAL_SERVER_ID)
    if not celestial_guild:
        pretty_log(
            tag="error",
            message=f"Failed to fetch celestial guild with ID {CELESTIAL_SERVER_ID} for DM fallback",
        )
        return

    # First attempt: DM the member directly, retry once if rate limited
    for attempt in range(2):
        try:
            await member.send(content=content, embed=embed)
            return
        except discord.errors.RateLimited as e:
            if attempt == 0:
                pretty_log(
                    tag="warn",
                    message=f"Rate limited when DMing {member} (ID: {member.id}), retrying once...",
                )
                continue
            else:
                pretty_log(
                    tag="error",
                    message=f"Rate limited again when DMing {member} (ID: {member.id}). Skipping DM.",
                )
        except Exception as e:
            pretty_log(
                tag="info",
                message=f"Failed to DM member {member} (ID: {member.id}): {e}. Attempting fallback to celestial channel.",
            )
            break
    # Second attempt: Send to their celestial channel if they have one, retry once if rate limited
    member_channel_id = fetch_channel_id_cache(member.id)
    if member_channel_id:
        member_channel = celestial_guild.get_channel(member_channel_id)
        if member_channel:
            for attempt in range(2):
                try:
                    await member_channel.send(content=content, embed=embed)
                    return
                except discord.errors.RateLimited as e:
                    if attempt == 0:
                        pretty_log(
                            tag="warn",
                            message=f"Rate limited when sending to celestial channel {member_channel} for {member} (ID: {member.id}), retrying once...",
                        )
                        continue
                    else:
                        pretty_log(
                            tag="error",
                            message=f"Rate limited again when sending to celestial channel {member_channel} for {member} (ID: {member.id}). Skipping.",
                        )
                except Exception as e:
                    pretty_log(
                        tag="info",
                        message=f"Failed to send message to celestial channel {member_channel} for member {member} (ID: {member.id}): {e}. Attempting fallback to public channel.",
                    )
                    break
    # Final attempt: Send to a public channel in the celestial guild, retry once if rate limited
    fallback_channel = celestial_guild.get_channel(CELESTIAL_TEXT_CHANNELS.shuckles_swamp)
    if fallback_channel:
        for attempt in range(2):
            try:
                await fallback_channel.send(content=content, embed=embed)
                pretty_log(
                    tag="info",
                    message=f"Sent message to fallback channel {fallback_channel} for member {member} (ID: {member.id}) after DM and celestial channel attempts failed.",
                )
                return
            except discord.errors.RateLimited as e:
                if attempt == 0:
                    pretty_log(
                        tag="warn",
                        message=f"Rate limited when sending to fallback channel {fallback_channel} for {member} (ID: {member.id}), retrying once...",
                    )
                    continue
                else:
                    pretty_log(
                        tag="error",
                        message=f"Rate limited again when sending to fallback channel {fallback_channel} for {member} (ID: {member.id}). All DM attempts failed.",
                    )
            except Exception as e:
                pretty_log(
                    tag="error",
                    message=f"Failed to send message to fallback channel {fallback_channel} for member {member} (ID: {member.id}): {e}. All DM attempts failed.",
                )
                break
    else:
        pretty_log(
            tag="error",
            message=f"Failed to find fallback channel with ID {CELESTIAL_TEXT_CHANNELS.shuckles_swamp} in celestial guild for member {member} (ID: {member.id}). All DM attempts failed.",
        )