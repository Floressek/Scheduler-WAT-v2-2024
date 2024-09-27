from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build, logger
from googleapiclient.errors import HttpError
import os
import datetime

# Path: update_google_calendar.py
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as e:
        print(f"An error occurred: {e}")
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


def delete_calendar(service, calendar_id):
    try:
        service.calendars().delete(calendarId=calendar_id).execute()
        logger.debug(f"Deleted calendar: {calendar_id}")
    except HttpError as e:
        logger.error(f"An error occurred: {e}")
        return None


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
    delete_all_events(service, calendar_id)

    # Then add new events from the parsed schedule
    for lesson in schedule_data:
        event = {
            'summary': lesson['Subject'],
            'location': lesson['Location'],
            'description': lesson['Description'],
            'start': {
                'dateTime': f"{lesson['Start Date']}T{lesson['Start Time']}:00",
                'timeZone': 'Europe/Warsaw',
            },
            'end': {
                'dateTime': f"{lesson['End Date']}T{lesson['End Time']}:00",
                'timeZone': 'Europe/Warsaw',
            },
        }
        create_event(service, calendar_id, event)


def main(schedule_data):
    service = get_calendar_service()
    if not service:
        return

    # Create a new calendar for the schedule
    calendar_name = f"WAT-calendar+{datetime.date.today().isoformat()}"
    calendar_id = create_calendar(service, calendar_name)

    if calendar_id:
        update_calendar_with_schedule(service, calendar_id, schedule_data)
        logger.info(f"Schedule updated in calendar: {calendar_name}")
    else:
        logger.info("Failed to create calendar")


if __name__ == '__main__':
    pass