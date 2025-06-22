import os
import re

from flask import flash, render_template, request, current_app
from flask.views import MethodView
from flask_login import login_user
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

from app.models import User, db
from app.utils import (
    UPLOAD_FOLDER,
    allowed_file,
    redirect_based_on_role,
    sanitise_html,
    log_audit_event,
)


class RegisterView(MethodView):
    def get(self):
        return render_template("register.html")

    def post(self):
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        role = request.form.get("role")
        profile_image = request.files.get("profile_image")

        # Check if the name contains numbers
        if any(char.isdigit() for char in name):
            current_app.logger.warning(
                "Registration validation error (name digits) from %s",
                request.remote_addr,
            )
            flash("Name cannot contain numbers.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the name is empty
        if not name.strip():
            current_app.logger.warning(
                "Registration validation error (empty name) from %s",
                request.remote_addr,
            )
            flash("Name cannot be empty.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Validate email format
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.fullmatch(email_regex, email):
            current_app.logger.warning(
                "Registration validation error (invalid email) from %s",
                request.remote_addr,
            )
            flash("Invalid email address.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            current_app.logger.warning(
                "Registration validation error (duplicate email) from %s",
                request.remote_addr,
            )
            flash("Email address already in use.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check password complexity
        if len(password) < 8:
            current_app.logger.warning(
                "Registration validation error (password length) from %s",
                request.remote_addr,
            )
            flash("Password must be at least 8 characters long.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char.isdigit() for char in password):
            current_app.logger.warning(
                "Registration validation error (password digit) from %s",
                request.remote_addr,
            )
            flash("Password must contain at least one number.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char.isupper() for char in password):
            current_app.logger.warning(
                "Registration validation error (password uppercase) from %s",
                request.remote_addr,
            )
            flash("Password must contain at least one uppercase letter.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char.islower() for char in password):
            current_app.logger.warning(
                "Registration validation error (password lowercase) from %s",
                request.remote_addr,
            )
            flash("Password must contain at least one lowercase letter.", "warning")
            return render_template("register.html", name=name, email=email, role=role)
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in password):
            current_app.logger.warning(
                "Registration validation error (password special char) from %s",
                request.remote_addr,
            )
            flash("Password must contain at least one special character.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Check if the role is valid
        valid_roles = {"admin", "support", "regular"}
        if role not in valid_roles:
            current_app.logger.warning(
                "Registration validation error (invalid role) from %s",
                request.remote_addr,
            )
            flash("Invalid role selected.", "warning")
            return render_template("register.html", name=name, email=email, role=role)

        # Sanitise inputs before saving
        name = sanitise_html(name)
        email = sanitise_html(email)

        # Create the new user
        new_user = User(
            name=name,  # type: ignore
            email=email,  # type: ignore
            role=role,  # type: ignore
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()  # Commit to generate the new_user.id

        # Handle profile image upload
        if profile_image and allowed_file(profile_image.filename):
            try:
                if profile_image.filename and "." in profile_image.filename:
                    file_ext = profile_image.filename.rsplit(".", 1)[1].lower()
                    filename = secure_filename(f"user_{new_user.id}.{file_ext}")
                    file_path = os.path.join(UPLOAD_FOLDER, filename)

                    # Ensure the upload folder exists
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)

                    # Save and resize the file
                    profile_image.save(file_path)
                    img = Image.open(file_path)
                    img = ImageOps.fit(img, (200, 200), Image.Resampling.LANCZOS)
                    img.save(file_path)

                    # Update DB with filename
                    new_user.profile_image = filename
                    db.session.commit()
                else:
                    current_app.logger.warning(
                        "Registration validation error (invalid filename) from %s",
                        request.remote_addr,
                    )
                    flash("Invalid profile image filename.", "warning")
            except Exception as e:
                current_app.logger.error(
                    "Image upload error from %s: %s", request.remote_addr, e
                )
                flash(f"An error occurred while uploading the image: {e}", "danger")

        # Log the new user in
        login_user(new_user)
        log_audit_event(new_user.id, "user registered")

        return redirect_based_on_role()
