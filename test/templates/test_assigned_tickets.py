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
        user.set_password("ValidPassword1!")
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
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data.decode("utf-8"))
    assert csrf_token is not None, "Could not find CSRF token in login page"
    login_data = {
        "email": email,
        "password": password,
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    print(response.data.decode("utf-8"))
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
        user.set_password("ValidPassword1!")
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


@pytest.mark.parametrize("user_role", ["admin", "support"])
def test_assigned_tickets_page_renders_correctly_for_admin_and_support(
    client, app, user_role, admin_user, support_user
):
    with app.app_context():
        if user_role == "admin":
            user = db.session.merge(admin_user)
        elif user_role == "support":
            user = db.session.merge(support_user)
        response = login_user(client, user.email, "ValidPassword1!")
        assert b"Logout" in response.data, "User is not logged in"
        response = client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")
        header = soup.find("h2", class_="text-primary")
        assert header is not None, "Assigned Tickets header not found"
        assert "Assigned Tickets" == header.text.strip(), "Incorrect page header"
        greeting = soup.find("p", class_="lead")
        assert greeting is not None, "Greeting not found"
        assert f"Welcome, {user.name}!" == greeting.text.strip(), "Incorrect greeting"


def test_all_tickets_button_visible_for_admin(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        response = login_user(client, admin_user.email, "ValidPassword1!")
        assert b"Logout" in response.data, "User is not logged in"
        response = client.get(url_for("main.all_tickets"), follow_redirects=False)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")
        all_tickets_button = None
        for a_tag in soup.find_all("a"):
            if a_tag.text.strip() == "All Tickets":
                all_tickets_button = a_tag
                break
        assert all_tickets_button is not None, "All Tickets button not found for admin"
        classes = all_tickets_button.get("class", [])
        print(f"Classes for 'All Tickets' button: {classes}")
        assert "btn" in classes
        assert "btn-toggle" in classes
        assert "active" in classes, "All Tickets button is not active"
        assert "view" in response.data.decode(), "'view' context not found in response"


def test_admin_delete_button_visibility_for_assigned_ticket(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        response = login_user(client, admin_user.email, "ValidPassword1!")
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
        response = client.get(url_for("main.assigned_tickets"))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
        delete_form = soup.find(
            "form",
            {
                "action": url_for(
                    "main.delete_ticket", ticket_id=ticket.id, _external=False
                )
            },
        )
        assert delete_form is not None, "Delete form not found"

        csrf_token = delete_form.find("input", {"name": "csrf_token"})["value"]
        assert csrf_token is not None, "CSRF token not found in delete form"
        delete_data = {
            "csrf_token": csrf_token,
        }
        response = client.post(
            url_for("main.delete_ticket", ticket_id=ticket.id),
            data=delete_data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        deleted_ticket = Ticket.query.get(ticket.id)
        assert deleted_ticket is None, "Ticket was not deleted"
