import os
from datetime import date, datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from src.config import SCOPES, TOKEN_PATH, TIMEZONE
from src.utils.custom_logger import google_api_logger as logger


def get_calendar_service() -> Resource | None:
    creds: Credentials | None = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found. Visit /login to authorize the application.")
            return None

        logger.info("Saving credentials to token.json")
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    try:
        logger.info("Building calendar service")
        return build("calendar", "v3", credentials=creds)
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        return None


def create_calendar(service: Resource, calendar_name: str) -> str | None:
    calendar = {
        "summary": calendar_name,
        "timeZone": TIMEZONE,
    }
    try:
        created_calendar = service.calendars().insert(body=calendar).execute()
        logger.debug(f"Created calendar: {created_calendar['id']}")
        return created_calendar["id"]
    except HttpError as e:
        logger.error(f"An error occurred: {e}")
        return None


def delete_old_calendars(service: Resource, prefix: str = "WAT-calendar") -> None:
    try:
        calendar_result = service.calendarList().list().execute()
        for calendar_entry in calendar_result["items"]:
            if calendar_entry["summary"].startswith(prefix):
                calendar_id = calendar_entry["id"]
                logger.debug(f"Deleting calendar: {calendar_entry['summary']} (ID: {calendar_id})")
                service.calendars().delete(calendarId=calendar_id).execute()
                logger.debug(f"Deleted calendar: {calendar_entry['summary']} (ID: {calendar_id})")
    except HttpError as error:
        logger.error(f"Error occurred: {error}")


def update_calendar_with_schedule(service: Resource, schedule_data: list[dict[str, Any]]) -> None:
    logger.info(f"Starting calendar update with {len(schedule_data)} events")

    try:
        delete_old_calendars(service, prefix="WAT-calendar")
        logger.info("Old calendars deleted")

        calendar_name = f"WAT-calendar+{date.today().isoformat()}"
        logger.info(f"Creating new calendar: {calendar_name}")
        calendar_id = create_calendar(service, calendar_name)

        if not calendar_id:
            logger.error("Failed to create new calendar")
            return

        logger.info(f"Created new calendar ID: {calendar_id}")

        def batch_callback(request_id: str, response: Any, exception: Exception | None) -> None:
            if exception is not None:
                logger.error(f"Error in batch request {request_id}: {exception}")
            else:
                logger.debug(f"Event created successfully: {response.get('id', 'unknown')}")

        batch = service.new_batch_http_request(callback=batch_callback)
        batch_start_index = 0

        for index, lesson in enumerate(schedule_data):
            try:
                start_date = datetime.strptime(lesson["Start Date"], "%d/%m/%Y").strftime("%Y-%m-%d")
                end_date = datetime.strptime(lesson["End Date"], "%d/%m/%Y").strftime("%Y-%m-%d")

                event: dict[str, Any] = {
                    "summary": lesson["Subject"],
                    "location": lesson["Location"],
                    "description": lesson["Description"],
                    "start": {
                        "dateTime": f"{start_date}T{lesson['Start Time']}:00",
                        "timeZone": TIMEZONE,
                    },
                    "end": {
                        "dateTime": f"{end_date}T{lesson['End Time']}:00",
                        "timeZone": TIMEZONE,
                    },
                }

                batch.add(service.events().insert(calendarId=calendar_id, body=event))

                if (index + 1) % 50 == 0:
                    logger.info(f"Executing batch request for events {batch_start_index + 1}-{index + 1}")
                    batch.execute()
                    batch = service.new_batch_http_request(callback=batch_callback)
                    batch_start_index = index + 1

            except Exception as e:
                logger.error(f"Error creating event {index + 1}: {e}")

        if len(batch._requests) > 0:
            logger.info(f"Executing batch request for events {batch_start_index + 1}-{len(schedule_data)}")
            batch.execute()

        logger.info("Calendar update completed successfully")
    except Exception as e:
        logger.error(f"Error during calendar update: {e}")


def main(schedule_data: list[dict[str, Any]]) -> None:
    service = get_calendar_service()
    if not service:
        return
    update_calendar_with_schedule(service, schedule_data)


if __name__ == "__main__":
    print("This script is meant to be imported, not run directly.")
