from flask import redirect, render_template, request, sessionmaker
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/doc/1.0/patterns/viewdecorates/
    """
    @wraps(f)
    def decorated_funtion(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_funtion
