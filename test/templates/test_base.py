import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app import create_app
from app.models import User, db


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
def admin_user(app):
    """Fixture to create an admin user in the test database."""
    with app.app_context():
        user = User(name="Test Admin", email="admin@test.com", role="admin")
        user.set_password("ValidPassword1!")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def client(app):
    """Fixture to provide a test client for the app."""
    return app.test_client()


def get_csrf_token(response_data):
    """Extract the CSRF token from the HTML response."""
    soup = BeautifulSoup(response_data, "html.parser")
    return soup.find("input", {"name": "csrf_token"})["value"]


def login_user(client, email, password):
    """Helper function to log in a user during tests."""
    login_data = {
        "email": email,
        "password": password,
    }
    response = client.post(
        url_for("main.login"), data=login_data, follow_redirects=True
    )
    assert response.status_code == 200, "Login failed"
    return response


def test_base_template_unauthenticated(client):
    with client:
        response = client.get(url_for("main.index"))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")
        logo_img = soup.find("img", {"class": "logo-circle"})
        assert logo_img["src"] == url_for("static", filename="logo.png")
        profile_link = soup.find("a", {"class": "profile-badge"})
        logout_link = soup.find("a", {"class": "logout-badge"})
        assert profile_link is None
        assert logout_link is None


def test_base_template_authenticated(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        login_user(client, admin_user.email, "ValidPassword1!")
        response = client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")
        profile_img = soup.find("img", {"class": "logo-circle"})
        assert profile_img is not None
        assert "default.jpg" in profile_img["src"]


def test_base_template_role_badge(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        user_in_db = User.query.filter_by(email=admin_user.email).first()
        assert user_in_db is not None, "Admin user not found in database"
        response = login_user(client, admin_user.email, "ValidPassword1!")
        assert b"Logout" in response.data, "User is not logged in"
        response = client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")
        role_badge = soup.find("span", {"class": "badge-role-admin"})
        assert role_badge is not None, "Admin role badge not found"
        assert "Admin" in role_badge.text


def test_base_template_flash_messages(client, app, admin_user):
    with app.app_context():
        admin_user = db.session.merge(admin_user)
        login_user(client, admin_user.email, "ValidPassword1!")
        with client.session_transaction() as session:
            session["_flashes"] = [("success", "This is a success message.")]
        response = client.get(url_for("main.index"), follow_redirects=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")
        flash_message = soup.find("div", {"class": "alert-success"})
        assert flash_message is not None
        assert "This is a success message." in flash_message.text
