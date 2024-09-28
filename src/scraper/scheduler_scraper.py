import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
from src.utils.custom_logger import scheduler_logger as logger

# Dictionary mapping blocks to hours (adjust if needed)
block_hours = {
    "block1": {"START": "08:00", "END": "09:35"},
    "block2": {"START": "09:50", "END": "11:25"},
    "block3": {"START": "11:40", "END": "13:15"},
    "block4": {"START": "13:30", "END": "15:05"},
    "block5": {"START": "15:45", "END": "17:20"},
    "block6": {"START": "17:35", "END": "19:10"},
    "block7": {"START": "19:25", "END": "21:10"}
}

# Adding a constant value - location
location = "academic grounds"

# List of User-Agent strings
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 '
    'Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 '
    'Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 '
    'Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
    'Safari/537.36 Edg/91.0.864.59',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
    'Safari/537.36 OPR/77.0.4054.277'
]


def get_random_user_agent():
    return random.choice(USER_AGENTS)


def parse_date(date_str):
    return datetime.strptime(date_str, '%Y_%m_%d')


def scrape_schedule(group, user_agent=None):
    # Get current timestamp in seconds
    current_timestamp = int(datetime.now().timestamp())

    url = f'https://planzajec.wcy.wat.edu.pl/pl/rozklad?date={current_timestamp}&grupa_id={group}'
    headers = {
        'User-Agent': user_agent or get_random_user_agent()
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # logging.debug(f"Full HTML content:\n{soup.prettify()}")

        schedule_data = []

        lessons = soup.find('div', class_='lessons hidden')
        if not lessons:
            logger.error("Could not find 'lessons hidden' div")
            return None, "Schedule data not found on the page"

        lesson_divs = lessons.find_all('div', class_='lesson')

        # logging.debug(f"Found {len(lesson_divs)} lessons")

        if not lesson_divs:
            logger.warning("No lessons found on the page.")
            return None, "No lessons found in the schedule"

        for lesson in lesson_divs:
            date = parse_date(lesson.find('span', class_='date').text)
            block_id = lesson.find('span', class_='block_id').text
            name = lesson.find('span', class_='name').text.replace('<br>', ' ').strip()
            info = lesson.find('span', class_='info').text
            color = lesson.find('span', class_='colorp').text
            teacher_initials = lesson.find('span', class_='sSkrotProwadzacego').text

            # Extract time from block_id
            time_range = {
                'block1': '08:00-09:35',
                'block2': '09:50-11:25',
                'block3': '11:40-13:15',
                'block4': '13:30-15:05',
                'block5': '15:45-17:20',
                'block6': '17:35-19:10',
                'block7': '19:25-21:10'
            }.get(block_id, '')

            start_time, end_time = time_range.split('-') if time_range else ('', '')

            lesson_info = {
                'Subject': name,
                'Start Date': date.strftime('%d/%m/%Y'),
                'Start Time': start_time,
                'End Date': date.strftime('%d/%m/%Y'),
                'End Time': end_time,
                'All Day Event': False,
                'Description': info,
                'Location': 'academic grounds',
                'Private': True,
            }

            schedule_data.append(lesson_info)
            # logging.debug(f"Added lesson: {lesson_info}")

        if not schedule_data:
            logger.warning("No lessons found in the schedule.")
            return None, "No lessons found in the schedule"

        return schedule_data, None
    except requests.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None, f"Failed to retrieve the page: {str(e)}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None, f"An unexpected error occurred: {str(e)}"
