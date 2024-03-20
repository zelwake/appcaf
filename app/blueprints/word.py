from flask import Blueprint, render_template, request, abort, redirect

from db import db
from helpers.database_helpers import get_word_id, AllowedWordTables, insert_word_pair, DatabaseWordPairTable
from helpers.htmx import htmx
from helpers.login_required import login_required
from helpers.render_htmx import render_htmx

word_bp = Blueprint('word', __name__)


@word_bp.get('/app/word')
@login_required
def words():
    czech_word = request.args.get('c')
    french_word = request.args.get('f')
    english_word = request.args.get('e')
    content = {"czech_word": czech_word, "english_word": english_word, "french_word": french_word}
    query_url = request.url[request.url.find("?"):]
    if htmx():
        return render_htmx('partials/words.html', f'/app/word{query_url if len(query_url) > 1 else ""}', content=content)
    return render_template('words.html', content=content)


@word_bp.post('/app/word')
@login_required
def new_word():
    french_word = request.form.get('french_word').strip().lower() or ''
    czech_word = request.form.get('czech_word').strip().lower() or ''
    english_word = request.form.get('english_word').strip().lower() or ''

    english_id, czech_id, french_id = 0, 0, 0

    if (english_word and french_word) or (czech_word and french_word) or (czech_word and english_word) or (
            czech_word and french_word and english_word):
        db.execute('BEGIN TRANSACTION')

        if english_word:
            english_id = get_word_id(english_word, AllowedWordTables.ENGLISH.value)
            if not english_id:
                db.execute('ROLLBACK')
                return abort(500)

        if czech_word:
            czech_id = get_word_id(czech_word, AllowedWordTables.CZECH.value)
            if not czech_id:
                db.execute('ROLLBACK')
                return abort(500)

        if french_word:
            french_id = get_word_id(french_word, AllowedWordTables.FRENCH.value)
            if not french_id:
                db.execute('ROLLBACK')
                return abort(500)

        db.execute('COMMIT')
    else:
        query = ''
        if czech_word:
            query += f'?c={czech_word}'
        if english_word:
            query += f'{"&" if len(query) else "?"}e={english_word}'
        if french_word:
            query += f'{"&" if len(query) else "?"}f={french_word}'

        return redirect(f'/app/word{query}')

    try:
        db.execute('BEGIN TRANSACTION')
        if english_id and french_id:
            if not insert_word_pair(DatabaseWordPairTable.ENGLISH_FRENCH_PAIR.value, english_id, french_id):
                db.execute('ROLLBACK')
                return abort(500)

        if english_id and czech_id:
            if not insert_word_pair(DatabaseWordPairTable.CZECH_ENGLISH_PAIR.value, czech_id, english_id):
                db.execute('ROLLBACK')
                return abort(500)

        if czech_id and french_id:
            if not insert_word_pair(DatabaseWordPairTable.CZECH_FRENCH_PAIR.value, czech_id, french_id):
                db.execute('ROLLBACK')
                return abort(500)

        db.execute('COMMIT')
    except RuntimeError as e:
        print(f'Error while creating pairs:\n{e}')
        db.execute('ROLLBACK')
        return abort(500)

    if htmx():
        return render_htmx('partials/words.html', content={'message': 'Successfully added!'})
    return render_htmx('words.html', content={'message': 'Successfully added!'})


