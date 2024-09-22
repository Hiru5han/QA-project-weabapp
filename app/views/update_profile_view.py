import os
import re

from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from PIL import Image, ImageOps

from app.models import User, db
from app.utils import UPLOAD_FOLDER, allowed_file, is_safe_url


class UpdateProfileView(MethodView):
    decorators = [login_required]

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

        # Update user profile and save to database
        current_user.name = name
        current_user.email = email
        db.session.commit()

        flash("Your profile has been updated.", "success")
        return redirect(next_url)
