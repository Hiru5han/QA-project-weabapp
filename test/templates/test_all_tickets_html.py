import pytest
from flask import url_for
from app.models import Ticket, User, db
from werkzeug.security import generate_password_hash

@pytest.fixture
def existing_user(app):
    """
    Create an existing user in the database for testing.
    This fixture creates a user with a predefined name, email, and password,
    and adds the user to the database.
    Args:
        app (Flask): The Flask application instance.
    Returns:
        User: The created user object.
    """
    with app.app_context():
        user = User(
            name="Existing User",
            email="existing@example.com",
            password=generate_password_hash("ValidPassword1!", method="pbkdf2:sha256"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()

        # Return the user object, which is now attached to a session
        return User.query.get(user.id)

@pytest.fixture
def regular_user(app):
    with app.app_context():
        # Create a regular user
        user = User(
            name="Regular User",
            email="regular@example.com",
            role="regular",
            password="ValidPassword1!"  # You might need to hash this according to your app's auth system
        )
        db.session.add(user)
        db.session.commit()
        return user

def test_all_tickets_page_renders_correctly(client, existing_user):
    # Log in as the existing user
    client.post('/login', data={
        'email': existing_user.email,
        'password': 'ValidPassword1!'
    })

    # Access the all tickets page
    response = client.get(url_for('main.all_tickets'))
    assert response.status_code == 200

    # Check that the correct template is used
    assert b"All Tickets" in response.data
    assert b"Your Tickets" in response.data

def test_ticket_table_content(client, app, existing_user):
    with app.app_context():
        # Explicitly re-attach the user to the session
        user = db.session.merge(existing_user)
        
        # Create some test tickets with a non-null description
        ticket1 = Ticket(
            title="Test Ticket 1",
            description="This is a description for Test Ticket 1",
            priority="High",
            status="Open",
            assignee=user  # Use the re-attached user
        )
        ticket2 = Ticket(
            title="Test Ticket 2",
            description="This is a description for Test Ticket 2",
            priority="Medium",
            status="Closed",
            assignee=None  # Unassigned ticket
        )
        db.session.add_all([ticket1, ticket2])
        db.session.commit()

    # Log in as the existing user
    client.post('/login', data={
        'email': existing_user.email,
        'password': 'ValidPassword1!'
    })

    # Access the all tickets page
    response = client.get(url_for('main.all_tickets'))
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

def test_admin_toggle_buttons_visibility(client, app, existing_user):
    # Ensure the existing user is an admin
    with app.app_context():
        existing_user.role = "admin"
        db.session.commit()

    # Log in as the admin user
    client.post('/login', data={
        'email': existing_user.email,
        'password': 'ValidPassword1!'
    })

    # Access the all tickets page
    response = client.get(url_for('main.all_tickets'))
    assert response.status_code == 200

    # Check that the toggle buttons are visible
    assert b'btn-toggle' in response.data
    assert b'Unassigned' in response.data
    assert b'Assigned' in response.data
    assert b'All Tickets' in response.data

def test_create_ticket_button_visibility(client, app, existing_user):
    # Log in as the existing user
    client.post('/login', data={
        'email': existing_user.email,
        'password': 'ValidPassword1!'
    })

    # Access the all tickets page
    response = client.get(url_for('main.all_tickets'))
    assert response.status_code == 200

    # Check that the "Create Ticket" button is visible
    assert b"Create Ticket" in response.data

def test_admin_delete_button_visibility(client, app, existing_user):
    with app.app_context():
        # Ensure the existing user is an admin
        existing_user.role = "admin"
        db.session.commit()

        # Re-attach the user to the session
        user = db.session.merge(existing_user)

        # Create a test ticket with a non-null description
        ticket = Ticket(
            title="Admin's Ticket",
            description="This is a description for Admin's Ticket",
            priority="High",
            status="Open",
            assignee=user  # Use the re-attached user
        )
        db.session.add(ticket)
        db.session.commit()

    # Log in as the admin user
    client.post('/login', data={
        'email': existing_user.email,
        'password': 'ValidPassword1!'
    })

    # Access the all tickets page
    response = client.get(url_for('main.all_tickets'))
    assert response.status_code == 200

    # Check that the delete button is visible for admin
    assert b"Delete" in response.data

def test_non_admin_delete_button_visibility(client, app, existing_user):
    with app.app_context():
        # Ensure the existing user is not an admin
        existing_user.role = "user"
        db.session.commit()

        # Re-attach the user to the session
        user = db.session.merge(existing_user)

        # Create a test ticket with a non-null description
        ticket = Ticket(
            title="User's Ticket",
            description="This is a description for User's Ticket",
            priority="Low",
            status="Open",
            assignee=user  # Use the re-attached user
        )
        db.session.add(ticket)
        db.session.commit()

    # Log in as the non-admin user
    client.post('/login', data={
        'email': existing_user.email,
        'password': 'ValidPassword1!'
    })

    # Access the all tickets page
    response = client.get(url_for('main.all_tickets'))
    assert response.status_code == 200

    # Check that the delete button is not visible for non-admin
    assert b"Delete" not in response.data

def test_regular_user_toggle_buttons_visibility(client, app, regular_user):
    with app.app_context():
        # Set the user's role to 'regular' and commit the change
        regular_user.role = "regular"
        db.session.commit()

        # Re-bind the user to the session to avoid DetachedInstanceError
        db.session.add(regular_user)

        # Alternatively, re-query the user from the session directly
        refreshed_user = db.session.query(User).get(regular_user.id)
        
        assert refreshed_user.role == "regular", \
            f"Expected role to be 'regular', but got '{refreshed_user.role}'"

        # Log out any existing session to ensure a fresh login as a regular user
        client.get('/logout')

        # Log in as the regular user and follow the redirect
        response = client.post('/login', data={
            'email': refreshed_user.email,
            'password': 'ValidPassword1!'
        }, follow_redirects=True)
        assert response.status_code == 200

        # Access the all_tickets page as a regular user
        response = client.get(url_for('main.all_tickets'))
        assert response.status_code == 200

        # Ensure that the response does not contain the 'btn-toggle' class, which is only for admins
        assert b'btn-toggle' not in response.data, \
            "The 'btn-toggle' buttons should not be visible to regular users."

        # Optionally, verify that content appropriate for regular users is present
        assert b'All Tickets' in response.data, \
            "The All Tickets page content should be visible to regular users."
