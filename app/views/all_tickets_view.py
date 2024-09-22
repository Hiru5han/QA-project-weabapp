from flask import render_template
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket


class AllTicketsView(MethodView):
    decorators = [login_required]

    def get(self):
        """
        Renders a page displaying all tickets.
        """
        if current_user.role in ["admin", "support"]:
            tickets = Ticket.query.all()
            view = "all"
        else:
            tickets = Ticket.query.filter_by(user_id=current_user.id).all()
            view = "active"

        return render_template(
            "all_tickets.html", tickets=tickets, current_user=current_user, view=view
        )
