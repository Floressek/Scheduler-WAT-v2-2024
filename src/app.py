from flask import Flask, jsonify, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.scheduler_scraper import scrape_schedule
from google_api.update_google_calendar import main as update_google_calendar, get_calendar_service
from src.utils.custom_logger import main_logger as logger
from google_auth_oauthlib.flow import Flow
import os

app = Flask(__name__)

# Allow HTTP in local development environment
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def scheduled_job():
    logger.info("Starting scheduled job")
    group = "WCY22IJ1S1"
    user_agent = "Automated Scheduler Bot"

    data, error = scrape_schedule(group, user_agent)
    if error:
        logger.error(f"Error from scrape_schedule: {error}")
        return

    logger.info("Successfully scraped schedule")

    update_google_calendar(data)
    logger.info("Job completed")


scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_job, trigger="interval", minutes=30)
scheduler.start()


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
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri='http://localhost:5000/oauth2callback'
    )

    flow.fetch_token(authorization_response=request.url)

    # Save the credentials
    creds = flow.credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    return redirect('/')



@app.route('/')
def home():
    return "WAT Scheduler is running. Use /scrape/<group> to manually trigger a scrape and update."


if __name__ == '__main__':
    # Uruchom job od razu przy starcie
    scheduled_job()

    # Uruchom aplikację Flask
    app.run(debug=True, use_reloader=False)