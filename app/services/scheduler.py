import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.email.outlook import scan_outlook_inbox


logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _timezone() -> ZoneInfo:
    settings = get_settings()

    try:
        return ZoneInfo(settings.outlook_scan_timezone)
    except ZoneInfoNotFoundError:
        logger.warning(
            "Unknown OUTLOOK_SCAN_TIMEZONE=%s; falling back to UTC",
            settings.outlook_scan_timezone,
        )
        return ZoneInfo("UTC")


def _run_scheduled_outlook_scan() -> None:
    try:
        result = scan_outlook_inbox()
        logger.info(
            "Scheduled Outlook scan completed: %s",
            result.to_dict(),
        )
    except Exception:
        logger.exception("Scheduled Outlook scan failed")


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler

    settings = get_settings()

    if not settings.outlook_scan_enabled:
        return None

    if _scheduler and _scheduler.running:
        return _scheduler

    timezone = _timezone()
    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.add_job(
        _run_scheduled_outlook_scan,
        CronTrigger(
            day_of_week="wed",
            hour=10,
            minute=0,
            timezone=timezone,
        ),
        id="outlook_weekly_report_scan",
        name="Outlook AP BTS weekly report scan",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)

    _scheduler = None


def scheduler_status() -> dict[str, str | bool | None]:
    if not _scheduler:
        return {
            "enabled": False,
            "running": False,
            "next_run_time": None,
        }

    job = _scheduler.get_job("outlook_weekly_report_scan")
    next_run_time = job.next_run_time.isoformat() if job and job.next_run_time else None

    return {
        "enabled": True,
        "running": _scheduler.running,
        "next_run_time": next_run_time,
    }
