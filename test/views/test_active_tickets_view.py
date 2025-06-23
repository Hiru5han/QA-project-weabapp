from bs4 import BeautifulSoup
from flask import url_for
import pytest

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


def test_active_tickets_view(client, setup_test_data):
    login_user(client)
    with client.application.app_context():
        user = User.query.filter_by(email="testuser@example.com").first()
        assert user is not None, "Test user does not exist in the database"
        open_ticket = Ticket(
            title="Open Ticket",
            description="This is an open ticket",
            status="open",
            priority="High",
            user_id=user.id,
            assigned_to=user.id,
        )
        closed_ticket = Ticket(
            title="Closed Ticket",
            description="This is a closed ticket",
            status="closed",
            priority="Low",
            user_id=user.id,
            assigned_to=user.id,
        )
        db.session.add_all([open_ticket, closed_ticket])
        db.session.commit()
    response = client.get("/active_tickets")
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"
    soup = BeautifulSoup(response.data, "html.parser")
    table_body = soup.find("tbody")
    assert table_body is not None, "Table body not found in the response"
    ticket_titles = []
    for row in table_body.find_all("tr"):
        title_cell = row.find("td", class_="text-center")
        if title_cell:
            ticket_titles.append(title_cell.text.strip())
    assert "Open Ticket" in ticket_titles, "Open ticket not found in the table"
    assert (
        "Closed Ticket" not in ticket_titles
    ), "Closed ticket should not be in the table"
