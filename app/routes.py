from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Ticket, Comment, db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    print("Rendering index page")  # Debug information
    return render_template("index.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(f"Login attempt with Email: {email}, Password: {password}")  # Debug information
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User found: {user.email}")  # Debug information
            if user.password == password:
                print(f"Password match for user: {user.email}")  # Debug information
                login_user(user)
                return redirect(url_for("main.dashboard"))
            else:
                print(f"Password mismatch for user: {user.email}")  # Debug information
        else:
            print("No user found with that email")  # Debug information
        flash("Login failed. Check your email and password.")
    else:
        print("Rendering login page")  # Debug information
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already in use.")
            return redirect(url_for("main.register"))

        print(f"Registering new user with Name: {name}, Email: {
              email}, Role: {role}")  # Debug information
        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("main.dashboard"))
    else:
        print("Rendering register page")  # Debug information
    return render_template("register.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    print(f"Loading dashboard for user: {current_user.email}, Role: {current_user.role}")  # Debug information
    if current_user.role == "admin":
        tickets = Ticket.query.all()
        print("Admin user: loading all tickets")  # Debug information
    elif current_user.role == "support":
        tickets = Ticket.query.filter_by(assigned_to=current_user.id).all()
        print("Support user: loading assigned tickets")  # Debug information
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).all()
        print("Regular user: loading own tickets")  # Debug information
    return render_template("dashboard.html", tickets=tickets)


@bp.route("/create_ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")
        print(f"Creating ticket with Title: {title}, Description: {description}, Priority: {priority}")  # Debug information
        new_ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            status="open",
            user_id=current_user.id,
        )
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for("main.dashboard"))
    else:
        print("Rendering create ticket page")  # Debug information
    return render_template("create_ticket.html")


@bp.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_details(ticket_id):
    print(f"Loading ticket details for ticket ID: {ticket_id}")  # Debug information
    ticket = Ticket.query.get_or_404(ticket_id)
    if request.method == 'POST':
        if 'comment_text' in request.form:
            comment_text = request.form.get('comment_text')
            print(f"Adding comment to ticket ID: {ticket_id}, Comment: {comment_text}")  # Debug information
            new_comment = Comment(comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id)
            db.session.add(new_comment)
        if 'status' in request.form:
            status = request.form.get('status')
            if ticket.status != status:
                ticket.status = status
                # Add a comment about the status change
                status_comment_text = f"Status changed to {status}."
                status_comment = Comment(comment_text=status_comment_text, ticket_id=ticket.id, user_id=current_user.id)
                db.session.add(status_comment)
        if 'priority' in request.form and current_user.role == 'admin':
            priority = request.form.get('priority')
            if ticket.priority != priority:
                ticket.priority = priority
                # Add a comment about the priority change
                priority_comment_text = f"Priority changed to {priority}."
                priority_comment = Comment(comment_text=priority_comment_text, ticket_id=ticket.id, user_id=current_user.id)
                db.session.add(priority_comment)
        db.session.commit()
        return redirect(url_for('main.ticket_details', ticket_id=ticket_id))
    comments = Comment.query.filter_by(ticket_id=ticket.id).all()
    return render_template('ticket_details.html', ticket=ticket, comments=comments)


@bp.route("/logout")
@login_required
def logout():
    print(f"Logging out user: {current_user.email}")  # Debug information
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/unassigned_tickets", methods=["GET", "POST"])
@login_required
def unassigned_tickets():
    if current_user.role != "support" and current_user.role != "admin":
        flash("Only support staff and admins can view this page.")
        return redirect(url_for("main.dashboard"))

    unassigned_tickets = Ticket.query.filter_by(assigned_to=None).all()
    print(f"Unassigned tickets: {unassigned_tickets}")  # Debug information

    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        ticket = Ticket.query.get(ticket_id)
        if current_user.role == "support":
            ticket.assigned_to = current_user.id
            comment_text = f"Ticket assigned to {current_user.name}."
        elif current_user.role == "admin":
            assigned_to_id = request.form.get("assigned_to")
            ticket.assigned_to = assigned_to_id
            assignee = User.query.get(assigned_to_id)
            comment_text = f"Ticket assigned to {assignee.name}."
        db.session.commit()

        # Add a comment about the assignment
        new_comment = Comment(
            comment_text=comment_text, ticket_id=ticket.id, user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()

        flash("Ticket assigned successfully.")
        return redirect(url_for("main.unassigned_tickets"))

    support_staff = User.query.filter_by(role="support").all()
    return render_template(
        "unassigned_tickets.html",
        unassigned_tickets=unassigned_tickets,
        support_staff=support_staff,
    )


@bp.route("/assign_ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def assign_ticket(ticket_id):
    if current_user.role != "admin":
        flash("Only admins can assign tickets.")
        return redirect(url_for("main.dashboard"))

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

        flash("Ticket assigned successfully.")
        return redirect(url_for("main.dashboard"))

    return render_template(
        "assign_ticket.html", ticket=ticket, support_staff=support_staff
    )
