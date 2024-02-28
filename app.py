from cs50 import SQL
from flask import Flask, render_template, request, redirect, flash, make_response, session
from helpers.render_htmx import render_htmx
from flask_session import Session

app = Flask(__name__)

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
        if username is None or username.strip() == '':
            if htmx:
                return render_template('partials/login.html', error='Missing username')
            flash('Please enter username')
            return render_template('login.html')

        password = request.form.get('password')
        if password is None or password.strip() == '':
            if htmx:
                return render_template('partials/login.html', error='Missing password')
            flash('Please enter password')
            return render_template('login.html')

        # TODO connect to db and check if user exists and password hashes to same
        if username == 'admin' and password == 'password':
            session['account_id'] = 1

        if htmx:
            response = make_response(render_template('partials/dashboard.html'))
            response.headers['HX-Push-Url'] = '/app/dashboard'
            return response
        return redirect("/app/dashboard")

    if htmx:
        response = make_response(render_template('partials/login.html'))
        response.headers['HX-Push-Url'] = '/login'
        return response

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    htmx = request.headers.get('HX-Request') is not None
    if request.method == 'POST':
        return 'TBD'

    return render_htmx('partials/register.html', '/register') if htmx else render_template('register.html')


if __name__ == '__main__':
    app.run()
