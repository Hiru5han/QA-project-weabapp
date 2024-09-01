import os
from sqlite3 import IntegrityError

import logging
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
        logging.info("Populating the database with initial data...")

        try:
            # Check if the database already contains initial data
            if User.query.filter_by(email="admin@example.com").first():
                logging.info("Initial data already exists. Skipping population.")
                return

            # Creating users with hashed passwords
            admin = User(name="Admin User", email="admin@example.com", role="admin")
            admin.set_password("adminpassword")

            user1 = User(name="John Doe", email="john@example.com", role="user")
            user1.set_password("password")

            user2 = User(name="Jane Smith", email="jane@example.com", role="user")
            user2.set_password("password")

            db.session.add_all([admin, user1, user2])

            # Creating tickets
            ticket1 = Ticket(
                title="Sample Ticket 1",
                description="This is the first sample ticket.",
                priority="high",
                status="open",
                creator=admin,
            )
            ticket2 = Ticket(
                title="Sample Ticket 2",
                description="This is the second sample ticket.",
                priority="medium",
                status="in-progress",
                creator=user1,
            )
            ticket3 = Ticket(
                title="Sample Ticket 3",
                description="This is the third sample ticket.",
                priority="low",
                status="closed",
                creator=user2,
            )

            db.session.add_all([ticket1, ticket2, ticket3])

            # Creating comments
            comment1 = Comment(
                comment_text="This is a sample comment on ticket 1.",
                ticket=ticket1,
                commenter=admin,
            )
            comment2 = Comment(
                comment_text="This is another comment on ticket 1.",
                ticket=ticket1,
                commenter=user1,
            )
            comment3 = Comment(
                comment_text="This is a comment on ticket 2.",
                ticket=ticket2,
                commenter=user2,
            )

            db.session.add_all([comment1, comment2, comment3])

            # Commit the changes
            db.session.commit()
            logging.info("Initial data successfully added.")

        except IntegrityError as e:
            db.session.rollback()
            logging.error(f"Error occurred while populating the database: {e}")

        except Exception as e:
            db.session.rollback()
            logging.error(f"An unexpected error occurred: {e}")


def reset_database():
    """Resets the database by performing all necessary steps."""
    drop_database()
    initialize_database()
    create_migration()
    apply_migration()
    populate_database()
    print("Database reset complete.")


if __name__ == "__main__":
    reset_database()
