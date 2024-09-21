import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app.models import Ticket, User, db


# Helper function to extract CSRF token from HTML
def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    return soup.find("input", {"name": "csrf_token"})["value"]


# Helper function to log in a user with CSRF token
def login_user(test_client, email, password):
    """Helper function to log in a user during tests."""
    # First, get the CSRF token from the login page
    response = test_client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)

    # Submit the login form with the CSRF token included
    login_data = {
        "email": email,
        "password": password,
        "csrf_token": csrf_token,  # Include the CSRF token in the form data
    }
    response = test_client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


# Fixture to create an existing user
@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(name="Admin User", email="admin@example.com", role="admin")
        user.set_password("ValidPassword1!")  # Hash the password
        db.session.add(user)
        db.session.commit()
        return user


# Fixture to create an existing user
@pytest.fixture
def existing_user(app):
    with app.app_context():
        user = User(name="Existing User", email="existing@example.com", role="existing")
        user.set_password("ValidPassword1!")  # Hash the password
        db.session.add(user)
        db.session.commit()
        return user


# Fixture to create an existing user
@pytest.fixture
def support_user(app):
    with app.app_context():
        user = User(name="Support User", email="support@example.com", role="support")
        user.set_password("ValidPassword1!")  # Hash the password
        db.session.add(user)
        db.session.commit()
        return user


# Fixture to create a regular user
@pytest.fixture
def regular_user(app):
    with app.app_context():
        user = User(name="Regular User", email="regular@example.com", role="regular")
        user.set_password("ValidPassword1!")  # Hash the password
        db.session.add(user)
        db.session.commit()
        return user


def test_all_tickets_page_renders_correctly_for_admin(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the user to the session
        admin_user = db.session.merge(admin_user)

        # Log in as the existing user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Access the all tickets page
        response = test_client.get(url_for("main.all_tickets"))
        assert response.status_code == 200

        # Check that the correct template is used
        assert b"All Tickets" in response.data
        assert b"Unassigned Tickets" in response.data
        assert b"Assigned Tickets" in response.data
        assert b"Active Tickets" not in response.data
        assert b"Closed Tickets" in response.data
        assert b"Your Tickets" not in response.data


def test_ticket_table_content(test_client, app, existing_user):
    with app.app_context():
        # Re-attach the user to the session
        existing_user = db.session.merge(existing_user)

        # Ensure the user has the 'admin' role so they can view all tickets
        existing_user.role = "admin"
        db.session.commit()  # Commit the role change

        # Create some test tickets with a non-null description
        ticket1 = Ticket(
            title="Test Ticket 1",
            description="This is a description for Test Ticket 1",
            priority="High",
            status="Open",
            assignee=existing_user,  # Assign to existing user
        )
        ticket2 = Ticket(
            title="Test Ticket 2",
            description="This is a description for Test Ticket 2",
            priority="Medium",
            status="Closed",
            assignee=None,  # Unassigned ticket
        )
        db.session.add_all([ticket1, ticket2])

        # Commit the session to persist the tickets
        db.session.commit()

        # Log in as the existing user
        login_user(test_client, existing_user.email, "ValidPassword1!")

        # Access the all tickets page
        response = test_client.get(url_for("main.all_tickets"))
        assert response.status_code == 200

        # Verify the tickets are displayed in the table
        assert b"Test Ticket 1" in response.data
        assert b"High" in response.data
        assert b"Open" in response.data
        assert b"Existing User" in response.data  # Assignee name

        assert b"Test Ticket 2" in response.data
        assert b"Medium" in response.data
        assert b"Closed" in response.data
        assert b"Unassigned" in response.data  # Unassigned ticket


# Test for checking visibility of the create ticket button
def test_create_ticket_button_visibility(test_client, app, existing_user):
    with app.app_context():
        # Re-attach the user to the session
        existing_user = db.session.merge(existing_user)

        # Ensure the user has the 'admin' role so they can view all tickets
        existing_user.role = "admin"
        db.session.commit()  # Commit the role change

        # Log in as the existing user
        login_user(test_client, existing_user.email, "ValidPassword1!")

        # Access the all tickets page
        response = test_client.get(url_for("main.all_tickets"))
        assert response.status_code == 200

        # Check that the "Create Ticket" button is visible
        assert b"Create Ticket" in response.data


# Test for admin's ability to see the delete button
def test_admin_delete_button_visibility(test_client, app, admin_user):
    with app.app_context():

        # Re-attach the user to the session
        admin_user = db.session.merge(admin_user)

        # Create a test ticket
        ticket = Ticket(
            title="Admin's Ticket",
            description="This is a description for Admin's Ticket",
            priority="High",
            status="Open",
            assignee=admin_user,  # Assign to existing user
        )
        db.session.add(ticket)
        db.session.commit()

        # Log in as the admin user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Access the all tickets page
        response = test_client.get(url_for("main.all_tickets"))
        assert response.status_code == 200

        # Check that the delete button is visible for admin
        assert b"Delete" in response.data


# Test that non-admin users cannot see the delete button
def test_non_admin_delete_button_visibility(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular_user to the session
        regular_user = db.session.merge(regular_user)

        # Create a test ticket
        ticket = Ticket(
            title="User's Ticket",
            description="This is a description for User's Ticket",
            priority="Low",
            status="Open",
            assignee=regular_user,  # Assign to regular user
        )
        db.session.add(ticket)
        db.session.commit()

    # Re-attach regular_user before login (in case the object became detached)
    with app.app_context():
        regular_user = db.session.merge(regular_user)

    # Log in as the regular user
    login_user(test_client, regular_user.email, "ValidPassword1!")

    # Access the all tickets page
    response = test_client.get(url_for("main.all_tickets"))
    assert response.status_code == 200

    # Check that the delete button is not visible for non-admin
    assert b"Delete" not in response.data


import pytest


@pytest.mark.parametrize("user_role", ["admin", "support", "regular"])
def test_closed_tickets_button_visible_for_all_roles(
    test_client, app, user_role, admin_user, support_user, regular_user
):
    with app.app_context():
        # Re-attach the user to the session based on their role
        if user_role == "admin":
            admin_user = db.session.merge(admin_user)
            login_user(test_client, admin_user.email, "ValidPassword1!")
        elif user_role == "support":
            support_user = db.session.merge(support_user)
            login_user(test_client, support_user.email, "ValidPassword1!")
        elif user_role == "regular":
            regular_user = db.session.merge(regular_user)
            login_user(test_client, regular_user.email, "ValidPassword1!")

        # Access the all tickets page
        response = test_client.get(url_for("main.all_tickets"))

        # Verify the response is successful
        assert response.status_code == 200

        # Check that the "Closed Tickets" button is visible for all roles
        assert b"Closed Tickets" in response.data
