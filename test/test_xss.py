import pytest
from markupsafe import escape
from bs4 import BeautifulSoup
from flask import url_for

from app.models import Ticket
from .test_routes import get_csrf_token, login_user, setup_test_data


def test_create_ticket_sanitizes_input(client, setup_test_data):
    login_user(client)
    response = client.get(url_for("main.create_ticket"))
    csrf_token = get_csrf_token(response.data)

    malicious_title = "<script>alert('xss')</script>"
    malicious_description = "<img src=x onerror=alert('xss')>"

    response = client.post(
        url_for("main.create_ticket"),
        data={
            "title": malicious_title,
            "description": malicious_description,
            "priority": "low",
            "status": "open",
            "csrf_token": csrf_token,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with client.application.app_context():
        ticket = Ticket.query.filter_by(title=escape(malicious_title)).first()
        assert ticket is not None
        assert ticket.description == escape(malicious_description)
