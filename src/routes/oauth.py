from flask import Blueprint, Response, jsonify, redirect, request, session
from google_auth_oauthlib.flow import Flow

from src.config import REDIRECT_URI, SCOPES
from src.google_api.credentials import delete_token as remove_token
from src.google_api.credentials import load_client_config, save_token
from src.utils.custom_logger import main_logger as logger

oauth_bp = Blueprint("oauth", __name__)


@oauth_bp.route("/login", methods=["GET"])
def login() -> Response:
    """
    Start Google OAuth2 authorization flow.
    ---
    responses:
      302:
        description: Redirect to Google consent screen.
    """
    flow = Flow.from_client_config(load_client_config(), scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(prompt="consent")
    session["oauth_state"] = state
    session["code_verifier"] = flow.code_verifier
    logger.info(f"Authorization for URL: {auth_url}")
    return redirect(auth_url)


@oauth_bp.route("/oauth2callback", methods=["GET"])
def oauth2callback() -> Response:
    """
    Google OAuth2 callback. Exchanges authorization code for credentials.
    ---
    parameters:
      - name: code
        in: query
        type: string
        required: true
        description: Authorization code from Google.
      - name: state
        in: query
        type: string
        required: true
        description: CSRF state token.
    responses:
      302:
        description: Redirect to home on success.
      400:
        description: Missing OAuth state (flow not started from /login).
    """
    # /login is protected, so a missing state means someone skipped it - without this check
    # oauthlib silently skips state validation and anyone could plant their own token.
    if "oauth_state" not in session:
        logger.warning("OAuth callback without session state - rejected")
        return Response("Missing OAuth state. Start from /login.", 400)
    flow = Flow.from_client_config(
        load_client_config(),
        scopes=SCOPES,
        state=session.get("oauth_state"),
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(
        authorization_response=request.url,
        code_verifier=session.get("code_verifier"),
    )
    save_token(flow.credentials.to_json())
    logger.info("Token saved to token.json")
    return redirect("/")


@oauth_bp.route("/delete-token", methods=["DELETE"])
def delete_token() -> tuple[Response, int]:
    """
    Delete the stored Google OAuth2 token.
    ---
    responses:
      200:
        description: Token deleted.
        schema:
          $ref: '#/definitions/Message'
      404:
        description: Token not found.
        schema:
          $ref: '#/definitions/Message'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        if remove_token():
            logger.info("Token deleted")
            return jsonify({"message": "Token deleted successfully"}), 200
        logger.info("Token not found")
        return jsonify({"message": "Token does not exist"}), 404
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
