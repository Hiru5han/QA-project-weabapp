from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect  # Import CSRFProtect
from flask_moment import Moment  # Import Flask-Moment


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()  # Initialize CSRFProtect
moment = Moment()  # Initialize Flask-Moment


def create_app(config=None):
    """
    Initialise the Flask application.

    This function is the application factory, responsible for setting up the Flask
    application instance. It configures the application with the provided settings
    or defaults to a development configuration. Additionally, it initialises
    extensions such as SQLAlchemy, Flask-Login, and Flask-Migrate, and registers
    blueprints for routing.

    This file (`__init__.py`) is crucial in the structure of a Flask application, as
    it defines the application instance and sets up all the necessary components
    required to run the app.

    :param config: Optional; the configuration object or path to a configuration file.
                   If not provided, defaults to loading configuration from "config.py".
    :type config: object or str, optional

    :return: The configured Flask application instance.
    :rtype: Flask
    """
    app = Flask(__name__, instance_relative_config=True)

    if config:
        app.config.from_object(config)
    else:
        app.config.from_pyfile("config.py")  # Default to development config

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # Initialize CSRF protection with the app
    moment.init_app(app)  # Initialize Flask-Moment with the app

    from .models import User  # Ensure User model is correctly defined

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user by their user ID.

        This function is used by Flask-Login to retrieve a user from the database
        based on their user ID.

        :param user_id: The ID of the user to load.
        :type user_id: int

        :return: The User object corresponding to the given user ID, or None if no user is found.
        :rtype: User or None
        """
        return User.query.get(int(user_id))

    from .routes import bp  # Ensure bp is defined as a Blueprint in routes.py

    app.register_blueprint(bp)

    return app
