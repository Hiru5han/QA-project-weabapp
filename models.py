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
        'Ticket', foreign_keys='Ticket.user_id', backref='creator')
    assigned_tickets = db.relationship(
        'Ticket', foreign_keys='Ticket.assigned_to', backref='assignee')
    comments = db.relationship('Comment', backref='commenter')


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
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship('Ticket', backref='ticket_comments')
    user = db.relationship('User', backref='user_comments')
