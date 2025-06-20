from flask import Flask
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

    @app.after_request
    def set_security_headers(response):
        """Add security headers to mitigate XSS."""
        csp = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://cdn.datatables.net https://cdnjs.cloudflare.com; "
            "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdnjs.cloudflare.com https://cdn.datatables.net https://stackpath.bootstrapcdn.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
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
