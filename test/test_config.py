# tests/test_config.py
import os

class TestConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'test_secret_key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
