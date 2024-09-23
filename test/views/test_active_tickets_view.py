from bs4 import BeautifulSoup
from flask import url_for
import pytest

from app import create_app, db
from app.models import Ticket, User


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


# Helper function to extract CSRF token from HTML
def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    return soup.find("input", {"name": "csrf_token"})["value"]


# Helper function to log in a user with CSRF token
def login_user(client):
    """Helper function to log in a user during tests."""
    # First, get the CSRF token from the login page
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    # Submit the login form with the CSRF token included
    login_data = {
        "email": "testuser@example.com",
        "password": "gyjvo9-kewvoh-Vurmuj!",
        "csrf_token": csrf_token,  # Include the CSRF token
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


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


def test_active_tickets_view(client, setup_test_data):
    # Log in as the test user
    login_user(client)

    # Create additional tickets in the test database
    with client.application.app_context():
        # Get the test user from the database
        user = User.query.filter_by(email="testuser@example.com").first()

        # Ensure the user exists
        assert user is not None, "Test user does not exist in the database"

        # Create open and closed tickets for the test user
        open_ticket = Ticket(
            title="Open Ticket",
            description="This is an open ticket",
            status="open",
            priority="High",
            user_id=user.id,
            assigned_to=user.id,
        )
        closed_ticket = Ticket(
            title="Closed Ticket",
            description="This is a closed ticket",
            status="closed",
            priority="Low",
            user_id=user.id,
            assigned_to=user.id,
        )

        # Add tickets to the database
        db.session.add_all([open_ticket, closed_ticket])
        db.session.commit()

    # Make a GET request to the '/active_tickets' route
    response = client.get("/active_tickets")

    # Check that the response status code is 200
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"

    # Parse the response data
    soup = BeautifulSoup(response.data, "html.parser")

    # Find the table body
    table_body = soup.find("tbody")

    # Check if table_body is found
    assert table_body is not None, "Table body not found in the response"

    # Get all ticket titles from the table
    ticket_titles = []
    for row in table_body.find_all("tr"):
        title_cell = row.find("td", class_="text-center")
        if title_cell:
            ticket_titles.append(title_cell.text.strip())

    # Check that "Open Ticket" is in the ticket titles
    assert "Open Ticket" in ticket_titles, "Open ticket not found in the table"

    # Check that "Closed Ticket" is not in the ticket titles
    assert (
        "Closed Ticket" not in ticket_titles
    ), "Closed ticket should not be in the table"
