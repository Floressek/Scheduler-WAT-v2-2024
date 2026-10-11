import json
import os
from typing import Any

from src.config import CREDENTIALS_PATH, REDIRECT_URI, TOKEN_PATH


def ensure_credentials_file() -> None:
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


def load_client_config() -> dict[str, Any]:
    with open(CREDENTIALS_PATH, "r") as f:
        return json.load(f)


def save_token(token_json: str) -> None:
    with open(TOKEN_PATH, "w") as token:
        token.write(token_json)


def delete_token() -> bool:
    if not os.path.exists(TOKEN_PATH):
        return False
    os.remove(TOKEN_PATH)
    return True


def token_exists() -> bool:
    return os.path.exists(TOKEN_PATH)


def read_token_info() -> dict[str, Any] | None:
    if not token_exists():
        return None
    with open(TOKEN_PATH) as f:
        token = json.load(f)
    return {"expiry": token.get("expiry"), "refresh": bool(token.get("refresh_token"))}
