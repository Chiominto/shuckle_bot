import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from cogs.commands import fetch_message


class FetchMessageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.message = SimpleNamespace(id=1, delete=AsyncMock(), edit=AsyncMock())
        self.interaction = SimpleNamespace(
            user=SimpleNamespace(id=fetch_message.WHITELIST_IDS[0]),
            response=SimpleNamespace(is_done=lambda: False, send_message=AsyncMock()),
            original_response=AsyncMock(return_value=self.message),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        self.bot = SimpleNamespace(http=SimpleNamespace(token="test-token"))
        response = SimpleNamespace(
            status=200,
            json=AsyncMock(
                return_value={
                    "author": {"username": "test"},
                    "id": "456",
                    "channel_id": "123",
                    "timestamp": "2026-01-01",
                    "content": "hello",
                }
            ),
        )
        request = MagicMock()
        request.__aenter__ = AsyncMock(return_value=response)
        request.__aexit__ = AsyncMock(return_value=False)
        session = SimpleNamespace(get=lambda *args, **kwargs: request)
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=session)
        client.__aexit__ = AsyncMock(return_value=False)
        self.patches = [
            patch.object(fetch_message.aiohttp, "ClientSession", return_value=client),
            patch.object(fetch_message.discord, "File", return_value=object()),
            patch.object(
                fetch_message,
                "Path",
                side_effect=lambda name: Path(self.directory.name) / name,
            ),
            patch.object(fetch_message, "pretty_log"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    async def fetch(self):
        await fetch_message.fetch_message_from_link_func(
            self.bot, self.interaction, "https://discord.com/channels/1/123/456"
        )

    async def test_file_send_deletes_loading_message(self):
        await self.fetch()

        self.interaction.followup.send.assert_awaited_once()
        self.message.delete.assert_awaited_once()
        self.assertFalse((Path(self.directory.name) / "message_456.txt").exists())

    async def test_file_send_failure_replaces_loader_with_error(self):
        self.interaction.followup.send.side_effect = RuntimeError("send failed")

        await self.fetch()

        self.message.delete.assert_not_awaited()
        self.message.edit.assert_awaited_once()
        self.assertIn("Failed to send the output", self.message.edit.await_args.kwargs["content"])
        self.assertFalse((Path(self.directory.name) / "message_456.txt").exists())


if __name__ == "__main__":
    unittest.main()
