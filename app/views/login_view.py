from flask import flash, render_template, request, current_app
from flask.views import MethodView
from flask_login import current_user, login_user

from app.models import User
from app.utils import redirect_based_on_role, sanitise_html, log_audit_event


class LoginView(MethodView):
    def get(self):
        if current_user.is_authenticated:
            return redirect_based_on_role()
        return render_template("login.html")

    def post(self):
        if current_user.is_authenticated:
            return redirect_based_on_role()

        email = sanitise_html(request.form.get("email", ""))
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            log_audit_event(user.id, "login success")
            return redirect_based_on_role()
        else:
            current_app.logger.warning(
                "Failed login attempt for %s from %s",
                email,
                request.remote_addr,
            )
            log_audit_event(None, "login failed", details=f"email={email}")
            flash("Login failed. Check your email and password.", "warning")
            return render_template("login.html")
