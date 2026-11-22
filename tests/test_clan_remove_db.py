import unittest
from types import SimpleNamespace
from unittest.mock import patch

from utils.db import celestial_members_db


class ClanRemoveDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        class FailingConnection:
            async def fetchrow(self, *_args):
                raise RuntimeError("database unavailable")

        class FailingAcquire:
            async def __aenter__(self):
                return FailingConnection()

            async def __aexit__(self, *_args):
                return False

        self.bot = SimpleNamespace(
            pg_pool=SimpleNamespace(acquire=lambda: FailingAcquire())
        )
        self.log = patch.object(celestial_members_db, "pretty_log")
        self.log.start()
        self.addCleanup(self.log.stop)

    async def test_channel_lookup_preserves_legacy_none_on_error(self):
        channel_id = await celestial_members_db.fetch_clan_channel_id(
            self.bot, user_id=123
        )

        self.assertIsNone(channel_id)

    async def test_channel_lookup_can_raise_on_error(self):
        with self.assertRaisesRegex(RuntimeError, "database unavailable"):
            await celestial_members_db.fetch_clan_channel_id(
                self.bot, user_id=123, raise_on_error=True
            )


if __name__ == "__main__":
    unittest.main()
