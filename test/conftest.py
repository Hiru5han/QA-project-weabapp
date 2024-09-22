import pytest

from app import create_app, db


@pytest.fixture
def client():
    app = create_app("TestingConfig")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()
