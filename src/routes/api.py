from flask import Blueprint, Response, jsonify, request

from src.google_api.update_google_calendar import main as update_google_calendar
from src.jobs import last_run, scheduled_job, sync_from_html
from src.scraper.scheduler_scraper import scrape_schedule
from src.utils.custom_logger import main_logger as logger

api_bp = Blueprint("api", __name__)


@api_bp.route("/scrape/<group>", methods=["POST"])
def scrape(group: str) -> tuple[Response, int]:
    """
    Scrape WAT schedule for a given group and sync to Google Calendar.
    ---
    parameters:
      - name: group
        in: path
        type: string
        required: true
        description: Group ID (e.g. WCY25IX1S4).
    responses:
      200:
        description: List of scraped lessons.
        schema:
          type: array
          items:
            $ref: '#/definitions/Lesson'
      400:
        description: Scraping error.
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/Error'
    """
    logger.info(f"Received request for group: {group}")
    try:
        user_agent = request.headers.get("User-Agent")
        logger.info(f"Using User-Agent: {user_agent}")

        data, error = scrape_schedule(group, user_agent)
        if error:
            logger.error(f"Error from scrape_schedule: {error}")
            return jsonify({"error": error}), 400

        logger.info("Successfully scraped schedule")
        update_google_calendar(data)
        logger.info("Successfully updated Google Calendar")

        return jsonify(data), 200
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/run-job", methods=["POST"])
def run_job() -> tuple[Response, int]:
    """
    Manually trigger the scheduled scrape-and-sync job.
    ---
    responses:
      200:
        description: Job finished and the calendar was synced.
        schema:
          $ref: '#/definitions/Message'
      500:
        description: Job ran but scraping or calendar sync failed.
        schema:
          $ref: '#/definitions/Error'
    """
    scheduled_job()
    if last_run.get("ok"):
        logger.info("Job executed successfully")
        return jsonify({"message": last_run["message"]}), 200
    return jsonify({"error": last_run.get("message", "Job failed")}), 500


@api_bp.route("/upload-schedule", methods=["POST"])
def upload_schedule() -> tuple[Response, int]:
    """
    Sync Google Calendar from a schedule page saved in the browser (Ctrl+S).
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: HTML of planzajec.wcy.wat.edu.pl group page for DEFAULT_GROUP.
    responses:
      200:
        description: Page parsed and calendar synced.
        schema:
          $ref: '#/definitions/Message'
      400:
        description: Missing file, wrong group or no lessons in the page.
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Page parsed but calendar sync failed.
        schema:
          $ref: '#/definitions/Error'
    """
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"error": "No file uploaded"}), 400

    html = upload.read().decode("utf-8", errors="replace")
    if not sync_from_html(html):
        return jsonify({"error": last_run["message"]}), 400
    if not last_run["ok"]:
        return jsonify({"error": last_run["message"]}), 500
    return jsonify({"message": f"{last_run['message']} ({last_run['lessons']} lessons)"}), 200
