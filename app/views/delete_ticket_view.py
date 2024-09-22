from flask import flash, redirect, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket, db


class DeleteTicketView(MethodView):
    decorators = [login_required]

    def post(self, ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)

        if current_user.role != "admin":
            flash("You do not have permission to delete this ticket.", "danger")
            return redirect(url_for("main.ticket_details", ticket_id=ticket_id))

        db.session.delete(ticket)
        db.session.commit()
        flash("Ticket has been deleted successfully.", "success")
        return redirect(url_for("main.all_tickets"))
