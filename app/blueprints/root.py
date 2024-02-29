from flask import Blueprint, request, render_template, make_response

from helpers.render_htmx import render_htmx

root_bp = Blueprint('root', __name__)


@root_bp.route('/')
def index():
    htmx = request.headers.get('HX-Request') is not None
    reload_page = request.args.get('r') is not None
    if htmx and not reload_page:
        return render_htmx('partials/index.html', '/')
    response = make_response(render_template('index.html'))
    response.headers['HX-Push-Url'] = '/'
    return response
