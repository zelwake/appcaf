from flask import Blueprint, request, session, flash, render_template, make_response, redirect
from werkzeug.security import check_password_hash, generate_password_hash

from db import db
from helpers.check_password import check_password
from helpers.htmx import htmx
from helpers.render_htmx import render_htmx

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/?r=1')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.clear()
        username = request.form.get('username', '').strip()
        if not username:
            if htmx():
                return render_template('partials/login.html', error='Missing username')
            flash('Please enter username')
            return render_template('login.html')

        password = request.form.get('password')
        if not password:
            if htmx():
                return render_template('partials/login.html', error='Missing password')
            flash('Please enter password')
            return render_template('login.html')

        user = db.execute('SELECT * FROM account WHERE username = ?', username)
        valid_user = True
        check_pw = False
        if not user:
            valid_user = False
        else:
            check_pw = check_password_hash(user[0]['password'], password)

        if not check_pw or not valid_user:
            error = "Username or password is incorrect"
            if htmx():
                return render_htmx('partials/login.html', '/login', error=error)
            return render_template('login.html', error=error)

        session['account_id'] = user[0]['id']

        response = redirect('/app?r=1')
        response.headers['X-Reload-Page'] = 'true'
        return response

    if htmx():
        return render_htmx('partials/login.html', '/login')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        correction = request.form.get('correction', '').strip()

        if not username:
            return render_register_page('Missing username', username=username)

        if not password:
            return render_register_page('Missing password', username=username)

        if not correction:
            return render_register_page('Missing repeated password', username=username)

        password = password
        if password != correction.strip():
            return render_register_page('Passwords do not match', username=username)

        valid_pw = check_password(password)
        if not valid_pw:
            return render_register_page('Password not met requirements', username=username)

        user_exist = db.execute('SELECT * FROM account WHERE LOWER(username) = ?',
                                username.lower())
        if len(user_exist) != 0:
            return render_register_page(error_text='Username already in use')

        hash_pw = generate_password_hash(password)
        try:
            db.execute('INSERT INTO account (username, password) VALUES (?, ?)',
                       username, hash_pw)
        except RuntimeError:
            return render_register_page('Something went wrong', username=username)

        if htmx():
            return render_htmx('partials/login.html', '/login', username=username)
        return redirect('/login')

    return render_htmx('partials/register.html', '/register') if htmx else render_template('register.html')


def render_register_page(error_text, username=''):
    message = {'error': error_text}
    return render_htmx(
        'partials/register.html', '/register', message=message, username=username
    ) if htmx() else render_template('register.html', message=message, username=username)
