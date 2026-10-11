import hmac
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, request

from src.config import ADMIN_TOKEN
from src.utils.custom_logger import main_logger as logger

# Everything else (incl. flasgger's /apidocs, /apispec_1.json, /flasgger_static) requires ADMIN_TOKEN.
PUBLIC_PATHS: tuple[str, ...] = ("/", "/oauth2callback")
SAFE_METHODS: tuple[str, ...] = ("GET", "HEAD", "OPTIONS")


def _is_authorized() -> bool:
    auth = request.authorization
    if not auth or not ADMIN_TOKEN:
        return False
    candidate = auth.password if auth.type == "basic" else auth.token if auth.type == "bearer" else None
    return candidate is not None and hmac.compare_digest(candidate.encode(), ADMIN_TOKEN.encode())


def _protect() -> Response | tuple[Response, int] | None:
    # Browsers attach cached Basic credentials to cross-site form posts, so reject foreign origins.
    if request.method not in SAFE_METHODS:
        origin = request.headers.get("Origin")
        if origin and urlparse(origin).netloc != request.host:
            return jsonify({"error": "Cross-origin request rejected"}), 403

    if request.path in PUBLIC_PATHS:
        return None
    if not ADMIN_TOKEN:
        logger.error("ADMIN_TOKEN is not set - refusing access to protected routes")
        return jsonify({"error": "ADMIN_TOKEN is not configured on the server"}), 503
    if _is_authorized():
        return None
    return Response(
        "Authentication required", 401, {"WWW-Authenticate": 'Basic realm="WAT Scheduler"'}
    )


def init_auth(app: Flask) -> None:
    # App-wide hook (not per-blueprint) so routes outside our blueprints are protected too.
    app.before_request(_protect)
