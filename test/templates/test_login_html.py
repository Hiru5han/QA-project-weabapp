from flask import url_for  # Add this line to import url_for

import pytest
from flask import url_for  # Importing url_for for URL generation
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

def test_login_form_submission_success(client, app):
    """
    Test form submission on the login page with correct credentials.
    
    This test simulates a POST request to the login form with valid credentials
    and checks that the user is redirected to the dashboard.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    """
    with client:
        with app.app_context():
            response = client.post(url_for('main.login'), data={
                'email': 'test@example.com',
                'password': 'password'
            }, follow_redirects=True)
    
            assert response.status_code == 200
            assert b'Welcome, Test User!' in response.data  # Adjust according to what the dashboard displays
            assert b'Logout' in response.data  # Ensure the "Logout" link is visible

def test_login_form_submission_failure(client, app):
    """
    Test form submission on the login page with incorrect credentials.
    
    This test simulates a POST request to the login form with invalid credentials
    and checks that the user stays on the login page with an error message.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    """
    with client:
        with app.app_context():
            response = client.post(url_for('main.login'), data={
                'email': 'wrong@example.com',
                'password': 'wrongpassword'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Login failed. Check your email and password.' in response.data  # Error message check
            assert b'<h2 class="login-title">Login</h2>' in response.data  # Ensure the login form is still visible
