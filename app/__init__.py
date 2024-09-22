from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
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
    elif config:
        app.config.from_object(config)
    else:
        app.config.from_pyfile("config.py")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    moment.init_app(app)

    from .models import User

    login_manager.login_view = "main.login"
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
