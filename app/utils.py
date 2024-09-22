from urllib.parse import urljoin, urlparse

from flask import redirect, request, url_for
from flask_login import current_user

from app.models import Ticket

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
UPLOAD_FOLDER = "app/static/uploads/profile_images"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_safe_url(target):
    """
    Check if the target URL is safe by ensuring it's a local URL.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def redirect_based_on_role():
    """
    Redirects the user to a different page based on their role.
    """
    if current_user.role == "admin":
        return redirect(url_for("main.all_tickets"))
    elif current_user.role == "support":
        return redirect(url_for("main.assigned_tickets"))
    else:
        return redirect(url_for("main.all_tickets"))


def inject_open_tickets_count():
    open_tickets_count = Ticket.query.filter(
        Ticket.status.in_(["open", "in-progress"])
    ).count()

    # Determine the badge class based on the count
    if open_tickets_count > 10:
        badge_class = "badge-active-tickets-high"  # Red
    elif open_tickets_count > 5:
        badge_class = "badge-active-tickets-medium"  # Yellow
    elif open_tickets_count > 0:
        badge_class = "badge-active-tickets-low"  # Green
    else:
        badge_class = "badge-active-tickets-info"  # Blue or default color

    return {"open_tickets_count": open_tickets_count, "badge_class": badge_class}
