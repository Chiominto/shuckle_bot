# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⏰ scheduler.py 🐰✨
# Schedules all cron jobs for Wooper using SchedulerManager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
import calendar
import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.logs.pretty_log import pretty_log

from .battle_tower_reminder import send_battle_tower_closing_reminder
from .donation_role_reset import reset_donation_roles
from .monthly_stats_reminder import send_monthly_stats_reminder
from .os_lotto_reminder import send_lotto_reminder
from .schedule_manager import SchedulerManager

# Timezones
MANILA = zoneinfo.ZoneInfo("Asia/Manila")
NYC = zoneinfo.ZoneInfo("America/New_York")  # auto-handles EST/EDT

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")


def get_last_day_of_month_est(year, month):
    # Get the last day as integer
    last_day = calendar.monthrange(year, month)[1]
    # Create a datetime for the last day at 23:59:59 EST
    est = ZoneInfo("America/New_York")
    last_dt = datetime(year, month, last_day, 23, 59, 59, tzinfo=est)
    return last_dt


def format_next_run_manila(next_run_time):
    """
    Converts a timezone-aware datetime to Asia/Manila time and returns a readable string.
    """
    if next_run_time is None:
        return "No scheduled run time."
    # Convert to Manila timezone
    manila_tz = ZoneInfo("Asia/Manila")
    manila_time = next_run_time.astimezone(manila_tz)
    # Format as: Sunday, Nov 3, 2025 at 12:00 PM (Asia/Manila)
    return manila_time.strftime("%A, %b %d, %Y at %I:%M %p (Asia/Manila)")


# ────────────────────────────────────────────────────────────────────────────
# 🌸 setup_schedulers — Registers all scheduled tasks
# ────────────────────────────────────────────────────────────────────────────
async def setup_schedulers(bot):

    # 🚀 Start the scheduler engine
    scheduler_manager.start()
    schedules = []
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ☀️ DAILY SCHEDULED TASKS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 🎯 Lotto Reminder — 10 mins before lottery draw (8:50 PM New York time)
    try:
        os_lotto_reminder = scheduler_manager.add_cron_job(
            send_lotto_reminder,
            "lotto_reminder",
            day_of_week="mon,wed,fri,sun",
            hour=20,
            minute=50,
            timezone=NYC,
            args=[bot],
        )
        readable_next_run = format_next_run_manila(os_lotto_reminder.next_run_time)
        schedules.append(f"🎲 OS Lotto Reminder scheduled for {readable_next_run}")
    except Exception as e:
        pretty_log("error", f"Failed to schedule OS Lotto Reminder: {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📅 WEEKLY TASKS (Friday - Saturday)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ⚔️ Battle Tower End Reminder — 10 mins before reset (8:50 PM New York time)
    try:
        battle_tower_reminder = scheduler_manager.add_cron_job(
            send_battle_tower_closing_reminder,
            name="battle_tower_end",
            day_of_week="mon,wed,fri",
            hour=20,
            minute=50,
            timezone=NYC,  # ⏰ New York timezone, matches in-game schedule
            args=[bot],
        )
        readable_next_run = format_next_run_manila(battle_tower_reminder.next_run_time)
        schedules.append(
            f"⚔️ Battle Tower Closing Reminder scheduled for {readable_next_run
        }"
        )
    except Exception as e:
        pretty_log("error", f"Failed to schedule Battle Tower Closing Reminder: {e}")

    # 🏰 Donation Role Reset 5 minutes before sunday 12 am EST
    try:
        donation_role_reset = scheduler_manager.add_cron_job(
            reset_donation_roles,
            name="donation_role_reset",
            day_of_week="sat",
            hour=23,
            minute=55,
            timezone=NYC,
            args=[bot],
        )
        readable_next_run = format_next_run_manila(donation_role_reset.next_run_time)
        schedules.append(f"🏰 Donation Role Reset scheduled for {readable_next_run}")
    except Exception as e:
        pretty_log("error", f"Failed to schedule Donation Role Reset: {e}")

    # 📊 Monthly Stats Reminder — last day of month at 11:50 PM New York time
    try:
        monthly_stats_reminder = scheduler_manager.add_cron_job(
            send_monthly_stats_reminder,
            name="monthly_stats_reminder",
            day_of_month="last",
            hour=23,
            minute=50,
            timezone=NYC,
            args=[bot],
        )
        readable_next_run = format_next_run_manila(monthly_stats_reminder.next_run_time)
        schedules.append(f"📊 Monthly Stats Reminder scheduled for {readable_next_run}")
    except Exception as e:
        pretty_log("error", f"Failed to schedule Monthly Stats Reminder: {e}")

    schedule_checklist(schedules)


# 🟣────────────────────────────────────────────
#         ⚡ Startup Checklist ⚡
# 🟣────────────────────────────────────────────
def schedule_checklist(schedules):
    print("\n── · 𖨠 · ───────────────────────────────────────────────── · 𖨠 · ──")
    for schedule in schedules:
        print(f"✅ {schedule}")
    print("── · 𖨠 · ───────────────────────────────────────────────── · 𖨠 · ──\n")
