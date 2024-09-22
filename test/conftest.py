import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
from test.test_config import TestConfig  # Import your test configuration


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

        # Create a test user without passing `password` directly
        user = User(name="Test User", email="test@example.com", role="Admin")
        user.set_password("ValidPassword1!")  # Set password via the model's method
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
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


@pytest.fixture
def runner(app):
    """
    Create a test command-line runner for the app.

    This fixture provides a runner that can be used to invoke
    command-line commands in the Flask application during testing.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        FlaskCliRunner: A CLI runner for the Flask application.
    """
    return app.test_cli_runner()


@pytest.fixture
def existing_user(app):
    """
    Create an existing user in the database for testing.

    This fixture creates a user with a predefined name, email, and password,
    and adds the user to the database.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        User: The created user object.
    """
    with app.app_context():
        user = User(
            name="Existing User",
            email="existing@example.com",
            role="admin",
        )
        user.set_password("ValidPassword1!")  # Use `set_password` instead of `password`
        db.session.add(user)
        db.session.commit()
    return user
