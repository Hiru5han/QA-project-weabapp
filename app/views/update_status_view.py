from flask import flash, redirect, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket, db


class UpdateStatusView(MethodView):
    decorators = [login_required]

    def post(self, ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if current_user.role not in ["admin", "support"]:
            flash("You do not have permission to update the status.", "warning")
            return redirect(url_for("main.ticket_details", ticket_id=ticket.id))

        status = request.form.get("status")
        if status:
            ticket.status = status
            db.session.commit()
            flash("Status has been updated.", "success")
        return redirect(url_for("main.ticket_details", ticket_id=ticket.id))
