from flask import redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Comment, Ticket, User, db


class TicketDetailsView(MethodView):
    decorators = [login_required]

    def get(self, ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        comments = Comment.query.filter_by(ticket_id=ticket.id).all()
        users = User.query.filter(User.role.in_(["admin", "support"])).all()

        return render_template(
            "ticket_details.html", ticket=ticket, comments=comments, users=users
        )

    def post(self, ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)

        if "comment_text" in request.form:
            comment_text = request.form.get("comment_text")
            new_comment = Comment(
                comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
            )
            db.session.add(new_comment)

        if "status" in request.form:
            status = request.form.get("status")
            if ticket.status != status:
                ticket.status = status
                status_comment_text = f"Status changed to {status}."
                status_comment = Comment(
                    comment_text=status_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(status_comment)

        if "priority" in request.form and current_user.role == "admin":
            priority = request.form.get("priority")
            if ticket.priority != priority:
                ticket.priority = priority
                priority_comment_text = f"Priority changed to {priority}."
                priority_comment = Comment(
                    comment_text=priority_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(priority_comment)

        if "assignee" in request.form and current_user.role == "admin":
            new_assignee_id = request.form.get("assignee")
            if ticket.assigned_to != new_assignee_id:
                ticket.assigned_to = new_assignee_id
                assignee_name = (
                    User.query.get(new_assignee_id).name
                    if new_assignee_id
                    else "Unassigned"
                )
                assignee_comment_text = f"Assignee changed to {assignee_name}."
                assignee_comment = Comment(
                    comment_text=assignee_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(assignee_comment)

        db.session.commit()
        return redirect(url_for("main.ticket_details", ticket_id=ticket_id))
