from bs4 import BeautifulSoup
from flask import url_for
import pytest
from app import create_app, db
from app.models import User, Ticket
from app.routes import load_user


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


def get_csrf_token(response_data):
    """Helper function to extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    token = soup.find("input", {"name": "csrf_token"})
    if token:
        return token.get("value")
    return None


def login_user(client):
    response = client.get(url_for("main.login"))
    csrf_token = get_csrf_token(response.data)
    response = client.post(
        "/login",
        data={
            "email": "testuser@example.com",
            "password": "gyjvo9-kewvoh-Vurmuj!",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200 or response.status_code == 302, "Login failed"
    with client.session_transaction() as session:
        assert "_user_id" in session, "User ID not in session after login"


def test_home_route(client):
    """
    Test the home route ("/").
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Help Desk Ticketing System" in response.data


def test_login_route_get(client):
    """
    Test the GET method for the login route ("/login").
    """
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_route_post(client, setup_test_data):
    response = client.get("/login")
    csrf_token = get_csrf_token(response.data)
    assert csrf_token, "CSRF token not found"
    response = client.post(
        "/login",
        data={
            "email": "testuser@example.com",
            "password": "gyjvo9-kewvoh-Vurmuj",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )
    assert response.status_code in [
        302,
        200,
    ], f"Expected 302 or 200, but got {response.status_code}"


def test_register_route_get(client):
    """
    Test the GET method for the register route ("/register").
    """
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_register_route_post(client):
    response = client.get(url_for("main.register"))
    csrf_token = get_csrf_token(response.data)

    response = client.post(
        "/register",
        data={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "gyjvo9-kewvoh-Vurmuj!",
            "confirm": "gyjvo9-kewvoh-Vurmuj!",
            "role": "regular",
            "csrf_token": csrf_token,
        },
    )
    assert response.status_code == 302


def test_create_ticket_route_get(client, setup_test_data):
    login_user(client)
    response = client.get("/create_ticket")
    assert response.status_code == 200
    assert b"Create Ticket" in response.data


def test_create_ticket_route_post(client, setup_test_data):
    login_user(client)
    response = client.get("/create_ticket")
    csrf_token = get_csrf_token(response.data)
    response = client.post(
        "/create_ticket",
        data={
            "title": "Test Ticket",
            "description": "Test description",
            "priority": "high",
            "status": "open",
            "csrf_token": csrf_token,
        },
    )
    print(response.data.decode())
    assert response.status_code == 302


def test_all_tickets_route(client, setup_test_data):
    login_user(client)
    response = client.get("/all_tickets")
    assert response.status_code == 200
    assert b"All Tickets" in response.data


def test_active_tickets_route(client, setup_test_data):
    login_user(client)
    response = client.get("/active_tickets")
    assert response.status_code == 200
    assert (
        b"All Tickets" in response.data or b"0 active" in response.data
    ), "Expected active tickets content not found"


def test_assigned_tickets_route(client, setup_test_data):
    login_user(client)
    response = client.get("/assigned_tickets", follow_redirects=True)
    assert (
        response.status_code == 200
    ), f"Expected status code 200 but got {response.status_code}"
    assert b"Assigned Tickets" in response.data


def test_update_profile_route_get(client, setup_test_data):
    login_user(client)
    response = client.get("/update_profile")
    assert response.status_code == 200
    assert b"Update Profile" in response.data


def test_update_profile_route_post(client, setup_test_data):
    login_user(client)
    response = client.get(url_for("main.update_profile"))
    csrf_token = get_csrf_token(response.data)
    assert csrf_token, "CSRF token not found"
    update_data = {
        "name": "Updated Test User",
        "email": "updatedtestuser@example.com",
        "csrf_token": csrf_token,
    }
    response = client.post(
        url_for("main.update_profile"),
        data=update_data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your profile has been updated." in response.data


def test_logout_route(client):
    """
    Test the logout route ("/logout").
    """
    response = client.get("/logout")
    assert response.status_code == 302


def test_ticket_details_readonly_route(client, setup_test_data):
    login_user(client)
    response = client.get("/ticket/1/readonly")
    assert response.status_code == 200
    assert b"Ticket Details" in response.data


def test_delete_ticket_route_post(client, setup_test_data):
    login_user(client)
    response = client.get(url_for("main.create_ticket"))
    csrf_token = get_csrf_token(response.data)
    assert csrf_token, "CSRF token not found"
    response = client.post(
        url_for("main.delete_ticket", ticket_id=1),
        data={"csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert (
        response.status_code == 302
    ), f"Failed to delete ticket, got {response.status_code}"
    response = client.get(response.headers["Location"], follow_redirects=True)
    assert b"Ticket has been deleted successfully." in response.data


def test_load_user_valid_user(setup_test_data, app):
    with app.app_context():
        user = User.query.first()
        assert user is not None, "Test user not found in the database."
        result = load_user(user.id)
        assert result is not None, "load_user returned None for a valid user ID."
        assert result.id == user.id, "User IDs do not match."
        assert result.email == user.email, "User emails do not match."


def test_load_user_invalid_user(setup_test_data, app):
    with app.app_context():
        non_existent_user_id = 999
        result = load_user(non_existent_user_id)
        assert result is None, "load_user should return None for an invalid user ID."
