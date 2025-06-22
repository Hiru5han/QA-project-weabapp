from test.test_config import TestConfig


def test_testing_config_values():
    assert TestConfig.TESTING is True
    assert TestConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert TestConfig.SECRET_KEY == "test-secret-key"
    assert TestConfig.WTF_CSRF_ENABLED is False
