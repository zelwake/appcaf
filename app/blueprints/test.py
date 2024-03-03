from datetime import datetime, timezone

from flask import Blueprint, render_template, session, request, redirect

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
    if not pair_table:
        content['error'] = 'No valid pair table'
        return render_htmx('partials/test_new.html', content=content)

    query = f'SELECT * FROM {pair_table} WHERE {language_from}_word_id IN (' \
            f'SELECT DISTINCT {language_from}_word_id FROM {pair_table} ORDER BY random() LIMIT ?)'
    print(query)
    word_pairs = db.execute(query, number_of_words)
    number_of_words = len(word_pairs)
    print(word_pairs)

    if number_of_words < 1:
        content['error'] = 'There a no pairs for this language combination'
        return render_htmx('partials/test_new.html', content=content)

    try:
        test_name = f'{language_from}-{language_to}-{datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S")}'
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
            print(
                f'INSERT INTO test_word_relation (test_id, word_id, round) VALUES ({test_id}, {word_id}, {test_round})')
            db.execute('INSERT INTO test_word_relation (test_id, word_id, round) VALUES (?, ?, ?)',
                       test_id, word_id, test_round)
            test_round += 1

        db.execute('COMMIT')
        content = {
            'language_from': language_from,
            'language_to': language_to,
            'round': test_round,
            'total': number_of_words,
            'word_from': word_pairs[0][f'{language_from}_word_id'],
            'test_id': test_id
        }
        return render_htmx('partials/test.html', f'app/test/{test_id}', content=content)

    except RuntimeError as e:
        print(e)
        db.execute('ROLLBACK')
        content['error'] = 'Something went wrong. Try again later.'
        return render_htmx('partials.test_new.html', content=content)


@test_bp.get('/app/test/<int:test_id>')
@login_required
def show_test(test_id):
    content = {}
    is_users_test = db.execute('SELECT * FROM test_account_relation WHERE test_id = ? AND account_id = ?',
                               test_id, session.get('account_id'))
    if not is_users_test:
        return render_htmx('partials/text_landing_page.html', 'app/test')

    test_info = db.execute('SELECT * FROM test WHERE id = ?',
                           test_id)
    if not test_info:
        return render_htmx('partials/text_landing_page.html', 'app/test')
    if test_info[0]['finished'] == 1:
        return redirect(f'/app/test/{test_id}/results')
    test_info = test_info[0]
    content['language_from'] = test_info['language_from']
    content['language_to'] = test_info['language_to']
    content['test_id'] = test_id
    content['total'] = test_info['total']
    content['round'] = test_info['round']

    word_from = db.execute(f'SELECT * FROM test_word_relation AS twr '
                           f'JOIN {test_info["language_from"]}_word AS w ON twr.word_id = w.id '
                           f'WHERE twr.test_id = ? AND twr.round = ?',
                           test_id, test_info["round"])
    if not word_from:
        return render_htmx('partials/text_landing_page.html', 'app/test')
    word_from = word_from[0]
    content['word_from'] = word_from['word']
    if word_from['try'] == 1:
        content['correct_answer'] = '?'
    if word_from['try'] == 2:
        # TODO: make a helper function
        allowed_pair_tables = [table.value for table in DatabaseWordPairTable]
        pair_table = ''
        for table in allowed_pair_tables:
            if test_info["language_from"] in table and test_info["language_to"] in table:
                pair_table = table
                break
        if not pair_table:
            content['error'] = 'No valid pair table'
            return render_htmx('partials/test_new.html', content=content)
        dict_answers = db.execute(
            f'SELECT word FROM {pair_table} '
            f'JOIN {test_info["language_to"]}_word ew on ew.id = {test_info["language_to"]}_word_id '
            f'WHERE {test_info["language_from"]}_word_id IN (?)',
            word_from['word_id'])
        answers = ''
        for word in dict_answers:
            if len(answers) > 0:
                answers += ', '
            answers += word['word']

        content['answers'] = answers
        content['disable_again'] = True

    if htmx():
        return render_htmx('partials/test.html', f'app/test/{test_id}', content=content)
    return render_template('test.html', content=content)
