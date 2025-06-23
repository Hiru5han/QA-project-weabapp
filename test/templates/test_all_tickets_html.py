import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app import create_app
from app.models import Ticket, User, db


@pytest.fixture
def app():
    """Fixture to create a Flask app instance for testing."""
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
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
    return soup.find("input", {"name": "csrf_token"})["value"]


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


def test_all_tickets_page_renders_correctly_for_admin(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        login_user(client, admin_user.email, "ValidPassword1!")
        response = client.get(url_for("main.all_tickets"))
        assert response.status_code == 200
        assert b"All Tickets" in response.data
        assert b"Unassigned Tickets" in response.data
        assert b"Assigned Tickets" in response.data
        assert b"Active Tickets" not in response.data
        assert b"Closed Tickets" in response.data
        assert b"Your Tickets" not in response.data


def test_ticket_table_content(client, app, existing_user):
    with app.app_context():
        existing_user = db.session.merge(existing_user)

        existing_user.role = "admin"
        db.session.commit()
        ticket1 = Ticket(
            title="Test Ticket 1",
            description="This is a description for Test Ticket 1",
            priority="High",
            status="Open",
            assignee=existing_user,
        )
        ticket2 = Ticket(
            title="Test Ticket 2",
            description="This is a description for Test Ticket 2",
            priority="Medium",
            status="Closed",
            assignee=None,
        )
        db.session.add_all([ticket1, ticket2])
        db.session.commit()
        login_user(client, existing_user.email, "ValidPassword1!")
        response = client.get(url_for("main.all_tickets"))
        assert response.status_code == 200
        assert b"Test Ticket 1" in response.data
        assert b"High" in response.data
        assert b"Open" in response.data
        assert b"Existing User" in response.data

        assert b"Test Ticket 2" in response.data
        assert b"Medium" in response.data
        assert b"Closed" in response.data
        assert b"Unassigned" in response.data


def test_create_ticket_button_visibility(client, app, existing_user):
    with app.app_context():
        existing_user = db.session.merge(existing_user)
        existing_user.role = "admin"
        db.session.commit()
        login_user(client, existing_user.email, "ValidPassword1!")
        response = client.get(url_for("main.all_tickets"))
        assert response.status_code == 200
        assert b"Create Ticket" in response.data


def test_admin_delete_button_visibility(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        ticket = Ticket(
            title="Admin's Ticket",
            description="This is a description for Admin's Ticket",
            priority="High",
            status="Open",
            assignee=admin_user,
        )
        db.session.add(ticket)
        db.session.commit()
        login_user(client, admin_user.email, "ValidPassword1!")
        response = client.get(url_for("main.all_tickets"))
        assert response.status_code == 200
        assert b"Delete" in response.data


def test_non_admin_delete_button_visibility(client, app, regular_user):
    with app.app_context():
        regular_user = db.session.merge(regular_user)
        ticket = Ticket(
            title="User's Ticket",
            description="This is a description for User's Ticket",
            priority="Low",
            status="Open",
            assignee=regular_user,
        )
        db.session.add(ticket)
        db.session.commit()
    with app.app_context():
        regular_user = db.session.merge(regular_user)
    login_user(client, regular_user.email, "ValidPassword1!")
    response = client.get(url_for("main.all_tickets"))
    assert response.status_code == 200
    assert b"Delete" not in response.data


@pytest.mark.parametrize("user_role", ["admin", "regular"])
def test_closed_tickets_button_visible_for_all_roles(
    client, app, user_role, admin_user, support_user, regular_user
):
    with app.app_context():
        if user_role == "admin":
            admin_user = db.session.merge(admin_user)
            login_user(client, admin_user.email, "ValidPassword1!")
        elif user_role == "regular":
            regular_user = db.session.merge(regular_user)
            login_user(client, regular_user.email, "ValidPassword1!")
        response = client.get(url_for("main.all_tickets"))
        expected_status = 403 if user_role == "support" else 200
        assert response.status_code == expected_status
        if expected_status == 200:
            assert b"Closed Tickets" in response.data
