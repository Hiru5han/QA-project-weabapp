import pytest
from flask import url_for
from app.models import User, Ticket, db

@pytest.fixture
def test_admin_user(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@example.com").first()
        if not user:
            user = User(name="Admin User", email="admin@example.com", password="password", role="admin")
            db.session.add(user)
            db.session.commit()
    return user

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        if not user:
            user = User(name="Regular User", email="user@example.com", password="password", role="user")
            db.session.add(user)
            db.session.commit()
    return user

@pytest.fixture
def create_tickets(app, test_user):
    with app.app_context():
        tickets = []
        for i in range(3):
            ticket = Ticket(
                title=f"Ticket {i}",
                description=f"Description for Ticket {i}",  # Provide a description
                priority="high",
                status="open",
                assignee=test_user if i % 2 == 0 else None
            )
            db.session.add(ticket)
            tickets.append(ticket)
        db.session.commit()
    return tickets

def test_dashboard_header_rendering(client, app, test_user):
    with client:
        with app.app_context():
            from flask_login import login_user
            test_user = db.session.merge(test_user)  # Ensure test_user is attached to the session
            login_user(test_user)

            # Access the correct view that should render the "All Tickets" header
            response = client.get(url_for('main.index'), follow_redirects=True)
            assert response.status_code == 200

            # Check for the "All Tickets" header in the response data
            assert b"All Tickets" in response.data

            # Check for the welcome message
            assert f"Welcome, {test_user.name}!".encode('utf-8') in response.data

def test_toggle_buttons_rendering(client, app, test_admin_user):
    with client:
        with app.app_context():
            from flask_login import login_user
            test_admin_user = db.session.merge(test_admin_user)  # Ensure test_admin_user is attached to the session
            login_user(test_admin_user)

            response = client.get(url_for('main.index', view='all'), follow_redirects=True)
            assert response.status_code == 200

            # Check for active 'All Tickets' toggle button
            assert b'class="btn btn-toggle active"' in response.data
            assert b'href="/unassigned_tickets"' in response.data
            assert b'href="/assigned_tickets"' in response.data
            assert b'href="/all_tickets"' in response.data

def test_tickets_table_rendering(client, app, test_user, create_tickets):
    with client:
        with app.app_context():
            from flask_login import login_user
            test_user = db.session.merge(test_user)  # Ensure test_user is attached to the session
            login_user(test_user)

            # Re-attach ticket instances to the session
            tickets = [db.session.merge(ticket) for ticket in create_tickets]

            response = client.get(url_for('main.index', view='assigned'), follow_redirects=True)
            assert response.status_code == 200

            # Check that the tickets table is present
            assert b'<table class="table table-striped table-hover">' in response.data

            # Verify tickets are rendered correctly
            for ticket in tickets:
                assert f"{ticket.title}".encode('utf-8') in response.data
                assert f"{ticket.priority}".encode('utf-8') in response.data
                assert f"{ticket.status}".encode('utf-8') in response.data
                assignee_name = ticket.assignee.name if ticket.assignee else 'Unassigned'
                assert f"{assignee_name}".encode('utf-8') in response.data

def test_admin_actions_rendering(client, app, test_admin_user, create_tickets):
    with client:
        with app.app_context():
            from flask_login import login_user
            test_admin_user = db.session.merge(test_admin_user)  # Ensure test_admin_user is attached to the session
            login_user(test_admin_user)

            response = client.get(url_for('main.index', view='all'), follow_redirects=True)
            assert response.status_code == 200

            # Check that delete button is present for admin
            assert b'<button type="submit" class="btn btn-outline-danger btn-sm">' in response.data
            assert b'<i class="fas fa-trash"></i>' in response.data

def test_non_admin_no_delete_buttons(client, app, test_user, create_tickets):
    with client:
        with app.app_context():
            from flask_login import login_user
            test_user = db.session.merge(test_user)  # Ensure test_user is attached to the session
            login_user(test_user)

            response = client.get(url_for('main.index', view='assigned'), follow_redirects=True)
            assert response.status_code == 200

            # Verify delete buttons are not present for non-admin users
            assert b'<button type="submit" class="btn btn-outline-danger btn-sm">' not in response.data
            assert b'<i class="fas fa-trash"></i>' not in response.data
