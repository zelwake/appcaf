from datetime import datetime, timezone

from flask import Blueprint, render_template, session, request

from db import db
from helpers.database_helpers import DatabaseWordPairTable
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


@test_bp.get('/app/test/new')
@login_required
def create_test_page():
    content = {'languages': languages}

    if htmx():
        return render_htmx('partials/test_new.html', '/app/test/new', content=content)
    return render_template('test_new.html', content=content)


@test_bp.post('/app/test/new')
@login_required
def create_test():
    language_from = request.form.get('first_language', '').strip().lower()
    language_to = request.form.get('second_language', '').strip().lower()
    number_of_words = request.form.get('number', '0').strip()

    content = {'languages': languages}

    if not language_from or not language_to:
        content['error'] = 'Please provide a language'
        return render_htmx('partials/test_new.html', content=content)

    if language_from not in languages or language_to not in languages:
        content['error'] = 'Languages must be valid'
        return render_htmx('partials/test_new.html', content=content)

    if language_from == language_to:
        content['error'] = 'Languages cannot be the same'
        return render_htmx('partials/test_new.html', content=content)

    if not number_of_words:
        content['error'] = 'Please provide number of words'
        return render_htmx('partials/test_new.html', content=content)

    try:
        number_of_words = int(number_of_words)
    except ValueError:
        content['error'] = 'Number must be an integer'
        return render_htmx('partials/test_new.html', content=content)

    if number_of_words < 1:
        content['error'] = 'Number must be a positive integer'
        return render_htmx('partials/test_new.html', content=content)

    # https://stackoverflow.com/questions/1253561/sqlite-order-by-rand
    allowed_pair_tables = [table.value for table in DatabaseWordPairTable]
    pair_table = ''
    for table in allowed_pair_tables:
        if language_from in table and language_to in table:
            pair_table = table
            break
    else:
        content['error'] = 'No valid pair table'
        return render_htmx('partials/test_new.html', content=content)

    query = f'''
        SELECT * 
          FROM {pair_table} 
         WHERE {language_from}_word_id IN (
               SELECT DISTINCT {language_from}_word_id 
                 FROM {pair_table} 
                ORDER BY random()
                LIMIT ?)'''
    print(query)
    word_pairs = db.execute(query, number_of_words)
    number_of_words = len(word_pairs)
    print(word_pairs)

    if number_of_words < 1:
        content['error'] = 'There a no pairs for this language combination'
        return render_htmx('partials/test_new.html', content=content)

    try:
        test_name = f'{language_from}-{language_to}-{datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")}'
        db.execute('BEGIN TRANSACTION')
        create_test_query = (
            'INSERT INTO test (name, total, finished, language_from, language_to) VALUES (?, ?, ?, ?, ?)')
        print(
            f'INSERT INTO test (name, total, finished, language_from, language_to) '
            f'VALUES ({test_name}, {number_of_words}, 0, {language_from}, {language_to})')
        db.execute(create_test_query, test_name, number_of_words, 0, language_from, language_to)
        print(f'SELECT id FROM test WHERE name = {test_name} ORDER BY start_time DESC LIMIT 1')
        rows = db.execute('SELECT id FROM test WHERE name = ? ORDER BY start_time DESC LIMIT 1',
                          test_name)
        print(f'rows: {rows}')
        test_id = rows[0]['id']
        test_round = 1
        for word in word_pairs:
            word_id = word[f'{language_from}_word_id']
            print(f'INSERT INTO test_word_relation (test_id, word_id, round) VALUES ({test_id}, {word_id}, {test_round})')
            db.execute('INSERT INTO test_word_relation (test_id, word_id, round) VALUES (?, ?, ?)',
                       test_id, word_id, test_round)
            test_round += 1

        db.execute('COMMIT')

    except RuntimeError as e:
        print(e)
        db.execute('ROLLBACK')
        content['error'] = 'Something went wrong. Try again later.'
        return render_htmx('partials.test_new.html', content=content)

    return 'DATABASE INSERTION NOT CREATED'
