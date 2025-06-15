from flask import render_template
from flask.views import MethodView
from flask_login import current_user, login_required

from app.models import Ticket
from typing import Any, Callable, ClassVar


class ActiveTicketsView(MethodView):
    decorators: ClassVar[list[Callable[[Any], Any]]] = [login_required]

    def get(self):
        tickets = Ticket.query.filter_by(user_id=current_user.id, status="open").all()
        return render_template("all_tickets.html", tickets=tickets, view="active")
