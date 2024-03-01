import os

from dotenv import load_dotenv
from flask import Flask

from app.blueprints.app import app_bp
from app.blueprints.auth import auth_bp
from app.blueprints.root import root_bp
from flask_session import Session

from app.blueprints.test import test_bp
from app.blueprints.word import word_bp


def create_app():
    app = Flask(__name__)

    load_dotenv()

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    Session(app)

    app.register_blueprint(root_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(app_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(word_bp)

    return app
