import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Ticket, Comment, db
from urllib.parse import urlparse, urljoin
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, ImageDraw
import os

bp = Blueprint("main", __name__)

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


@bp.route("/")
@bp.route("/index")
def index():
    """
    Renders the index page or redirects to a role-based page if the user is authenticated.

    Returns
    -------
    str
        Rendered template for the index page or a redirect to a role-based page.
    """
    print(f"User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        return redirect_based_on_role()
    return render_template("index.html", title="Welcome")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles the login process. If the user is authenticated, redirects based on role.
    On POST, attempts to log the user in with the provided credentials.

    Returns
    -------
    str
        Rendered template for the login page or a redirect to a role-based page.
    """
    if current_user.is_authenticated:
        return redirect_based_on_role()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(f"Login attempt with Email: {email}, Password: {password}")
        user = User.query.filter_by(email=email).first()

        if user:
            print(f"User found: {user.email}")
            if user.check_password(
                password
            ):  # Use the check_password method from the User model
                print(f"Password match for user: {user.email}")
                login_user(user)
                print(f"User logged in: {current_user.is_authenticated}")

                # Redirect based on the user's role
                return redirect_based_on_role()
            else:
                flash(f"Password mismatch for user: {user.email}")
        else:
            flash("No user found with that email", "warning")
        # flash("Login failed. Check your email and password.", "warning")
    else:
        print("Rendering login page")

    return render_template("login.html")


def redirect_based_on_role():
    """
    Redirects the user to a different page based on their role.

    Returns
    -------
    Response
        A redirect response to the appropriate page for the user's role.
    """
    if current_user.role == "admin":
        return redirect(url_for("main.all_tickets"))
    elif current_user.role == "support":
        return redirect(url_for("main.assigned_tickets"))
    else:
        return redirect(url_for("main.all_tickets"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles the user registration process. Validates input, checks for existing users,
    and creates a new user if valid.

    Returns
    -------
    str
        Rendered template for the registration page or a redirect to the all_tickets page.
    """
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        profile_image = request.files.get("profile_image")

        # Check if the name contains numbers
        if any(char.isdigit() for char in name):
            flash("Name cannot contain numbers.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the name is empty
        if not name.strip():
            flash("Name cannot be empty.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Validate email format
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            flash("Invalid email address.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already in use.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check password complexity
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char.isdigit() for char in password):
            flash("Password must contain at least one number.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char.isupper() for char in password):
            flash("Password must contain at least one uppercase letter.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char.islower() for char in password):
            flash("Password must contain at least one lowercase letter.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in password):
            flash("Password must contain at least one special character.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the role is valid
        valid_roles = {"admin", "support", "regular"}
        if role not in valid_roles:
            flash("Invalid role selected.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Create the new user (commit first to generate the ID)
        new_user = User(
            name=name,
            email=email,
            role=role,
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()  # Commit to generate the new_user.id

        # Handle profile image upload
        if profile_image and allowed_file(profile_image.filename):
            try:
                # Generate a unique filename based on the new user's ID and the file extension
                file_ext = profile_image.filename.rsplit(".", 1)[1].lower()
                filename = f"user_{new_user.id}.{file_ext}"  # Use new_user.id

                file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Ensure the upload folder exists
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                # Save the file
                profile_image.save(file_path)

                # Optionally resize or crop the image
                img = Image.open(file_path)
                img = ImageOps.fit(img, (200, 200), Image.Resampling.LANCZOS)
                img.save(file_path)

                # Update the new user's profile image field in the database
                new_user.profile_image = filename
                db.session.commit()

            except Exception as e:
                flash(f"An error occurred while uploading the image: {e}", "danger")

        # Log the new user in
        login_user(new_user)

        return redirect_based_on_role()

    return render_template("register.html")


@bp.route("/all_tickets")
def all_tickets():
    """
    Renders a page displaying all tickets.

    Returns
    -------
    str
        Rendered template for the all_tickets page with all tickets.
    """
    if current_user.role == "admin" or current_user.role == "support":
        tickets = Ticket.query.all()
        view = "all"

    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).all()
        view = "active"

    return render_template(
        "all_tickets.html", tickets=tickets, current_user=current_user, view=view
    )


from flask import flash
from datetime import datetime


@bp.route("/create_ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    """
    Handles the creation of a new ticket. On POST, validates and saves the new ticket.

    Returns
    -------
    str
        Rendered template for the create_ticket page or a redirect to the previous page.
    """
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")
        status = None

        # Default status to 'open' if the user is not admin or support
        if current_user.role in ["admin", "support"]:
            status = request.form.get("status")
        else:
            status = "open"

        user_id = request.form.get("user_id")  # Get user_id from the form
        assigned_to_id = request.form.get(
            "assigned_to"
        )  # Get assigned_to value from the form

        # If no user is selected, default to the current user
        if not user_id:
            user_id = current_user.id

        # Validation: Title should not be empty, not only numbers, length should be between 5-100
        if not title or title.isdigit() or len(title) < 5 or len(title) > 100:
            flash(
                "Title must contain non-numeric characters, be at least 5 characters long, and not exceed 100 characters.",
                "warning",
            )
            return redirect(request.referrer or url_for("main.create_ticket"))

        # Validation: Description should not be empty, not only numbers, length should be between 10-1000
        if (
            not description
            or description.isdigit()
            or len(description) < 10
            or len(description) > 1000
        ):
            flash(
                "Description must contain non-numeric characters, be at least 10 characters long, and not exceed 1000 characters.",
                "warning",
            )
            return redirect(request.referrer or url_for("main.create_ticket"))

        # Validation: Priority must be one of 'low', 'medium', or 'high'
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            flash(
                "Invalid priority value. Choose either 'low', 'medium', or 'high'.",
                "warning",
            )
            return redirect(request.referrer or url_for("main.create_ticket"))

        # Validation: If 'assigned_to' exists, it must be a valid user
        if current_user.role == "admin" and assigned_to_id:
            assigned_user = User.query.get(assigned_to_id)
            if not assigned_user:
                flash("Invalid user selected for assignment.", "warning")
                return redirect(request.referrer or url_for("main.create_ticket"))

        # Prevent Duplicate Tickets based on title and creation time (within 1 minute)
        recent_ticket = (
            Ticket.query.filter_by(user_id=current_user.id, title=title)
            .order_by(Ticket.created_at.desc())
            .first()
        )
        if (
            recent_ticket
            and (datetime.utcnow() - recent_ticket.created_at).total_seconds() < 60
        ):  # 1 minute
            flash(
                "A similar ticket was created within the last minute. Please wait before creating a new one.",
                "warning",
            )
            return redirect(request.referrer or url_for("main.create_ticket"))

        # Create new ticket
        new_ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            status=status,
            user_id=user_id,
        )

        # If the user is an admin and has selected a user to assign the ticket to
        if current_user.role == "admin" and assigned_to_id:
            new_ticket.assigned_to = assigned_to_id

        # Save the new ticket in the database
        db.session.add(new_ticket)
        db.session.commit()

        # Get the referrer URL from the form and redirect to it
        referrer = request.form.get("referrer")
        flash("Ticket created successfully!", "success")
        return redirect(referrer or url_for("main.all_tickets"))

    else:
        print("Rendering create ticket page")

    # Store the referrer URL passed as a query parameter (GET request)
    referrer = request.args.get("referrer", url_for("main.all_tickets"))

    # If the user is an admin or support staff, query the list of users and support staff
    all_users = []
    support_staff = []
    if current_user.role in ["admin", "support"]:
        all_users = User.query.all()
    if current_user.role == "admin":
        support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()

    return render_template(
        "create_ticket.html",
        support_staff=support_staff,
        all_users=all_users,
        referrer=referrer,
    )


@bp.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def ticket_details(ticket_id):
    """
    Displays the details of a specific ticket. Allows for comments and status/priority updates.

    Parameters
    ----------
    ticket_id : int
        The ID of the ticket to display.

    Returns
    -------
    str
        Rendered template for the ticket_details page.
    """
    print(f"Loading ticket details for ticket ID: {ticket_id}")
    ticket = Ticket.query.get_or_404(ticket_id)

    if request.method == "POST":
        if "comment_text" in request.form:
            comment_text = request.form.get("comment_text")
            print(f"Adding comment to ticket ID: {ticket_id}, Comment: {comment_text}")
            new_comment = Comment(
                comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
            )
            db.session.add(new_comment)

        if "status" in request.form:
            status = request.form.get("status")
            if ticket.status != status:
                ticket.status = status
                # Add a comment about the status change
                status_comment_text = f"Status changed to {status}."
                status_comment = Comment(
                    comment_text=status_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(status_comment)

        if "priority" in request.form and current_user.role == "admin":
            priority = request.form.get("priority")
            if ticket.priority != priority:
                ticket.priority = priority
                # Add a comment about the priority change
                priority_comment_text = f"Priority changed to {priority}."
                priority_comment = Comment(
                    comment_text=priority_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(priority_comment)

        if "assignee" in request.form and current_user.role == "admin":
            new_assignee_id = request.form.get("assignee")
            if ticket.assigned_to != new_assignee_id:
                ticket.assigned_to = new_assignee_id
                # Add a comment about the assignee change
                assignee_comment_text = (
                    f"Assignee changed to {User.query.get(new_assignee_id).name}."
                )
                assignee_comment = Comment(
                    comment_text=assignee_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(assignee_comment)

        db.session.commit()
        return redirect(url_for("main.ticket_details", ticket_id=ticket_id))

    comments = Comment.query.filter_by(ticket_id=ticket.id).all()

    # Fetch only users with the role 'admin' or 'support' for the assignee dropdown
    users = User.query.filter(User.role.in_(["admin", "support"])).all()

    return render_template(
        "ticket_details.html", ticket=ticket, comments=comments, users=users
    )


@bp.route("/logout")
@login_required
def logout():
    """
    Logs the current user out and redirects to the index page.

    Returns
    -------
    Response
        A redirect response to the index page.
    """
    print(f"Logging out user: {current_user.email}")
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/unassigned_tickets", methods=["GET", "POST"])
@login_required
def unassigned_tickets():
    if current_user.role != "support" and current_user.role != "admin":
        flash("Only support staff and admins can view this page.", "warning")
        return redirect(url_for("main.all_tickets"))

    unassigned_tickets = Ticket.query.filter_by(assigned_to=None).all()
    print(f"Unassigned tickets: {unassigned_tickets}")

    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        ticket = Ticket.query.get(ticket_id)

        if current_user.role == "support":
            ticket.assigned_to = current_user.id
            comment_text = f"Ticket assigned to {current_user.name}."
        elif current_user.role == "admin":
            assigned_to_id = request.form.get("assigned_to")
            print(f"Assigned to ID: {assigned_to_id}")  # Debugging line
            if not assigned_to_id:
                flash("No assignee selected.", "warning")
                return redirect(url_for("main.unassigned_tickets"))

            assignee = User.query.get(assigned_to_id)

            if assignee is None:
                flash("The selected user does not exist.", "warning")
                return redirect(url_for("main.unassigned_tickets"))

            ticket.assigned_to = assigned_to_id
            comment_text = f"Ticket assigned to {assignee.name}."

        db.session.commit()

        new_comment = Comment(
            comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()

        flash("Ticket assigned successfully.", "success")
        return redirect(url_for("main.unassigned_tickets"))

    support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()
    return render_template(
        "unassigned_tickets.html",
        unassigned_tickets=unassigned_tickets,
        support_staff=support_staff,
        view="unassigned",
    )


@bp.route("/assign_ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def assign_ticket(ticket_id):
    """
    Allows admins to assign a ticket to a support staff member.

    Parameters
    ----------
    ticket_id : int
        The ID of the ticket to assign.

    Returns
    -------
    str
        Rendered template for the assign_ticket page or a redirect to the all_tickets page.
    """
    if current_user.role != "admin":
        flash("Only admins can assign tickets.", "warning")
        return redirect(url_for("main.all_tickets"))

    ticket = Ticket.query.get_or_404(ticket_id)
    support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()

    if request.method == "POST":
        assigned_to_id = request.form.get("assigned_to")
        ticket.assigned_to = assigned_to_id
        db.session.commit()

        # Add a comment about the assignment
        assignee = User.query.get(assigned_to_id)
        comment_text = f"Ticket assigned to {assignee.name}."
        new_comment = Comment(
            comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()

        flash("Ticket assigned successfully.", "success")
        return redirect(url_for("main.all_tickets"))

    return render_template(
        "assign_ticket.html", ticket=ticket, support_staff=support_staff
    )


@bp.route("/delete_ticket/<int:ticket_id>", methods=["POST"])
@login_required
def delete_ticket(ticket_id):
    """
    Allows admins to delete a specific ticket.

    Parameters
    ----------
    ticket_id : int
        The ID of the ticket to delete.

    Returns
    -------
    Response
        A redirect response to the all_tickets page after deleting the ticket.
    """
    ticket = Ticket.query.get_or_404(ticket_id)

    if current_user.role != "admin":
        flash("You do not have permission to delete this ticket.", "danger")
        return redirect(url_for("main.ticket_details", ticket_id=ticket_id))

    db.session.delete(ticket)
    db.session.commit()
    flash("Ticket has been deleted successfully.", "success")
    return redirect(url_for("main.all_tickets"))


@bp.route("/update_status/<int:ticket_id>", methods=["POST"])
@login_required
def update_status(ticket_id):
    """
    Allows support staff or admins to update the status of a specific ticket.

    Parameters
    ----------
    ticket_id : int
        The ID of the ticket to update.

    Returns
    -------
    Response
        A redirect response to the ticket details page after updating the status.
    """
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and current_user.role != "support":
        flash("You do not have permission to update the status.", "warning")
        return redirect(url_for("main.ticket_details", ticket_id=ticket.id))

    status = request.form.get("status")
    if status:
        ticket.status = status
        db.session.commit()
        flash("Status has been updated.", "success")
    return redirect(url_for("main.ticket_details", ticket_id=ticket.id))


@bp.route("/assigned_tickets", methods=["GET", "POST"])
@login_required
def assigned_tickets():
    """
    Displays tickets assigned to support staff or admins.

    Returns
    -------
    str
        Rendered template for the assigned_tickets page.
    """
    if current_user.role != "support" and current_user.role != "admin":
        flash("Only support staff and admins can view this page.", "warning")
        return redirect(url_for("main.all_tickets"))

    if current_user.role == "support":
        # Support staff only see tickets assigned to themselves
        assigned_tickets = (
            Ticket.query.filter_by(assigned_to=current_user.id)
            .filter(Ticket.status != "closed")
            .all()
        )
    else:
        # Admins see all assigned tickets
        assigned_tickets = (
            Ticket.query.filter(Ticket.assigned_to.isnot(None))
            .filter(Ticket.status != "closed")
            .all()
        )

    support_staff = User.query.filter(User.role.in_(["admin", "support"])).all()
    return render_template(
        "assigned_tickets.html",
        assigned_tickets=assigned_tickets,  # Ensure this matches the template variable
        support_staff=support_staff,
        view="assigned",  # Pass 'view' as 'assigned' to the template
    )


@bp.context_processor
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


@bp.route("/update_priority/<int:ticket_id>", methods=["POST"])
@login_required
def update_priority(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin":
        flash("You do not have permission to update the priority.", "warning")
        return redirect(url_for("main.ticket_details", ticket_id=ticket.id))

    priority = request.form.get("priority")
    if priority:
        ticket.priority = priority
        db.session.commit()
        flash("Priority has been updated.", "success")
    return redirect(url_for("main.ticket_details", ticket_id=ticket.id))


@bp.route("/update_assignee/<int:ticket_id>", methods=["POST"])
@login_required
def update_assignee(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin":
        flash("You do not have permission to update the assignee.", "warning")
        return redirect(url_for("main.ticket_details", ticket_id=ticket.id))

    assignee_id = request.form.get("assignee")
    if assignee_id:
        ticket.assigned_to = assignee_id
        db.session.commit()
        flash("Assignee has been updated.", "success")
    return redirect(url_for("main.ticket_details", ticket_id=ticket.id))


@bp.route("/update_ticket_status/<int:ticket_id>", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    """
    Allows support staff or admins to update the status of a specific ticket from the ticket list view.

    Parameters
    ----------
    ticket_id : int
        The ID of the ticket to update.

    Returns
    -------
    Response
        A redirect response to the all_tickets page after updating the status.
    """
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role not in ["admin", "support"]:
        flash("You do not have permission to update the status.", "warning")
        return redirect(url_for("main.all_tickets"))

    status = request.form.get("status")
    if status:
        ticket.status = status
        db.session.commit()
        flash("Ticket status has been updated.", "success")
    return redirect(url_for("main.all_tickets"))


@bp.route("/closed_tickets", methods=["GET"])
@login_required
def closed_tickets():
    """
    Displays closed tickets based on the user's role.

    Returns
    -------
    str
        Rendered template for the closed_tickets page.
    """
    if current_user.role == "admin":
        # Admins can see all closed tickets
        closed_tickets = Ticket.query.filter_by(status="closed").all()
    elif current_user.role == "support":
        # Support staff see all closed tickets assigned to them
        closed_tickets = Ticket.query.filter_by(
            status="closed", assigned_to=current_user.id
        ).all()
    else:
        # Regular users see all closed tickets they created
        closed_tickets = Ticket.query.filter_by(
            status="closed", user_id=current_user.id
        ).all()

    return render_template(
        "closed_tickets.html", closed_tickets=closed_tickets, view="closed"
    )


@bp.route("/active_tickets")
@login_required
def active_tickets():
    # Filtering tickets by the current user and by active status
    tickets = Ticket.query.filter_by(user_id=current_user.id, status="open").all()
    return render_template("all_tickets.html", tickets=tickets, view="active")


@bp.route("/ticket/<int:ticket_id>/readonly", methods=["GET"])
@login_required
def ticket_details_readonly(ticket_id):
    """
    Displays the read-only details of a specific ticket without any interactivity.
    """
    print(f"Loading read-only ticket details for ticket ID: {ticket_id}")
    ticket = Ticket.query.get_or_404(ticket_id)
    comments = Comment.query.filter_by(ticket_id=ticket.id).all()

    return render_template(
        "ticket_details_readonly.html", ticket=ticket, comments=comments
    )


@bp.route("/update_profile", methods=["GET", "POST"])
@login_required
def update_profile():
    """
    Allows the user to update their profile information, including profile image.
    """
    # Get the 'next' parameter from the query string or form data
    next_url = (
        request.args.get("next") or request.form.get("next") or url_for("main.index")
    )

    # Ensure the next_url is safe
    if not is_safe_url(next_url):
        next_url = url_for("main.index")

    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        file = request.files.get("profile_image")

        # Validate name
        if not name.strip():
            flash("Name cannot be empty.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        if any(char.isdigit() for char in name):
            flash("Name cannot contain numbers.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        # Validate email format
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            flash("Invalid email address.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        # Check if email is already in use by another user
        if User.query.filter(User.email == email, User.id != current_user.id).first():
            flash("Email address already in use.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        # Update password if provided
        if password:
            if password != password_confirm:
                flash("Passwords do not match.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )

            # Password complexity checks
            if len(password) < 8:
                flash("Password must be at least 8 characters long.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char.isdigit() for char in password):
                flash("Password must contain at least one number.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char.isupper() for char in password):
                flash("Password must contain at least one uppercase letter.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char.islower() for char in password):
                flash("Password must contain at least one lowercase letter.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in password):
                flash(
                    "Password must contain at least one special character.", "warning"
                )
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )

            # Set new password
            current_user.set_password(password)

        # Handle profile image upload
        if file and allowed_file(file.filename):
            try:
                # Generate a unique filename based on the user's ID
                file_ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"user_{current_user.id}.{file_ext}"

                file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Ensure the upload folder exists
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                # Save the file
                file.save(file_path)

                # Optionally resize or crop the image
                img = Image.open(file_path)
                img = ImageOps.fit(img, (200, 200), Image.Resampling.LANCZOS)
                img.save(file_path)

                # Update the user's profile image in the database
                current_user.profile_image = filename
                db.session.commit()  # Save the new filename in the database

                flash("Profile image updated successfully!", "success")
            except Exception as e:
                flash(f"An error occurred while uploading the image: {e}", "danger")
        else:
            if file:
                flash(
                    "Invalid file format. Only PNG, JPG, JPEG, and GIF are allowed.",
                    "warning",
                )

        # Update name and email
        current_user.name = name
        current_user.email = email
        db.session.commit()

        flash("Your profile has been updated.", "success")
        return redirect(next_url)

    return render_template(
        "update_profile.html", current_user=current_user, next_url=next_url
    )
