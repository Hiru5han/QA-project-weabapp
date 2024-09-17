import pytest
from flask import url_for
from app.models import Ticket, User, db
from bs4 import BeautifulSoup


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


# Test for verifying the "Assigned Tickets" page renders correctly for different roles
@pytest.mark.parametrize("user_role", ["admin", "support"])
def test_assigned_tickets_page_renders_correctly_for_admin_and_support(
    test_client, app, user_role, admin_user, support_user
):
    with app.app_context():
        # Re-attach the user to the session based on their role
        if user_role == "admin":
            user = db.session.merge(admin_user)
            login_user(test_client, user.email, "ValidPassword1!")
        elif user_role == "support":
            user = db.session.merge(support_user)
            login_user(test_client, user.email, "ValidPassword1!")

        # Access the "Assigned Tickets" page
        response = test_client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200

        # Verify that the page header is displayed correctly
        assert b"Assigned Tickets" in response.data
        assert f"Welcome, {user.name}!".encode() in response.data


# Test for checking visibility of the "Assigned" toggle button for all roles
@pytest.mark.parametrize("user_role", ["admin", "support"])
def test_assigned_toggle_button_visible_for_admin_support(
    test_client, app, user_role, admin_user, support_user
):
    with app.app_context():
        # Re-attach the user to the session based on their role
        if user_role == "admin":
            user = db.session.merge(admin_user)
            login_user(test_client, user.email, "ValidPassword1!")
        elif user_role == "support":
            user = db.session.merge(support_user)
            login_user(test_client, user.email, "ValidPassword1!")

        # Access the "Assigned Tickets" page
        response = test_client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200

        # Check that the "Assigned" button is visible and active
        assert b"Assigned" in response.data
        assert b"btn-toggle active" in response.data


# Test for ensuring "All Tickets" button is visible only for admin users
def test_all_tickets_button_visible_for_admin(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin user to the session
        admin_user = db.session.merge(admin_user)
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Access the "Assigned Tickets" page
        response = test_client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200

        # Check that the "All Tickets" button is visible for admin
        assert b"All Tickets" in response.data


# Test for admin's ability to see the delete button
def test_admin_delete_button_visibility_for_assigned_ticket(
    test_client, app, admin_user
):
    with app.app_context():
        # Re-attach the admin user to the session
        admin_user = db.session.merge(admin_user)

        # Create a test ticket
        ticket = Ticket(
            title="Admin's Assigned Ticket",
            description="This is a description for Admin's Assigned Ticket",
            priority="High",
            status="Open",
            assignee=admin_user,  # Assign to admin user
        )
        db.session.add(ticket)
        db.session.commit()

        # Log in as the admin user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Access the "Assigned Tickets" page
        response = test_client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200

        # Check that the delete button is visible for admin
        assert b"Delete" in response.data


@pytest.mark.parametrize("user_role", ["admin", "support", "regular"])
def test_closed_tickets_button_visible_for_all_roles(
    test_client, app, user_role, admin_user, support_user, regular_user
):
    with app.app_context():
        # Log in as a user based on their role
        if user_role == "admin":
            user = db.session.merge(admin_user)
        elif user_role == "support":
            user = db.session.merge(support_user)
        else:
            user = db.session.merge(regular_user)

        # Log in the user
        login_response = login_user(test_client, user.email, "ValidPassword1!")

        # Check if the login was successful (HTTP status 200)
        assert (
            login_response.status_code == 200
        ), f"Login failed with status code {login_response.status_code}"

        # Access the "Assigned Tickets" page
        response = test_client.get(
            url_for("main.assigned_tickets"), follow_redirects=False
        )

        if user_role == "regular":
            # Expect a 302 redirect for regular users
            assert response.status_code == 302
            assert response.headers.get("Location") == url_for("main.all_tickets")

            # Follow the redirect to the "All Tickets" page
            response = test_client.get(
                url_for("main.all_tickets"), follow_redirects=True
            )

            # Check that the button reads "Active" for regular users
            assert response.status_code == 200
            assert b"btn-toggle active" in response.data
            assert b"Active" in response.data
        else:
            # For admin and support, ensure the response is 200 and the "Closed" button is visible
            assert response.status_code == 200
            assert b"Closed" in response.data


@pytest.mark.parametrize("user_role", ["admin", "support", "regular"])
def test_closed_button_active_for_closed_view(
    test_client, app, user_role, admin_user, support_user, regular_user
):
    with app.app_context():
        # Log in as a user based on their role
        if user_role == "admin":
            user = db.session.merge(admin_user)
        elif user_role == "support":
            user = db.session.merge(support_user)
        else:
            user = db.session.merge(regular_user)

        # Log in the user
        login_response = login_user(test_client, user.email, "ValidPassword1!")

        # Check if the login was successful (HTTP status 200)
        assert (
            login_response.status_code == 200
        ), f"Login failed with status code {login_response.status_code}"

        # Access the "Closed Tickets" page (view = closed)
        response = test_client.get(
            url_for("main.closed_tickets"), follow_redirects=True
        )

        # Ensure the response is 200 and the "Closed" button is active
        assert response.status_code == 200
        assert b"Closed" in response.data
        assert (
            b"btn-toggle active" in response.data
        )  # The active class for the "Closed" button
