from datetime import datetime, timezone

from flask import Blueprint, render_template, session, request, redirect, make_response

from db import db
from helpers.database_helpers import find_word_pair, dict_to_list
from helpers.htmx import htmx
from helpers.login_required import login_required
from helpers.render_htmx import render_htmx
from languages import languages

test_bp = Blueprint('test', __name__)


@test_bp.route('/app/test')
@login_required
def test_landing_page():
    tests = db.execute(
        'SELECT id, language_from, language_to, start_time, finish_time, round, total, finished FROM test WHERE id IN ('
        'SELECT test_id FROM test_account_relation WHERE account_id = ?'
        ') ORDER BY start_time DESC, finish_time DESC LIMIT 10',
        session.get('account_id'))
    for test in tests:
        test['start_time'] = datetime.strptime(test['start_time'], '%Y-%m-%d %H:%M:%S').strftime('%d %B %Y %H:%M')
        test['name'] = f'{test["language_from"]} - {test["language_to"]}'
    content = {'tests': tests}

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

    pair_table = find_word_pair(language_from, language_to)
    if not pair_table:
        content['error'] = 'No valid pair table'
        return render_htmx('partials/test_new.html', content=content)

    # https://stackoverflow.com/questions/1253561/sqlite-order-by-rand
    query = (f'SELECT DISTINCT {language_from}_word_id, word  FROM {pair_table} as wp '
             f'JOIN {language_from}_word as wf ON wf.id = wp.{language_from}_word_id WHERE {language_from}_word_id IN ('
             f'SELECT DISTINCT {language_from}_word_id FROM {pair_table} ORDER BY random() LIMIT ?)')

    print(language_from)
    print(pair_table)
    print(query)

    word_pairs = db.execute(query, number_of_words)
    number_of_words = len(word_pairs)

    if number_of_words < 1:
        content['error'] = 'There are no pairs for this language combination'
        return render_htmx('partials/test_new.html', content=content)

    try:
        test_name = f'{language_from}-{language_to}-{datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S")}'
        db.execute('BEGIN TRANSACTION')
        create_test_query = (
            'INSERT INTO test (name, total, finished, language_from, language_to) VALUES (?, ?, ?, ?, ?)')
        db.execute(create_test_query, test_name, number_of_words, 0, language_from, language_to)
        rows = db.execute('SELECT id FROM test WHERE name = ? ORDER BY start_time DESC LIMIT 1',
                          test_name)
        test_id = rows[0]['id']
        test_round = 1
        for word in word_pairs:
            word_id = word[f'{language_from}_word_id']
            db.execute('INSERT INTO test_word_relation (test_id, word_id, round) VALUES (?, ?, ?)',
                       test_id, word_id, test_round)
            test_round += 1
        db.execute('INSERT INTO test_account_relation VALUES (?, ?)',
                   session.get('account_id'), test_id)

        db.execute('COMMIT')
        content = {
            'language_from': language_from,
            'language_to': language_to,
            'round': 1,
            'total': number_of_words,
            'word_from': word_pairs[0]['word'],
            'test_id': test_id
        }
        return render_htmx('partials/test.html', f'/app/test/{test_id}', content=content)

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
        return redirect('/app/test')

    test_info = db.execute('SELECT * FROM test WHERE id = ?',
                           test_id)
    if not test_info:
        return redirect('/app/test')
    test_info = test_info[0]
    if test_info['finished'] == 1:
        return redirect(f'/app/test/{test_id}/results')

    check_if_skip = request.args.get('skip')
    if check_if_skip:
        if test_info['round'] < test_info['total']:
            try:
                db.execute('UPDATE test SET round = ? WHERE id = ?',
                           test_info['round'] + 1, test_id)
                db.execute('UPDATE test_word_relation SET try = 2 WHERE test_id = ? AND round = ?',
                           test_id, test_info['round'])
                return redirect(f'/app/test/{test_id}')
            except RuntimeError as e:
                print(e)
                return redirect('/app/test/')
        else:
            try:
                db.execute('UPDATE test_word_relation SET try = 2 WHERE test_id = ? AND round = ?',
                           test_id, test_info['round'])
                db.execute('UPDATE test SET finished = 1, finish_time = CURRENT_TIMESTAMP WHERE id = ?',
                           test_id)
                return redirect(f'/app/test/{test_id}')
            except RuntimeError as e:
                print(e)
                return redirect('/app/test/')

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
        return redirect('/app/test')
    word_from = word_from[0]
    content['word_from'] = word_from['word']
    if word_from['try'] == 1:
        content['correct_answer'] = '?'
    if word_from['try'] == 2:
        pair_table = find_word_pair(test_info["language_from"], test_info["language_to"])
        if not pair_table:
            return redirect('/app/test')

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
        return render_htmx('partials/test.html', f'/app/test/{test_id}', content=content)
    return render_template('test.html', content=content)


