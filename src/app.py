import os
import secrets

from flasgger import Swagger
from flask import Flask
from werkzeug import run_simple

from src.auth import init_auth
from src.google_api.credentials import ensure_credentials_file
from src.jobs import scheduled_job, start_scheduler
from src.routes import admin_bp, api_bp, oauth_bp
from src.swagger import SWAGGER_TEMPLATE

app = Flask(__name__)
# Random fallback is fine with a single gunicorn worker: the session only carries OAuth state.
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # saved schedule pages are ~200 KB
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

Swagger(app, template=SWAGGER_TEMPLATE)
init_auth(app)
for blueprint in (admin_bp, oauth_bp, api_bp):
    app.register_blueprint(blueprint)

ensure_credentials_file()
start_scheduler()


def create_app() -> Flask:
    with app.app_context():
        scheduled_job()
    return app


if __name__ == "__main__":
    app = create_app()
    run_simple("localhost", 5000, app, use_reloader=False, use_debugger=True)
