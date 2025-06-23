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


def login_user(client):
    """Helper function to log in a user during tests."""
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)
    login_data = {
        "email": "testuser@example.com",
        "password": "gyjvo9-kewvoh-Vurmuj!",
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


@pytest.fixture
def setup_test_data(app):
    """Fixture to set up test data in the in-memory database."""
    with app.app_context():
        db.create_all()
        db.session.query(User).delete()
        db.session.query(Ticket).delete()
        user = User(email="testuser@example.com", name="Test User", role="admin")
        user.set_password("gyjvo9-kewvoh-Vurmuj!")
        db.session.add(user)
        db.session.commit()
        ticket = Ticket(
            title="Active Ticket",
            description="An active test ticket",
            status="Open",
            priority="High",
            user_id=user.id,
            assigned_to=user.id,
        )
        db.session.add(ticket)
        db.session.commit()
        yield
        db.drop_all()


def login_regular_user(client):
    """Helper function to log in a regular user during tests."""
    with client.application.app_context():
        user = User.query.filter_by(email="regularuser@example.com").first()
        if user is None:
            user = User(
                email="regularuser@example.com", name="Regular User", role="regular"
            )
            user.set_password("gyjvo9-kewvoh-Vurmuj!")
            db.session.add(user)
            db.session.commit()
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)
    login_data = {
        "email": "regularuser@example.com",
        "password": "gyjvo9-kewvoh-Vurmuj!",
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200
    return response


def test_all_tickets_view_admin(client, setup_test_data):
    login_user(client)
    with client.application.app_context():
        admin_user = User.query.filter_by(email="testuser@example.com").first()
        assert admin_user is not None, "Admin user does not exist in the database"
        regular_user = User(
            email="regularuser@example.com", name="Regular User", role="regular"
        )
        regular_user.set_password("gyjvo9-kewvoh-Vurmuj!")
        db.session.add(regular_user)
        db.session.commit()
        admin_ticket = Ticket(
            title="Admin Ticket",
            description="Ticket for admin user",
            status="open",
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )
        regular_ticket = Ticket(
            title="Regular Ticket",
            description="Ticket for regular user",
            status="open",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )
        db.session.add_all([admin_ticket, regular_ticket])
        db.session.commit()
    response = client.get("/all_tickets")
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"
    soup = BeautifulSoup(response.data, "html.parser")
    table_body = soup.find("tbody")
    assert table_body is not None, "Table body not found in the response"
    ticket_titles = [row.find("td").text.strip() for row in table_body.find_all("tr")]
    assert "Admin Ticket" in ticket_titles, "Admin ticket not found in the table"
    assert "Regular Ticket" in ticket_titles, "Regular ticket not found in the table"


def test_all_tickets_view_regular_user(client, setup_test_data):
    login_regular_user(client)
    with client.application.app_context():
        regular_user = User.query.filter_by(email="regularuser@example.com").first()
        admin_user = User.query.filter_by(email="testuser@example.com").first()
        assert regular_user is not None, "Regular user does not exist in the database"
        assert admin_user is not None, "Admin user does not exist in the database"
        regular_ticket = Ticket(
            title="Regular User Ticket",
            description="Ticket for regular user",
            status="open",
            priority="Low",
            user_id=regular_user.id,
            assigned_to=regular_user.id,
        )
        admin_ticket = Ticket(
            title="Admin User Ticket",
            description="Ticket for admin user",
            status="open",
            priority="High",
            user_id=admin_user.id,
            assigned_to=admin_user.id,
        )
        db.session.add_all([regular_ticket, admin_ticket])
        db.session.commit()
    response = client.get("/all_tickets")
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"
    soup = BeautifulSoup(response.data, "html.parser")
    table_body = soup.find("tbody")
    assert table_body is not None, "Table body not found in the response"
    ticket_titles = [row.find("td").text.strip() for row in table_body.find_all("tr")]
    assert (
        "Regular User Ticket" in ticket_titles
    ), "Regular user's ticket not found in the table"
    assert (
        "Admin User Ticket" not in ticket_titles
    ), "Admin user's ticket should not be in the table"
