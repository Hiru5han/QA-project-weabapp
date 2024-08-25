import os

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///helpdesk.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
