from . import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """
    Represents a user in the system.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    created_tickets = db.relationship(
        "Ticket",
        foreign_keys="Ticket.user_id",
        back_populates="creator",
        overlaps="assigned_tickets,comments",
    )
    assigned_tickets = db.relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_to",
        back_populates="assignee",
        overlaps="created_tickets,comments",
    )
    user_comments = db.relationship(
        "Comment", back_populates="commenter", overlaps="commenter,comments"
    )

    # Set password
    def set_password(self, password):
        """Sets the user's password after validating its complexity."""
        if not self.validate_password(password):
            raise ValueError("Password does not meet complexity requirements.")

        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    @staticmethod
    def validate_password(password):
        """Validates the password complexity."""
        if len(password) < 8:
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in password):
            return False
        return True

    # Verify password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Ticket(db.Model):
    """
    Represents a ticket in the system.
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    creator = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="created_tickets",
        overlaps="assigned_tickets,comments",
    )
    assignee = db.relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets",
        overlaps="created_tickets,comments",
    )
    ticket_comments = db.relationship("Comment", back_populates="ticket")


class Comment(db.Model):
    """
    Represents a comment on a ticket.
    """

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    ticket = db.relationship("Ticket", back_populates="ticket_comments")
    commenter = db.relationship(
        "User", back_populates="user_comments", overlaps="comments"
    )
