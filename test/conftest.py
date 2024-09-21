from test.test_config import TestConfig  # Import your test configuration

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """
    Create and configure a new app instance for each test.

    This fixture sets up the application context, initializes the database,
    creates a test user, and yields the app for testing. After the test,
    the database is cleaned up.

    Yields:
        Flask: The Flask application instance with a test configuration.
    """
    app = create_app(config=TestConfig)  # Pass the test configuration here

    with app.app_context():
        db.create_all()

        # Create a test user with a hashed password
        hashed_password = generate_password_hash("password", method="pbkdf2:sha256")
        user = User(
            name="Test User",
            email="test@example.com",
            password_hash=hashed_password,
            role="Admin",
        )
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_client(app):
    """
    Create a test client for the app.

    This fixture provides a client that can be used to send HTTP requests
    to the Flask application during testing.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        FlaskClient: A test client for the Flask application.
    """
    return app.test_client()
