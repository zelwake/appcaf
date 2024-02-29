from flask import render_template

# from run import app


# @app.errorhandler(404)
def page_not_found(error):
    print(error)
    return render_template('page_not_found.html'), 404
