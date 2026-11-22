import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg

from utils.db import general_db


class RemoveUserFromDbsTests(unittest.IsolatedAsyncioTestCase):
    async def test_table_error_does_not_stop_later_deletions(self):
        for error in (
            asyncpg.UndefinedColumnError("column user_id does not exist"),
            asyncpg.UndefinedTableError("table does not exist"),
        ):
            with self.subTest(error=type(error).__name__):
                conn = SimpleNamespace(
                    execute=AsyncMock(side_effect=["DELETE 0", error, "DELETE 1"])
                )
                acquire = MagicMock()
                acquire.__aenter__ = AsyncMock(return_value=conn)
                acquire.__aexit__ = AsyncMock(return_value=False)
                bot = SimpleNamespace(pg_pool=SimpleNamespace(acquire=lambda: acquire))
                with (
                    patch.object(general_db, "TABLE_NAMES", ["first", "broken", "last"]),
                    patch.object(general_db, "pretty_log") as log,
                ):
                    await general_db.remove_user_from_dbs(bot, 123)

                self.assertEqual(conn.execute.await_count, 3)
                self.assertEqual(
                    conn.execute.await_args_list[-1].args,
                    ("DELETE FROM last WHERE user_id = $1;", 123),
                )
                self.assertTrue(
                    any(
                        call.kwargs.get("tag") == "error"
                        and "broken" in call.kwargs.get("message", "")
                        for call in log.call_args_list
                    )
                )
                self.assertFalse(
                    any(call.kwargs.get("tag") == "info" for call in log.call_args_list)
                )

    async def test_no_matching_user_is_successful(self):
        conn = SimpleNamespace(execute=AsyncMock(return_value="DELETE 0"))
        acquire = MagicMock()
        acquire.__aenter__ = AsyncMock(return_value=conn)
        acquire.__aexit__ = AsyncMock(return_value=False)
        bot = SimpleNamespace(pg_pool=SimpleNamespace(acquire=lambda: acquire))
        with (
            patch.object(general_db, "TABLE_NAMES", ["first", "last"]),
            patch.object(general_db, "pretty_log") as log,
        ):
            await general_db.remove_user_from_dbs(bot, 123)

        self.assertEqual(conn.execute.await_count, 2)
        self.assertEqual(log.call_args.kwargs["tag"], "info")


if __name__ == "__main__":
    unittest.main()
