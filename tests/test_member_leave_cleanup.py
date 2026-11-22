import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import discord

from cogs.events import on_message_create
from utils.functions import member_leave_cleanup as cleanup


def context_manager(value):
    manager = MagicMock()
    manager.__aenter__ = AsyncMock(return_value=value)
    manager.__aexit__ = AsyncMock(return_value=False)
    return manager


class MemberCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_ignores_members_and_reports_missing_columns(self):
        conn = SimpleNamespace(
            fetch=AsyncMock(
                side_effect=[
                    [{"attname": "user_id"}, {"attname": "user_name"}],
                    [
                        {"user_id": 1, "user_name": "present"},
                        {"user_id": 2, "user_name": "gone"},
                    ],
                    [{"attname": "other"}],
                    [{"attname": "user_id"}],
                    [{"user_id": 2, "user_name": None}, {"user_id": 3, "user_name": None}],
                ]
            )
        )
        bot = SimpleNamespace(pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)))
        with patch.object(cleanup, "TABLE_NAMES", ["first", "missing", "last", "first"]):
            candidates, tables, skipped = await cleanup._build_preview(bot, {1})
        self.assertEqual(candidates, {"2": "gone", "3": ""})
        self.assertEqual(tables, ["first", "last"])
        self.assertEqual(skipped, ["missing"])

    async def test_empty_member_list_aborts(self):
        async def no_members(*, limit):
            if False:
                yield None

        with self.assertRaisesRegex(RuntimeError, "empty"):
            await cleanup._member_ids(SimpleNamespace(fetch_members=no_members))

    async def test_failed_member_fetch_never_deletes(self):
        async def members(*, limit):
            yield SimpleNamespace(id=1)
            raise RuntimeError("member fetch failed")

        acquire = MagicMock()
        bot = SimpleNamespace(
            pg_pool=SimpleNamespace(acquire=acquire),
            get_guild=lambda _: SimpleNamespace(fetch_members=members),
        )
        interaction = SimpleNamespace(
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        with patch.object(cleanup, "pretty_log"):
            await cleanup.CleanupReview(bot, 7).proceed.callback(interaction)
        acquire.assert_not_called()
        self.assertIn("Cleanup failed", interaction.followup.send.await_args.args[0])

    async def test_continue_rechecks_members_and_deletes_only_approved_ids(self):
        async def members(*, limit):
            yield SimpleNamespace(id=1)
            yield SimpleNamespace(id=2)

        review = {
            "status": "pending",
            "candidates": json.dumps({"2": "returned", "3": "gone"}),
            "tables": ["first", "last"],
        }
        conn = SimpleNamespace(
            transaction=lambda: context_manager(None),
            fetchrow=AsyncMock(return_value=review),
            execute=AsyncMock(return_value="DELETE 1"),
        )
        bot = SimpleNamespace(
            pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)),
            get_guild=lambda _: SimpleNamespace(fetch_members=members),
        )
        interaction = SimpleNamespace(
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
            message=SimpleNamespace(edit=AsyncMock()),
        )
        with patch.object(cleanup, "load_celestial_members_cache", new=AsyncMock(return_value=True)):
            view = cleanup.CleanupReview(bot, 7)
            await view.proceed.callback(interaction)
        deletes = [call.args for call in conn.execute.await_args_list if call.args[0].startswith("DELETE")]
        self.assertEqual(
            deletes,
            [
                ('DELETE FROM "first" WHERE user_id = ANY($1::bigint[])', [3]),
                ('DELETE FROM "last" WHERE user_id = ANY($1::bigint[])', [3]),
            ],
        )
        self.assertIn("completed for 1 user IDs", interaction.followup.send.await_args.args[0])

    async def test_continue_failure_rolls_back_and_reports_error(self):
        async def members(*, limit):
            yield SimpleNamespace(id=1)

        review = {"status": "pending", "candidates": '{"2": "gone"}', "tables": ["bad"]}
        transaction = context_manager(None)
        conn = SimpleNamespace(
            transaction=lambda: transaction,
            fetchrow=AsyncMock(return_value=review),
            execute=AsyncMock(side_effect=asyncpg.UndefinedColumnError("missing user_id")),
        )
        bot = SimpleNamespace(
            pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)),
            get_guild=lambda _: SimpleNamespace(fetch_members=members),
        )
        interaction = SimpleNamespace(
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
            message=SimpleNamespace(edit=AsyncMock()),
        )
        with patch.object(cleanup, "pretty_log"):
            view = cleanup.CleanupReview(bot, 7)
            await view.proceed.callback(interaction)
        self.assertIs(transaction.__aexit__.await_args.args[0], asyncpg.UndefinedColumnError)
        self.assertIn("Cleanup failed", interaction.followup.send.await_args.args[0])
        interaction.message.edit.assert_not_awaited()

    async def test_only_owner_role_can_review(self):
        view = cleanup.CleanupReview(object(), 7)
        member = MagicMock(spec=discord.Member)
        member.roles = []
        interaction = SimpleNamespace(
            guild_id=cleanup.CELESTIAL_SERVER_ID,
            user=member,
            response=SimpleNamespace(send_message=AsyncMock()),
        )
        self.assertFalse(await view.interaction_check(interaction))
        member.roles = [SimpleNamespace(id=cleanup.CELESTIAL_ROLES.clan_owner_)]
        self.assertTrue(await view.interaction_check(interaction))

    async def test_remove_excludes_selected_user_from_review(self):
        review = {
            "status": "pending",
            "candidates": '{"2": "keep", "3": "remove"}',
            "page": 0,
            "skipped": [],
        }
        updated = {**review, "candidates": '{"2": "keep"}'}
        conn = SimpleNamespace(
            transaction=lambda: context_manager(None),
            fetchrow=AsyncMock(side_effect=[review, updated]),
        )
        bot = SimpleNamespace(pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)))
        interaction = SimpleNamespace(
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
            message=SimpleNamespace(edit=AsyncMock()),
        )
        view = cleanup.CleanupReview(bot, 7)
        modal = cleanup.RemoveCandidateModal(view)
        modal.candidate._value = "remove"
        with patch.object(view, "interaction_check", new=AsyncMock(return_value=True)):
            await modal.on_submit(interaction)
        saved = json.loads(conn.fetchrow.await_args.args[1])
        self.assertEqual(saved, {"2": "keep"})
        interaction.message.edit.assert_awaited_once()

    async def test_cancel_does_not_delete_any_user_rows(self):
        conn = SimpleNamespace(execute=AsyncMock(return_value="UPDATE 1"))
        bot = SimpleNamespace(pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)))
        interaction = SimpleNamespace(
            response=SimpleNamespace(edit_message=AsyncMock(), send_message=AsyncMock())
        )
        view = cleanup.CleanupReview(bot, 7)
        await view.cancel.callback(interaction)
        self.assertEqual(conn.execute.await_count, 1)
        self.assertIn("status = 'cancelled'", conn.execute.await_args.args[0])
        interaction.response.edit_message.assert_awaited_once()

    async def test_pending_reviews_restore_persistent_buttons(self):
        conn = SimpleNamespace(
            execute=AsyncMock(),
            fetch=AsyncMock(return_value=[{"id": 7, "message_id": 42}]),
        )
        bot = SimpleNamespace(
            pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)),
            add_view=MagicMock(),
        )
        await cleanup.setup_member_cleanup(bot)
        view = bot.add_view.call_args.args[0]
        self.assertTrue(view.is_persistent())
        self.assertEqual(view.review_id, 7)
        self.assertEqual(bot.add_view.call_args.kwargs["message_id"], 42)

    async def test_manual_trigger_requires_allowlisted_user(self):
        ctx = SimpleNamespace(
            guild=SimpleNamespace(id=cleanup.CELESTIAL_SERVER_ID),
            author=SimpleNamespace(id=123, bot=False),
            message=SimpleNamespace(webhook_id=None),
            reply=AsyncMock(),
        )
        cog = on_message_create.MessageCreateListener(bot=object())
        with (
            patch.object(on_message_create, "MANUAL_CLEANUP_USER_IDS", {123}),
            patch.object(on_message_create, "create_member_cleanup_preview", new_callable=AsyncMock) as create,
        ):
            await cog.db_cleanup.callback(cog, ctx)
            create.assert_awaited_once()
            ctx.author.id = 456
            await cog.db_cleanup.callback(cog, ctx)
            create.assert_awaited_once()
            self.assertIn("not authorized", ctx.reply.await_args.args[0])

    async def test_manual_command_is_registered_by_cog(self):
        from discord.ext import commands

        bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
        try:
            await bot.add_cog(on_message_create.MessageCreateListener(bot))
            self.assertIsNotNone(bot.get_command("db_cleanup"))
        finally:
            await bot.close()

    async def test_delete_is_batched(self):
        async def members(*, limit):
            yield SimpleNamespace(id=1)

        review = {
            "status": "pending",
            "candidates": json.dumps({str(i): "" for i in range(2, 1003)}),
            "tables": ["first"],
        }
        conn = SimpleNamespace(
            transaction=lambda: context_manager(None),
            fetchrow=AsyncMock(return_value=review),
            execute=AsyncMock(),
        )
        bot = SimpleNamespace(
            pg_pool=SimpleNamespace(acquire=lambda: context_manager(conn)),
            get_guild=lambda _: SimpleNamespace(fetch_members=members),
        )
        interaction = SimpleNamespace(
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
            message=SimpleNamespace(edit=AsyncMock()),
        )
        with patch.object(cleanup, "load_celestial_members_cache", new=AsyncMock(return_value=True)):
            view = cleanup.CleanupReview(bot, 7)
            await view.proceed.callback(interaction)
        deletes = [call.args for call in conn.execute.await_args_list if call.args[0].startswith("DELETE")]
        self.assertEqual([len(args[1]) for args in deletes], [500, 500, 1])


if __name__ == "__main__":
    unittest.main()
