from functools import wraps
from flask import redirect, session, request, render_template, make_response

from helpers.htmx import htmx
from helpers.render_htmx import render_htmx


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('account_id') is None:
            if htmx():
                return render_htmx('partials/login.html', '/login')
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function