@test_bp.post('/app/test/<int:test_id>')
@login_required
def check_answer(test_id):
    test_info = db.execute('SELECT * FROM test WHERE id = ('
                           'SELECT test_id FROM test_account_relation WHERE test_id = ? AND account_id = ?)',
                           test_id, session.get('account_id'))
    if not test_info:
        return redirect('/app/test')
    test_info = test_info[0]

    answer = request.form.get('answer', '').strip()
    if not answer:
        r = make_response('Answer is empty')
        r.headers['HX-Retarget'] = '#error_message'
        return r
    pair_table = find_word_pair(test_info['language_from'], test_info['language_to'])
    if not pair_table:
        r = make_response("Pair doesn't exist")
        r.headers['HX-Retarget'] = '#error_message'
        return r

    possible_answers = db.execute(f'SELECT word FROM {test_info["language_to"]}_word WHERE id IN ('
                                  f'SELECT {test_info["language_to"]}_word_id FROM {pair_table} '
                                  f'WHERE {test_info["language_from"]}_word_id = ('
                                  'SELECT word_id FROM test_word_relation WHERE test_id = ? AND round = ?))',
                                  test_id, test_info['round'])

    if not possible_answers:
        r = make_response('Nothing to compare with')
        r.headers['HX-Retarget'] = '#error_message'
        return r

    list_answers = dict_to_list(possible_answers, 'word')
    word_info = db.execute('SELECT * FROM test_word_relation '
                           f'JOIN {test_info["language_from"]}_word w ON word_id = w.id '
                           'WHERE test_id = ? AND round = ?',
                           test_id, test_info['round'])[0]
    answer_number = 'answer_'
    if word_info['try'] == 0:
        answer_number += 'one'
    elif word_info['try'] == 1:
        answer_number += 'two'
    else:
        return redirect(f'/app/test/{test_id}')

    try:
        db.execute(f'UPDATE test_word_relation SET try = ?, {answer_number} = ? WHERE test_id = ? AND word_id = ?',
                   word_info['try'] + 1, answer.lower(), test_id, word_info['word_id'])
    except RuntimeError as e:
        print(e)
        return redirect(f'/app/test/{test_id}')

    content = {
        'test_id': test_id,
        'language_from': test_info['language_from'],
        'language_to': test_info['language_to'],
        'round': test_info['round'],
        'total': test_info['total'],
        'word_from': word_info['word']
    }
    if answer.lower() not in list_answers:
        content['wrong'] = True
        content['word_from'] = word_info['word']
        if word_info['try'] == 0:
            content['correct_answer'] = '?'
        else:
            content['correct_answer'] = ', '.join(list_answers)
            content['disable_again'] = True
    else:
        content['success'] = True
        content['user_answer'] = answer
        if test_info['round'] < test_info['total']:
            try:
                db.execute('UPDATE test SET round = ? WHERE id = ?',
                           test_info['round'] + 1, test_id)
            except RuntimeError as e:
                print(e)
                r = make_response('Something went wrong. Try again later.')
                r.headers['HX-Retarget'] = '#error_message'
                return r
        else:
            try:
                db.execute('UPDATE test SET finished = 1, finish_time = CURRENT_TIMESTAMP WHERE id = ?',
                           test_id)
                content['finish'] = True
            except RuntimeError as e:
                print(e)
                r = make_response('Something went wrong. Try again later.')
                r.headers['HX-Retarget'] = '#error_message'
                return r

    return render_htmx('partials/test.html', content=content)


@test_bp.get('/app/test/<int:test_id>/results')
@login_required
def test_result(test_id):
    test = db.execute('SELECT * FROM test_account_relation WHERE test_id = ? AND account_id = ?',
                      test_id, session.get('account_id'))
    if not test:
        return redirect('/app/test')

    test_info = db.execute('SELECT * FROM test WHERE id = ? AND finished = true',
                           test_id)
    if not test_info:
        return redirect('/app/test')

    test_info = test_info[0]
    lang_from, lang_to = test_info['language_from'], test_info['language_to']
    table_pair = find_word_pair(lang_from, lang_to)

    query = ('SELECT twr.round, wf.word as word_from, wt.word as word_to, twr.try, twr.answer_one, twr.answer_two '
             'FROM test_word_relation as twr '
             f'JOIN {lang_from}_word as wf ON wf.id = twr.word_id '
             f'JOIN {table_pair} as wp ON wp.{lang_from}_word_id = wf.id '
             f'JOIN {lang_to}_word as wt ON wt.id = wp.{lang_to}_word_id '
             'WHERE twr.test_id = ? ORDER BY twr.round')
    test_word_info = db.execute(query, test_id)
    normalized_info = {
        'rounds': test_info['total'],
        'language_from': lang_from,
        'language_to': lang_to,
        'right': 0,
        'wrong': 0,
        'rows': {}
    }
    for row in test_word_info:
        if row['round'] in normalized_info['rows']:
            normalized_info['rows'][row['round']]['word_to'] += f', {row['word_to']}'
        else:
            normalized_info['rows'][row['round']] = row

    for _, row in normalized_info['rows'].items():
        if row['try'] == 2 and (not row['answer_two'] or row['answer_two'] not in row['word_to']):
            normalized_info['wrong'] += 1
            row['result'] = 'wrong'
        else:
            normalized_info['right'] += 1
            row['result'] = 'right'

    if htmx():
        return render_htmx('partials/results.html', url=f'/app/test/{test_id}/results', content=normalized_info)
    return render_template('results.html', content=normalized_info)
