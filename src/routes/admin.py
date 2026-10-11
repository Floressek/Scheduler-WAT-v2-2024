from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template

from src.config import DEFAULT_GROUP, TIMEZONE
from src.google_api.credentials import read_token_info, token_exists
from src.jobs import last_run, next_run_time
from src.utils.custom_logger import main_logger as logger

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
def home() -> str:
    """
    Health check and authorization status.
    ---
    responses:
      200:
        description: Status page with optional login prompt.
        schema:
          type: string
    """
    if not token_exists():
        logger.info("Token not found")
        return (
            "WAT Scheduler is running.<br><br>"
            "<b>Google Calendar not authorized.</b> "
            "<a href='/login'>Click here to authorize</a>."
        )
    logger.info("Token found")
    return "WAT Scheduler is running. <a href='/admin'>Admin panel</a>."


@admin_bp.route("/admin", methods=["GET"])
def admin() -> str:
    """
    Admin panel with token and job status.
    ---
    responses:
      200:
        description: HTML admin panel.
    """
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    upcoming = [
        lesson
        for lesson in last_run.get("data", [])
        if datetime.strptime(lesson["Start Date"], "%d/%m/%Y").date() >= today
    ][:8]

    return render_template(
        "admin.html",
        group=DEFAULT_GROUP,
        token=read_token_info(),
        last_run=last_run,
        next_run=next_run_time(),
        upcoming=upcoming,
    )
