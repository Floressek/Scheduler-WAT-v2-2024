import json
import os
import sys
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from flasgger import Swagger
from flask import Flask, Response, jsonify, redirect, request, session
from google_auth_oauthlib.flow import Flow
from werkzeug import run_simple

from src.config import (
    CREDENTIALS_PATH,
    DEFAULT_GROUP,
    REDIRECT_URI,
    SCHEDULE_INTERVAL_HOURS,
    SCOPES,
    TOKEN_PATH,
)
from src.google_api.update_google_calendar import main as update_google_calendar
from src.scraper.scheduler_scraper import scrape_schedule
from src.utils.custom_logger import main_logger as logger

print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")
print(f"Contents of current directory: {os.listdir('.')}")
print(f"Contents of /app directory: {os.listdir('/app')}")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

swagger_template: dict[str, Any] = {
    "info": {
        "title": "WAT Scheduler API",
        "description": "API for WAT class schedule scraping and Google Calendar synchronization.",
        "version": "1.0.0",
    },
    "host": "scheduler-wat-v2-2024-production.up.railway.app",
    "basePath": "/",
    "schemes": ["https"],
    "definitions": {
        "Lesson": {
            "type": "object",
            "properties": {
                "Subject": {"type": "string", "example": "Matematyka"},
                "Start Date": {"type": "string", "example": "01/10/2024"},
                "Start Time": {"type": "string", "example": "08:00"},
                "End Date": {"type": "string", "example": "01/10/2024"},
                "End Time": {"type": "string", "example": "09:35"},
                "All Day Event": {"type": "boolean", "example": False},
                "Description": {"type": "string", "example": "Wyklad"},
                "Location": {"type": "string", "example": "academic grounds"},
                "Private": {"type": "boolean", "example": True},
            },
        },
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Internal server error"}
            },
        },
        "Message": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Token deleted successfully"}
            },
        },
    },
}

Swagger(app, template=swagger_template)


def _ensure_credentials_file() -> None:
    if os.path.exists(CREDENTIALS_PATH):
        return
    credentials: dict[str, Any] = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
            "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": [REDIRECT_URI],
        }
    }
    with open(CREDENTIALS_PATH, "w") as f:
        json.dump(credentials, f)


_ensure_credentials_file()


def scheduled_job() -> None:
    logger.info("Starting scheduled job")
    user_agent = "Automated Scheduler Bot"

    logger.info(f"Scraping schedule for group: {DEFAULT_GROUP}")
    data, error = scrape_schedule(DEFAULT_GROUP, user_agent)
    if error:
        logger.error(f"Error from scrape_schedule: {error}")
        return

    logger.info("Successfully scraped schedule")
    logger.info(f"Scraped data: {data[:2] if data else 'No data'}...")

    logger.info("Updating Google Calendar")
    update_google_calendar(data)
    logger.info("Job completed")


scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_job, trigger="interval", hours=SCHEDULE_INTERVAL_HOURS)
scheduler.start()
logger.info("Scheduler started")


def create_app() -> Flask:
    with app.app_context():
        scheduled_job()
    return app


@app.route("/")
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
    if not os.path.exists(TOKEN_PATH):
        return (
            "WAT Scheduler is running.<br><br>"
            "<b>Google Calendar not authorized.</b> "
            "<a href='/login'>Click here to authorize</a>."
        )
    return "WAT Scheduler is running. Use /scrape/&lt;group&gt; to manually trigger a scrape and update."


@app.route("/login")
def login() -> Response:
    """
    Start Google OAuth2 authorization flow.
    ---
    responses:
      302:
        description: Redirect to Google consent screen.
    """
    with open(CREDENTIALS_PATH, "r") as f:
        client_config = json.load(f)
    flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(prompt="consent")
    session["oauth_state"] = state
    session["code_verifier"] = flow.code_verifier
    return redirect(auth_url)


@app.route("/oauth2callback")
def oauth2callback() -> Response:
    """
    Google OAuth2 callback. Exchanges authorization code for credentials.
    ---
    parameters:
      - name: code
        in: query
        type: string
        required: true
        description: Authorization code from Google.
      - name: state
        in: query
        type: string
        required: true
        description: CSRF state token.
    responses:
      302:
        description: Redirect to home on success.
    """
    with open(CREDENTIALS_PATH, "r") as f:
        client_config = json.load(f)
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=session.get("oauth_state"),
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(
        authorization_response=request.url,
        code_verifier=session.get("code_verifier"),
    )
    creds = flow.credentials
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
    return redirect("/")


@app.route("/delete-token", methods=["POST"])
def delete_token() -> tuple[Response, int]:
    """
    Delete the stored Google OAuth2 token.
    ---
    responses:
      200:
        description: Token deleted.
        schema:
          $ref: '#/definitions/Message'
      404:
        description: Token not found.
        schema:
          $ref: '#/definitions/Message'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
            return jsonify({"message": "Token deleted successfully"}), 200
        return jsonify({"message": "Token does not exist"}), 404
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/scrape/<group>")
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


@app.route("/run-job")
def run_job() -> tuple[str, int]:
    """
    Manually trigger the scheduled scrape-and-sync job.
    ---
    responses:
      200:
        description: Job executed successfully.
        schema:
          type: string
    """
    scheduled_job()
    return "Job executed successfully", 200


if __name__ == "__main__":
    app = create_app()
    run_simple("localhost", 5000, app, use_reloader=False, use_debugger=True)
