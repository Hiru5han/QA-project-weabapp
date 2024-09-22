from flask import render_template
from flask.views import MethodView
from flask_login import current_user

from app.utils import redirect_based_on_role


class IndexView(MethodView):
    def get(self):
        """
        Renders the index page or redirects to a role-based page if the user is authenticated.
        """
        if current_user.is_authenticated:
            return redirect_based_on_role()
        return render_template("index.html", title="Welcome")
