from utils.logs.pretty_log import pretty_log


webhook_url_cache: dict[tuple[int, int], dict[str, str]] = {}
#     ...
#
# }
# key = (bot_id, channel_id)
# Structure:
# webhook_url_cache = {
# (bot_id, channel_id): {
#     "url": "https://discord.com/api/webhooks/..."
#     "channel_name": "alerts-channel",
# },
#


celestial_members_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "pokemeow_name": str,
#   "channel_id": int
#   "actual_perks": str
#   "clan_bank_donation": int
#   "clan_treasury_doantion": int
#   "date_joined": int
# }
# 🔮────────────────────────────────────────────
#        ⚡ Pokemon Cache
# 👻────────────────────────────────────────────
pokemon_cache: dict[str, dict[str, str | int]] = {}
#     ...
#
# }
# Structure:
# pokemon_cache = {
# "pokemon_name": {
#     "dex_number": int,
#     "rarity": str,
#     "current_listing": int,
#     "lowest_market": int,
#     "true_lowest": int,
#     "listing_seen": str,
#     "emoji_id": str,
#     "image_link": str,
#     "last_updated": datetime
# },

# 🧩────────────────────────────────────────────
#        ⚡ Pokémon List Cache
# 🧩────────────────────────────────────────────
pokemon_list_cache: dict[str, int] = {}
# Structure:
# pokemon_list_cache = {
#     "pokemon_name": "dex_number",
#     }
