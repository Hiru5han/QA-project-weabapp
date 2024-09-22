import os
import re

from flask import flash, render_template, request
from flask.views import MethodView
from flask_login import login_user
from PIL import Image, ImageOps

from app.models import User, db
from app.utils import UPLOAD_FOLDER, allowed_file, redirect_based_on_role


class RegisterView(MethodView):
    def get(self):
        return render_template("register.html")

    def post(self):
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

        # Create the new user
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
                filename = f"user_{new_user.id}.{file_ext}"

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
