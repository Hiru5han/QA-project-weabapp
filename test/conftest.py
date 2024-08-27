# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
from test.test_config import TestConfig  # Import your test configuration

@pytest.fixture
def app():
    app = create_app(config=TestConfig)  # Pass the test configuration here

    with app.app_context():
        db.create_all()

        # Create a test user with a hashed password
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        user = User(name="Test User", email="test@example.com", password=hashed_password, role="Admin")
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def existing_user(app):
    with app.app_context():
        user = User(
            name="Existing User",
            email="existing@example.com",
            password=generate_password_hash("ValidPassword1!", method="pbkdf2:sha256"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
    return user
