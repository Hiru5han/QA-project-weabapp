import pytest
from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """
    Create and configure a new app instance for each test.

    This fixture sets up the application with an in-memory database
    and creates a test user for authentication-related tests.

    :return: Flask application instance
    :rtype: Flask
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with app.app_context():
        db.create_all()

        # Create a test user with hashed password
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        user = User(name="Test User", email="test@example.com", password=hashed_password, role="Admin")
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """
    A test client for the app.

    This fixture provides a test client that can be used to send
    requests to the application during tests.

    :param app: The Flask application instance.
    :type app: Flask
    :return: Test client
    :rtype: FlaskClient
    """
    return app.test_client()

@pytest.fixture
def runner(app):
    """
    A test runner for the app's Click commands.

    This fixture provides a runner for testing the app's command-line
    commands using the Flask CLI.

    :param app: The Flask application instance.
    :type app: Flask
    :return: Test CLI runner
    :rtype: FlaskCliRunner
    """
    return app.test_cli_runner()

# @pytest.fixture
# def existing_user(app):
#     """
#     Fixture to create an existing user in the database for duplicate email tests.
    
#     :param app: The Flask application instance.
#     :type app: Flask
#     :return: The created user instance.
#     :rtype: User
#     """
#     with app.app_context():
#         user = User(
#             name="Existing User",
#             email="existing@example.com",
#             password=generate_password_hash("ValidPassword1!", method="pbkdf2:sha256"),
#             role="admin"
#         )
#         db.session.add(user)
#         db.session.commit()
#     return user
