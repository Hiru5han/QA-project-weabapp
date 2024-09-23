from datetime import datetime, timedelta

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
            status="closed",
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

        # Open tickets
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

        # Yield the users for use in tests
        yield {
            "admin_user": admin_user,
            "support_user": support_user,
            "regular_user": regular_user,
        }

    # Cleanup: Drop tables from the in-memory database
    with app.app_context():
        db.drop_all()


def test_create_ticket_view_get_regular_user(client, setup_test_data):
    """Test that regular users can access the create ticket form with limited options."""
    # Log in as the regular user
    login_regular_user(client)

    # Make a GET request to the '/create_ticket' route
    response = client.get("/create_ticket")

    # Check that the response status code is 200
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"

    # Parse the response data
    soup = BeautifulSoup(response.data, "html.parser")

    # Verify that the form is present
    form = soup.find("form")
    assert form is not None, "Create Ticket form not found"

    # Verify that regular users cannot assign tickets to others
    assigned_to = soup.find("select", {"name": "assigned_to"})
    assert assigned_to is None, "Regular user should not see Assigned To select field"


def test_create_ticket_view_get_unauthenticated(client):
    """Test that unauthenticated users are redirected to the login page when accessing create_ticket."""
    # Make a GET request to the '/create_ticket' route without logging in
    response = client.get("/create_ticket", follow_redirects=True)

    # Check that the response status code is 200 (after redirect)
    assert (
        response.status_code == 200
    ), f"Expected status code 200 after redirect, got {response.status_code}"

    # Verify that the user is on the login page
    assert (
        "Login" in response.data.decode()
    ), "Did not redirect to login page for unauthenticated user"


