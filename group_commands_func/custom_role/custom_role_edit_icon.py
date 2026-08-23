import asyncio
import base64
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord.http import Route

from constants.celestial_constants import (
    CELESTIAL_ROLES,
    CELESTIAL_SERVER_ID,
    CELESTIAL_TEXT_CHANNELS,
    DEFAULT_EMBED_COLOR,
    KHY_USER_ID,
)
from utils.db.custom_roles_db_func import fetch_custom_role_id
from utils.functions.webhook_func import send_webhook
from utils.logs.pretty_log import pretty_log

LOG_CHANNEL_ID = CELESTIAL_TEXT_CHANNELS.server_logs
REFERENCE_ROLE_ID = CELESTIAL_ROLES.personal_role_divider
ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp",)
MAX_FILE_SIZE = 256 * 1024  # 256 KB


# 🍭──────────────────────────────
#   🎀 Slash Command: Edit Custom Role Icon
# 🍭──────────────────────────────
async def custom_role_edit_icon_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """Edit the icon of a member's custom role."""
    guild = interaction.guild
    user = interaction.user

    # Check if user has a custom role
    custom_role_id = await fetch_custom_role_id(bot, user)
    if not custom_role_id:
        await interaction.response.send_message(
            "You don't have a custom role to edit.", ephemeral=True
        )
        return

    custom_role = guild.get_role(custom_role_id)
    if not custom_role:
        await interaction.response.send_message(
            "Your custom role was not found in the server.", ephemeral=True
        )
        return

    # Check if custom role is below the position variable, if below move above
    custom_role_position = custom_role.position
    reference_role = guild.get_role(REFERENCE_ROLE_ID)
    top_grinder_role = guild.get_role(CELESTIAL_ROLES.top_catcher)
    top_grinder_role_position = top_grinder_role.position
    reference_position = reference_role.position
    if custom_role_position < top_grinder_role_position:
        new_position = reference_position - 1
        try:
            await custom_role.edit(
                position=new_position,
                reason="Ensuring custom role is below reference role",
            )
            pretty_log(
                "info",
                f"Moved role {custom_role.name} ({custom_role.id}) below reference role.",
                label="CUSTOM ROLE",
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Could not move role position: {e}",
            )

    if not guild.premium_tier or guild.premium_tier < 2:
        await interaction.response.send_message(
            "Server needs to be at least Level 2 to have role icons.",
            ephemeral=True,
        )
        return

    # Defer
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="🖼️ Discord Custom Role Icon Specs",
        color=discord.Color.purple(),
        description="\n".join(
            [
                "✅ **Max Dimensions:** 512 × 512 pixels",
                "✅ **Max File Size:** 256 KB",
                "✅ **Accepted Formats:** `.png`, `.jpg`, `.jpeg`, `.webp`",
            ]
        ),
    )
    view = UploadRoleIconView(bot=bot, role=custom_role, user=interaction.user)
    await interaction.edit_original_response(embed=embed, view=view)
    pretty_log(
        "info",
        f"📤 Started custom role icon upload for {interaction.user}",
    )


