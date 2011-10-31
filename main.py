 # -*- coding: utf-8 -*-

from flask import (Flask, render_template, request, redirect, session, g,
                   flash, send_from_directory, abort)

from functools import wraps

from jinja2 import FileSystemLoader

from flaskext.bcrypt import check_password_hash, generate_password_hash

import db
import os


app = Flask(__name__)

app.secret_key = 'secret key'

SESSION_USERID = 'userid'

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


# custom static directories
STATIC_DIRS = (
    os.path.join(ROOT_DIR, 'css'),
    os.path.join(ROOT_DIR, 'js'),
)


# configure template directories
app.jinja_loader = FileSystemLoader([
    os.path.join(ROOT_DIR, 'templates'),
    os.path.join(ROOT_DIR, 'templates_helpers'),
])


## database handlers

@app.before_first_request
def init_database():
    """Create database if it doesn't exist.
    """
    db.create_db_connection(migrate=True)


@app.before_request
def before_request():
    """Connect to database before each request.
    """
    g.db = db.create_db_connection()


@app.teardown_request
def teardown_request(exception):
    """Close database connection after each request.
    """
    db.close_db_connection(g.db)


## helpers

def register_user(username, password):
    """Register new user. Returns user database row. If fails, returns None.
    """
    try:
        user = g.db.users.insert(username=username,
                                 password=generate_password_hash(password))
        g.db.commit()
        return user
    except Exception as ex:
        return None


def login_user(username, password):
    """Login user. Returns user database row. If fails, returns None.
    """
    user = g.db.users(username=username)
    if user and check_password_hash(user.password, password):
        session[SESSION_USERID] = user.id
        return user
    return None


def login_required(func):
    """Decorator to enforce login.

    If user is already logged in, call decorated function passing user
    database row as first argument.

    If user is not logged in, redirect to login page.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        userid = session.get(SESSION_USERID)
        user = userid and g.db.users(id=userid)  # query database
        if user:
            return func(user, *args, **kwargs)
        else:
            return redirect('/login')
    return wrapper


## controllers

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        # should validate user input but this is just an example...
        user = register_user(request.form.get('username'),
                             request.form.get('password'))
        if user:
            flash('Registration successful.')
            return redirect('/')
        else:
            error = 'Failed to register user. Try another username.'
    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = login_user(request.form.get('username'),
                          request.form.get('password'))
        if user:
            flash('Successful login.')
            return redirect('/user')
        else:
            error = 'Invalid login.'
    return render_template('login.html', error=error)


@app.route('/user')
@login_required
def user_homepage(user):
    return render_template('user.html', username=user.username)


@app.route('/logout')
def logout():
    session.pop(SESSION_USERID, None)
    return redirect('/')


@app.route('/s/<filename>')
def static(filename):
    """Serve static files from multiple directories.

    WARNING: Use this function only in development.
    """
    for directory in STATIC_DIRS:
        if os.path.isfile(os.path.join(directory, filename)):
            return send_from_directory(directory, filename)
    abort(404)


if __name__ == '__main__':
    app.run(debug=True)
