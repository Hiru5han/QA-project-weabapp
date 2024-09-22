import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app.models import User, db


@pytest.fixture
def admin_user(app):
    """Fixture to create an admin user."""
    with app.app_context():
        # Create an admin user
        user = User(name="Admin User", email="admin@example.com", role="admin")
        user.set_password("ValidPassword1!")  # Set a valid password
        db.session.add(user)
        db.session.commit()
        return user


# Helper function to extract CSRF token from HTML
def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    return soup.find("input", {"name": "csrf_token"})["value"]


# Helper function to log in a user with CSRF token
def login_user(test_client, email, password):
    """Helper function to log in a user during tests."""
    # First, get the CSRF token from the login page
    response = test_client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    # Submit the login form with the CSRF token included
    login_data = {
        "email": email,
        "password": password,
        "csrf_token": csrf_token,  # Include the CSRF token in the form data
    }
    response = test_client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


# Test for the unauthenticated navbar
def test_base_template_unauthenticated(test_client):
    # Access any page that uses the base template (assuming "/" uses base.html)
    response = test_client.get(url_for("main.index"))
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


def test_base_template_authenticated(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin_user to the session
        admin_user = db.session.merge(admin_user)

        # Log in the user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Access a page that uses the base template (assuming "/" uses base.html)
        response = test_client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200  # Ensure successful page load

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check if the user's profile image is displayed
        profile_img = soup.find("img", {"class": "logo-circle"})
        assert profile_img is not None
        assert "default.jpg" in profile_img["src"]  # Assuming user has default image


def test_base_template_role_badge(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin_user to the session
        admin_user = db.session.merge(admin_user)

        # Log in the user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Access any page that uses the base template (assuming "/" uses base.html)
        response = test_client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200  # Ensure successful page load

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check if the role badge is displayed with the correct role
        role_badge = soup.find("span", {"class": "badge-role-admin"})
        assert role_badge is not None
        assert "Admin" in role_badge.text


def test_base_template_flash_messages(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin_user to the session
        admin_user = db.session.merge(admin_user)

        # Log in the user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Send a flash message
        with test_client.session_transaction() as session:
            session["_flashes"] = [("success", "This is a success message.")]

        # Access any page that uses the base template (assuming "/" uses base.html)
        response = test_client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200  # Ensure successful page load

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Check if the flash message is displayed
        flash_message = soup.find("div", {"class": "alert-success"})
        assert flash_message is not None
        assert "This is a success message." in flash_message.text
