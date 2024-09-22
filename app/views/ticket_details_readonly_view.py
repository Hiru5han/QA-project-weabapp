from flask import render_template
from flask.views import MethodView
from flask_login import login_required

from ..models import Comment, Ticket


class TicketDetailsReadonlyView(MethodView):
    decorators = [login_required]

    def get(self, ticket_id):
        """
        Displays the read-only details of a specific ticket without any interactivity.
        """
        ticket = Ticket.query.get_or_404(ticket_id)
        comments = Comment.query.filter_by(ticket_id=ticket.id).all()
        return render_template(
            "ticket_details_readonly.html", ticket=ticket, comments=comments
        )
