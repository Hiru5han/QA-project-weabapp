import os

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///helpdesk.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Allow debug mode to be toggled via an environment variable. It defaults to
# False to avoid running in debug mode unintentionally in production.
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("1", "true", "t")
