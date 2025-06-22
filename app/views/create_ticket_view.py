from datetime import datetime

from flask import flash, redirect, render_template, request, url_for, current_app
from flask.views import MethodView
from flask_login import current_user, login_required

from app.utils import is_safe_url, sanitise_html, log_audit_event
from typing import Any, Callable, ClassVar

from app.models import Ticket, User, db


class CreateTicketView(MethodView):
    decorators: ClassVar[list[Callable[[Any], Any]]] = [login_required]

    def get(self):
        referrer = request.args.get("referrer")
        if not referrer or not is_safe_url(referrer):
            referrer = url_for("main.all_tickets")

        all_users = []
        support_staff = []
        if current_user.role in ["admin", "support"]:
            all_users = User.query.all()
        if current_user.role == "admin":
            support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()

        # Pass an empty form_data dictionary to the template
        return render_template(
            "create_ticket.html",
            support_staff=support_staff,
            all_users=all_users,
            referrer=referrer,
            form_data={},  # Pass empty form_data for GET requests
        )

    def post(self):
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")
        status = None

        all_users = []
        support_staff = []
        if current_user.role in ["admin", "support"]:
            all_users = User.query.all()
        if current_user.role == "admin":
            support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()

        # Default status to 'open' if the user is not admin or support
        if current_user.role in ["admin", "support"]:
            status = request.form.get("status")
        else:
            status = "open"

        user_id = request.form.get("user_id")
        assigned_to_id = request.form.get("assigned_to")

        if not user_id:
            user_id = current_user.id

        safe_referrer = (
            request.referrer
            if request.referrer and is_safe_url(request.referrer)
            else url_for("main.all_tickets")
        )

        # Validation: Title should not be empty, not only numbers, length should be between 5-100
        if not title or title.isdigit() or len(title) < 5 or len(title) > 100:
            current_app.logger.warning(
                "Ticket validation error (title) from %s", request.remote_addr
            )
            flash(
                "Title must contain non-numeric characters, be at least 5 characters long, and not exceed 100 characters.",
                "warning",
            )
            return render_template(
                "create_ticket.html",
                support_staff=support_staff,
                all_users=all_users,
                referrer=safe_referrer,
                form_data=request.form,  # Pass the form data back on validation failure
            )

        # Validation: Description should not be empty, not only numbers, length should be between 10-1000
        if (
            not description
            or description.isdigit()
            or len(description) < 10
            or len(description) > 1000
        ):
            current_app.logger.warning(
                "Ticket validation error (description) from %s", request.remote_addr
            )
            flash(
                "Description must contain non-numeric characters, be at least 10 characters long, and not exceed 1000 characters.",
                "warning",
            )
            return render_template(
                "create_ticket.html",
                support_staff=support_staff,
                all_users=all_users,
                referrer=safe_referrer,
                form_data=request.form,  # Pass the form data back on validation failure
            )

        # Validation: Priority must be one of 'low', 'medium', or 'high'
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            current_app.logger.warning(
                "Ticket validation error (priority) from %s", request.remote_addr
            )
            flash(
                "Invalid priority value. Choose either 'low', 'medium', or 'high'.",
                "warning",
            )
            return render_template(
                "create_ticket.html",
                support_staff=support_staff,
                all_users=all_users,
                referrer=safe_referrer,
                form_data=request.form,  # Pass the form data back on validation failure
            )

        # Validation: If 'assigned_to' exists, it must be a valid user
        if current_user.role == "admin" and assigned_to_id:
            assigned_user = User.query.get(assigned_to_id)
            if not assigned_user:
                current_app.logger.warning(
                    "Ticket validation error (invalid assignee) from %s",
                    request.remote_addr,
                )
                flash("Invalid user selected for assignment.", "warning")
                return render_template(
                    "create_ticket.html",
                    support_staff=support_staff,
                    all_users=all_users,
                    referrer=safe_referrer,
                    form_data=request.form,  # Pass the form data back on validation failure
                )

        # Prevent duplicate tickets based on title and creation time (within 1 minute)
        recent_ticket = (
            Ticket.query.filter_by(user_id=current_user.id, title=title)
            .order_by(Ticket.created_at.desc())
            .first()
        )
        if (
            recent_ticket
            and (datetime.utcnow() - recent_ticket.created_at).total_seconds() < 60
        ):
            current_app.logger.warning(
                "Ticket validation error (duplicate) from %s", request.remote_addr
            )
            flash(
                "A similar ticket was created within the last minute. Please wait before creating a new one.",
                "warning",
            )
            return render_template(
                "create_ticket.html",
                support_staff=support_staff,
                all_users=all_users,
                referrer=safe_referrer,
                form_data=request.form,  # Pass the form data back on validation failure
            )

        # Sanitise the title and description to prevent XSS
        title = sanitise_html(title)
        description = sanitise_html(description)

        # Create new ticket and save to database
        new_ticket = Ticket(
            title=title,  # type: ignore
            description=description,  # type: ignore
            priority=priority,  # type: ignore
            status=status,  # type: ignore
            user_id=user_id,  # type: ignore
        )

        if current_user.role == "admin" and assigned_to_id:
            new_ticket.assigned_to = assigned_to_id

        db.session.add(new_ticket)
        db.session.commit()
        log_audit_event(current_user.id, "ticket created", "ticket", new_ticket.id)

        referrer = request.form.get("referrer")
        if not referrer or not is_safe_url(referrer):
            referrer = url_for("main.all_tickets")
        flash("Ticket created successfully!", "success")
        return redirect(referrer)
