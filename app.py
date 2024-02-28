from cs50 import SQL
from flask import Flask, render_template, request, redirect, flash, make_response, session

from helpers.check_password import check_password
from helpers.render_htmx import render_htmx
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = '95d97acd1f953da32861b4aede789c74e4e1e3a8ea5fc89ffbf53e7615b41f04'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.debug = True
Session(app)

db = SQL('sqlite:///appcaf.db')


@app.route('/')
def index():
    htmx = request.headers.get('HX-Request') is not None
    return render_htmx('partials/index.html', '/') if htmx else render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    htmx = request.headers.get('HX-Request') is not None
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            if htmx:
                return render_template('partials/login.html', error='Missing username')
            flash('Please enter username')
            return render_template('login.html')

        password = request.form.get('password')
        if not password:
            if htmx:
                return render_template('partials/login.html', error='Missing password')
            flash('Please enter password')
            return render_template('login.html')

        # TODO connect to db and check if user exists and password hashes to same
        if username == 'admin' and password == 'password':
            session['account_id'] = 1

        render_htmx("partials/dashboard.html", "/app/dashboard.html") if htmx else redirect("/app/dashboard")

    if htmx:
        response = make_response(render_template('partials/login.html'))
        response.headers['HX-Push-Url'] = '/login'
        return response

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    htmx = request.headers.get('HX-Request') is not None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        correction = request.form.get('correction')
        print(f"username: {username}, password: {password}, correction: {correction}")
        if not username:
            return render_page(htmx, 'Missing username', username=username)
        username = username.strip().lower()

        if not password:
            return render_page(htmx, 'Missing password', username=username)

        if not correction:
            return render_page(htmx, 'Missing repeated password', username=username)

        password = password.strip()
        if password != correction.strip():
            return render_page(htmx, 'Passwords do not match', username=username)

        valid_pw = check_password(password)
        if not valid_pw:
            return render_page(htmx, 'Password not met requirements', username=username)

        user_exist = db.execute('SELECT * FROM account WHERE username = ?', username)
        if len(user_exist) != 0:
            return render_page(htmx, error_text='Username already in use')

        hash_pw = generate_password_hash(password, method='scrypt', salt_length=16)
        try:
            db.execute('INSERT INTO account (username, password) VALUES (?, ?)', username, hash_pw)
        except RuntimeError:
            return render_page(htmx, 'Something went wrong', username=username)

        if htmx:
            return render_htmx('partial/dashboard.html', '/app/dashboard', username=username)
        return redirect('/app/dashboard.html')

    return render_htmx('partials/register.html', '/register') if htmx else render_template('register.html')


def render_page(htmx, error_text, username=''):
    message = {'error': error_text}
    return render_htmx(
        'partials/register.html', '/register', message=message, username=username
    ) if htmx else render_template('register.html', message=message, username=username)


@app.errorhandler(404)
def page_not_found(error):
    print(error)
    return render_template('page_not_found.html'), 404


if __name__ == '__main__':
    app.run()
