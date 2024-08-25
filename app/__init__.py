from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile("config.py")  # Ensure this file exists in the instance folder

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .models import User  # Make sure User model is correctly defined

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import bp  # Ensure bp is defined as a Blueprint in routes.py
    app.register_blueprint(bp)

    return app
