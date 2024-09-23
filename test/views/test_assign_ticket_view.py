from bs4 import BeautifulSoup
from flask import url_for
import pytest

from app import create_app
from app.models import Ticket, User, db


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


def login_user(client, email, password):
    """Helper function to log in a user during tests."""
    # Get the CSRF token from the login page
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    # Submit the login form with the CSRF token included
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


def test_assign_ticket_get_admin(client, setup_test_data):
    # Create a support user to assign the ticket to
    with client.application.app_context():
        support_user = User(
            email="supportuser@example.com", name="Support User", role="support"
        )
        support_user.set_password("gyjvo9-kewvoh-Vurmuj")
        db.session.add(support_user)
        db.session.commit()

    # Log in as the admin user
    login_user(client, "testuser@example.com", "gyjvo9-kewvoh-Vurmuj!")

    # Make a GET request to the assign_ticket route
    response = client.get(url_for("main.assign_ticket", ticket_id=1))
    assert response.status_code == 200

    # Check that the support user's name appears in the response
    assert b"Support User" in response.data
    assert b"Assign Ticket" in response.data


def test_assign_ticket_get_non_admin(client, setup_test_data):
    # Create a regular user
    with client.application.app_context():
        regular_user = User(
            email="regularuser@example.com", name="Regular User", role="regular"
        )
        regular_user.set_password("gyjvo9-kewvoh-Vurmuj")
        db.session.add(regular_user)
        db.session.commit()

    # Log in as the regular user
    login_user(client, "regularuser@example.com", "gyjvo9-kewvoh-Vurmuj")

    # Make a GET request to the assign_ticket route
    response = client.get(
        url_for("main.assign_ticket", ticket_id=1), follow_redirects=True
    )
    assert response.status_code == 200

    # Check that the user is redirected with a warning message
    assert b"Only admins can assign tickets." in response.data
    assert b"All Tickets" in response.data


def test_assign_ticket_post_admin_success(client, setup_test_data):
    with client:
        # Create a support user to assign the ticket to
        with client.application.app_context():
            support_user = User(
                email="supportuser@example.com", name="Support User", role="support"
            )
            support_user.set_password("gyjvo9-kewvoh-Vurmuj")
            db.session.add(support_user)
            db.session.commit()
            support_user_id = support_user.id

            # Get the ticket's id
            ticket = Ticket.query.filter_by(title="Active Ticket").first()
            assert ticket is not None, "Test ticket does not exist in the database"
            ticket_id = ticket.id

        # Log in as the admin user
        login_user(client, "testuser@example.com", "gyjvo9-kewvoh-Vurmuj!")

        # Submit the form to assign the ticket without CSRF token
        response = client.post(
            url_for("main.assign_ticket", ticket_id=ticket_id),
            data={"assigned_to": support_user_id},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Check that the ticket was assigned and a success message is shown
        with client.application.app_context():
            ticket = Ticket.query.get(ticket_id)
            assert ticket.assigned_to == support_user_id

        assert b"Ticket assigned successfully." in response.data


def test_assign_ticket_post_admin_no_assignee(client, setup_test_data):
    # Log in as the admin user
    login_user(client, "testuser@example.com", "gyjvo9-kewvoh-Vurmuj!")

    # Get CSRF token from the assign ticket page
    response = client.get(url_for("main.assign_ticket", ticket_id=1))

    # Submit the form without selecting an assignee
    response = client.post(
        url_for("main.assign_ticket", ticket_id=1),
        data={},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Check that a warning message is shown
    assert b"No assignee selected." in response.data
    assert b"Assign Ticket" in response.data


def test_assign_ticket_post_admin_invalid_assignee(client, setup_test_data):
    # Log in as the admin user
    login_user(client, "testuser@example.com", "gyjvo9-kewvoh-Vurmuj!")

    # Get CSRF token from the assign ticket page
    response = client.get(url_for("main.assign_ticket", ticket_id=1))

    # Submit the form with an invalid assignee ID
    response = client.post(
        url_for("main.assign_ticket", ticket_id=1),
        data={
            "assigned_to": 999,  # Assuming this ID doesn't exist
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Check that a warning message is shown
    assert b"Invalid assignee selected." in response.data
    assert b"Assign Ticket" in response.data


def test_assign_ticket_post_non_admin(client, setup_test_data):
    # Create a regular user
    with client.application.app_context():
        regular_user = User(
            email="regularuser@example.com", name="Regular User", role="regular"
        )
        regular_user.set_password("gyjvo9-kewvoh-Vurmuj")
        db.session.add(regular_user)
        db.session.commit()
        regular_user_id = regular_user.id  # Store the ID for later use

    # Log in as the regular user
    login_user(client, "regularuser@example.com", "gyjvo9-kewvoh-Vurmuj")

    # Attempt to submit the POST request to assign the ticket
    response = client.post(
        url_for("main.assign_ticket", ticket_id=1),
        data={
            "assigned_to": regular_user_id,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Check that the user is redirected with a warning message
    assert b"Only admins can assign tickets." in response.data
    assert b"All Tickets" in response.data
