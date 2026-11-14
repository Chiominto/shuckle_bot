import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord

from utils.listener_func import auto_wb_spawn


class WorldBossRelayTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        auto_wb_spawn.cc_shared_cooldowns.clear()
        self.messages = []
        self.channel = SimpleNamespace(
            name="cc-wb",
            send=AsyncMock(),
            history=self.history,
            permissions_for=lambda _: SimpleNamespace(read_message_history=True),
        )
        self.guild = SimpleNamespace(id=123, me=object(), get_channel=lambda _: self.channel)
        self.channel.guild = self.guild
        self.bot = SimpleNamespace(get_guild=lambda _: self.guild)
        self.upsert = patch.object(auto_wb_spawn, "upsert_active_wb", new_callable=AsyncMock)
        self.upsert_mock = self.upsert.start()
        self.addCleanup(self.upsert.stop)
        self.log = patch.object(auto_wb_spawn, "pretty_log")
        self.log_mock = self.log.start()
        self.addCleanup(self.log.stop)

    async def history(self, *, limit):
        for message in self.messages[:limit]:
            yield message

    def add_alert(self, title, timestamp, *, bot=True):
        self.messages.append(
            SimpleNamespace(
                author=SimpleNamespace(bot=bot),
                embeds=[discord.Embed(title=title, description=timestamp)],
            )
        )

    async def test_existing_other_bot_alert_is_not_forwarded(self):
        self.add_alert("Drednaw", "1794629044")
        await auto_wb_spawn.send_cc_other_wb_reminder(
            self.bot, "regular", "drednaw", "1794629044"
        )
        self.channel.send.assert_not_awaited()
        self.upsert_mock.assert_not_awaited()

    async def test_different_variant_or_timestamp_is_forwarded(self):
        for title, timestamp in [
            ("Drednaw", "1794629044"),
            ("Shiny Drednaw", "1794629043"),
        ]:
            with self.subTest(title=title, timestamp=timestamp):
                auto_wb_spawn.cc_shared_cooldowns.clear()
                self.channel.send.reset_mock()
                self.messages.clear()
                self.add_alert(title, timestamp)
                await auto_wb_spawn.send_cc_other_wb_reminder(
                    self.bot, "shiny", "Drednaw", "1794629044"
                )
                self.channel.send.assert_awaited_once()

    async def test_existing_ee_alert_is_not_forwarded(self):
        self.add_alert("Shiny EE Spawned", "1794629044")
        await auto_wb_spawn.send_cc_bump_reminder(
            self.bot, "spawned", variant="shiny", timestamp="1794629044"
        )
        self.channel.send.assert_not_awaited()

    async def test_human_message_does_not_block_alert(self):
        self.add_alert("Drednaw", "1794629044", bot=False)
        await auto_wb_spawn.send_cc_other_wb_reminder(
            self.bot, "regular", "Drednaw", "1794629044"
        )
        self.channel.send.assert_awaited_once()

    async def test_history_failure_does_not_send_or_consume_cooldown(self):
        async def failed_history(*, limit):
            raise discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "")
            yield

        self.channel.history = failed_history
        with self.assertRaises(discord.Forbidden):
            await auto_wb_spawn.send_cc_other_wb_reminder(
                self.bot, "regular", "Drednaw", "1794629044"
            )
        self.channel.send.assert_not_awaited()
        self.assertFalse(auto_wb_spawn.cc_shared_cooldowns)
        self.log_mock.assert_called()

    async def test_missing_history_permission_does_not_send(self):
        self.channel.permissions_for = lambda _: SimpleNamespace(
            read_message_history=False
        )
        with self.assertRaises(PermissionError):
            await auto_wb_spawn.send_cc_other_wb_reminder(
                self.bot, "regular", "Drednaw", "1794629044"
            )
        self.channel.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
