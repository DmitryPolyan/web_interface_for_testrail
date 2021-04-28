from flask import render_template
from app import app

@app.errorhandler(403)
def forbidden_err(error):
    return render_template('403.html'), 403