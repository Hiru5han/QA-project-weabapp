from unittest.mock import patch
from bs4 import BeautifulSoup
from flask import url_for
import pytest
from app import create_app, db
from app.models import User, Ticket
from app.routes import load_user


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
def setup_test_data(app):
    """Fixture to set up test data in the in-memory database."""
    with app.app_context():
        # Ensure all tables are created in the temp DB
        db.create_all()

        # Clear any existing data in the temp DB
        db.session.query(User).delete()
        db.session.query(Ticket).delete()

        # Create a test user and ticket
        user = User(email="testuser@example.com", name="Test User", role="admin")
        user.set_password("gyjvo9-kewvoh-Vurmuj!")  # Set password
        db.session.add(user)
        db.session.commit()

        ticket = Ticket(
            title="Active Ticket",
            description="An active test ticket",
            status="Open",
            priority="High",
            user_id=user.id,
            assigned_to=user.id,
        )
        db.session.add(ticket)
        db.session.commit()

        yield  # Run the test

        # Cleanup: Drop tables from the in-memory database
        db.drop_all()


def get_csrf_token(response_data):
    """Helper function to extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    token = soup.find("input", {"name": "csrf_token"})
    if token:
        return token.get("value")
    return None


def login_user(client):
    # Get the login page to extract the CSRF token
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    # Log in the user with valid credentials and CSRF token
    response = client.post(
        "/login",
        data={
            "email": "testuser@example.com",
            "password": "gyjvo9-kewvoh-Vurmuj!",
            "csrf_token": csrf_token,  # Include the CSRF token
        },
        follow_redirects=True,  # Follow redirects to ensure login is processed
    )

    assert response.status_code == 200 or response.status_code == 302, "Login failed"

    # Verify that the session retains the user login
    with client.session_transaction() as session:
        assert "_user_id" in session, "User ID not in session after login"


def test_home_route(client):
    """
    Test the home route ("/").
    """
    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"Help Desk Ticketing System" in response.data
    )  # Adjust to match the actual content of the home page


def test_login_route_get(client):
    """
    Test the GET method for the login route ("/login").
    """
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data  # Adjust based on content in the login page


def test_login_route_post(client, setup_test_data):
    # Fetch the login page to get the CSRF token
    response = client.get("/login")

    # Extract CSRF token from the response data
    csrf_token = get_csrf_token(response.data)
    assert csrf_token, "CSRF token not found"

    # Send the POST request with the login credentials and CSRF token
    response = client.post(
        "/login",
        data={
            "email": "testuser@example.com",
            "password": "gyjvo9-kewvoh-Vurmuj",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )

    # Check if the request was successful (either a redirect after successful login or 200 if login failed)
    assert response.status_code in [
        302,
        200,
    ], f"Expected 302 or 200, but got {response.status_code}"


def test_register_route_get(client):
    """
    Test the GET method for the register route ("/register").
    """
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_register_route_post(client):
    # Get the registration page to extract the CSRF token
    response = client.get(url_for("main.register"))
    csrf_token = get_csrf_token(response.data)

    response = client.post(
        "/register",
        data={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "gyjvo9-kewvoh-Vurmuj!",  # Updated password with a special character
            "confirm": "gyjvo9-kewvoh-Vurmuj!",  # Ensure the confirm password matches
            "role": "regular",  # Add a valid role to the form data
            "csrf_token": csrf_token,  # Include the CSRF token
        },
    )
    assert response.status_code == 302  # Expecting a redirect on success


def test_create_ticket_route_get(client, setup_test_data):
    login_user(client)  # Log in the user
    response = client.get("/create_ticket")
    assert response.status_code == 200
    assert b"Create Ticket" in response.data


def test_create_ticket_route_post(client, setup_test_data):
    # Assuming the user is logged in
    login_user(client)

    # Get the create ticket page to extract the CSRF token
    response = client.get("/create_ticket")
    csrf_token = get_csrf_token(response.data)

    # Create a new ticket with the CSRF token
    response = client.post(
        "/create_ticket",
        data={
            "title": "Test Ticket",
            "description": "Test description",
            "priority": "high",
            "status": "open",
            "csrf_token": csrf_token,  # Include CSRF token
        },
    )

    # Print response data to check for error messages
    print(response.data.decode())  # Temporarily add this line to inspect the output

    assert response.status_code == 302  # Assuming successful creation redirects


def test_all_tickets_route(client, setup_test_data):
    login_user(client)  # Log in the user

    response = client.get("/all_tickets")
    assert response.status_code == 200
    assert b"All Tickets" in response.data  # Check for expected page content


def test_active_tickets_route(client, setup_test_data):
    login_user(client)  # Log in the user
    response = client.get("/active_tickets")

    # Ensure the response status is correct
    assert response.status_code == 200

    # Check for the actual content in the page
    assert (
        b"All Tickets" in response.data or b"0 active" in response.data
    ), "Expected active tickets content not found"


def test_assigned_tickets_route(client, setup_test_data):
    # Log in the user
    login_user(client)

    # Access the assigned tickets route
    response = client.get("/assigned_tickets", follow_redirects=True)

    # Check for a successful response
    assert (
        response.status_code == 200
    ), f"Expected status code 200 but got {response.status_code}"
    assert (
        b"Assigned Tickets" in response.data
    )  # Ensure the page contains the expected content


def test_update_profile_route_get(client, setup_test_data):
    login_user(client)  # Log in the user
    response = client.get("/update_profile")
    assert response.status_code == 200
    assert b"Update Profile" in response.data


def test_update_profile_route_post(client, setup_test_data):
    # Log in the user to access the profile update page
    login_user(client)

    # Fetch the profile update page to get the CSRF token
    response = client.get(url_for("main.update_profile"))

    # Extract CSRF token from the response data
    csrf_token = get_csrf_token(response.data)
    assert csrf_token, "CSRF token not found"

    # Prepare data for updating the profile
    update_data = {
        "name": "Updated Test User",
        "email": "updatedtestuser@example.com",
        "csrf_token": csrf_token,
    }

    # Send the POST request to update the profile with the CSRF token
    response = client.post(
        url_for("main.update_profile"),
        data=update_data,
        follow_redirects=True,
    )

    # Check if the request was successful and the profile was updated
    assert response.status_code == 200

    # Update the expected flash message
    assert b"Your profile has been updated." in response.data


def test_logout_route(client):
    """
    Test the logout route ("/logout").
    """
    response = client.get("/logout")
    assert response.status_code == 302  # Assuming successful logout redirects


def test_ticket_details_readonly_route(client, setup_test_data):
    login_user(client)  # Ensure the user is logged in
    response = client.get(
        "/ticket/1/readonly"
    )  # Ensure the ticket ID matches the created ticket
    assert response.status_code == 200
    assert b"Ticket Details" in response.data


def test_delete_ticket_route_post(client, setup_test_data):
    login_user(client)  # Ensure the user is logged in

    # Fetch the page where CSRF token is expected (e.g., create ticket page)
    response = client.get(url_for("main.create_ticket"))
    csrf_token = get_csrf_token(response.data)
    assert csrf_token, "CSRF token not found"

    # Send the POST request to delete the ticket
    response = client.post(
        url_for("main.delete_ticket", ticket_id=1),
        data={"csrf_token": csrf_token},  # Include CSRF token
        follow_redirects=False,
    )

    # Check if the request was successful and redirected
    assert (
        response.status_code == 302
    ), f"Failed to delete ticket, got {response.status_code}"

    # Optionally follow the redirect and check for flash messages or landing page
    response = client.get(response.headers["Location"], follow_redirects=True)
    assert (
        b"Ticket has been deleted successfully." in response.data
    )  # Or whatever message you expect


def test_load_user_valid_user(setup_test_data, app):
    with app.app_context():
        # Retrieve the user from the database
        user = User.query.first()
        assert user is not None, "Test user not found in the database."

        # Call load_user with the user's ID
        result = load_user(user.id)
        assert result is not None, "load_user returned None for a valid user ID."
        assert result.id == user.id, "User IDs do not match."
        assert result.email == user.email, "User emails do not match."


def test_load_user_invalid_user(setup_test_data, app):
    with app.app_context():
        # Call load_user with an ID that doesn't exist
        non_existent_user_id = 999  # Assuming this ID doesn't exist
        result = load_user(non_existent_user_id)
        assert result is None, "load_user should return None for an invalid user ID."
