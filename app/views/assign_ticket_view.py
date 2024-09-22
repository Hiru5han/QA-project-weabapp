from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Comment, Ticket, User, db


class AssignTicketView(MethodView):
    decorators = [login_required]

    def get(self, ticket_id):
        """
        Allows admins to assign a ticket to a support staff member.
        """
        if current_user.role != "admin":
            flash("Only admins can assign tickets.", "warning")
            return redirect(url_for("main.all_tickets"))

        ticket = Ticket.query.get_or_404(ticket_id)
        support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()

        return render_template(
            "assign_ticket.html", ticket=ticket, support_staff=support_staff
        )

    def post(self, ticket_id):
        """
        Handles the assignment of a ticket to a support staff member.
        """
        if current_user.role != "admin":
            flash("Only admins can assign tickets.", "warning")
            return redirect(url_for("main.all_tickets"))

        ticket = Ticket.query.get_or_404(ticket_id)
        assigned_to_id = request.form.get("assigned_to")

        if not assigned_to_id:
            flash("No assignee selected.", "warning")
            return redirect(url_for("main.assign_ticket", ticket_id=ticket_id))

        # Validate that the assigned user exists and is support staff
        assignee = User.query.filter_by(id=assigned_to_id).first()
        if not assignee or assignee.role not in ["admin", "support"]:
            flash("Invalid assignee selected.", "warning")
            return redirect(url_for("main.assign_ticket", ticket_id=ticket_id))

        ticket.assigned_to = assigned_to_id
        db.session.commit()

        # Add a comment about the assignment
        comment_text = f"Ticket assigned to {assignee.name}."
        new_comment = Comment(
            comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()

        flash("Ticket assigned successfully.", "success")
        return redirect(url_for("main.all_tickets"))
