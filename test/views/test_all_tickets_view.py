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


def login_regular_user(client):
    """Helper function to log in a regular user during tests."""
    # Create a regular user if not already created
    with client.application.app_context():
        user = User.query.filter_by(email="regularuser@example.com").first()
        if user is None:
            user = User(
                email="regularuser@example.com", name="Regular User", role="regular"
            )
            user.set_password("gyjvo9-kewvoh-Vurmuj!")
            db.session.add(user)
            db.session.commit()

    # Get the CSRF token from the login page
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    # Submit the login form with the CSRF token included
    login_data = {
        "email": "regularuser@example.com",
        "password": "gyjvo9-kewvoh-Vurmuj!",
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


def test_all_tickets_view_admin(client, setup_test_data):
    # Log in as the admin user
    login_user(client)

    # Create additional tickets for multiple users
    with client.application.app_context():
        # Get the admin user from the database
        admin_user = User.query.filter_by(email="testuser@example.com").first()
        assert admin_user is not None, "Admin user does not exist in the database"

        # Create a regular user
        regular_user = User(
            email="regularuser@example.com", name="Regular User", role="regular"
        )
        regular_user.set_password("gyjvo9-kewvoh-Vurmuj!")
        db.session.add(regular_user)
        db.session.commit()

        # Create a ticket for the admin user
        admin_ticket = Ticket(
            title="Admin Ticket",
            description="Ticket for admin user",
            status="open",
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )

        # Create a ticket for the regular user
        regular_ticket = Ticket(
            title="Regular Ticket",
            description="Ticket for regular user",
            status="open",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )

        # Add tickets to the database
        db.session.add_all([admin_ticket, regular_ticket])
        db.session.commit()

    # Make a GET request to the '/all_tickets' route
    response = client.get("/all_tickets")

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
    ticket_titles = [row.find("td").text.strip() for row in table_body.find_all("tr")]

    # Check that both tickets are displayed
    assert "Admin Ticket" in ticket_titles, "Admin ticket not found in the table"
    assert "Regular Ticket" in ticket_titles, "Regular ticket not found in the table"


def test_all_tickets_view_regular_user(client, setup_test_data):
    # Log in as the regular user
    login_regular_user(client)

    # Create tickets for multiple users
    with client.application.app_context():
        # Get users from the database
        regular_user = User.query.filter_by(email="regularuser@example.com").first()
        admin_user = User.query.filter_by(email="testuser@example.com").first()
        assert regular_user is not None, "Regular user does not exist in the database"
        assert admin_user is not None, "Admin user does not exist in the database"

        # Create a ticket for the regular user
        regular_ticket = Ticket(
            title="Regular User Ticket",
            description="Ticket for regular user",
            status="open",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )

        # Create a ticket for the admin user
        admin_ticket = Ticket(
            title="Admin User Ticket",
            description="Ticket for admin user",
            status="open",
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )

        # Add tickets to the database
        db.session.add_all([regular_ticket, admin_ticket])
        db.session.commit()

    # Make a GET request to the '/all_tickets' route
    response = client.get("/all_tickets")

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
    ticket_titles = [row.find("td").text.strip() for row in table_body.find_all("tr")]

    # Check that only the regular user's ticket is displayed
    assert (
        "Regular User Ticket" in ticket_titles
    ), "Regular user's ticket not found in the table"
    assert (
        "Admin User Ticket" not in ticket_titles
    ), "Admin user's ticket should not be in the table"
