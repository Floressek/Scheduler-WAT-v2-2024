import random
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from src.config import BLOCK_HOURS, LOCATION, USER_AGENTS
from src.utils.custom_logger import scheduler_logger as logger


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y_%m_%d")


def scrape_schedule(
    group: str, user_agent: str | None = None
) -> tuple[list[dict[str, Any]], None] | tuple[None, str]:
    current_timestamp = int(datetime.now().timestamp())
    url = f"https://planzajec.wcy.wat.edu.pl/pl/rozklad?date={current_timestamp}&grupa_id={group}"
    headers = {"User-Agent": user_agent or get_random_user_agent()}

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        schedule_data: list[dict[str, Any]] = []

        lessons = soup.find("div", class_="lessons hidden")
        if not lessons:
            logger.error("Could not find 'lessons hidden' div")
            return None, "Schedule data not found on the page"

        lesson_divs = lessons.find_all("div", class_="lesson")
        if not lesson_divs:
            logger.warning("No lessons found on the page.")
            return None, "No lessons found in the schedule"

        for lesson in lesson_divs:
            lesson_date = parse_date(lesson.find("span", class_="date").text)
            block_id: str = lesson.find("span", class_="block_id").text
            name: str = lesson.find("span", class_="name").text.replace("<br>", " ").strip()
            info: str = lesson.find("span", class_="info").text

            block_time = BLOCK_HOURS.get(block_id, {})
            lesson_info: dict[str, Any] = {
                "Subject": name,
                "Start Date": lesson_date.strftime("%d/%m/%Y"),
                "Start Time": block_time.get("START", ""),
                "End Date": lesson_date.strftime("%d/%m/%Y"),
                "End Time": block_time.get("END", ""),
                "All Day Event": False,
                "Description": info,
                "Location": LOCATION,
                "Private": True,
            }
            schedule_data.append(lesson_info)

        if not schedule_data:
            logger.warning("No lessons found in the schedule.")
            return None, "No lessons found in the schedule"

        return schedule_data, None

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None, f"Failed to retrieve the page: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {e}"