# 🌸────────────────────────────────────────────
#       🖼️ Custom Role Icon Upload View
# 🌸────────────────────────────────────────────
class UploadRoleIconView(discord.ui.View):
    def __init__(self, bot, role, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.role = role
        self.user = user
        self.interaction = None

    @discord.ui.button(label="📤 Upload Icon", style=discord.ButtonStyle.green)
    async def upload_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            if interaction.user.id != self.user.id:
                return await interaction.edit_original_response(
                    "❌ Only the original user can use this.", ephemeral=True
                )

            await interaction.response.send_message(
                "📎 Please upload your image now (accepted formats: PNG, JPG, JPEG, WEBP; max 256KB)."
            )

            def check(m):
                return (
                    m.author.id == self.user.id
                    and m.attachments
                    and m.channel == interaction.channel
                )

            msg = await self.bot.wait_for("message", check=check, timeout=120)
            attachment = msg.attachments[0]

            # -------------------- Validation --------------------
            if not any(
                attachment.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS
            ):
                pretty_log(
                    "info",
                    f"❌ Invalid file type: {attachment.filename}",
                )
                return await interaction.followup.send(
                    "❌ Invalid file type! Accepted: PNG, JPG, JPEG, WEBP",
                    ephemeral=True,
                )

            if attachment.size > MAX_FILE_SIZE:
                pretty_log(
                    "info",
                    f"⚠️ File too large: {attachment.size} bytes",
                )
                return await interaction.followup.send(
                    "⚠️ File too large! Max size is 256KB.", ephemeral=True
                )

            icon_bytes = await attachment.read()
            pretty_log(
                "info",
                f"📥 Received file '{attachment.filename}' ({len(icon_bytes)} bytes) from {self.user}",
            )

            # -------------------- Convert to Base64 --------------------
            icon_b64 = base64.b64encode(icon_bytes).decode("ascii")

            ext = attachment.filename.lower().split(".")[-1]
            mime = "image/png"
            if ext == "jpg" or ext == "jpeg":
                mime = "image/jpeg"
            elif ext == "webp":
                mime = "image/webp"

            icon_data = f"data:{mime};base64,{icon_b64}"

            route = Route(
                "PATCH", f"/guilds/{interaction.guild.id}/roles/{self.role.id}"
            )

            try:
                await self.bot.http.request(
                    route,
                    json={"icon": icon_data},
                    reason="Updated via /edit-role-icon",
                )
                pretty_log(
                    "success",
                    f"💙 Role icon updated for {self.role.name} (ID: {self.role.id})",
                )
            except Exception as e:
                pretty_log(
                    "critical",
                    f"⚠️ Critical failure updating role icon: {e}",
                )
                return await interaction.followup.send(
                    "⚠️ Failed to update role icon due to an error.", ephemeral=True
                )

            # -------------------- Success Embed --------------------
            embed = discord.Embed(
                title="🖼️ Role Icon Updated! ✨",
                description=f"**Role:** {self.role.mention}\n**Updated by:** {self.user.mention} 💜",
                color=self.role.color,
            )
            embed.set_author(
                name=self.user.display_name, icon_url=self.user.display_avatar.url
            )
            embed.set_thumbnail(url=attachment.url)
            content = (
                f"✅ Successfully updated the icon for the role {self.role.mention}."
            )
            await interaction.edit_original_response(content=content, embed=embed)

            # -------------------- Log Channel --------------------
            try:
                log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed.set_footer(
                        text=f"User ID: {self.user.id}",
                        icon_url=interaction.guild.icon.url,
                    )
                    embed.timestamp = datetime.now()
                    await send_webhook(
                        bot=self.bot,
                        channel=log_channel,
                        embed=embed,
                    )
                    pretty_log(
                        "info",
                        f"💙 Logged role icon update for {self.user}",
                    )
            except Exception as e:
                pretty_log(
                    "error",
                    f"⚠️ Failed to log role icon update: {e}",
                )

        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏰ Timed out! Please run the command again when you're ready.",
                ephemeral=True,
            )
        except Exception as e:
            pretty_log(
                "critical",
                f"💀 Unexpected error in upload_button: {e}",
            )
            await interaction.followup.send(
                "⚠️ An unexpected error occurred. Please contact staff.", ephemeral=True
            )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.grey)
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message(
                    "❌ Only the original user can cancel.", ephemeral=True
                )
            await interaction.response.edit_message(
                content="❌ Upload cancelled.", view=None
            )
            pretty_log("info", f"❌ Upload cancelled by {self.user}")
            self.stop()
        except Exception as e:
            pretty_log(
                "critical",
                f"💀 Unexpected error in cancel_button: {e}",
            )
