from flask import flash, redirect, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket, db
from app.utils import log_audit_event
from typing import Any, Callable, ClassVar


class UpdateStatusView(MethodView):
    decorators: ClassVar[list[Callable[[Any], Any]]] = [login_required]

    def post(self, ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if current_user.role not in ["admin", "support"]:
            flash("You do not have permission to update the status.", "warning")
            return redirect(url_for("main.ticket_details", ticket_id=ticket.id))

        status = request.form.get("status")
        if status:
            ticket.status = status
            db.session.commit()
            log_audit_event(current_user.id, "status updated", "ticket", ticket.id, status)
            flash("Status has been updated.", "success")
        return redirect(url_for("main.ticket_details", ticket_id=ticket.id))
