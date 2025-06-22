import os
import re

from flask import flash, redirect, render_template, request, url_for, current_app
from flask.views import MethodView
from flask_login import current_user, login_required
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

from app.models import User, db
from app.utils import (
    UPLOAD_FOLDER,
    allowed_file,
    is_safe_url,
    sanitise_html,
    log_audit_event,
)
from typing import Any, Callable, ClassVar


class UpdateProfileView(MethodView):
    decorators: ClassVar[list[Callable[[Any], Any]]] = [login_required]

    def get(self):
        next_url = request.args.get("next") or url_for("main.index")
        if not is_safe_url(next_url):
            next_url = url_for("main.index")
        return render_template(
            "update_profile.html", current_user=current_user, next_url=next_url
        )

    def post(self):
        next_url = request.form.get("next") or url_for("main.index")
        if not is_safe_url(next_url):
            next_url = url_for("main.index")

        # Get form data
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        file = request.files.get("profile_image")

        # Validate name
        if not name.strip():
            current_app.logger.warning(
                "Profile update validation error (empty name) for %s from %s",
                current_user.id,
                request.remote_addr,
            )
            flash("Name cannot be empty.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        if any(char.isdigit() for char in name):
            current_app.logger.warning(
                "Profile update validation error (name digits) for %s from %s",
                current_user.id,
                request.remote_addr,
            )
            flash("Name cannot contain numbers.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        # Validate email format
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            current_app.logger.warning(
                "Profile update validation error (invalid email) for %s from %s",
                current_user.id,
                request.remote_addr,
            )
            flash("Invalid email address.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        # Check if email is already in use by another user
        if User.query.filter(User.email == email, User.id != current_user.id).first():
            current_app.logger.warning(
                "Profile update validation error (duplicate email) for %s from %s",
                current_user.id,
                request.remote_addr,
            )
            flash("Email address already in use.", "warning")
            return render_template(
                "update_profile.html", current_user=current_user, next_url=next_url
            )

        # Update password if provided
        if password:
            if password != password_confirm:
                current_app.logger.warning(
                    "Profile update validation error (password mismatch) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash("Passwords do not match.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )

            # Password complexity checks
            if len(password) < 8:
                current_app.logger.warning(
                    "Profile update validation error (password length) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash("Password must be at least 8 characters long.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char.isdigit() for char in password):
                current_app.logger.warning(
                    "Profile update validation error (password digit) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash("Password must contain at least one number.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char.isupper() for char in password):
                current_app.logger.warning(
                    "Profile update validation error (password uppercase) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash("Password must contain at least one uppercase letter.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char.islower() for char in password):
                current_app.logger.warning(
                    "Profile update validation error (password lowercase) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash("Password must contain at least one lowercase letter.", "warning")
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )
            if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in password):
                current_app.logger.warning(
                    "Profile update validation error (password special char) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash(
                    "Password must contain at least one special character.", "warning"
                )
                return render_template(
                    "update_profile.html", current_user=current_user, next_url=next_url
                )

            # Set new password
            current_user.set_password(password)

        # Handle profile image upload
        if file and hasattr(file, "filename") and allowed_file(file.filename):
            try:
                filename_raw = file.filename
                if not filename_raw or "." not in filename_raw:
                    raise ValueError("Filename is missing or invalid.")

                # Generate a unique filename based on the user's ID
                file_ext = filename_raw.rsplit(".", 1)[1].lower()
                filename = secure_filename(f"user_{current_user.id}.{file_ext}")

                file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Ensure the upload folder exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                # Save the file
                file.save(file_path)

                # Resize/crop the image
                img = Image.open(file_path)
                img = ImageOps.fit(img, (200, 200), Image.Resampling.LANCZOS)
                img.save(file_path)

                current_user.profile_image = filename
                db.session.commit()

                flash("Profile image updated successfully!", "success")
            except Exception as e:
                flash(f"An error occurred while uploading the image: {e}", "danger")
        else:
            if file:
                current_app.logger.warning(
                    "Profile update validation error (invalid image) for %s from %s",
                    current_user.id,
                    request.remote_addr,
                )
                flash(
                    "Invalid file format. Only PNG, JPG, JPEG, and GIF are allowed.",
                    "warning",
                )

        # Sanitise inputs before saving
        sanitised_name = sanitise_html(name)
        sanitised_email = sanitise_html(email)

        # Update user profile and save to database
        current_user.name = sanitised_name
        current_user.email = sanitised_email
        db.session.commit()
        log_audit_event(current_user.id, "profile updated", "user", current_user.id)

        flash("Your profile has been updated.", "success")
        return redirect(next_url)
