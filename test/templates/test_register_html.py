import pytest
from flask import url_for
from app.models import User, db
from werkzeug.security import generate_password_hash

def test_successful_registration(client, app):
    """
    Test a successful registration with valid inputs.
    
    This test submits a valid registration form and ensures the user is redirected
    to the main tickets page after successful registration.
    
    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    """
    response = client.post(url_for('main.register'), data={
        'name': 'New User',
        'email': 'newuser@example.com',
        'password': 'ValidPassword1!',
        'role': 'admin'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"All Tickets" in response.data  # Replace with actual content from the redirected page
    assert User.query.filter_by(email='newuser@example.com').first() is not None

def test_registration_invalid_name(client, app):
    """
    Test registration with an invalid name containing numbers.
    
    This test checks that the form is re-rendered with an error message
    when the user submits a name that contains numbers.
    
    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    """
    response = client.post(url_for('main.register'), data={
        'name': 'User123',
        'email': 'invalidname@example.com',
        'password': 'ValidPassword1!',
        'role': 'admin'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Name cannot contain numbers." in response.data
    assert User.query.filter_by(email='invalidname@example.com').first() is None

def test_registration_invalid_email(client, app):
    """
    Test registration with an invalid email format.
    
    This test checks that the form is re-rendered with an error message
    when the user submits an invalid email address.
    
    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    """
    response = client.post(url_for('main.register'), data={
        'name': 'Valid User',
        'email': 'invalid-email',
        'password': 'ValidPassword1!',
        'role': 'admin'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid email address." in response.data
    assert User.query.filter_by(email='invalid-email').first() is None

def test_registration_weak_password(client, app):
    """
    Test registration with a weak password.
    
    This test checks that the form is re-rendered with an error message
    when the user submits a password that does not meet the complexity requirements.
    
    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    """
    response = client.post(url_for('main.register'), data={
        'name': 'Valid User',
        'email': 'validuser@example.com',
        'password': 'weak',
        'role': 'admin'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data
    assert User.query.filter_by(email='validuser@example.com').first() is None

def test_registration_duplicate_email(client, app, existing_user):
    """
    Test registration with a duplicate email.

    This test checks that the form is re-rendered with an error message
    when the user submits an email that is already registered in the system.

    :param client: The test client for making requests to the application.
    :type client: FlaskClient
    :param app: The Flask application instance.
    :type app: Flask
    :param existing_user: A fixture that provides an existing user.
    :type existing_user: User
    """
    with app.app_context():
        existing_user = db.session.merge(existing_user)  # Re-attach the user to the session
        response = client.post(url_for('main.register'), data={
            'name': 'New User',
            'email': existing_user.email,
            'password': 'ValidPassword1!',
            'role': 'admin'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Email address already in use." in response.data
        assert User.query.filter_by(email=existing_user.email).count() == 1
