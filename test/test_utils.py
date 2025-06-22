from flask import url_for
from flask_login import login_user, logout_user

from app.models import User, Ticket, db
from app.utils import (
    allowed_file,
    sanitize_html,
    is_safe_url,
    redirect_based_on_role,
    inject_open_tickets_count,
)


def test_allowed_file():
    assert allowed_file("test.PNG")
    assert allowed_file("photo.jpg")
    assert not allowed_file("archive.zip")


def test_sanitize_html():
    assert sanitize_html("<b>bold</b>") == "&lt;b&gt;bold&lt;/b&gt;"
    assert sanitize_html(None) == ""


def test_is_safe_url(app):
    with app.test_request_context():
        assert is_safe_url("/relative")
        assert not is_safe_url("http://evil.com")


def test_redirect_based_on_role(app):
    with app.test_request_context():
        user = User(name="Admin", email="admin@test", role="admin")
        login_user(user)
        resp = redirect_based_on_role()
        assert resp.location == url_for("main.all_tickets")
        logout_user()

        user = User(name="Support", email="support@test", role="support")
        login_user(user)
        resp = redirect_based_on_role()
        assert resp.location == url_for("main.assigned_tickets")
        logout_user()

        user = User(name="Regular", email="reg@test", role="regular")
        login_user(user)
        resp = redirect_based_on_role()
        assert resp.location == url_for("main.all_tickets")
        logout_user()


def test_inject_open_tickets_count(app):
    with app.app_context():
        user = User(name="User", email="u@e", role="admin", password_hash="x")
        db.session.add(user)
        db.session.commit()
        db.session.add(
            Ticket(
                title="Open",
                description="d",
                status="open",
                priority="low",
                user_id=user.id,
            )
        )
        db.session.add(
            Ticket(
                title="Closed",
                description="d",
                status="closed",
                priority="low",
                user_id=user.id,
            )
        )
        db.session.commit()
        result = inject_open_tickets_count()
        assert result["open_tickets_count"] == 1
