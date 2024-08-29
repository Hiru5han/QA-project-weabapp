import pytest
from flask import url_for

def test_homepage_content_rendering(client, app):
    """
    Test that the homepage content is rendered correctly.

    This test checks that the main elements like the title, lead paragraph, 
    and the login/register buttons are present and have the correct links.
    """
    with client:
        response = client.get(url_for('main.index'), follow_redirects=True)
        assert response.status_code == 200

        # Check for the main heading
        assert b'Help Desk Ticketing System' in response.data

        # Check for the lead paragraph
        assert b'A simple and efficient way to manage IT support requests.' in response.data

        # Check for the "Login" button and its link
        assert b'Login' in response.data
        assert f'href="{url_for("main.login")}"'.encode('utf-8') in response.data

        # Check for the "Register" button and its link
        assert b'Register' in response.data
        assert f'href="{url_for("main.register")}"'.encode('utf-8') in response.data

def test_homepage_buttons(client, app):
    """
    Test that the homepage buttons are rendered with correct attributes.
    
    This test checks that the "Login" and "Register" buttons have the correct
    classes and roles.
    """
    with client:
        response = client.get(url_for('main.index'), follow_redirects=True)
        assert response.status_code == 200

        # Check that the "Login" button has the correct class and role
        assert b'class="btn btn-primary btn-lg mx-2"' in response.data
        assert b'role="button"' in response.data
        assert f'href="{url_for("main.login")}"'.encode('utf-8') in response.data

        # Check that the "Register" button has the correct class and role
        assert b'class="btn btn-secondary btn-lg mx-2"' in response.data
        assert b'role="button"' in response.data
        assert f'href="{url_for("main.register")}"'.encode('utf-8') in response.data
