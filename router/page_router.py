from flask import Blueprint
from flask import current_app

page = Blueprint('page', __name__, static_folder='static', template_folder="static")


@page.route('/')
@page.route('/index')
def index():
    return current_app.send_static_file('page/index.html')
