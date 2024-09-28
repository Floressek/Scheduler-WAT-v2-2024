import json

from flask import Flask, jsonify, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug import run_simple

from src.scraper.scheduler_scraper import scrape_schedule
from src.google_api.update_google_calendar import main as update_google_calendar, get_calendar_service
from src.utils.custom_logger import main_logger as logger
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
import os
import sys

# Print some useful information for debugging
print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")
print(f"Contents of current directory: {os.listdir('.')}")
print(f"Contents of /app directory: {os.listdir('/app')}")

app = Flask(__name__)

# Allow HTTP in local development environment
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = '/storage/token.json'

if not os.path.exists('credentials.json'):
    credentials = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
            "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": [
                "https://scheduler-wat-v2-2024-production.up.railway.app/oauth2callback"
            ]
        }
    }
    with open('credentials.json', 'w') as f:
        json.dump(credentials, f)


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                client_config, SCOPES,
                redirect_uri='https://scheduler-wat-v2-2024-production.up.railway.app/oauth2callback')
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"Please visit this URL to authorize the application: {auth_url}")
            # Tutaj powinieneś dodać logikę do obsługi autoryzacji
            # Na przykład, możesz zwrócić auth_url do frontendu
            # i oczekiwać na callback z kodem autoryzacyjnym
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds


def scheduled_job():
    logger.info("Starting scheduled job")
    group = "WCY22IJ1S1"
    user_agent = "Automated Scheduler Bot"

    logger.info(f"Scraping schedule for group: {group}")
    data, error = scrape_schedule(group, user_agent)
    if error:
        logger.error(f"Error from scrape_schedule: {error}")
        return

    logger.info("Successfully scraped schedule")
    logger.info(f"Scraped data: {data[:2] if data else 'No data'}...")  # Log first two items or 'No data' if data is None

    logger.info("Updating Google Calendar")
    update_google_calendar(data)
    logger.info("Job completed")

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_job, trigger="interval", minutes=30)
scheduler.start()
logger.info("Scheduler started")


def create_app():
    with app.app_context():
        scheduled_job()
    return app

@app.route('/scrape/<group>')
def scrape(group):
    logger.info(f"Received request for group: {group}")
    try:
        user_agent = request.headers.get('User-Agent')
        logger.info(f"Using User-Agent: {user_agent}")

        data, error = scrape_schedule(group, user_agent)
        if error:
            logger.error(f"Error from scrape_schedule: {error}")
            return jsonify({"error": error}), 400

        logger.info("Successfully scraped schedule")

        update_google_calendar(data)
        logger.info("Successfully updated Google Calendar")

        return jsonify(data)
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri='https://scheduler-wat-v2-2024-production.up.railway.app/oauth2callback'
    )

    flow.fetch_token(authorization_response=request.url)

    # Save the credentials
    creds = flow.credentials
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

    return redirect('/')


@app.route('/')
def home():
    return "WAT Scheduler is running. Use /scrape/<group> to manually trigger a scrape and update."


@app.route('/run-job')
def run_job():
    scheduled_job()
    return "Job executed successfully"


if __name__ == '__main__':
    app = create_app()
    run_simple('localhost', 5000, app, use_reloader=False, use_debugger=True)
