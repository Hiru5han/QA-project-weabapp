import os
from bs4 import BeautifulSoup
import pytest
from flask import url_for
from werkzeug.datastructures import FileStorage

import app
from app.models import Ticket, User, db
from app.routes import allowed_file, is_safe_url


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


# Fixture to create an existing ticket for tests
@pytest.fixture
def existing_ticket(app, admin_user):
    with app.app_context():
        # Create a test ticket and assign it to the admin user
        ticket = Ticket(
            title="Test Ticket",
            description="This is a test ticket.",
            priority="High",
            status="Open",
            assignee=admin_user,  # Assign to admin user
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket


# Fixtures to create test users for different roles
@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(name="Admin User", email="admin@example.com", role="admin")
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def existing_user(app):
    with app.app_context():
        user = User(name="Existing User", email="existing@example.com", role="existing")
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def support_user(app):
    with app.app_context():
        user = User(name="Support User", email="support@example.com", role="support")
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def regular_user(app):
    with app.app_context():
        user = User(name="Regular User", email="regular@example.com", role="regular")
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


# Test allowed_file
def test_allowed_file():
    assert allowed_file("image.png") is True
    assert allowed_file("document.pdf") is False
    assert allowed_file("profile.jpg") is True
    assert allowed_file("script.js") is False


# Test is_safe_url
def test_is_safe_url(app, test_client):
    with app.test_request_context():
        assert is_safe_url("/local/path") is True
        assert is_safe_url("http://malicious.com") is False


def test_index_anonymous_user(test_client):
    response = test_client.get("/")

    # Check that the response status code is 200 (OK)
    assert response.status_code == 200

    # Ensure that the content of the page includes the heading of your landing page
    assert b"Help Desk Ticketing System" in response.data
    assert b"Login or register to get started." in response.data


# Test login page rendering
def test_login_page(test_client):
    response = test_client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


# Test invalid login credentials
def test_login_invalid_credentials(test_client):
    response = login_user(test_client, "wrong@example.com", "WrongPassword!")
    assert response.status_code == 200  # Remains on login page
    assert b"No user found with that email" in response.data


# Test register page rendering
def test_register_page(test_client):
    response = test_client.get("/register")
    assert response.status_code == 200


# Test successful user registration
def test_register_user(test_client):
    # Get CSRF token
    response = test_client.get("/register")
    csrf_token = get_csrf_token(response.data)

    # Submit form with CSRF token
    data = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "Password123!",
        "role": "regular",
        "csrf_token": csrf_token,
    }
    response = test_client.post("/register", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_create_ticket_page(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Access the create ticket page after logging in
        response = test_client.get("/create_ticket")

        # Ensure the page loads successfully
        assert response.status_code == 200
        assert b"Create Ticket" in response.data  # Optional: Check for specific content


def test_create_ticket_success(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in as the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the create ticket page
        response = test_client.get("/create_ticket")
        csrf_token = get_csrf_token(response.data)

        # Prepare the valid ticket data with the CSRF token
        data = {
            "title": "Sample Ticket",
            "description": "Sample ticket description",
            "priority": "medium",
            "csrf_token": csrf_token,  # Include the CSRF token in the data
        }

        # Submit the ticket creation form
        response = test_client.post("/create_ticket", data=data, follow_redirects=True)

        # Ensure the ticket is created successfully
        assert response.status_code == 200
        assert b"Ticket created successfully" in response.data


def test_create_ticket_invalid_title(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in as the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the create ticket page
        response = test_client.get("/create_ticket")
        csrf_token = get_csrf_token(response.data)

        # Prepare the invalid title data with the CSRF token
        data = {
            "title": "123",  # Invalid title (numeric only)
            "description": "Valid description",
            "priority": "low",
            "csrf_token": csrf_token,
        }

        # Submit the ticket creation form with the invalid title
        response = test_client.post("/create_ticket", data=data, follow_redirects=True)

        # Ensure the validation error message is displayed
        assert b"Title must contain non-numeric characters" in response.data


def test_ticket_details_page(test_client, app, regular_user, existing_ticket):
    with app.app_context():
        # Re-attach the regular user and the existing ticket to the session
        regular_user = db.session.merge(regular_user)
        existing_ticket = db.session.merge(existing_ticket)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Perform the GET request for the ticket details page
        response = test_client.get(f"/ticket/{existing_ticket.id}")

        # Ensure the page is loaded successfully
        assert response.status_code == 200
        assert (
            b"Ticket Details" in response.data
        )  # Optional: Check for specific content


def test_ticket_details_add_comment(test_client, app, regular_user, existing_ticket):
    with app.app_context():
        # Re-attach the regular user and the ticket to the session
        regular_user = db.session.merge(regular_user)
        existing_ticket = db.session.merge(existing_ticket)

        # Log in as the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the ticket details page
        response = test_client.get(f"/ticket/{existing_ticket.id}")
        csrf_token = get_csrf_token(response.data)

        # Prepare the comment data with the CSRF token
        data = {"comment_text": "New comment", "csrf_token": csrf_token}

        # Post the comment to the ticket details page
        response = test_client.post(
            f"/ticket/{existing_ticket.id}", data=data, follow_redirects=True
        )

        # Ensure the comment was added successfully
        assert b"New comment" in response.data
        assert response.status_code == 200


def test_logout(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Now attempt to log out
        response = test_client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Help Desk Ticketing System" in response.data
        assert b"Login or register to get started." in response.data


# Test access to unassigned tickets by admin
def test_unassigned_tickets_admin(test_client, admin_user):
    login_user(test_client, admin_user.email, "ValidPassword1!")
    response = test_client.get("/unassigned_tickets")
    assert response.status_code == 200


def test_update_profile_page(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Get the CSRF token and log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Now try to access the update profile page
        response = test_client.get("/update_profile")
        assert response.status_code == 200


def test_update_profile_name(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the profile update page
        response = test_client.get("/update_profile")
        csrf_token = get_csrf_token(response.data)

        # Submit the form to update the profile name and email
        data = {
            "name": "New Name",
            "email": regular_user.email,
            "csrf_token": csrf_token,
        }
        response = test_client.post("/update_profile", data=data, follow_redirects=True)

        # Assert that the profile name was updated successfully
        assert b"Your profile has been updated" in response.data
        assert response.status_code == 200


def test_update_profile_image(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular_user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Prepare the image file for upload
        file = FileStorage(
            stream=open("test/test_files/profile.jpg", "rb"),
            filename="profile.jpg",
            content_type="image/jpeg",
        )

        # Get the CSRF token from the profile update page
        response = test_client.get("/update_profile")
        csrf_token = get_csrf_token(response.data)

        # Prepare the data for the profile update with the CSRF token
        data = {
            "name": "New Name",
            "email": regular_user.email,
            "profile_image": file,
            "csrf_token": csrf_token,  # Include CSRF token
        }

        # Post the form data to update the profile
        response = test_client.post(
            "/update_profile",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        # Ensure the profile image is updated successfully
        assert b"Profile image updated successfully" in response.data


def test_regular_user_cannot_delete_ticket(
    test_client, app, regular_user, existing_ticket
):
    with app.app_context():
        # Re-attach the regular user and the ticket to the session
        regular_user = db.session.merge(regular_user)
        existing_ticket = db.session.merge(existing_ticket)

        # Log in as the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the create_ticket page (or another page with CSRF token)
        response = test_client.get(url_for("main.create_ticket"))
        csrf_token = get_csrf_token(response.data)

        # Try to delete the ticket with the CSRF token included
        response = test_client.post(
            f"/delete_ticket/{existing_ticket.id}",
            data={"csrf_token": csrf_token},  # Include CSRF token in POST data
            follow_redirects=True,
        )

        # Ensure the regular user cannot delete the ticket (expected failure message or behavior)
        assert b"You do not have permission to delete this ticket" in response.data
        assert response.status_code == 200


def test_support_user_cannot_delete_ticket(
    test_client, app, support_user, existing_ticket
):
    with app.app_context():
        # Re-attach the support user and the ticket to the session
        support_user = db.session.merge(support_user)
        existing_ticket = db.session.merge(existing_ticket)

        # Log in as the support user
        login_user(test_client, support_user.email, "ValidPassword1!")

        # Get the CSRF token from the create_ticket page (or another page that includes a CSRF token)
        response = test_client.get(url_for("main.create_ticket"))
        csrf_token = get_csrf_token(response.data)

        # Try to delete the ticket with the CSRF token included
        response = test_client.post(
            f"/delete_ticket/{existing_ticket.id}",
            data={"csrf_token": csrf_token},  # Include CSRF token in POST data
            follow_redirects=True,
        )

        # Ensure the support user cannot delete the ticket (expected failure message or behavior)
        assert b"You do not have permission to delete this ticket" in response.data
        assert response.status_code == 200


def test_admin_user_can_delete_ticket(test_client, app, admin_user, existing_ticket):
    with app.app_context():
        # Re-attach the admin user and the ticket to the session
        admin_user = db.session.merge(admin_user)
        existing_ticket = db.session.merge(existing_ticket)

        # Log in as the admin user
        login_user(test_client, admin_user.email, "ValidPassword1!")

        # Ensure the ticket exists before attempting to delete it
        response = test_client.get(url_for("main.all_tickets"))
        assert response.status_code == 200
        assert b"Test Ticket" in response.data

        # Get the CSRF token from the all_tickets page (or another page that includes a CSRF token)
        csrf_token = get_csrf_token(response.data)

        # Attempt to delete the ticket with the CSRF token included
        response = test_client.post(
            f"/delete_ticket/{existing_ticket.id}",
            data={"csrf_token": csrf_token},  # Include CSRF token in POST data
            follow_redirects=True,
        )

        # Ensure the ticket is deleted successfully
        assert b"Ticket has been deleted successfully" in response.data
        assert response.status_code == 200


def test_regular_user_assigned_tickets(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Try to access the assigned tickets page
        response = test_client.get("/assigned_tickets")

        # Since regular users may not have access, expect a 302 redirect
        assert response.status_code == 302  # Check if they are redirected

        # Check if they are redirected to /all_tickets
        assert "/all_tickets" in response.headers["Location"]


def test_login_valid_credentials(test_client, app, existing_user):
    with app.app_context():
        # Re-attach the user to the session
        existing_user = db.session.merge(existing_user)

        # Get the CSRF token from the login page
        response = test_client.get("/login")
        csrf_token = get_csrf_token(response.data)

        # Log in the user with the CSRF token
        login_data = {
            "email": existing_user.email,
            "password": "ValidPassword1!",
            "csrf_token": csrf_token,
        }

        # Submit the login form
        response = test_client.post("/login", data=login_data, follow_redirects=False)

        # Assert that the login is successful and it redirects (status code 302)
        assert response.status_code == 302  # Successful login redirects


def test_register_existing_user(test_client, app, existing_user):
    with app.app_context():
        # Re-attach the user to the session
        existing_user = db.session.merge(existing_user)

        # Get the CSRF token from the registration page
        response = test_client.get("/register")
        csrf_token = get_csrf_token(response.data)

        # Include the CSRF token in the registration form
        data = {
            "name": "New User",
            "email": existing_user.email,
            "password": "Password123!",
            "role": "regular",
            "csrf_token": csrf_token,  # Include the CSRF token
        }

        # Submit the registration form
        response = test_client.post("/register", data=data, follow_redirects=True)

        # Assert that the "Email address already in use" message is displayed
        assert b"Email address already in use" in response.data


def test_unassigned_tickets_admin(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin user to the session
        admin_user = db.session.merge(admin_user)

        login_user(test_client, admin_user.email, "ValidPassword1!")
        response = test_client.get("/unassigned_tickets")
        assert response.status_code == 200


def test_unassigned_tickets_no_access(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        login_user(test_client, regular_user.email, "ValidPassword1!")
        response = test_client.get("/unassigned_tickets", follow_redirects=True)
        assert b"Only support staff and admins can view this page" in response.data
        assert response.status_code == 200


def test_regular_user_create_ticket(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        login_user(test_client, regular_user.email, "ValidPassword1!")
        response = test_client.get("/create_ticket")
        assert response.status_code == 200


def test_support_user_create_ticket(test_client, app, support_user):
    with app.app_context():
        # Re-attach the support user to the session
        support_user = db.session.merge(support_user)

        login_user(test_client, support_user.email, "ValidPassword1!")
        response = test_client.get("/create_ticket")
        assert response.status_code == 200


def test_admin_user_create_ticket(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin user to the session
        admin_user = db.session.merge(admin_user)

        login_user(test_client, admin_user.email, "ValidPassword1!")
        response = test_client.get("/create_ticket")
        assert response.status_code == 200


def test_support_user_assigned_tickets(test_client, app, support_user):
    with app.app_context():
        # Re-attach the support user to the session
        support_user = db.session.merge(support_user)

        login_user(test_client, support_user.email, "ValidPassword1!")
        response = test_client.get("/assigned_tickets")
        assert response.status_code == 200
        assert b"Assigned Tickets" in response.data


def test_admin_user_assigned_tickets(test_client, app, admin_user):
    with app.app_context():
        # Re-attach the admin user to the session
        admin_user = db.session.merge(admin_user)

        login_user(test_client, admin_user.email, "ValidPassword1!")
        response = test_client.get("/assigned_tickets")
        assert response.status_code == 200
        assert b"Assigned Tickets" in response.data


# ------------------------------


def test_allowed_file_invalid_extension():
    assert allowed_file("invalid.txt") is False
    assert allowed_file("no_extension") is False
    assert allowed_file("") is False


def test_allowed_file_valid_extension():
    assert allowed_file("valid.png") is True
    assert allowed_file("valid.jpg") is True
    assert allowed_file("valid.gif") is True


def test_is_safe_url_invalid(app):
    with app.test_request_context():
        assert is_safe_url("http://evil.com") is False


def test_is_safe_url_valid(app):
    with app.test_request_context():
        assert is_safe_url("/valid/local") is True


def test_login_non_existent_user(test_client):
    response = login_user(test_client, "fakeuser@example.com", "fakepassword")
    assert b"No user found with that email" in response.data
    assert response.status_code == 200


def test_login_wrong_password(test_client, app, existing_user):
    with app.app_context():
        # Re-attach the existing user to the session
        existing_user = db.session.merge(existing_user)

        # Attempt login with incorrect password
        response = login_user(test_client, existing_user.email, "WrongPassword123")
        assert b"Password mismatch" in response.data
        assert response.status_code == 200


def test_register_invalid_name(test_client, app):
    # Get the CSRF token from the registration page
    response = test_client.get("/register")
    csrf_token = get_csrf_token(response.data)

    # Submit the form with an invalid name (containing numbers)
    response = test_client.post(
        "/register",
        data={
            "name": "12345",  # Invalid name
            "email": "valid@example.com",
            "password": "ValidPass123!",
            "role": "regular",
            "csrf_token": csrf_token,  # Add CSRF token
        },
        follow_redirects=True,
    )

    assert b"Name cannot contain numbers" in response.data
    assert response.status_code == 200


def test_register_invalid_email(test_client):
    # Get the CSRF token from the registration page
    response = test_client.get("/register")
    csrf_token = get_csrf_token(response.data)

    # Submit the form with an invalid email format
    response = test_client.post(
        "/register",
        data={
            "name": "ValidName",
            "email": "invalid-email",  # Invalid email format
            "password": "ValidPass123!",
            "role": "regular",
            "csrf_token": csrf_token,  # Ensure CSRF token is included
        },
        follow_redirects=True,
    )

    # Check that the correct error message is shown
    assert b"Invalid email address" in response.data
    assert response.status_code == 200


def test_register_duplicate_email(test_client, app, existing_user):
    with app.app_context():
        # Re-attach the existing user to the session
        existing_user = db.session.merge(existing_user)

        # Get the CSRF token from the registration page
        response = test_client.get("/register")
        csrf_token = get_csrf_token(response.data)

        # Submit the form with the existing user's email (to trigger duplicate email error)
        response = test_client.post(
            "/register",
            data={
                "name": "New User",
                "email": existing_user.email,  # Duplicate email
                "password": "ValidPass123!",
                "role": "regular",
                "csrf_token": csrf_token,  # Ensure CSRF token is included
            },
            follow_redirects=True,
        )

        # Check for the duplicate email error message
        assert b"Email address already in use" in response.data
        assert response.status_code == 200


def test_create_ticket_invalid_title(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the create_ticket page
        response = test_client.get("/create_ticket")
        csrf_token = get_csrf_token(response.data)

        # Submit the form with an invalid title
        response = test_client.post(
            "/create_ticket",
            data={
                "title": "1234",  # Invalid title
                "description": "Valid description",
                "priority": "medium",
                "csrf_token": csrf_token,  # Add CSRF token
            },
            follow_redirects=True,
        )

        assert b"Title must contain non-numeric characters" in response.data
        assert response.status_code == 200


def test_create_ticket_invalid_priority(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the create_ticket page
        response = test_client.get("/create_ticket")
        csrf_token = get_csrf_token(response.data)

        # Submit the form with an invalid priority
        response = test_client.post(
            "/create_ticket",
            data={
                "title": "Valid Title",
                "description": "Valid description",
                "priority": "invalid_priority",  # Invalid priority
                "csrf_token": csrf_token,  # Add CSRF token
            },
            follow_redirects=True,
        )

        assert b"Invalid priority value" in response.data
        assert response.status_code == 200


def test_update_profile_invalid_name(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the update profile page
        response = test_client.get("/update_profile")
        csrf_token = get_csrf_token(response.data)

        # Submit the form with an invalid name
        response = test_client.post(
            "/update_profile",
            data={
                "name": "12345",  # Invalid name
                "email": regular_user.email,
                "csrf_token": csrf_token,
            },
            follow_redirects=True,
        )

        assert b"Name cannot contain numbers" in response.data
        assert response.status_code == 200


def test_update_profile_password_mismatch(test_client, app, regular_user):
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Get the CSRF token from the update profile page
        response = test_client.get("/update_profile")
        csrf_token = get_csrf_token(response.data)

        # Submit the form with mismatched passwords
        response = test_client.post(
            "/update_profile",
            data={
                "name": "Valid Name",
                "email": regular_user.email,
                "password": "NewPassword123",
                "password_confirm": "MismatchPassword123",  # Mismatched passwords
                "csrf_token": csrf_token,
            },
            follow_redirects=True,
        )

        assert b"Passwords do not match" in response.data
        assert response.status_code == 200


def test_login_authenticated_user_redirects_based_on_role(
    test_client, app, regular_user
):
    """
    Test that an authenticated user is redirected based on their role when accessing the login page.
    """
    with app.app_context():
        # Re-attach the regular user to the session
        regular_user = db.session.merge(regular_user)

        # Log in the regular user
        login_user(test_client, regular_user.email, "ValidPassword1!")

        # Simulate accessing the login page as an authenticated user
        response = test_client.get("/login", follow_redirects=False)

        # Check that the response is a redirect to the role-based page (in this case, '/all_tickets')
        assert response.status_code == 302  # 302 is a redirect
        assert (
            "/all_tickets" in response.headers["Location"]
        )  # Ensure redirection to the regular user's page
