import os
from src.utils.custom_logger import google_api_logger as logger
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import datetime
from flask import session, redirect
from datetime import datetime, date

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = '/storage/token.json'

def get_calendar_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("Starting new authorization flow")
            flow = Flow.from_client_secrets_file(
                'credentials.json', SCOPES,
                redirect_uri='https://scheduler-wat-v2-2024-production.up.railway.app/oauth2callback')
            auth_url, _ = flow.authorization_url(prompt='consent')
            logger.info(f"Please visit this URL to authorize the application: {auth_url}")
            # Zamiast prosić o wprowadzenie kodu, zwróć None
            return None

        logger.info("Saving credentials to token.json")
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    try:
        logger.info("Building calendar service")
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        return None


def create_calendar(service, calendar_name):
    calendar = {
        'summary': calendar_name,
        'timeZone': 'Europe/Warsaw',
    }

    try:
        created_calendar = service.calendars().insert(body=calendar).execute()
        logger.debug(f"Created calendar: {created_calendar['id']}")
        return created_calendar['id']
    except HttpError as e:
        logger.error(f"An error occurred: {e}")
        return None


def delete_old_calendars(service, prefix='WAT-calendar'):
    try:
        calendar_result = service.calendarList().list().execute()

        for calendar_entry in calendar_result['items']:
            if calendar_entry['summary'].startswith(prefix):
                calendar_id = calendar_entry['id']
                logger.debug(f"Deleting calendar: {calendar_entry['summary']} (ID: {calendar_id})")
                service.calendars().delete(calendarId=calendar_id).execute()
                logger.debug(f"Deleted calendar: {calendar_entry['summary']} (ID: {calendar_id})")
    except HttpError as error:
        logger.error(f"Error occurred: {error}")


def create_event(service, calendar_id, event):
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.debug(f"Created event: {created_event['id']}")
        return created_event['id']
    except HttpError as e:
        logger.error(f"An error occurred: {e}")
        return None


def delete_all_events(service, calendar_id):
    try:
        events_result = service.events().list(calendarId=calendar_id, singleEvents=True).execute()
        events = events_result.get('items', [])

        for event in events:
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            logger.debug(f"Deleted event: {event['id']}")
    except HttpError as e:
        logger.error(f"An error occurred: {e}")
        return None


def update_calendar_with_schedule(service, calendar_id, schedule_data):
    # First, delete all events from the calendar
    delete_old_calendars(service, prefix='WAT-calendar')

    # Log the schedule data for debugging
    calendar_name = f"WAT-calendar+{date.today().isoformat()}"
    logger.info(f"Creating new calendar: {calendar_name}")
    calendar_id = create_calendar(service, calendar_name)

    if not calendar_id:
        logger.error("Nie udało się utworzyć nowego kalendarza. Operacja przerwana.")
        return

    logger.info(f"Created new calendar ID: {calendar_id}")

    for lesson in schedule_data:
        # Parse and reformat the dates to be in 'YYYY-MM-DD' format
        start_date = datetime.strptime(lesson['Start Date'], '%d/%m/%Y').strftime('%Y-%m-%d')
        end_date = datetime.strptime(lesson['End Date'], '%d/%m/%Y').strftime('%Y-%m-%d')

        # Construct the event with corrected date format
        event = {
            'summary': lesson['Subject'],
            'location': 'academy grounds',
            'private': True,
            'description': lesson['Description'],
            'start': {
                'dateTime': f"{start_date}T{lesson['Start Time']}:00",
                'timeZone': 'Europe/Warsaw',
            },
            'end': {
                'dateTime': f"{end_date}T{lesson['End Time']}:00",
                'timeZone': 'Europe/Warsaw',
            },
        }

        # Log the event data before creating it
        logger.debug(f"Creating event: {event}")
        create_event(service, calendar_id, event)


def main(schedule_data):
    service = get_calendar_service()
    if not service:
        return

    # Create a new calendar for the schedule
    calendar_name = f"WAT-calendar+{date.today().isoformat()}"
    calendar_id = create_calendar(service, calendar_name)

    if calendar_id:
        update_calendar_with_schedule(service, calendar_id, schedule_data)
        logger.info(f"Schedule updated in calendar: {calendar_name}")
    else:
        logger.error("Failed to create calendar")


if __name__ == '__main__':
    # To jest tylko do testów, gdy uruchamiamy ten skrypt bezpośrednio
    print("This script is meant to be imported, not run directly.")
