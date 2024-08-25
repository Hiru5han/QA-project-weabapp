from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("Ticket", back_populates="ticket_comments")
    commenter = db.relationship("User", back_populates="user_comments", overlaps="comments")
