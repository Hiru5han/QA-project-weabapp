from flask import redirect, url_for
from flask.views import MethodView
from flask_login import login_required, logout_user


class LogoutView(MethodView):
    decorators = [login_required]

    def get(self):
        logout_user()
        return redirect(url_for("main.index"))
