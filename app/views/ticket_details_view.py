from flask import redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Comment, Ticket, User, db
from app.utils import sanitise_html
from typing import Any, Callable, ClassVar


class TicketDetailsView(MethodView):
    decorators: ClassVar[list[Callable[[Any], Any]]] = [login_required]

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
            comment_text = sanitise_html(request.form.get("comment_text", ""))
            new_comment = Comment(
                comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id  # type: ignore
            )
            db.session.add(new_comment)

        if "status" in request.form:
            status = request.form.get("status")
            if ticket.status != status:
                ticket.status = status
                status_comment_text = sanitise_html(f"Status changed to {status}.")
                status_comment = Comment(
                    comment_text=status_comment_text,  # type: ignore
                    ticket_id=ticket.id,  # type: ignore
                    user_id=current_user.id,  # type: ignore
                )
                db.session.add(status_comment)

        if "priority" in request.form:
            priority = request.form.get("priority")
            if ticket.priority != priority:
                ticket.priority = priority
                priority_comment_text = sanitise_html(
                    f"Priority changed to {priority}."
                )
                priority_comment = Comment(
                    comment_text=priority_comment_text,  # type: ignore
                    ticket_id=ticket.id,  # type: ignore
                    user_id=current_user.id,  # type: ignore
                )
                db.session.add(priority_comment)

        if "assignee" in request.form:
            new_assignee_id = request.form.get("assignee")
            if ticket.assigned_to != new_assignee_id:
                ticket.assigned_to = new_assignee_id
                user = User.query.get(new_assignee_id)
                assignee_name = user.name if user else "Unassigned"
                assignee_comment_text = sanitise_html(
                    f"Assignee changed to {assignee_name}."
                )
                assignee_comment = Comment(
                    comment_text=assignee_comment_text,  # type: ignore
                    ticket_id=ticket.id,  # type: ignore
                    user_id=current_user.id,  # type: ignore
                )
                db.session.add(assignee_comment)

        db.session.commit()
        return redirect(url_for("main.ticket_details", ticket_id=ticket_id))
