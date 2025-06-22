from flask import Flask, request, redirect, url_for
from flask_login import current_user
import logging
import json
from logging.handlers import RotatingFileHandler
import os
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager: LoginManager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
moment = Moment()


def create_app(config=None):
    """
    Initialise the Flask application.
    """
    app = Flask(__name__, instance_relative_config=True)

    if isinstance(config, str):
        # Load the config by string reference, assuming 'TestingConfig' is in app.config
        app.config.from_object(f"app.config.{config}")
    elif isinstance(config, dict):
        # Load the configuration directly from the dictionary (useful for testing)
        app.config.update(config)
    else:
        app.config.from_pyfile("config.py")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    moment.init_app(app)

    # Configure application logging
    if not app.testing:
        class RequestFilter(logging.Filter):
            def filter(self, record):
                try:
                    record.remote_addr = request.remote_addr
                except RuntimeError:
                    record.remote_addr = None
                try:
                    record.user_id = current_user.get_id()
                except Exception:
                    record.user_id = None
                return True

        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "time": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "pathname": record.pathname,
                    "lineno": record.lineno,
                    "remote_addr": getattr(record, "remote_addr", None),
                    "user_id": getattr(record, "user_id", None),
                }
                return json.dumps(log_record)

        logs_dir = os.path.join(app.root_path, "..", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, "app.log"), maxBytes=10240, backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        file_handler.addFilter(RequestFilter())
        file_handler.setFormatter(JsonFormatter())
        app.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.addFilter(RequestFilter())
        stream_handler.setFormatter(JsonFormatter())
        app.logger.addHandler(stream_handler)

        app.logger.setLevel(logging.INFO)

    @app.after_request
    def set_security_headers(response):
        """Add security headers to mitigate XSS."""
        csp = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://cdn.datatables.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "script-src 'self' https://code.jquery.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://cdn.datatables.net https://stackpath.bootstrapcdn.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "connect-src 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Embedder-Policy", "require-corp")
        return response

    from .models import User

    setattr(login_manager, "login_view", "main.login")
    login_manager.login_message_category = "info"

    @login_manager.unauthorized_handler
    def unauthorized():
        app.logger.warning(
            "Unauthorized access attempt from %s to %s",
            request.remote_addr,
            request.path,
        )
        from .utils import log_audit_event
        log_audit_event(None, "unauthorized access", details=request.path)
        return redirect(url_for("main.login"))

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user by their user ID.
        """
        return User.query.get(int(user_id))

    from .routes import bp

    app.register_blueprint(bp)

    from .utils import inject_open_tickets_count

    app.context_processor(inject_open_tickets_count)

    return app
