from flask import Blueprint
from flask_login import LoginManager, login_manager

from app.models import User
from app.utils import inject_open_tickets_count
from app.views.active_tickets_view import ActiveTicketsView
from app.views.all_tickets_view import AllTicketsView
from app.views.assign_ticket_view import AssignTicketView
from app.views.assigned_tickets_view import AssignedTicketsView
from app.views.closed_tickets_view import ClosedTicketsView
from app.views.create_ticket_view import CreateTicketView
from app.views.delete_ticket_view import DeleteTicketView
from app.views.index_view import IndexView
from app.views.login_view import LoginView
from app.views.logout_view import LogoutView
from app.views.register_view import RegisterView
from app.views.ticket_details_readonly_view import TicketDetailsReadonlyView
from app.views.ticket_details_view import TicketDetailsView
from app.views.unassigned_tickets_view import UnassignedTicketsView
from app.views.update_profile_view import UpdateProfileView
from app.views.update_status_view import UpdateStatusView

bp = Blueprint("main", __name__)

# Register class-based views with the blueprint
bp.add_url_rule("/", view_func=IndexView.as_view("home"))
bp.add_url_rule("/index", view_func=IndexView.as_view("index"))
bp.add_url_rule("/login", view_func=LoginView.as_view("login"), methods=["GET", "POST"])
bp.add_url_rule(
    "/register", view_func=RegisterView.as_view("register"), methods=["GET", "POST"]
)
bp.add_url_rule("/logout", view_func=LogoutView.as_view("logout"))
bp.add_url_rule("/all_tickets", view_func=AllTicketsView.as_view("all_tickets"))
bp.add_url_rule(
    "/create_ticket",
    view_func=CreateTicketView.as_view("create_ticket"),
    methods=["GET", "POST"],
)
bp.add_url_rule(
    "/ticket/<int:ticket_id>",
    view_func=TicketDetailsView.as_view("ticket_details"),
    methods=["GET", "POST"],
)
bp.add_url_rule(
    "/ticket/<int:ticket_id>/readonly",
    view_func=TicketDetailsReadonlyView.as_view("ticket_details_readonly"),
    methods=["GET"],
)
bp.add_url_rule(
    "/unassigned_tickets",
    view_func=UnassignedTicketsView.as_view("unassigned_tickets"),
    methods=["GET", "POST"],
)
bp.add_url_rule(
    "/assign_ticket/<int:ticket_id>",
    view_func=AssignTicketView.as_view("assign_ticket"),
    methods=["GET", "POST"],
)
bp.add_url_rule(
    "/delete_ticket/<int:ticket_id>",
    view_func=DeleteTicketView.as_view("delete_ticket"),
    methods=["POST"],
)
bp.add_url_rule(
    "/update_status/<int:ticket_id>",
    view_func=UpdateStatusView.as_view("update_status"),
    methods=["POST"],
)
bp.add_url_rule(
    "/assigned_tickets", view_func=AssignedTicketsView.as_view("assigned_tickets")
)
bp.add_url_rule(
    "/closed_tickets", view_func=ClosedTicketsView.as_view("closed_tickets")
)
bp.add_url_rule(
    "/active_tickets", view_func=ActiveTicketsView.as_view("active_tickets")
)
bp.add_url_rule(
    "/update_profile",
    view_func=UpdateProfileView.as_view("update_profile"),
    methods=["GET", "POST"],
)

login_manager = LoginManager()
login_manager.login_view = "main.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.context_processor
def base_context():
    return inject_open_tickets_count()
