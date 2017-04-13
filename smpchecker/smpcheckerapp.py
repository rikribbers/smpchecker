import os
import sqlite3

from flask import Flask, request, session, g, redirect, url_for, render_template, flash, jsonify, abort
from werkzeug.utils import secure_filename

from smpchecker.smp import smpscanner
from smpchecker.model import model
from smpchecker.sml import smlchecker

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , smpcheckerapp.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'smpchecker.db'),
    SECRET_KEY='development key',
    USERNAME='rik.ribbers@sidn.nl',
    PASSWORD='default',
    UPLOAD_FOLDER = '/tmp/smpchecker',
    ALLOWED_EXTENSIONS = set(['txt', 'csv'])
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
    return render_template('check.html')


@app.route('/check', methods=['POST', 'GET'])
def check():
    error=None
    peppolid = None
    if request.method == 'POST':
        peppolid = extract_peppol_identifier(request.form['optradio'],request.form['businessid'])
        if smlchecker.check(peppolid):
            flash('PEPPOL Identifier found in SML')
            smpscanner.scan(peppolid)
        else:
            error = 'PEPPOL Identifier not found in SML'

    p = model.PeppolMember(peppolid)
    p.reload()
    result = p.get_scan_result()
    return render_template("check.html", error=error, result=result, peppolid=peppolid)


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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('File format not supported')
            return redirect(request.url)
        if file :
            filename = secure_filename(file.filename)
            f = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(f)
            results = smpscanner.readfile(f, request.form['optradio'])
            #TODO REMOVE FILE NAME
            return render_template('upload.html', results=results)
    return render_template('upload.html')


def extract_peppol_identifier(optradio, businessid):
    if optradio == 'PEPPOL':
        return businessid
    else:
        return optradio + ':' + businessid


@app.route('/api/participant/<string:peppol_id>', methods=['GET'])
def get_participant(peppol_id):
    p = model.PeppolMember(peppol_id)
    if not p.exists():
        abort(404)
    else:
        p.reload()

    return jsonify(p.serialize())

@app.route('/api/acesspoint', methods=['GET'])
def get_accesspoint():
    ap = model.AccessPoints()
    result = ap.load()
    return jsonify(accesspoints=[a.serialize() for a in result.accesspoints])
