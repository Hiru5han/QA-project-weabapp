import pytest
from flask import url_for
from app.models import User, db

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
def support_user(app):
    with app.app_context():
        user = User.query.filter_by(email="support@example.com").first()
        if not user:
            user = User(name="Support User", email="support@example.com", password="password", role="support")
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

def test_form_rendering_for_regular_user(client, app, regular_user):
    with client:
        with app.app_context():
            from flask_login import login_user

            # Reattach the user to the session
            regular_user = db.session.merge(regular_user)
            login_user(regular_user)

            response = client.get(url_for('main.create_ticket'), follow_redirects=True)
            assert response.status_code == 200

            # Check that the basic form fields are rendered
            assert b'<label for="title">Title</label>' in response.data
            assert b'<label for="description">Description</label>' in response.data
            assert b'<label for="priority">Priority</label>' in response.data

            # Check that the status and assigned_to fields are not rendered
            assert b'<label for="status">Current State</label>' not in response.data
            assert b'<label for="assigned_to">Assign to Support User</label>' not in response.data

def test_form_rendering_for_support_user(client, app, support_user):
    with client:
        with app.app_context():
            from flask_login import login_user

            # Reattach the user to the session
            support_user = db.session.merge(support_user)
            login_user(support_user)

            response = client.get(url_for('main.create_ticket'), follow_redirects=True)
            assert response.status_code == 200

            # Check that the basic form fields are rendered
            assert b'<label for="title">Title</label>' in response.data
            assert b'<label for="description">Description</label>' in response.data
            assert b'<label for="priority">Priority</label>' in response.data

            # Check that the status field is rendered and assigned_to is not
            assert b'<label for="status">Current State</label>' in response.data
            assert b'<label for="assigned_to">Assign to Support User</label>' not in response.data

def test_form_rendering_for_admin_user(client, app, admin_user):
    with client:
        with app.app_context():
            from flask_login import login_user

            # Reattach the user to the session
            admin_user = db.session.merge(admin_user)
            login_user(admin_user)

            response = client.get(url_for('main.create_ticket'), follow_redirects=True)
            assert response.status_code == 200

            # Check that the basic form fields are rendered
            assert b'<label for="title">Title</label>' in response.data
            assert b'<label for="description">Description</label>' in response.data
            assert b'<label for="priority">Priority</label>' in response.data

            # Check that both status and assigned_to fields are rendered
            assert b'<label for="status">Current State</label>' in response.data
            assert b'<label for="assigned_to">Assign to Support User</label>' in response.data
