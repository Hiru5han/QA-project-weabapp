from flask import render_template
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket


class ClosedTicketsView(MethodView):
    decorators = [login_required]

    def get(self):
        if current_user.role == "admin":
            closed_tickets = Ticket.query.filter_by(status="closed").all()
        elif current_user.role == "support":
            closed_tickets = Ticket.query.filter_by(
                status="closed", assigned_to=current_user.id
            ).all()
        else:
            closed_tickets = Ticket.query.filter_by(
                status="closed", user_id=current_user.id
            ).all()

        return render_template(
            "closed_tickets.html", closed_tickets=closed_tickets, view="closed"
        )
