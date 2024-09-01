import os
from app import create_app, db
from app.models import User, Ticket, Comment

# Create the Flask application instance using the application factory
app = create_app()


def drop_database():
    """Drops the database tables."""
    with app.app_context():
        print("Dropping all database tables...")
        db.drop_all()


def initialize_database():
    """Initializes the database."""
    with app.app_context():
        print("Initializing the database...")
        db.create_all()


def create_migration():
    """Creates a migration script."""
    print("Creating migration script...")
    os.system("flask db migrate -m 'Initial migration.'")


def apply_migration():
    """Applies the migration to the database."""
    print("Applying migration...")
    os.system("flask db upgrade")


def populate_database():
    """Populates the database with initial data."""
    with app.app_context():
        print("Populating the database with initial data...")

        # Example of adding initial data
        admin = User(name="Admin User", email="admin@example.com", role="admin")
        db.session.add(admin)

        ticket = Ticket(
            title="Sample Ticket", priority="High", status="Open", creator=admin
        )
        db.session.add(ticket)

        comment = Comment(
            content="This is a sample comment.", ticket=ticket, commenter=admin
        )
        db.session.add(comment)

        db.session.commit()
        print("Initial data added.")


def reset_database():
    """Resets the database by performing all necessary steps."""
    drop_database()
    initialize_database()
    create_migration()
    apply_migration()
    # populate_database()
    print("Database reset complete.")


if __name__ == "__main__":
    reset_database()
