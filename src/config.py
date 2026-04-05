import os

# --- Google OAuth ---
SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH: str = "/storage/token.json"
REDIRECT_URI: str = "https://scheduler-wat-v2-2024-production.up.railway.app/oauth2callback"

# --- Paths ---
CREDENTIALS_PATH: str = "credentials.json"

# --- Scheduler ---
DEFAULT_GROUP: str = os.getenv("DEFAULT_GROUP", "WCY25IX1S4")
SCHEDULE_INTERVAL_HOURS: int = 36

# --- Scraper ---
LOCATION: str = "academic grounds"
TIMEZONE: str = "Europe/Warsaw"

BLOCK_HOURS: dict[str, dict[str, str]] = {
    "block1": {"START": "08:00", "END": "09:35"},
    "block2": {"START": "09:50", "END": "11:25"},
    "block3": {"START": "11:40", "END": "13:15"},
    "block4": {"START": "13:30", "END": "15:05"},
    "block5": {"START": "16:00", "END": "17:35"},
    "block6": {"START": "17:50", "END": "19:25"},
    "block7": {"START": "19:40", "END": "21:15"},
}

USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277",
]
