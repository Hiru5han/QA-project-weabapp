class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory database for tests
    SECRET_KEY = "testing_secret_key"
    WTF_CSRF_ENABLED = False  # Disable CSRF protection for testing
