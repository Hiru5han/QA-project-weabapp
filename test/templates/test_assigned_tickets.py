import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app import create_app
from app.models import Ticket, User, db
from test.test_config import TestConfig


@pytest.fixture
def app():
    app = create_app(config=TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def existing_user(app):
    """
    Create an existing user in the database for testing.
    """
    with app.app_context():
        user = User(
            name="Existing User",
            email="existing@example.com",
            role="admin",
        )
        user.set_password("ValidPassword1!")  # Use the model's method to set password
        db.session.add(user)
        db.session.commit()
    return user


def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    csrf_input = soup.find("input", {"name": "csrf_token"})
    if csrf_input:
        return csrf_input["value"]
    return None


def test_password_validation():
    user = User(name="Test User", email="test@example.com", role="regular")
    try:
        user.set_password("ValidPassword1!")
    except ValueError as e:
        assert False, f"Password validation failed: {e}"


def login_user(client, email, password):
    """Helper function to log in a user during tests with CSRF protection enabled."""
    # Get the login page to retrieve the CSRF token
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data.decode("utf-8"))
    assert csrf_token is not None, "Could not find CSRF token in login page"

    # Submit the login form with the CSRF token included
    login_data = {
        "email": email,
        "password": password,
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    # Debug: Print the response to check for login success or failure
    print(response.data.decode("utf-8"))

    # Check if login was successful
    assert response.status_code == 200, "Login failed"
    assert (
        b"Logout" in response.data
    ), "Login unsuccessful, 'Logout' not found in response"
    return response


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(
            name="Admin User",
            email="admin@example.com",
            role="admin",
        )
        user.set_password(
            "ValidPassword1!"
        )  # Ensure the password meets complexity requirements
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def support_user(app):
    with app.app_context():
        user = User(
            name="Support User",
            email="support@example.com",
            role="support",
        )
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def regular_user(app):
    with app.app_context():
        user = User(
            name="Regular User",
            email="regular@example.com",
            role="regular",
        )
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


# Test for verifying the "Assigned Tickets" page renders correctly for admin and support
@pytest.mark.parametrize("user_role", ["admin", "support"])
def test_assigned_tickets_page_renders_correctly_for_admin_and_support(
    client, app, user_role, admin_user, support_user
):
    with app.app_context():
        # Re-attach the user to the session based on their role
        if user_role == "admin":
            user = db.session.merge(admin_user)
        elif user_role == "support":
            user = db.session.merge(support_user)

        # Log in the user
        response = login_user(client, user.email, "ValidPassword1!")

        # Ensure login was successful
        assert b"Logout" in response.data, "User is not logged in"

        # Access the "Assigned Tickets" page
        response = client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Verify that the page header is displayed correctly
        header = soup.find("h2", class_="text-primary")
        assert header is not None, "Assigned Tickets header not found"
        assert "Assigned Tickets" == header.text.strip(), "Incorrect page header"

        # Verify that the greeting is displayed correctly
        greeting = soup.find("p", class_="lead")
        assert greeting is not None, "Greeting not found"
        assert f"Welcome, {user.name}!" == greeting.text.strip(), "Incorrect greeting"


def test_all_tickets_button_visible_for_admin(client, app, admin_user):
    with app.app_context():
        # Merge admin user into session
        admin_user = db.session.merge(admin_user)

        # Log in as admin user
        response = login_user(client, admin_user.email, "ValidPassword1!")
        assert b"Logout" in response.data, "User is not logged in"

        # Access the "All Tickets" page
        response = client.get(url_for("main.all_tickets"), follow_redirects=False)
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.data, "html.parser")

        # Find the "All Tickets" button
        all_tickets_button = None
        for a_tag in soup.find_all("a"):
            if a_tag.text.strip() == "All Tickets":
                all_tickets_button = a_tag
                break
        assert all_tickets_button is not None, "All Tickets button not found for admin"

        # Check if the "All Tickets" button is active
        classes = all_tickets_button.get("class", [])
        print(f"Classes for 'All Tickets' button: {classes}")  # Debugging output
        assert "btn" in classes
        assert "btn-toggle" in classes
        assert "active" in classes, "All Tickets button is not active"

        # Add an extra check for the view context variable
        assert "view" in response.data.decode(), "'view' context not found in response"


def test_admin_delete_button_visibility_for_assigned_ticket(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)

        # Log in as the admin user
        response = login_user(client, admin_user.email, "ValidPassword1!")

        # Create a test ticket assigned to admin user
        ticket = Ticket(
            title="Admin's Assigned Ticket",
            description="Description",
            priority="High",
            status="Open",
            assignee=admin_user,
            creator=admin_user,
        )
        db.session.add(ticket)
        db.session.commit()

        # Access the assigned tickets page
        response = client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200

        # Parse the page to find the CSRF token in the delete form
        soup = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
        delete_form = soup.find(
            "form", {"action": url_for("main.delete_ticket", ticket_id=ticket.id)}
        )
        assert delete_form is not None, "Delete form not found"

        csrf_token = delete_form.find("input", {"name": "csrf_token"})["value"]
        assert csrf_token is not None, "CSRF token not found in delete form"

        # Submit the delete form
        delete_data = {
            "csrf_token": csrf_token,
        }
        response = client.post(
            url_for("main.delete_ticket", ticket_id=ticket.id),
            data=delete_data,
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify the ticket has been deleted
        deleted_ticket = Ticket.query.get(ticket.id)
        assert deleted_ticket is None, "Ticket was not deleted"
