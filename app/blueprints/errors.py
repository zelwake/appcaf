from flask import render_template, Blueprint

error_bp = Blueprint('errors', __name__)


@error_bp.errorhandler(404)
def page_not_found(error):
    print(error)
    return render_template('page_not_found.html')
