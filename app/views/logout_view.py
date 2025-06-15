from flask import redirect, url_for
from flask.views import MethodView
from flask_login import login_required, logout_user
from typing import Any, Callable, ClassVar


class LogoutView(MethodView):
    decorators: ClassVar[list[Callable[[Any], Any]]] = [login_required]

    def get(self):
        logout_user()
        return redirect(url_for("main.index"))
