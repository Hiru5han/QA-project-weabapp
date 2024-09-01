import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Ticket, Comment, db

bp = Blueprint("main", __name__)


@bp.route('/')
@bp.route('/index')
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
    return render_template('index.html', title='Welcome')


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
            if check_password_hash(user.password, password):
                print(f"Password match for user: {user.email}")
                login_user(user)
                print(f"User logged in: {current_user.is_authenticated}")
                
                # Redirect based on the user's role
                return redirect_based_on_role()
            else:
                print(f"Password mismatch for user: {user.email}")
        else:
            print("No user found with that email")
        flash("Login failed. Check your email and password.", "warning")
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
    if current_user.role == 'admin':
        return redirect(url_for('main.all_tickets'))
    elif current_user.role == 'support':
        return redirect(url_for('main.assigned_tickets'))
    else:
        return redirect(url_for('main.all_tickets'))

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

        # Check if the name contains numbers
        if any(char.isdigit() for char in name):
            flash("Name cannot contain numbers.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the name is empty
        if not name.strip():
            flash("Name cannot be empty.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the email format is valid
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            flash("Invalid email address.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already in use.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the password meets complexity requirements
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

        print(f"Registering new user with Name: {name}, Email: {email}, Role: {role}")
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method="pbkdf2:sha256"),
            role=role,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect_based_on_role()
    else:
        print("Rendering register page")
    return render_template("register.html")


@bp.route('/all_tickets')
def all_tickets():
    """
    Renders a page displaying all tickets.

    Returns
    -------
    str
        Rendered template for the all_tickets page with all tickets.
    """
    tickets = Ticket.query.all()  # or your logic to get all tickets

    return render_template('all_tickets.html', tickets=tickets, view='all')


@bp.route("/create_ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    """
    Handles the creation of a new ticket. On POST, validates and saves the new ticket.

    Returns
    -------
    str
        Rendered template for the create_ticket page or a redirect to the all_tickets page.
    """
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")
        
        # Default status to 'open' if the user is not admin or support
        if current_user.role in ['admin', 'support']:
            status = request.form.get("status")
        else:
            status = "open"

        assigned_to_id = request.form.get("assigned_to")  # Get assigned_to value from the form

        print(
            f"Creating ticket with Title: {title}, Description: {description}, Priority: {priority}, Status: {status}"
        )

        new_ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            status=status,
            user_id=current_user.id,
        )

        # If the user is an admin and has selected a user to assign the ticket to
        if current_user.role == 'admin' and assigned_to_id:
            new_ticket.assigned_to = assigned_to_id

        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for("main.all_tickets"))

    else:
        print("Rendering create ticket page")

    # If the user is an admin, query the list of support staff
    support_staff = []
    if current_user.role == 'admin':
        support_staff = User.query.filter_by(role='support').all()

    return render_template("create_ticket.html", support_staff=support_staff)


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
                assignee_comment_text = f"Assignee changed to {User.query.get(new_assignee_id).name}."
                assignee_comment = Comment(
                    comment_text=assignee_comment_text,
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                )
                db.session.add(assignee_comment)

        db.session.commit()
        return redirect(url_for("main.ticket_details", ticket_id=ticket_id))
    
    comments = Comment.query.filter_by(ticket_id=ticket.id).all()
    users = User.query.all()  # Fetch all users for the assignee dropdown
    return render_template("ticket_details.html", ticket=ticket, comments=comments, users=users)


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
                flash("No assignee selected.", "error")
                return redirect(url_for("main.unassigned_tickets"))
                
            assignee = User.query.get(assigned_to_id)
            
            if assignee is None:
                flash("The selected user does not exist.", "error")
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

    support_staff = User.query.filter_by(role="support").all()
    return render_template(
        "unassigned_tickets.html",
        unassigned_tickets=unassigned_tickets,
        support_staff=support_staff,
        view='unassigned'
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
    support_staff = User.query.filter_by(role="support").all()

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
    
    if current_user.role != 'admin':
        flash('You do not have permission to delete this ticket.', 'danger')
        return redirect(url_for('main.ticket_details', ticket_id=ticket_id))
    
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket has been deleted successfully.', 'success')
    return redirect(url_for('main.all_tickets'))


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
        assigned_tickets = Ticket.query.filter_by(assigned_to=current_user.id).all()
    else:
        # Admins see all assigned tickets
        assigned_tickets = Ticket.query.filter(Ticket.assigned_to.isnot(None)).all()

    support_staff = User.query.filter_by(role="support").all()
    return render_template(
        "assigned_tickets.html",
        assigned_tickets=assigned_tickets,
        support_staff=support_staff,
        view='assigned'  # Pass 'view' as 'assigned' to the template
    )

@bp.context_processor
def inject_open_tickets_count():
    open_tickets_count = Ticket.query.filter(Ticket.status.in_(['open', 'in progress'])).count()
    
    # Determine the badge class based on the count
    if open_tickets_count > 10:
        badge_class = "badge-active-tickets-high"  # Red
    elif open_tickets_count > 5:
        badge_class = "badge-active-tickets-medium"  # Yellow
    elif open_tickets_count > 0:
        badge_class = "badge-active-tickets-low"  # Green
    else:
        badge_class = "badge-active-tickets-info"  # Blue or default color

    return {
        'open_tickets_count': open_tickets_count,
        'badge_class': badge_class
    }

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
