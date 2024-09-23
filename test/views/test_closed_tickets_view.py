# tests/test_closed_tickets_view.py

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
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # In-memory DB for testing
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
        # Closed tickets
        closed_ticket_admin = Ticket(
            title="Closed Ticket Admin",
            description="Closed ticket created by admin",
            status="closed",  # Ensure lowercase to match view's filter
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )

        closed_ticket_support = Ticket(
            title="Closed Ticket Support",
            description="Closed ticket assigned to support",
            status="closed",
            priority="Medium",
            user_id=admin_user.id,
            assigned_to=support_user.id,
        )

        closed_ticket_regular = Ticket(
            title="Closed Ticket Regular",
            description="Closed ticket created by regular user",
            status="closed",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )

        # Open tickets (should not appear in closed_tickets_view)
        open_ticket_admin = Ticket(
            title="Open Ticket Admin",
            description="Open ticket created by admin",
            status="open",
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )

        open_ticket_support = Ticket(
            title="Open Ticket Support",
            description="Open ticket assigned to support",
            status="open",
            priority="Medium",
            user_id=admin_user.id,
            assigned_to=support_user.id,
        )

        open_ticket_regular = Ticket(
            title="Open Ticket Regular",
            description="Open ticket created by regular user",
            status="open",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )

        db.session.add_all(
            [
                closed_ticket_admin,
                closed_ticket_support,
                closed_ticket_regular,
                open_ticket_admin,
                open_ticket_support,
                open_ticket_regular,
            ]
        )
        db.session.commit()

    yield  # Run the test

    # Cleanup: Drop tables from the in-memory database
    with app.app_context():
        db.drop_all()


def test_closed_tickets_view_admin(client, setup_test_data):
    """Test that admin users see all closed tickets."""
    # Log in as the admin user
    login_admin_user(client)

    # Make a GET request to the '/closed_tickets' route
    response = client.get("/closed_tickets")

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

    # Admin should see all closed tickets
    assert "Closed Ticket Admin" in ticket_titles, "Closed Ticket Admin not found"
    assert "Closed Ticket Support" in ticket_titles, "Closed Ticket Support not found"
    assert "Closed Ticket Regular" in ticket_titles, "Closed Ticket Regular not found"

    # Ensure no open tickets are displayed
    assert (
        "Open Ticket Admin" not in ticket_titles
    ), "Open Ticket Admin should not be visible"
    assert (
        "Open Ticket Support" not in ticket_titles
    ), "Open Ticket Support should not be visible"
    assert (
        "Open Ticket Regular" not in ticket_titles
    ), "Open Ticket Regular should not be visible"


def test_closed_tickets_view_support(client, setup_test_data):
    """Test that support users see only closed tickets assigned to them."""
    # Log in as the support user
    login_support_user(client)

    # Make a GET request to the '/closed_tickets' route
    response = client.get("/closed_tickets")

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

    # Support should see only their assigned closed tickets
    assert "Closed Ticket Support" in ticket_titles, "Closed Ticket Support not found"
    assert (
        "Closed Ticket Admin" not in ticket_titles
    ), "Closed Ticket Admin should not be visible"
    assert (
        "Closed Ticket Regular" not in ticket_titles
    ), "Closed Ticket Regular should not be visible"

    # Ensure no open tickets are displayed
    assert (
        "Open Ticket Admin" not in ticket_titles
    ), "Open Ticket Admin should not be visible"
    assert (
        "Open Ticket Support" not in ticket_titles
    ), "Open Ticket Support should not be visible"
    assert (
        "Open Ticket Regular" not in ticket_titles
    ), "Open Ticket Regular should not be visible"


def test_closed_tickets_view_regular_user(client, setup_test_data):
    """Test that regular users see only closed tickets they created."""
    # Log in as the regular user
    login_regular_user(client)

    # Make a GET request to the '/closed_tickets' route
    response = client.get("/closed_tickets")

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

    # Regular user should see only their created closed tickets
    assert "Closed Ticket Regular" in ticket_titles, "Closed Ticket Regular not found"
    assert (
        "Closed Ticket Admin" not in ticket_titles
    ), "Closed Ticket Admin should not be visible"
    assert (
        "Closed Ticket Support" not in ticket_titles
    ), "Closed Ticket Support should not be visible"

    # Ensure no open tickets are displayed
    assert (
        "Open Ticket Admin" not in ticket_titles
    ), "Open Ticket Admin should not be visible"
    assert (
        "Open Ticket Support" not in ticket_titles
    ), "Open Ticket Support should not be visible"
    assert (
        "Open Ticket Regular" not in ticket_titles
    ), "Open Ticket Regular should not be visible"


def test_closed_tickets_view_unauthenticated(client):
    """Test that unauthenticated users are redirected to the login page."""
    # Make a GET request to the '/closed_tickets' route without logging in
    response = client.get("/closed_tickets", follow_redirects=True)

    # Check that the response status code is 200 (since we're following redirects)
    assert (
        response.status_code == 200
    ), f"Expected status code 200 after redirect, got {response.status_code}"

    # Verify redirection to the login page by checking for "Login" in the response
    assert (
        "Login" in response.data.decode()
    ), "Did not redirect to login page for unauthenticated user"

    # Optionally, verify that no tickets are displayed on the login page
    soup = BeautifulSoup(response.data, "html.parser")
    table_body = soup.find("tbody")
    if table_body:
        ticket_titles = [
            row.find_all("td")[0].text.strip() for row in table_body.find_all("tr")
        ]
        assert (
            not ticket_titles
        ), "Tickets should not be visible to unauthenticated users"
