from flask import Blueprint, render_template, request, abort

from db import db
from helpers.database_helpers import get_word_id
from helpers.htmx import htmx
from helpers.login_required import login_required
from helpers.render_htmx import render_htmx

word_bp = Blueprint('word', __name__)


@word_bp.get('/app/word')
@login_required
def words():
    if htmx():
        return render_htmx('partials/words.html', '/app/word')
    return render_template('words.html')


@word_bp.post('/app/word')
@login_required
def new_word():
    french_word = request.form.get('french_word').strip().lower() or ''
    czech_word = request.form.get('czech_word').strip().lower() or ''
    english_word = request.form.get('english_word').strip().lower() or ''

    english_id, czech_id, french_id = 0, 0, 0

    if (english_word and french_word) or (czech_word and french_word) or (czech_word and english_word) or (
            czech_word and french_word and english_word):
        db.execute('BEGIN TRANSACTION;')

        if english_word:
            english_id = get_word_id(english_word, 'english_word')
            if not english_id:
                db.execute('ROLLBACK')
                return abort(500)

        if czech_word:
            czech_id = get_word_id(czech_word, 'czech_word')
            if not czech_id:
                db.execute('ROLLBACK')
                return abort(500)

        if french_word:
            french_id = get_word_id(french_word, 'french_word')
            if not french_id:
                db.execute('ROLLBACK')
                return abort(500)

        db.execute('COMMIT')




