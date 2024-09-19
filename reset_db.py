import os
from sqlite3 import IntegrityError

import logging
from app import create_app, db
from app.models import User, Ticket, Comment
from datetime import datetime, timedelta
import random

# Create the Flask application instance using the application factory
app = create_app()


def drop_database():
    """Drops the database tables."""
    with app.app_context():
        print("Dropping all database tables...")
        db.drop_all()


def initialise_database():
    """Initialises the database."""
    with app.app_context():
        print("Initialising the database...")
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
    """Populates the database with initial data, including mock creation dates."""
    with app.app_context():
        logging.info("Populating the database with initial data...")

        try:
            # Check if the database already contains initial data
            if User.query.filter_by(email="admin@example.com").first():
                logging.info("Initial data already exists. Skipping population.")
                return

            password = "gyjvo9-kewvoh-Vurmuj"

            # Creating users with hashed passwords (1 admin, 3 support, 4 regular users)
            admin1 = User(
                name="Homer Simpson",
                email="homer@example.com",
                role="admin",
                profile_image="starting_user_profile_images/homer-profile.png",
            )
            admin1.set_password(password)

            admin2 = User(
                name="Marge Simpson",
                email="marge@example.com",
                role="admin",
                profile_image="starting_user_profile_images/marge-profile.png",
            )
            admin2.set_password(password)

            support1 = User(
                name="Bart Simpson",
                email="bart@support.com",
                role="support",
                profile_image="starting_user_profile_images/marge-profile.png",
            )
            support1.set_password(password)

            support2 = User(
                name="Lisa Simpson",
                email="lisa@support.com",
                role="support",
                profile_image="starting_user_profile_images/lisa-profile.png",
            )
            support2.set_password(password)

            support3 = User(
                name="Maggie Simpson",
                email="maggie@support.com",
                role="support",
                profile_image="starting_user_profile_images/maggie-profile.png",
            )
            support3.set_password(password)

            user1 = User(
                name="Ralph Wiggum",
                email="ralph@example.com",
                role="regular",
                profile_image="starting_user_profile_images/ralph-profile.png",
            )
            user1.set_password(password)

            user2 = User(
                name="Julius M. Hibbert, M.D.",
                email="doctor@example.com",
                role="regular",
                profile_image="starting_user_profile_images/doctor-profile.png",
            )
            user2.set_password(password)

            user3 = User(
                name="Krusty",
                email="krusty@example.com",
                role="regular",
                profile_image="starting_user_profile_images/krusty-profile.png",
            )
            user3.set_password(password)

            user4 = User(
                name="Mr. Burns",
                email="burns.rossi@example.com",
                role="regular",
                profile_image="starting_user_profile_images/burns-profile.png",
            )
            user4.set_password(password)

            db.session.add_all(
                [
                    admin1,
                    admin2,
                    support1,
                    support2,
                    support3,
                    user1,
                    user2,
                    user3,
                    user4,
                ]
            )

            # Commit the user data first
            db.session.commit()

            # Function to mock creation dates
            def mock_date(days_ago):
                return datetime.utcnow() - timedelta(days=days_ago)

            # Creating tickets with mocked creation dates
            tickets = [
                Ticket(
                    title="Cannot log in",
                    description="I am unable to log into my account after resetting the password.",
                    priority="high",
                    status="open",
                    creator=user1,
                    assignee=support1,
                    created_at=mock_date(random.randint(1, 30)),  # Mocked creation date
                ),
                Ticket(
                    title="Website is slow",
                    description="The website takes too long to load during peak hours.",
                    priority="medium",
                    status="in-progress",
                    creator=user2,
                    assignee=support2,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Feature request: Dark mode",
                    description="It would be great to have a dark mode option for the website.",
                    priority="low",
                    status="open",
                    creator=user3,
                    assignee=None,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Bug: Page not loading",
                    description="The settings page is not loading after the latest update.",
                    priority="high",
                    status="open",
                    creator=user4,
                    assignee=support2,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Error 404 on documentation link",
                    description="The link to the user documentation leads to a 404 error page.",
                    priority="low",
                    status="closed",
                    creator=user4,
                    assignee=None,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Profile update not saving",
                    description="I can't save the updated details on my profile page.",
                    priority="medium",
                    status="in-progress",
                    creator=user1,
                    assignee=support3,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Request for invoice copy",
                    description="I need a copy of my invoice for the past 6 months.",
                    priority="low",
                    status="open",
                    creator=user2,
                    assignee=None,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Security concern: Account hacked",
                    description="My account was accessed without my permission.",
                    priority="high",
                    status="open",
                    creator=user4,
                    assignee=support1,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Suggestion: Add multi-factor authentication",
                    description="It would be great to add multi-factor authentication for extra security.",
                    priority="medium",
                    status="open",
                    creator=user3,
                    assignee=support3,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Ticket(
                    title="Cannot download report",
                    description="The download button for reports is not functioning.",
                    priority="high",
                    status="open",
                    creator=user3,
                    assignee=None,
                    created_at=mock_date(random.randint(1, 30)),
                ),
            ]

            db.session.add_all(tickets)

            # Commit the ticket data
            db.session.commit()

            # Creating comments with mocked creation dates
            comments = [
                Comment(
                    comment_text="I am investigating the issue.",
                    ticket=tickets[0],
                    commenter=support1,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Comment(
                    comment_text="This issue seems to be caused by a server load spike.",
                    ticket=tickets[1],
                    commenter=support2,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Comment(
                    comment_text="I have experienced this as well. Please look into it.",
                    ticket=tickets[3],
                    commenter=user2,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Comment(
                    comment_text="Thank you for the suggestion! We will consider it in future updates.",
                    ticket=tickets[8],
                    commenter=support3,
                    created_at=mock_date(random.randint(1, 30)),
                ),
                Comment(
                    comment_text="Please try again after clearing your browser cache.",
                    ticket=tickets[5],
                    commenter=support3,
                    created_at=mock_date(random.randint(1, 30)),
                ),
            ]

            db.session.add_all(comments)

            # Commit the comment data
            db.session.commit()
            logging.info("Initial data with mocked dates successfully added.")

        except IntegrityError as e:
            db.session.rollback()
            logging.error(f"IntegrityError occurred while populating the database: {e}")
        except Exception as e:
            db.session.rollback()
            logging.error(f"An unexpected error occurred: {e}")


def reset_database():
    """Resets the database by performing all necessary steps."""
    drop_database()
    initialise_database()
    create_migration()
    apply_migration()
    populate_database()
    print("Database reset complete.")


if __name__ == "__main__":
    reset_database()
