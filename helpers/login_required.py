from functools import wraps
from flask import redirect, session, request, render_template, make_response


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('account_id') is None:
            htmx_request = request.headers.get('HX-Request') is not None
            if htmx_request:
                response = make_response(render_template('partials/login.html'))
                response.headers['HX-Push-Url'] = '/login'
                return response
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function
