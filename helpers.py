from flask import redirect, session
from functools import wraps

# From CS50 PSET8 code
def location_required(f):
    """
    Decorate routes to require location.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("state") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function