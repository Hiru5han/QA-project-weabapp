from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """
    Represents a user in the system.

    Attributes
    ----------
    id : int
        Primary key for the user.
    name : str
        The full name of the user. This is a required field.
    email : str
        The unique email address of the user. This is a required field.
    password : str
        The password for the user account. This is a required field.
    role : str
        The role of the user in the system. Can be 'admin', 'support', or 'regular'.

    Relationships
    -------------
    created_tickets : list[Ticket]
        List of tickets created by the user.
    assigned_tickets : list[Ticket]
        List of tickets assigned to the user.
    user_comments : list[Comment]
        List of comments made by the user.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    # 'admin', 'support', 'regular'
    role = db.Column(db.String(50), nullable=False)

    created_tickets = db.relationship(
        "Ticket",
        foreign_keys="Ticket.user_id",
        back_populates="creator",
        overlaps="assigned_tickets,comments"
    )
    assigned_tickets = db.relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_to",
        back_populates="assignee",
        overlaps="created_tickets,comments"
    )
    user_comments = db.relationship(
        "Comment", back_populates="commenter", overlaps="commenter,comments"
    )


class Ticket(db.Model):
    """
    Represents a ticket in the system.

    Attributes
    ----------
    id : int
        Primary key for the ticket.
    title : str
        The title of the ticket. This is a required field.
    description : str
        The detailed description of the ticket. This is a required field.
    status : str
        The current status of the ticket. Can be 'open', 'in-progress', or 'closed'.
    priority : str
        The priority level of the ticket. Can be 'low', 'medium', or 'high'.
    created_at : datetime
        The date and time when the ticket was created. Defaults to the current UTC time.
    updated_at : datetime
        The date and time when the ticket was last updated. Automatically updated on changes.
    assigned_to : int
        Foreign key referencing the user assigned to the ticket.
    user_id : int
        Foreign key referencing the user who created the ticket.

    Relationships
    -------------
    creator : User
        The user who created the ticket.
    assignee : User
        The user assigned to the ticket.
    ticket_comments : list[Comment]
        List of comments associated with the ticket.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # 'open', 'in-progress', 'closed'
    status = db.Column(db.String(50), nullable=False)
    # 'low', 'medium', 'high'
    priority = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    creator = db.relationship("User", foreign_keys=[user_id], back_populates="created_tickets", overlaps="assigned_tickets,comments")
    assignee = db.relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tickets", overlaps="created_tickets,comments")
    ticket_comments = db.relationship("Comment", back_populates="ticket")


class Comment(db.Model):
    """
    Represents a comment on a ticket.

    Attributes
    ----------
    id : int
        Primary key for the comment.
    ticket_id : int
        Foreign key referencing the associated ticket.
    user_id : int
        Foreign key referencing the user who made the comment.
    comment_text : str
        The content of the comment. This is a required field.
    created_at : datetime
        The date and time when the comment was created. Defaults to the current UTC time.

    Relationships
    -------------
    ticket : Ticket
        The ticket that the comment is associated with.
    commenter : User
        The user who made the comment.
    """
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("Ticket", back_populates="ticket_comments")
    commenter = db.relationship("User", back_populates="user_comments", overlaps="comments")
