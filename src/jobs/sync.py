from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from src.config import DEFAULT_GROUP, SCHEDULE_INTERVAL_HOURS, TIMEZONE
from src.google_api.update_google_calendar import main as update_google_calendar
from src.scraper.scheduler_scraper import parse_group, parse_schedule, scrape_schedule
from src.utils.custom_logger import main_logger as logger

# In-memory status of the latest run, read by the admin panel. Mutate only via .update().
last_run: dict[str, Any] = {}

scheduler = BackgroundScheduler()


def _record_run(
    ok: bool, message: str, source: str, data: list[dict[str, Any]] | None = None
) -> None:
    now = datetime.now(ZoneInfo(TIMEZONE))
    last_run.update(time=now, ok=ok, message=message, source=source, lessons=len(data) if data else 0)
    # Keep the last known schedule when a run fails before parsing (e.g. WAF 403 on the auto job).
    if data:
        last_run["data"] = data
    if ok:
        last_run["last_success"] = {"time": now, "source": source}


def scheduled_job() -> None:
    logger.info("Starting scheduled job")
    user_agent = "Automated Scheduler Bot"

    logger.info(f"Scraping schedule for group: {DEFAULT_GROUP}")
    data, error = scrape_schedule(DEFAULT_GROUP, user_agent)
    if error:
        logger.error(f"Error from scrape_schedule: {error}")
        _record_run(False, f"Scrape failed: {error}", "auto")
        return

    logger.info("Successfully scraped schedule")
    logger.info(f"Scraped data: {data[:2] if data else 'No data'}...")
    _sync_calendar(data, "auto")
    logger.info("Job completed")


def sync_from_html(html: str) -> bool:
    """Sync a schedule page saved from the browser. Returns False if the page itself is rejected."""
    group = parse_group(html)
    if group != DEFAULT_GROUP:
        message = (
            f"Uploaded page is for group {group}, expected {DEFAULT_GROUP}"
            if group
            else "Uploaded file is not a WCY group schedule page"
        )
        logger.error(message)
        _record_run(False, message, "upload")
        return False

    data, error = parse_schedule(html)
    if error:
        logger.error(f"Error parsing uploaded schedule: {error}")
        _record_run(False, f"Parse failed: {error}", "upload")
        return False

    logger.info(f"Parsed {len(data)} lessons from uploaded page")
    _sync_calendar(data, "upload")
    return True


def _sync_calendar(data: list[dict[str, Any]], source: str) -> None:
    logger.info("Updating Google Calendar")
    try:
        synced = update_google_calendar(data)
    except Exception as e:
        logger.exception("Google Calendar update failed")
        _record_run(False, f"Google Calendar update failed: {e}", source, data)
        return
    if not synced:
        message = "Google Calendar not updated - check logs, token may need /login"
        _record_run(False, message, source, data)
        return
    _record_run(True, "Schedule synced to Google Calendar", source, data)


def start_scheduler() -> None:
    scheduler.add_job(func=scheduled_job, trigger="interval", hours=SCHEDULE_INTERVAL_HOURS)
    scheduler.start()
    logger.info("Scheduler started")


def next_run_time() -> datetime | None:
    jobs = scheduler.get_jobs()
    return jobs[0].next_run_time if jobs else None
