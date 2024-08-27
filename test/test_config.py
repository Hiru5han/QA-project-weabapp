import os

class TestConfig:
    """
    Configuration class for testing environment.

    This class defines configuration settings for the testing environment, 
    including the secret key, database URI, and other relevant options.

    Attributes:
        SECRET_KEY (str): The secret key for the application, retrieved from the 
            environment variable 'SECRET_KEY' or set to a default value of 'test_secret_key'.
        SQLALCHEMY_DATABASE_URI (str): The URI for the in-memory SQLite database 
            used during testing.
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Whether to track modifications of 
            objects and emit signals. Disabled in this configuration to save resources.
        DEBUG (bool): Enables or disables debug mode. Set to True for testing.
    """
    SECRET_KEY = os.getenv('SECRET_KEY', 'test_secret_key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
