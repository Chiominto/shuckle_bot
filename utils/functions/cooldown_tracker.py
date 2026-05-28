# utils/cooldown_tracker.py

import time

class CooldownTracker:
    def __init__(self):
        self.user_cooldowns = {}
        self.channel_cooldowns = {}

    def is_on_user_cooldown(self, user_id: int, cooldown: int) -> int:
        now = time.time()
        last_used = self.user_cooldowns.get(user_id, 0)
        return max(0, int(cooldown - (now - last_used)))

    def is_on_channel_cooldown(self, channel_id: int, cooldown: int) -> int:
        now = time.time()
        last_used = self.channel_cooldowns.get(channel_id, 0)
        return max(0, int(cooldown - (now - last_used)))

    def update_user_cooldown(self, user_id: int):
        self.user_cooldowns[user_id] = time.time()

    def update_channel_cooldown(self, channel_id: int):
        self.channel_cooldowns[channel_id] = time.time()


# === GLOBAL TRACKER INSTANCE ===
tracker = CooldownTracker()


# === IMPORTABLE WRAPPERS ===
def check_cooldown(user_id: int, channel_id: int, seconds: int) -> str | None:
    user_remaining = tracker.is_on_user_cooldown(user_id, seconds)
    channel_remaining = tracker.is_on_channel_cooldown(channel_id, seconds)

    if user_remaining > 0:
        return f"⏳ Please wait **{user_remaining}s** before using this command again."

    if channel_remaining > 0:
        return f"⚠️ This channel is on cooldown. Try again in **{channel_remaining}s**."

    return None


def update_cooldown(user_id: int, channel_id: int):
    tracker.update_user_cooldown(user_id)
    tracker.update_channel_cooldown(channel_id)
