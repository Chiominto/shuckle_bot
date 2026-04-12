# 🌸────────────────────────────────────────────
#       🐾 Role Members Listing (Smart Paginated)
#       - Fully callback-based buttons
#       - Only pressable by command author
#       - Auto-hides after 120s
#       - Single defer, then edit the original response
#       - Added pretty logging for exceptions
# 🌸────────────────────────────────────────────
import discord
from discord.ext import commands

from constants.celestial_constants import DEFAULT_EMBED_COLOR
from utils.functions.pretty_defer import pretty_defer
from utils.logs.pretty_log import pretty_log


# 🌸────────────────────────────────────────────
#       🎐 Smart Paginated View for Role Members
# 🌸────────────────────────────────────────────
class RoleMembersView(discord.ui.View):

    def __init__(
        self,
        members,
        role_name,
        author_id: int,
        server_icon: str | None = None,
        thumbnail_url: str | None = None,
    ):
        super().__init__(timeout=120)
        self.members = members
        self.role_name = role_name
        self.author_id = author_id
        self.page = 0
        self.per_page = 25
        self.total_pages = (len(self.members) - 1) // self.per_page + 1
        self.thumbnail_url = thumbnail_url
        self.server_icon = server_icon
        self.message: discord.Message | None = None  # gets set later
        self.update_buttons()

    def format_page(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_members = self.members[start:end]

        desc = (
            "\n".join(f"{m.mention} – {m.name}" for m in page_members)
            or "No members with this role."
        )

        embed = discord.Embed(
            title=f"Members with {self.role_name} Role",
            description=desc,
            color=DEFAULT_EMBED_COLOR,
        )
        embed.set_thumbnail(url=self.thumbnail_url)

        footer_text = f"🐢 Total Members: {len(self.members)}"
        if self.total_pages > 1:
            footer_text += f" 📝 • Page {self.page + 1}/{self.total_pages}"
        if self.server_icon:
            embed.set_footer(text=footer_text, icon_url=self.server_icon)
        else:
            embed.set_footer(text=footer_text)

        return embed

    def update_buttons(self):
        self.clear_items()
        if self.page > 0:
            self.add_item(self.PrevButton(self))
        if self.page + 1 < self.total_pages:
            self.add_item(self.NextButton(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You cannot interact with this view.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        try:
            if self.message:
                await self.message.edit(view=None)
        except Exception as e:
            pretty_log(
                "error",
                f"[RoleMembersView.on_timeout] Failed to disable buttons: {e}",
            )

    class PrevButton(discord.ui.Button):
        def __init__(self, parent: "RoleMembersView"):
            super().__init__(emoji="⬅️", style=discord.ButtonStyle.primary)
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            try:
                self.parent.page -= 1
                self.parent.update_buttons()
                await self.parent.message.edit(
                    embed=self.parent.format_page(), view=self.parent
                )
                await interaction.response.defer()
            except Exception as e:
                pretty_log(
                    "error",
                    f"[PrevButton.callback] Exception: {e}",
                )

    class NextButton(discord.ui.Button):
        def __init__(self, parent: "RoleMembersView"):
            super().__init__(emoji="➡️", style=discord.ButtonStyle.primary)
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            try:
                self.parent.page += 1
                self.parent.update_buttons()
                await self.parent.message.edit(
                    embed=self.parent.format_page(), view=self.parent
                )
                await interaction.response.defer()
            except Exception as e:
                pretty_log(
                    "error",
                    f"[NextButton.callback] Exception: {e}",
                )


# 🌸────────────────────────────────────────────
#       🎐 Function to fetch and display role members (Fully try/catch)
# 🌸────────────────────────────────────────────
async def role_members_func(
    bot: commands.Bot, interaction: discord.Interaction, role: discord.Role
):

    try:
        # 💜 Initial defer (ephemeral False so we can edit later)
        await pretty_defer(
            interaction=interaction,
            content=f"Fetching member list for {role.name}...",
            ephemeral=False,
        )
        guild = await bot.fetch_guild(interaction.guild.id)
        server_icon = guild.icon.url if guild.icon else None
        thumbnail_url = server_icon
        # 🌿 Get members with this role
        members = [m for m in interaction.guild.members if role in m.roles]

        role_icon_url = role.icon.url
        if role_icon_url:
            thumbnail_url = role_icon_url

        embed_title = f"Members with {role.name} Role"

        if not members:
            embed = discord.Embed(
                title=embed_title,
                description="No members with this role.",
                color=DEFAULT_EMBED_COLOR,
            )
            embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text=f"🐢 Total Members: 0")
            await interaction.edit_original_response(
                embed=embed, content=None, view=None
            )
            return

        # ✅ Small list: single embed
        if len(members) <= 25:
            desc = "\n".join(f"{m.mention} – {m.name}" for m in members)
            embed = discord.Embed(
                title=embed_title,
                description=desc,
                color=DEFAULT_EMBED_COLOR,
            )
            embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(
                text=f"🐢 Total Members: {len(members)}", icon_url=server_icon
            )
            await interaction.edit_original_response(
                embed=embed, content=None, view=None
            )
        else:
            # 📑 Paginated view on the original deferred message
            view = RoleMembersView(
                members,
                role.name,
                author_id=interaction.user.id,
                thumbnail_url=thumbnail_url,
                server_icon=server_icon,
            )
            msg = await interaction.edit_original_response(
                embed=view.format_page(), content=None, view=view
            )
            # Attach the message back for on_timeout disabling
            view.message = msg

    except Exception as e:
        pretty_log(
            "error",
            f"[role_members_func] Unexpected error: {e}",
        )
        try:
            await interaction.edit_original_response(
                content=f"❌ Failed to fetch role members: {e}", embed=None, view=None
            )
        except Exception as inner:
            pretty_log(
                "error",
                f"[role_members_func] Fallback send failed: {inner}",
            )
