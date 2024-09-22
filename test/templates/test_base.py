import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app import create_app, db
from app.models import User, db


@pytest.fixture
def app():
    """Fixture to create a Flask app instance for testing."""
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",  # Add this line
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Use in-memory database
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,  # Optionally disable CSRF for testing
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin_user(app):
    """Fixture to create an admin user in the test database."""
    with app.app_context():
        user = User(name="Test Admin", email="admin@test.com", role="admin")
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def client(app):
    """Fixture to provide a test client for the app."""
    return app.test_client()


def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    return soup.find("input", {"name": "csrf_token"})["value"]


def login_user(client, email, password):
    """Helper function to log in a user during tests."""
    login_data = {
        "email": email,
        "password": password,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200, "Login failed"
    return response


def test_base_template_unauthenticated(client):
    # Access any page that uses the base template
    with client:
        response = client.get(url_for("main.index"))
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check that the profile image is the default logo
        logo_img = soup.find("img", {"class": "logo-circle"})
        assert logo_img["src"] == url_for("static", filename="logo.png")

        # Check that profile and logout links are not present
        profile_link = soup.find("a", {"class": "profile-badge"})
        logout_link = soup.find("a", {"class": "logout-badge"})
        assert profile_link is None
        assert logout_link is None


def test_base_template_authenticated(client, app, admin_user):
    with app.app_context():
        # Re-attach the admin_user to the session
        admin_user = db.session.merge(admin_user)

        # Log in the user
        login_user(client, admin_user.email, "ValidPassword1!")

        # Access a page that uses the base template (assuming "/" uses base.html)
        response = client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200  # Ensure successful page load

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check if the user's profile image is displayed
        profile_img = soup.find("img", {"class": "logo-circle"})
        assert profile_img is not None
        assert "default.jpg" in profile_img["src"]  # Assuming user has default image


def test_base_template_role_badge(client, app, admin_user):
    with app.app_context():
        # Re-attach admin_user to the current session
        admin_user = db.session.merge(admin_user)

        # Ensure the admin user exists in the test database
        user_in_db = User.query.filter_by(email=admin_user.email).first()
        assert user_in_db is not None, "Admin user not found in database"

        # Proceed to log in the admin user
        response = login_user(client, admin_user.email, "ValidPassword1!")
        assert b"Logout" in response.data, "User is not logged in"

        # Access a page that uses the base template
        response = client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check if the role badge is displayed with the correct role
        role_badge = soup.find("span", {"class": "badge-role-admin"})
        assert role_badge is not None, "Admin role badge not found"
        assert "Admin" in role_badge.text


def test_base_template_flash_messages(client, app, admin_user):
    with app.app_context():
        # Re-attach the admin_user to the session
        admin_user = db.session.merge(admin_user)

        # Log in the user
        login_user(client, admin_user.email, "ValidPassword1!")

        # Send a flash message
        with client.session_transaction() as session:
            session["_flashes"] = [("success", "This is a success message.")]

        # Access any page that uses the base template (assuming "/" uses base.html)
        response = client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200  # Ensure successful page load

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check if the flash message is displayed
        flash_message = soup.find("div", {"class": "alert-success"})
        assert flash_message is not None
        assert "This is a success message." in flash_message.text
