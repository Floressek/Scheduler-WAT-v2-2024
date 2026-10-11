from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from src.config import DEFAULT_GROUP, SCHEDULE_INTERVAL_HOURS, TIMEZONE
from src.google_api.update_google_calendar import main as update_google_calendar
from src.scraper.scheduler_scraper import scrape_schedule
from src.utils.custom_logger import main_logger as logger

# In-memory status of the latest run, read by the admin panel. Mutate only via .update().
last_run: dict[str, Any] = {}

scheduler = BackgroundScheduler()


def _record_run(ok: bool, message: str, data: list[dict[str, Any]] | None = None) -> None:
    last_run.update(
        time=datetime.now(ZoneInfo(TIMEZONE)),
        ok=ok,
        message=message,
        lessons=len(data) if data else 0,
        data=data or [],
    )


def scheduled_job() -> None:
    logger.info("Starting scheduled job")
    user_agent = "Automated Scheduler Bot"

    logger.info(f"Scraping schedule for group: {DEFAULT_GROUP}")
    data, error = scrape_schedule(DEFAULT_GROUP, user_agent)
    if error:
        logger.error(f"Error from scrape_schedule: {error}")
        _record_run(False, f"Scrape failed: {error}")
        return

    logger.info("Successfully scraped schedule")
    logger.info(f"Scraped data: {data[:2] if data else 'No data'}...")

    logger.info("Updating Google Calendar")
    try:
        synced = update_google_calendar(data)
    except Exception as e:
        logger.exception("Google Calendar update failed")
        _record_run(False, f"Google Calendar update failed: {e}", data)
        return
    if not synced:
        _record_run(False, "Google Calendar not updated - check logs, token may need /login", data)
        return
    _record_run(True, "Schedule synced to Google Calendar", data)
    logger.info("Job completed")


def start_scheduler() -> None:
    scheduler.add_job(func=scheduled_job, trigger="interval", hours=SCHEDULE_INTERVAL_HOURS)
    scheduler.start()
    logger.info("Scheduler started")


def next_run_time() -> datetime | None:
    jobs = scheduler.get_jobs()
    return jobs[0].next_run_time if jobs else None
