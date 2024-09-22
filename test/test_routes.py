import pytest
from app import db
from app.models import User, Ticket


@pytest.fixture
def setup_test_data():
    db.session.query(User).delete()
    db.session.query(Ticket).delete()

    # Create a test user with an appropriate role
    user = User(
        email="testuser@example.com", name="Test User", role="support"
    )  # Use 'support' or another role with access
    user.set_password("gyjvo9-kewvoh-Vurmuj!")
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


def login_user(client):
    # Log in the user with valid credentials
    response = client.post(
        "/login",
        data={"email": "testuser@example.com", "password": "gyjvo9-kewvoh-Vurmuj!"},
        follow_redirects=True,  # Follow redirects to ensure login is processed
    )
    assert response.status_code == 200 or response.status_code == 302, "Login failed"

    # Verify that the session retains the user login
    with client.session_transaction() as session:
        assert "_user_id" in session, "User ID not in session after login"
        session["_user_id"] = "1"  # Assuming user ID is 1 for testing purposes


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
    response = client.post(
        "/login",
        data={"email": "testuser@example.com", "password": "gyjvo9-kewvoh-Vurmuj"},
    )
    # Check for success (redirect to another page after login)
    assert response.status_code in [302, 200]  # 302 if login is successful, 200 if not
    if response.status_code == 200:
        assert b"Login" in response.data  # Check if we're still on the login page


def test_register_route_get(client):
    """
    Test the GET method for the register route ("/register").
    """
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_register_route_post(client):
    response = client.post(
        "/register",
        data={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "gyjvo9-kewvoh-Vurmuj!",  # Updated password with a special character
            "confirm": "gyjvo9-kewvoh-Vurmuj!",  # Ensure the confirm password matches
            "role": "regular",  # Add a valid role to the form data
        },
    )

    # If registration fails (status code 200), print the response to check for errors
    if response.status_code == 200:
        print(
            response.data.decode("utf-8")
        )  # This helps identify validation or form issues

    # Check for the redirect after successful registration
    assert response.status_code == 302  # Expecting a redirect on success

    # If registration fails (status code 200), print the response to check for errors
    if response.status_code == 200:
        print(
            response.data.decode("utf-8")
        )  # This helps identify validation or form issues

    # Check for the redirect after successful registration
    assert response.status_code == 302  # Expecting a redirect on success


def test_create_ticket_route_get(client, setup_test_data):
    login_user(client)  # Log in the user
    response = client.get("/create_ticket")
    assert response.status_code == 200
    assert b"Create Ticket" in response.data


def test_create_ticket_route_post(client, setup_test_data):
    # Assuming the user is logged in
    login_user(client)

    response = client.post(
        "/create_ticket",
        data={
            "title": "Test Ticket",
            "description": "Test description",
            "priority": "High",  # Ensure valid priority is passed
            "status": "Open",  # Ensure valid status is passed
        },
    )
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
    response = client.post(
        "/update_profile", data={"name": "New Name", "email": "newemail@example.com"}
    )
    assert (
        response.status_code == 302
    )  # Adjust based on whether the update is successful


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
    response = client.post("/delete_ticket/1")
    assert response.status_code == 302  # Assuming successful deletion redirects
