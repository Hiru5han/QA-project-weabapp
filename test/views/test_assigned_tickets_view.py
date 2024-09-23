# tests/test_assigned_tickets_view.py

import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app import create_app, db
from app.models import Ticket, User


@pytest.fixture
def app():
    """Fixture to create a Flask app instance for testing."""
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    token = soup.find("input", {"name": "csrf_token"})
    return token["value"] if token else None


def login_user(client, email, password):
    """Helper function to log in a user during tests."""
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    login_data = {
        "email": email,
        "password": password,
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


def login_admin_user(client):
    """Helper function to log in as the admin user."""
    return login_user(client, "admin@example.com", "gyjvo9-kewvoh-Vurmuj")


def login_support_user(client):
    """Helper function to log in as the support user."""
    return login_user(client, "support@example.com", "gyjvo9-kewvoh-Vurmuj")


def login_regular_user(client):
    """Helper function to log in as the regular user."""
    return login_user(client, "regular@example.com", "gyjvo9-kewvoh-Vurmuj")


@pytest.fixture
def setup_test_data(app):
    """Fixture to set up test data in the in-memory database."""
    with app.app_context():
        # Clear any existing data
        db.session.query(User).delete()
        db.session.query(Ticket).delete()

        # Create an admin user
        admin_user = User(email="admin@example.com", name="Admin User", role="admin")
        admin_user.set_password("gyjvo9-kewvoh-Vurmuj")
        db.session.add(admin_user)

        # Create a support user
        support_user = User(
            email="support@example.com", name="Support User", role="support"
        )
        support_user.set_password("gyjvo9-kewvoh-Vurmuj")
        db.session.add(support_user)

        # Create a regular user
        regular_user = User(
            email="regular@example.com", name="Regular User", role="regular"
        )
        regular_user.set_password("gyjvo9-kewvoh-Vurmuj")
        db.session.add(regular_user)

        db.session.commit()

        # Create tickets
        # Admin assigned ticket
        admin_ticket = Ticket(
            title="Admin Assigned Ticket",
            description="Ticket assigned to admin",
            status="Open",
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )

        # Support assigned ticket
        support_ticket = Ticket(
            title="Support Assigned Ticket",
            description="Ticket assigned to support",
            status="Open",
            priority="Medium",
            user_id=admin_user.id,
            assigned_to=support_user.id,
        )

        # Regular user assigned ticket (should not be visible to support/admin)
        regular_ticket = Ticket(
            title="Regular Assigned Ticket",
            description="Ticket assigned to regular user",
            status="Open",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )

        # Closed ticket (should not be visible)
        closed_ticket = Ticket(
            title="Closed Assigned Ticket",
            description="Closed ticket assigned to support",
            status="closed",
            priority="Low",
            user_id=admin_user.id,
            assigned_to=support_user.id,
        )

        db.session.add_all(
            [admin_ticket, support_ticket, regular_ticket, closed_ticket]
        )
        db.session.commit()

    yield  # Run the test

    # Cleanup: Drop tables from the in-memory database
    with app.app_context():
        db.drop_all()


# Test cases for AssignedTicketsView
def test_assigned_tickets_view_admin(client, setup_test_data):
    # Log in as the admin user
    login_admin_user(client)

    # Make a GET request to the '/assigned_tickets' route
    response = client.get("/assigned_tickets")

    # Check that the response status code is 200
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"

    # Parse the response data
    soup = BeautifulSoup(response.data, "html.parser")

    # Find the table body
    table_body = soup.find("tbody")
    assert table_body is not None, "Table body not found in the response"

    # Get all ticket titles from the table
    ticket_titles = [
        row.find_all("td")[0].text.strip() for row in table_body.find_all("tr")
    ]

    # Admin should see all assigned tickets except closed ones
    assert "Admin Assigned Ticket" in ticket_titles, "Admin assigned ticket not found"
    assert (
        "Support Assigned Ticket" in ticket_titles
    ), "Support assigned ticket not found"
    assert (
        "Regular Assigned Ticket" in ticket_titles
    ), "Regular assigned ticket not found"
    assert (
        "Closed Assigned Ticket" not in ticket_titles
    ), "Closed ticket should not be visible"


def test_assigned_tickets_view_support(client, setup_test_data):
    # Log in as the support user
    login_support_user(client)

    # Make a GET request to the '/assigned_tickets' route
    response = client.get("/assigned_tickets")

    # Check that the response status code is 200
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"

    # Parse the response data
    soup = BeautifulSoup(response.data, "html.parser")

    # Find the table body
    table_body = soup.find("tbody")
    assert table_body is not None, "Table body not found in the response"

    # Get all ticket titles from the table
    ticket_titles = [
        row.find_all("td")[0].text.strip() for row in table_body.find_all("tr")
    ]

    # Support should see only their assigned tickets and not closed tickets
    assert (
        "Support Assigned Ticket" in ticket_titles
    ), "Support assigned ticket not found"
    assert (
        "Admin Assigned Ticket" not in ticket_titles
    ), "Admin assigned ticket should not be visible"
    assert (
        "Regular Assigned Ticket" not in ticket_titles
    ), "Regular assigned ticket should not be visible"
    assert (
        "Closed Assigned Ticket" not in ticket_titles
    ), "Closed ticket should not be visible"


def test_assigned_tickets_view_regular_user(client, setup_test_data):
    # Log in as the regular user
    login_regular_user(client)

    # Make a GET request to the '/assigned_tickets' route
    response = client.get("/assigned_tickets", follow_redirects=True)

    # Check that the response status code is 200 (since we're following redirects)
    assert (
        response.status_code == 200
    ), f"Expected status code 200 after redirect, got {response.status_code}"

    # Verify redirection to '/all_tickets'
    assert (
        response.request.path == "/all_tickets"
    ), f"Expected to be redirected to '/all_tickets', but was on '{response.request.path}'"

    # Parse the response data
    soup = BeautifulSoup(response.data, "html.parser")

    # Verify that the user was flashed a warning message
    flash_messages = soup.find_all(
        "div", class_="alert-warning"
    )  # Adjust class if different

    warning_found = False
    for message in flash_messages:
        if "Only support staff and admins can view this page." in message.text:
            warning_found = True
            break

    assert (
        warning_found
    ), "Warning message not found when regular user accesses assigned_tickets_view"

    # Verify specific content unique to 'all_tickets' page
    # For example, a heading like "My Active Tickets"
    all_tickets_heading = soup.find("h2", text=lambda x: x and "My Active Tickets" in x)
    assert (
        all_tickets_heading is not None
    ), "Did not redirect to all_tickets page, 'My Active Tickets' heading not found"


def test_assigned_tickets_view_unauthenticated(client):
    # Make a GET request to the '/assigned_tickets' route without logging in
    response = client.get("/assigned_tickets", follow_redirects=True)

    # Check that the response redirects to the login page
    assert (
        response.status_code == 200
    ), f"Expected status code 200 after redirect, got {response.status_code}"
    assert (
        "Login" in response.data.decode()
    ), "Did not redirect to login page for unauthenticated user"
