import os
import sqlite3

from flask import Flask, request, session, g, redirect, url_for, render_template, flash

from smpchecker.sml import smlchecker
from smpchecker.accesspoint import apscanner
from smpchecker.model import model

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , smpchecker.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'smpchecker.db'),
    SECRET_KEY='development key',
    USERNAME='rik.ribbers@sidn.nl',
    PASSWORD='default'
))

app.config.from_envvar('SMPCHECKER_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def query_db(query, args=(), one=False):
    db= get_db()
    cur =db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    db.commit()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check_peppol', methods=['POST'])
def check_peppol():
    error=None
    if smlchecker.check(request.form['peppolid']):
        flash('PEPPOL Identifier found in SML')
        apscanner.scan(request.form['peppolid'])

    else:
        error = 'PEPPOL Identifier not found in SML'

    p = model.PeppolMember(request.form['peppolid'])
    p.reload()
    results = p.get_smpentries()
    return render_template("index.html", error=error, results=results, peppolid=p.peppolidentifier)

@app.route('/check_business', methods=['POST'])
def check_business():
    error=None
    peppolid=request.form['optradio']+':'+request.form['businessid']
    print(peppolid)
    if smlchecker.check(peppolid):
        flash('PEPPOL Identifier found in SML')
        apscanner.scan(peppolid)

    else:
        error = 'PEPPOL Identifier not found in SML'

    p = model.PeppolMember(peppolid)
    p.reload()
    results = p.get_smpentries()
    return render_template("index.html", error=error, results=results, peppolid=p.peppolidentifier)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['inputEmail'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['inputPassword'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))
