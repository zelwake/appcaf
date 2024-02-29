from flask import Blueprint, render_template, session, request

from db import db
from helpers.htmx import htmx
from helpers.login_required import login_required
from helpers.render_htmx import render_htmx
from languages import languages

test_bp = Blueprint('test', __name__)


@test_bp.route('/app/test')
@login_required
def test_landing_page():
    account_id = session.get('account_id')
    content = {}

    tests = db.execute('SELECT id, name, round, total, finished FROM test WHERE id IN ('
                       'SELECT test_id FROM test_account_relation WHERE account_id = ?'
                       ') ORDER BY start_time DESC, finish_time DESC LIMIT 10', account_id)
    content['tests'] = tests

    if htmx():
        return render_htmx('partials/test_landing_page.html', '/app/test', content=content)
    return render_template('test_landing_page.html', content=content)


@test_bp.route('/app/test/new')
@login_required
def create_test_page():
    content = {'languages': languages}

    if htmx():
        return render_htmx('partials/test_new.html', '/app/test/new', content=content)
    return render_template('test_new.html', content=content)


@test_bp.route('/app/test/new', methods=['POST'])
@login_required
def create_test():
    name = request.form.get('name')
    language_from = request.form.get('first_language')
    language_to = request.form.get('second_language')
    number_of_words = request.form.get('number')
    if not name or not name.strip():
        return render_htmx('partials/test_new.html', content={'error': 'Please provide test name'})

    if not language_from or not language_to:
        return render_htmx('partials/test_new.html', content={'error': 'Please provide language'})
    language_from = language_from.strip().lower()
    language_to = language_to.strip().lower()
    if language_from == language_to:
        return render_htmx('partials/test_new.html', content={'error': 'Languages cannot be same'})
    if language_from not in languages or language_to not in languages:
        return render_htmx('partials/test_new.html', content={'error': 'Languages must be valid'})

    if not number_of_words:
        return render_htmx('partials/test_new.html', content={'error': 'Please provide number of words'})
    try:
        number_of_words = int(number_of_words)
    except ValueError:
        return render_htmx('partials/test_new.html', content={'error': 'Number must be an integer'})
    if number_of_words < 1:
        return render_htmx('partials/test_new.html', content={'error': 'Number must be positive integer'})

    # TODO create new test and redirect user to said test
    return 'DATABASE INSERTION NOT CREATED'
