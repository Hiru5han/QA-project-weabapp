from flask import flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket, User


class AssignedTicketsView(MethodView):
    decorators = [login_required]

    def get(self):
        if current_user.role not in ["support", "admin"]:
            flash("Only support staff and admins can view this page.", "warning")
            return redirect(url_for("main.all_tickets"))

        if current_user.role == "support":
            assigned_tickets = (
                Ticket.query.filter_by(assigned_to=current_user.id)
                .filter(Ticket.status != "closed")
                .all()
            )
        else:
            assigned_tickets = (
                Ticket.query.filter(Ticket.assigned_to.isnot(None))
                .filter(Ticket.status != "closed")
                .all()
            )

        support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()
        return render_template(
            "assigned_tickets.html",
            assigned_tickets=assigned_tickets,
            support_staff=support_staff,
            view="assigned",
        )
