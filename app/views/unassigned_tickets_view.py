from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Comment, Ticket, User, db


class UnassignedTicketsView(MethodView):
    decorators = [login_required]

    def get(self):
        if current_user.role not in ["support", "admin"]:
            flash("Only support staff and admins can view this page.", "warning")
            return redirect(url_for("main.all_tickets"))

        unassigned_tickets = Ticket.query.filter_by(assigned_to=None).all()
        support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()

        return render_template(
            "unassigned_tickets.html",
            unassigned_tickets=unassigned_tickets,
            support_staff=support_staff,
            view="unassigned",
        )

    def post(self):
        ticket_id = request.form.get("ticket_id")
        ticket = Ticket.query.get(ticket_id)

        if current_user.role == "support":
            ticket.assigned_to = current_user.id
            comment_text = f"Ticket assigned to {current_user.name}."
        elif current_user.role == "admin":
            assigned_to_id = request.form.get("assigned_to")
            print(f"Assigned to ID: {assigned_to_id}")  # Debugging line
            if not assigned_to_id:
                flash("No assignee selected.", "warning")
                return redirect(url_for("main.unassigned_tickets"))

            assignee = User.query.get(assigned_to_id)

            if assignee is None:
                flash("The selected user does not exist.", "warning")
                return redirect(url_for("main.unassigned_tickets"))

            ticket.assigned_to = assigned_to_id
            comment_text = f"Ticket assigned to {assignee.name}."

        db.session.commit()

        new_comment = Comment(
            comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()

        flash("Ticket assigned successfully.", "success")
        return redirect(url_for("main.unassigned_tickets"))
