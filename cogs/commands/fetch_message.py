import re
from pathlib import Path
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from constants.celestial_constants import HANA_USER_ID, KHY_USER_ID
from utils.functions.pretty_defer import pretty_defer
from utils.logs.pretty_log import pretty_log

WHITELIST_IDS = [
    HANA_USER_ID,
    KHY_USER_ID,

]
# 💠────────────────────────────────────────────
# [🟣 HELPER] Fetch message from link • do all the thinking + respond
# ─────────────────────────────────────────────
async def fetch_message_from_link_func(
    bot: discord.Client,
    interaction: discord.Interaction,
    message_link: str,
    ephemeral: bool = True,
) -> None:
    """
    End-to-end:
      - shows loader (uses pretty_defer)
      - validates link, fetches via API
      - formats readable dump (text, embeds, attachments)
      - sends inline if short, otherwise as .txt file
      - cleans up temp file
    """
    save_to_file = True
    temp_file: Optional[Path] = None

    # [💙 READY] Start loader using Minccino-style pretty_defer
    try:
        loader = await pretty_defer(
            interaction,
            content="Fetching message…",
            ephemeral=ephemeral,
        )
    except Exception as e:
        loader = None
        pretty_log(tag="error", message=f"[fetch_message] Loader setup failed: {e}")

    if interaction.user.id not in WHITELIST_IDS:
        await loader.error(content="You are not whitelisted to use this command.")
        return

    # [💙 READY] Helper to send final text
    async def send_text(text: str):
        as_block = f"```{text}```" if len(text) <= 1900 else text
        if loader:
            try:
                if len(as_block) <= 2000:
                    await loader.success(content=as_block)
                else:
                    await interaction.followup.send(
                        content="📄 Output is large — sending as file…",
                        ephemeral=ephemeral,
                    )
            except Exception as e:
                pretty_log("error", f"[fetch_message] Loader stop failed: {e}")
                await interaction.followup.send(as_block[:1990], ephemeral=ephemeral)
        else:
            await interaction.followup.send(as_block[:2000], ephemeral=ephemeral)

    # [💙 READY] Helper to send a file then close loader
    async def send_file(path: Path, notice: str = "📄 Message contents saved to file:"):
        try:
            await interaction.followup.send(
                content=notice, file=discord.File(path), ephemeral=ephemeral
            )
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception as e:
                pretty_log("error", f"[fetch_message] Temp file cleanup failed: {e}")
            if loader:
                try:
                    await loader.stop(delete=True)
                except Exception:
                    pass

    # [💙 READY] Parse link → channel_id + message_id
    try:
        channel_id = message_id = None
        m = re.search(r"/channels/(\d+)/(\d+)/(\d+)$", message_link)
        if m:
            channel_id, message_id = m.group(2), m.group(3)
        else:
            m2 = re.search(r"/channels/(\d+)/messages/(\d+)$", message_link)
            if m2:
                channel_id, message_id = m2.group(1), m2.group(2)

        if not channel_id or not message_id:
            await send_text(
                "❌ Invalid message link. Expected:\n"
                "- https://discord.com/channels/<guild>/<channel>/<message>\n"
                "- https://discord.com/api/v10/channels/<channel>/messages/<message>"
            )
            return
    except Exception as e:
        pretty_log(tag="error", message=f"[fetch_message] Link parse failed: {e}")
        await send_text("❌ Could not parse the message link.")
        return

    # [💙 READY] Fetch via REST
    try:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
        headers = {"Authorization": f"Bot {bot.http.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await send_text(f"❌ Failed to fetch message: HTTP {resp.status}")
                    return
                data = await resp.json()
    except Exception as e:
        pretty_log(tag="error", message=f"[fetch_message] HTTP fetch failed: {e}")
        await send_text("❌ Network error while fetching the message.")
        return

    # [💙 READY] Build readable dump
    try:
        parts = ["━━━━━━━━━━━━━━━━━━━━━━━"]
        author_tag = (
            f"{data['author']['username']}#{data['author'].get('discriminator','0')}"
        )
        parts.append(f"👤 Author   : {author_tag}")
        parts.append(f"🆔 MessageID: {data['id']}")
        parts.append(f"💬 ChannelID: {data['channel_id']}")
        parts.append(f"🕒 Created  : {data['timestamp']}")
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━\n")

        content = data.get("content", "")
        if content.strip():
            parts.append("💬 Message Content:")
            parts.append(content)
            parts.append("")
        else:
            parts.append("💬 Message Content: [No text]\n")

        # Replies / references
        ref = data.get("referenced_message")
        if ref:
            ref_author = (
                f"{ref['author']['username']}#{ref['author'].get('discriminator','0')}"
            )
            parts.append("↩️ Replying To:")
            parts.append(f"- Author: {ref_author}")
            if ref.get("content"):
                parts.append(f"- Snippet: {ref['content'][:200]}")
            parts.append("")

        # Attachments
        atts = data.get("attachments") or []
        if atts:
            parts.append("📎 Attachments:")
            for att in atts:
                parts.append(f"- {att.get('filename','file')} → {att.get('url','')}")
            parts.append("")

        # Embeds
        # Embeds
        embeds = data.get("embeds") or []
        if embeds:
            parts.append("🖼 Embeds:")
            for idx, emb in enumerate(embeds, start=1):
                parts.append(f"━ Embed {idx} ━")

                # Color
                if emb.get("color") is not None:
                    color_val = emb["color"]
                    parts.append(f"🎨 Color: #{color_val:06X}")

                # Title
                if emb.get("title"):
                    parts.append(f"📌 Title:")
                    parts.append(f"{emb['title']}")

                # URL
                if emb.get("url"):
                    parts.append(f"🔗 URL:")
                    parts.append(f"{emb['url']}")

                # Author
                if emb.get("author") and emb["author"].get("name"):
                    parts.append("👤 Author:")
                    parts.append(f"{emb['author']['name']}")

                    # ✅ Add author URL if present
                    if emb["author"].get("url"):
                        parts.append(f"   🔗 {emb['author']['url']}")

                    # ✅ Add author icon URL if present
                    if emb["author"].get("icon_url"):
                        parts.append(f"   🖼 {emb['author']['icon_url']}")
                # Description
                if emb.get("description"):
                    parts.append("📝 Description:")
                    for line in emb["description"].splitlines():
                        parts.append(f"{line}")

                # Fields
                if emb.get("fields"):
                    parts.append("📂 Fields:")
                    for f in emb["fields"]:
                        name = f.get("name", "Field")
                        val = f.get("value", "")
                        inline = f.get("inline", False)
                        inline_note = "inline" if inline else "block"
                        parts.append(f"  • {name} [{inline_note}]:")
                        for line in val.splitlines():
                            parts.append(f"  {line}")

                # Footer
                if emb.get("footer") and emb["footer"].get("text"):
                    parts.append("🦶 Footer:")
                    for line in emb["footer"]["text"].splitlines():
                        parts.append(f"{line}")

                # Images / Thumbnails
                if emb.get("image") and emb["image"].get("url"):
                    parts.append("🖼 Image:")
                    parts.append(f"{emb['image']['url']}")
                if emb.get("thumbnail") and emb["thumbnail"].get("url"):
                    parts.append("🖼 Thumbnail:")
                    parts.append(f"{emb['thumbnail']['url']}")

                parts.append("")  # space after each embed

        result_text = "\n".join(parts).strip()
    except Exception as e:
        pretty_log("error", f"[fetch_message] Build dump failed: {e}")
        if loader:
            await loader.error("❌ Failed to format the message contents.")
        else:
            await send_text("❌ Failed to format the message contents.")
        return

    # [💙 READY] Decide: inline vs file
    try:
        if save_to_file or len(result_text) > 1800:
            temp_file = Path(f"message_{message_id}.txt")
            temp_file.write_text(result_text, encoding="utf-8")
            await send_file(temp_file, "📄 Message dump attached:")
        else:
            if loader:
                await loader.success(content=result_text)
            else:
                await send_text(result_text)
    except Exception as e:
        pretty_log("error", f"[fetch_message] Send failed: {e}")
        if loader:
            await loader.error("❌ Failed to send the output.")
        else:
            await send_text("❌ Failed to send the output.")


# 💠───────────────────────────────────────────────────────────────
# [📚 COG] FetchMessageCog
# ────────────────────────────────────────────────────────────────
class FetchMessageCog(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot

    @app_commands.command(
        name="fetch_message",
        description="Fetch and dump the raw contents of a message from its link.",
    )
    @app_commands.describe(message_link="The Discord message link to fetch")
    async def fetch_message(
        self, interaction: discord.Interaction, message_link: str
    ):
        await fetch_message_from_link_func(
            bot=self.bot,
            interaction=interaction,
            message_link=message_link,
        )

    fetch_message.extras = {"category": "Staff"}


# 💠───────────────────────────────────────────────────────────────
# [📦 SETUP]
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    try:
        await bot.add_cog(FetchMessageCog(bot))
    except Exception as e:
        pretty_log("error", f"[fetch_message] Failed to load FetchMessageCog: {e}")
