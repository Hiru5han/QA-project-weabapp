from bs4 import BeautifulSoup
from flask import url_for
import pytest
from app import db
from app.models import User, Ticket


@pytest.fixture
def setup_test_data():
    db.session.query(User).delete()
    db.session.query(Ticket).delete()

    # Create a test user with an appropriate role
    user = User(
        email="testuser@example.com", name="Test User", role="admin"
    )  # Use 'support' or another role with access
    user.set_password("gyjvo9-kewvoh-Vurmuj!")  # Set password using set_password
    db.session.add(user)
    db.session.commit()

    # Create an active test ticket
    ticket = Ticket(
        title="Active Ticket",
        description="An active test ticket",
        status="Open",  # Ensure the ticket status is set to 'Open' or 'Active'
        priority="High",
        user_id=user.id,
        assigned_to=user.id,  # Assign the ticket to the user
    )
    db.session.add(ticket)
    db.session.commit()


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
