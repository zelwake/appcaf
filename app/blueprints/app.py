from flask import Blueprint, request, render_template, make_response, session

from db import db
from helpers.login_required import login_required
from helpers.render_htmx import render_htmx

app_bp = Blueprint('app', __name__)


@app_bp.route('/app')
@login_required
def dashboard():
    htmx = request.headers.get('HX-Request') is not None
    reload_page = request.args.get('r') is not None
    account_id = session.get('account_id')
    content = {}

    last_five_tests = db.execute(
        'SELECT id, name, start_time, round, total FROM test WHERE id IN ('
        'SELECT test_id FROM test_account_relation WHERE account_id = ?'
        ') AND finished = 0 ORDER BY start_time DESC LIMIT 5',
        account_id)
    content['last_five_tests'] = last_five_tests

    username = db.execute('SELECT username FROM account WHERE id = ?', account_id)[0]['username']
    content['username'] = username

    if htmx and not reload_page:
        return render_htmx('partials/dashboard.html', '/app', content=content)
    response = make_response(render_template('dashboard.html', content=content))
    response.headers['HX-Push-Url'] = '/app'
    return response
