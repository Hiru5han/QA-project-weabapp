class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False  # Disable CSRF protection for testing
    # Required for flask.url_for calls outside a request context on Flask 3+
    SERVER_NAME = "localhost"
