"""
Test suite for the base HTML template.

This test suite covers various scenarios related to the `base.html` template,
including whether certain elements are rendered correctly depending on the
authentication status of the user.

Attributes:
    client (FlaskClient): The test client for making requests to the application.
    app (Flask): The application instance.
"""

import pytest
from flask import url_for
from app.models import User, db


@pytest.fixture
def test_user(app):
    """
    Fixture to create or retrieve a test user in the database.

    This user is used for authentication-related tests.

    :param app: The Flask application instance.
    :type app: Flask
    :return: The created or existing user instance.
    :rtype: User
    """
    with app.app_context():
        # Check if the user already exists
        user = User.query.filter_by(email="test@example.com").first()
        if not user:
            # Create a test user if none exists
            user = User(name="Test User", email="test@example.com", password="password", role="admin")
            db.session.add(user)
            db.session.commit()
    return user


def test_base_template_renders(client, app):
    """
    Test that the base template renders correctly for unauthenticated users.

    This test checks that the base template renders without errors for users
    who are not logged in.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The application instance.
    :type app: Flask
    """
    response = client.get(url_for('main.index'))
    assert response.status_code == 200
    assert b"Help Desk Ticketing System" in response.data  # Adjusted to match the actual content
    assert b"Login or register to get started." in response.data  # Another check for specific content


def test_authenticated_user_navbar(client, app, test_user):
    """
    Test that the navbar shows the correct information for an authenticated user.

    This test logs in a user and checks that the correct navbar items are displayed.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The application instance.
    :type app: Flask
    :param test_user: A test user fixture.
    :type test_user: User
    """
    with client:
        with app.app_context():
            from flask_login import login_user

            # Simulate a user logging in
            login_user(test_user)

            # Follow the redirect after login
            response = client.get(url_for('main.index'), follow_redirects=True)
            assert response.status_code == 200
            assert b"Logout" in response.data
            assert b"Tickets" in response.data  # Adjust based on your actual content


def test_redirect_for_authenticated_user(client, app, test_user):
    """
    Test that an authenticated user is redirected from the index page.

    This test checks that a logged-in user is redirected to their appropriate
    dashboard based on their role.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The application instance.
    :type app: Flask
    :param test_user: A test user fixture.
    :type test_user: User
    """
    with client:
        with app.app_context():
            from flask_login import login_user

            # Simulate a user logging in
            login_user(test_user)

            # Perform the request
            response = client.get(url_for('main.index'))
            assert response.status_code == 302  # Expecting a redirect
            assert url_for('main.all_tickets') in response.headers['Location']


def test_logout_functionality(client, app, test_user):
    """
    Test the logout functionality.

    This test ensures that a logged-in user can log out and is then redirected
    to the index page.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The application instance.
    :type app: Flask
    :param test_user: A test user fixture.
    :type test_user: User
    """
    with client:
        with app.app_context():
            from flask_login import login_user, logout_user

            # Simulate a user logging in
            login_user(test_user)

            # Logout the user
            response = client.get(url_for('main.logout'), follow_redirects=True)
            assert response.status_code == 200
            assert b"Login" in response.data
            assert b"Register" in response.data
            assert not b"Logout" in response.data
