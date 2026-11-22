import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from cogs.events import on_message_edit


class ClanRemovalMessageEditTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_pokemeow_triggers_clan_removal(self):
        cases = (
            ("You spent <:PokeCoin:123> **100,000** to kick user (ID: 456) from Celestial.", "kick"),
            ("You left **Celestial**", "leave"),
        )
        authors = (
            (123, False, None, False),
            (124, True, 789, False),
            (125, True, None, False),
            (on_message_edit.POKEMEOW_APPLICATION_ID, True, None, True),
        )
        for content, action in cases:
            for author_id, is_bot, webhook_id, allowed in authors:
                with self.subTest(action=action, author_id=author_id):
                    message = SimpleNamespace(
                        id=1,
                        guild=object(),
                        content=content,
                        embeds=[],
                        author=SimpleNamespace(id=author_id, bot=is_bot),
                        webhook_id=webhook_id,
                        channel=SimpleNamespace(name="test"),
                    )
                    with (
                        patch.object(on_message_edit, "pretty_log"),
                        patch.object(
                            on_message_edit, "process_clan_kick_message", new_callable=AsyncMock
                        ) as kick,
                        patch.object(
                            on_message_edit, "process_clan_leave_command", new_callable=AsyncMock
                        ) as leave,
                    ):
                        cog = on_message_edit.OnMessageEditCog(bot=object())
                        await cog.on_message_edit(message, message)
                        self.assertEqual(kick.await_count, int(allowed and action == "kick"))
                        self.assertEqual(leave.await_count, int(allowed and action == "leave"))


if __name__ == "__main__":
    unittest.main()