def test_create_ticket_post_admin_success(client, setup_test_data):
    """Test that admin users can successfully create a ticket with valid data."""
    # Log in as the admin user
    login_admin_user(client)

    # Prepare valid form data
    form_data = {
        "title": "Admin Created Ticket",
        "description": "This is a valid description for an admin ticket.",
        "priority": "high",
        "status": "closed",
        "user_id": "1",  # Assuming admin has ID 1
        "assigned_to": "2",  # Assign to support user with ID 2
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check that the response status code is 200
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"

    # Verify that the ticket was created in the database
    with client.application.app_context():
        ticket = Ticket.query.filter_by(title="Admin Created Ticket").first()
        assert ticket is not None, "Admin Created Ticket was not found in the database"
        assert (
            ticket.description == "This is a valid description for an admin ticket."
        ), "Ticket description mismatch"
        assert ticket.priority == "high", "Ticket priority mismatch"
        assert ticket.status == "closed", "Ticket status mismatch"
        assert ticket.assigned_to == 2, "Ticket assigned_to mismatch"

    # Verify that a success flash message is present
    assert (
        "Ticket created successfully!" in response.data.decode()
    ), "Success flash message not found"


def test_create_ticket_post_regular_user_success(client, setup_test_data):
    """Test that regular users can successfully create a ticket with valid data."""
    # Log in as the regular user
    login_regular_user(client)

    # Prepare valid form data
    form_data = {
        "title": "Regular Created Ticket",
        "description": "This is a valid description for a regular user ticket.",
        "priority": "low",
        # Regular users do not set status; it should default to 'open'
        "user_id": "3",  # Assuming regular user has ID 3
        # Regular users cannot assign tickets; 'assigned_to' should be ignored
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check that the response status code is 200
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"

    # Verify that the ticket was created in the database
    with client.application.app_context():
        ticket = Ticket.query.filter_by(title="Regular Created Ticket").first()
        assert (
            ticket is not None
        ), "Regular Created Ticket was not found in the database"
        assert (
            ticket.description
            == "This is a valid description for a regular user ticket."
        ), "Ticket description mismatch"
        assert ticket.priority == "low", "Ticket priority mismatch"
        assert ticket.status == "open", "Ticket status should default to 'open'"
        assert ticket.assigned_to is None, "Regular user should not assign tickets"

    # Verify that a success flash message is present
    assert (
        "Ticket created successfully!" in response.data.decode()
    ), "Success flash message not found"


def test_create_ticket_post_missing_title(client, setup_test_data):
    """Test that submitting a ticket without a title fails validation."""
    # Log in as the regular user
    login_regular_user(client)

    # Prepare form data with missing title
    form_data = {
        "description": "Description without a title.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check that the response contains a warning flash message
    assert (
        "Title must contain non-numeric characters, be at least 5 characters long, and not exceed 100 characters."
        in response.data.decode()
    ), "Validation warning for missing title not found"

    # Verify that the form is re-rendered with existing form data
    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form")
    assert form is not None, "Create Ticket form not found after validation failure"

    # Ensure that the previously entered description is retained
    description_input = form.find("textarea", {"name": "description"})
    assert description_input is not None, "Description field not found in the form"
    assert (
        description_input.text == "Description without a title."
    ), "Description not retained after validation failure"


def test_create_ticket_post_invalid_title(client, setup_test_data):
    """Test that submitting a ticket with an invalid title (only numbers) fails validation."""
    # Log in as the admin user
    login_admin_user(client)

    # Prepare form data with invalid title (only numbers)
    form_data = {
        "title": "12345",
        "description": "Valid description.",
        "priority": "high",
        "status": "closed",
        "user_id": "1",
        "assigned_to": "2",
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check for the appropriate validation warning
    assert (
        "Title must contain non-numeric characters, be at least 5 characters long, and not exceed 100 characters."
        in response.data.decode()
    ), "Validation warning for numeric title not found"

    # Verify that the form is re-rendered with existing form data
    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form")
    assert form is not None, "Create Ticket form not found after validation failure"

    # Ensure that the previously entered title is retained
    title_input = form.find("input", {"name": "title"})
    assert title_input is not None, "Title field not found in the form"
    assert (
        title_input.get("value") == "12345"
    ), "Title not retained after validation failure"


def test_create_ticket_post_title_length(client, setup_test_data):
    """Test that submitting a ticket with a title that's too short or too long fails validation."""
    # Log in as the regular user
    login_regular_user(client)

    # Test with title too short (less than 5 characters)
    form_data_short = {
        "title": "Abc",
        "description": "Valid description.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }

    response_short = client.post(
        "/create_ticket", data=form_data_short, follow_redirects=True
    )
    assert (
        "Title must contain non-numeric characters, be at least 5 characters long, and not exceed 100 characters."
        in response_short.data.decode()
    ), "Validation warning for short title not found"

    # Test with title too long (more than 100 characters)
    long_title = "A" * 101
    form_data_long = {
        "title": long_title,
        "description": "Valid description.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }

    response_long = client.post(
        "/create_ticket", data=form_data_long, follow_redirects=True
    )
    assert (
        "Title must contain non-numeric characters, be at least 5 characters long, and not exceed 100 characters."
        in response_long.data.decode()
    ), "Validation warning for long title not found"


def test_create_ticket_post_missing_description(client, setup_test_data):
    """Test that submitting a ticket without a description fails validation."""
    # Log in as the support user
    login_support_user(client)

    # Prepare form data with missing description
    form_data = {
        "title": "Valid Title",
        "priority": "medium",
        "status": "closed",
        "user_id": "2",
        "assigned_to": "2",
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check for the appropriate validation warning
    assert (
        "Description must contain non-numeric characters, be at least 10 characters long, and not exceed 1000 characters."
        in response.data.decode()
    ), "Validation warning for missing description not found"

    # Verify that the form is re-rendered with existing form data
    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form")
    assert form is not None, "Create Ticket form not found after validation failure"

    # Ensure that the previously entered title is retained
    title_input = form.find("input", {"name": "title"})
    assert title_input is not None, "Title field not found in the form"
    assert (
        title_input.get("value") == "Valid Title"
    ), "Title not retained after validation failure"


def test_create_ticket_post_invalid_description(client, setup_test_data):
    """Test that submitting a ticket with an invalid description (only numbers) fails validation."""
    # Log in as the support user
    login_support_user(client)

    # Prepare form data with invalid description (only numbers)
    form_data = {
        "title": "Valid Title",
        "description": "1234567890",
        "priority": "medium",
        "status": "closed",
        "user_id": "2",
        "assigned_to": "2",
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check for the appropriate validation warning
    assert (
        "Description must contain non-numeric characters, be at least 10 characters long, and not exceed 1000 characters."
        in response.data.decode()
    ), "Validation warning for numeric description not found"

    # Verify that the form is re-rendered with existing form data
    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form")
    assert form is not None, "Create Ticket form not found after validation failure"

    # Ensure that the previously entered description is retained
    description_input = form.find("textarea", {"name": "description"})
    assert description_input is not None, "Description field not found in the form"
    assert (
        description_input.text == "1234567890"
    ), "Description not retained after validation failure"


def test_create_ticket_post_description_length(client, setup_test_data):
    """Test that submitting a ticket with a description that's too short or too long fails validation."""
    # Log in as the admin user
    login_admin_user(client)

    # Test with description too short (less than 10 characters)
    form_data_short = {
        "title": "Valid Title",
        "description": "Short",
        "priority": "high",
        "status": "closed",
        "user_id": "1",
        "assigned_to": "2",
        "referrer": url_for("main.all_tickets"),
    }

    response_short = client.post(
        "/create_ticket", data=form_data_short, follow_redirects=True
    )
    assert (
        "Description must contain non-numeric characters, be at least 10 characters long, and not exceed 1000 characters."
        in response_short.data.decode()
    ), "Validation warning for short description not found"

    # Test with description too long (more than 1000 characters)
    long_description = "D" * 1001
    form_data_long = {
        "title": "Valid Title",
        "description": long_description,
        "priority": "high",
        "status": "closed",
        "user_id": "1",
        "assigned_to": "2",
        "referrer": url_for("main.all_tickets"),
    }

    response_long = client.post(
        "/create_ticket", data=form_data_long, follow_redirects=True
    )
    assert (
        "Description must contain non-numeric characters, be at least 10 characters long, and not exceed 1000 characters."
        in response_long.data.decode()
    ), "Validation warning for long description not found"


def test_create_ticket_post_invalid_assigned_to(client, setup_test_data, app):
    """Test that admin users cannot assign tickets to non-existent users."""
    admin_user = setup_test_data["admin_user"]

    # Log in as the admin user
    login_admin_user(client)

    # Prepare form data with invalid assigned_to (non-existent user ID)
    form_data = {
        "title": "Ticket with Invalid Assignment",
        "description": "Valid description.",
        "priority": "high",
        "status": "closed",
        "user_id": str(admin_user.id),
        "assigned_to": "999",  # Non-existent user ID
        "referrer": url_for("main.all_tickets"),
    }

    # Make a POST request to the '/create_ticket' route
    response = client.post("/create_ticket", data=form_data, follow_redirects=True)

    # Check for the appropriate validation warning
    assert (
        "Invalid user selected for assignment." in response.data.decode()
    ), "Validation warning for invalid assigned_to not found"

    # Verify that the form is re-rendered with existing form data
    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form")
    assert form is not None, "Create Ticket form not found after validation failure"

    # Ensure that the 'assigned_to' select field exists
    assigned_to_select = form.find("select", {"name": "assigned_to"})
    assert (
        assigned_to_select is not None
    ), "Assigned To select field not found in the form"

    # Since "999" is invalid, ensure that no option is selected or that a placeholder is selected
    selected_option = assigned_to_select.find("option", selected=True)
    if selected_option:
        # If a placeholder exists (e.g., value is empty), it should be selected
        placeholder_value = ""
        assert (
            selected_option.get("value") == placeholder_value
        ), "Placeholder option should be selected when invalid assigned_to is provided"
    else:
        # No option is selected, which is acceptable
        assert (
            selected_option is None
        ), "No option should be selected in Assigned To field when an invalid user is provided"


def test_create_ticket_post_duplicate_ticket(client, setup_test_data, app):
    """Test that creating a duplicate ticket within 1 minute fails."""
    # Log in as the regular user
    login_regular_user(client)

    # Step 1: Create the initial "Existing Ticket"
    initial_form_data = {
        "title": "Existing Ticket",
        "description": "Original ticket description.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }
    response_initial = client.post(
        "/create_ticket", data=initial_form_data, follow_redirects=True
    )

    # Assert that the initial ticket was created successfully
    assert (
        "Ticket created successfully!" in response_initial.data.decode()
    ), "Initial ticket creation failed"

    # Step 2: Attempt to create a duplicate ticket within 1 minute
    duplicate_form_data = {
        "title": "Existing Ticket",
        "description": "Another ticket with the same title.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }
    response_duplicate = client.post(
        "/create_ticket", data=duplicate_form_data, follow_redirects=True
    )

    # Step 3: Check for the appropriate validation warning
    assert (
        "A similar ticket was created within the last minute. Please wait before creating a new one."
        in response_duplicate.data.decode()
    ), "Validation warning for duplicate ticket not found"

    # Step 4: Verify that only one ticket exists with the title "Existing Ticket"
    with app.app_context():
        tickets = Ticket.query.filter_by(title="Existing Ticket", user_id=3).all()
        assert len(tickets) == 1, "Duplicate ticket was incorrectly created"


def test_create_ticket_post_success_duplicate_after_time(client, setup_test_data, app):
    """Test that creating a duplicate ticket after 1 minute succeeds."""
    # Log in as the regular user
    login_regular_user(client)

    # Step 1: Create the initial "Existing Ticket"
    initial_form_data = {
        "title": "Existing Ticket",
        "description": "Original ticket description.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }
    response_initial = client.post(
        "/create_ticket", data=initial_form_data, follow_redirects=True
    )

    # Assert that the initial ticket was created successfully
    assert (
        "Ticket created successfully!" in response_initial.data.decode()
    ), "Initial ticket creation failed"

    # Step 2: Modify the 'created_at' of the existing ticket to simulate passage of time
    with app.app_context():
        regular_user = User.query.filter_by(email="regular@example.com").first()
        existing_ticket = Ticket.query.filter_by(
            title="Existing Ticket", user_id=regular_user.id
        ).first()
        assert existing_ticket is not None, "Existing Ticket not found in the database"
        existing_ticket.created_at = datetime.utcnow() - timedelta(minutes=2)
        db.session.commit()

    # Step 3: Attempt to create a duplicate ticket after 2 minutes
    duplicate_form_data = {
        "title": "Existing Ticket",
        "description": "Creating a similar ticket after 2 minutes.",
        "priority": "low",
        "user_id": "3",
        "referrer": url_for("main.all_tickets"),
    }
    response_duplicate = client.post(
        "/create_ticket", data=duplicate_form_data, follow_redirects=True
    )

    # Step 4: Check that the ticket was created successfully
    assert (
        "Ticket created successfully!" in response_duplicate.data.decode()
    ), "Success flash message not found for duplicate after time"

    # Step 5: Verify that both tickets exist in the database
    with app.app_context():
        tickets = Ticket.query.filter_by(title="Existing Ticket", user_id=3).all()
        assert len(tickets) == 2, "Duplicate ticket was not created after 1 minute"
