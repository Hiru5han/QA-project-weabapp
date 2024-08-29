import pytest
from flask import url_for
from app.models import User, Ticket, db

@pytest.fixture
def ticket(app):
    with app.app_context():
        ticket = Ticket(title="Test Ticket", description="This is a test ticket.", priority="high", status="open")
        db.session.add(ticket)
        db.session.commit()
    return ticket

@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@example.com").first()
        if not user:
            user = User(name="Admin User", email="admin@example.com", password="password", role="admin")
            db.session.add(user)
            db.session.commit()
    return user

@pytest.fixture
def manager_user(app):
    with app.app_context():
        user = User.query.filter_by(email="manager@example.com").first()
        if not user:
            user = User(name="Manager User", email="manager@example.com", password="password", role="manager")
            db.session.add(user)
            db.session.commit()
    return user

@pytest.fixture
def regular_user(app):
    with app.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        if not user:
            user = User(name="Regular User", email="user@example.com", password="password", role="user")
            db.session.add(user)
            db.session.commit()
    return user

def test_ticket_details_rendering_for_regular_user(client, app, regular_user, ticket):
    with client:
        with app.app_context():
            from flask_login import login_user

            regular_user = db.session.merge(regular_user)
            ticket = db.session.merge(ticket)  # Reattach the ticket to the session
            login_user(regular_user)

            response = client.get(url_for('main.ticket_details', ticket_id=ticket.id), follow_redirects=True)
            assert response.status_code == 200

            # Check for the back button and header
            assert b'Ticket Details' in response.data
            assert b'<img src="/static/back_button.png"' in response.data

            # Check for the priority and status badges (non-clickable for regular user)
            assert b'<span><strong>Priority: </strong></span>' in response.data
            assert b'bg-danger' in response.data  # for high priority
            assert b'clickable-badge' not in response.data  # should not be clickable

            assert b'<span><strong>Status: </strong></span>' in response.data
            assert b'bg-success' in response.data  # for open status
            assert b'clickable-badge' not in response.data  # should not be clickable

            # Check for the description section
            assert b'This is a test ticket.' in response.data

            # Check that modals and JS are not present for regular user
            assert b'Update Status' not in response.data
            assert b'Update Priority' not in response.data
            assert b'<script>' not in response.data

def test_ticket_details_rendering_for_admin_user(client, app, admin_user, ticket):
    with client:
        with app.app_context():
            from flask_login import login_user

            admin_user = db.session.merge(admin_user)
            ticket = db.session.merge(ticket)  # Reattach the ticket to the session
            login_user(admin_user)

            response = client.get(url_for('main.ticket_details', ticket_id=ticket.id), follow_redirects=True)
            assert response.status_code == 200

            # Check for the back button and header
            assert b'Ticket Details' in response.data
            assert b'<img src="/static/back_button.png"' in response.data

            # Check for the priority and status badges (clickable for admin)
            assert b'<span><strong>Priority: </strong></span>' in response.data
            assert b'bg-danger' in response.data  # for high priority
            assert b'clickable-badge' in response.data  # should be clickable

            assert b'<span><strong>Status: </strong></span>' in response.data
            assert b'bg-success' in response.data  # for open status
            assert b'clickable-badge' in response.data  # should be clickable

            # Check for the description section
            assert b'This is a test ticket.' in response.data

            # Check that modals and JS are present for admin user
            assert b'Update Status' in response.data
            assert b'Update Priority' in response.data
            assert b'<script>' in response.data

def test_ticket_details_rendering_for_manager_user(client, app, manager_user, ticket):
    with client:
        with app.app_context():
            from flask_login import login_user

            manager_user = db.session.merge(manager_user)
            ticket = db.session.merge(ticket)  # Reattach the ticket to the session
            login_user(manager_user)

            response = client.get(url_for('main.ticket_details', ticket_id=ticket.id), follow_redirects=True)
            assert response.status_code == 200

            # Check for the back button and header
            assert b'Ticket Details' in response.data
            assert b'<img src="/static/back_button.png"' in response.data

            # Check for the priority and status badges (clickable for manager)
            assert b'<span><strong>Priority: </strong></span>' in response.data
            assert b'bg-danger' in response.data  # for high priority
            assert b'clickable-badge' in response.data  # should be clickable

            assert b'<span><strong>Status: </strong></span>' in response.data
            assert b'bg-success' in response.data  # for open status
            assert b'clickable-badge' in response.data  # should be clickable

            # Check for the description section
            assert b'This is a test ticket.' in response.data

            # Check that modals and JS are present for manager user
            assert b'Update Status' in response.data
            assert b'Update Priority' in response.data
            assert b'<script>' in response.data
