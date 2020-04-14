from functools import wraps
import json
from os import environ as env

import dotenv
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, redirect, render_template, session, url_for, request, Response, json
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
import pyodbc
from flask_cors import cross_origin

import lightwave_io

app = Flask(__name__)
AUTH0_AUDIENCE = 'https://dev-92zb026a.auth0.com/userinfo'
app.secret_key = 'secret_key'
JWT_PAYLOAD = 'jwt_payload'
PROFILE_KEY = 'profile'
conn_string = (
    r'DRIVER={ODBC Driver 11 for SQL Server};'
    r'SERVER=WIN-GHO929AITJN;'
    r'DATABASE=Authentication;'
    r'Trusted_Connection=yes;'
)
conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id='90ycfYTmNMgEpY7x4a2fquPoW5iB0N77',
    client_secret='RE-7Yz3KMufnrtZIQIHNYzPTfp8V_U2CSHuwkqK7mDinYZ5LW4CcCuQkCP64GvF6',
    api_base_url='https://dev-92zb026a.auth0.com',
    access_token_url='https://dev-92zb026a.auth0.com/oauth/token',
    authorize_url='https://dev-92zb026a.auth0.com/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)


@app.route('/')
def home():
    return render_template('homeScreen.html')


# Here we're using the /callback route.
@app.route('/callback')
def callback_handling():
    # Handles response from token endpoint
    print("redirected here")
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    # Store the user information in flask session.
    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    username=userinfo['name']
    print(username)
    query = "SELECT UserRoleId FROM Users WHERE Username = ?"
    cursor.execute(query, username)
    userRole = cursor.fetchone()
    print(userRole.UserRoleId)
    if userRole.UserRoleId == 1:
        return redirect('/adminDashboard')
    else:
        return redirect('/dashboard')


@app.route('/adminDashboard')
def adminDashboard():
    cursor.execute('SELECT * FROM Users')
    data = cursor.fetchall()
    return render_template('adminDashboard.html', output_data=data)


@app.route('/login')
def login():
    print("Login")
    #return auth0.authorize_redirect(redirect_uri='http://localhost:3000/callback', audience=AUTH0_AUDIENCE)
    return auth0.authorize_redirect(redirect_uri='http://localhost:5000/callback')


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            # Redirect to Login page here
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


@app.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html',
                           userinfo=session['profile'],
                           userinfo_pretty=json.dumps(session['jwt_payload'], indent=4))


@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('home', _external=True), 'client_id': '90ycfYTmNMgEpY7x4a2fquPoW5iB0N77'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

@app.route("/lightwave/")
def lightwaveclient():
    return render_template("lightwave.html")

@app.route('/lightwave/server')
@cross_origin()
def server():
    query = request.args

    t = {}
    if 'action' in query:
        action = query['action']
        if 'dblist' == action:
            # return list of databases the user can see

            t["database"] = []
            t["database"].append({"name":"mit-bit", "desc":"static database with only one static file as record"})
            t["success"] = True
        else:
            if 'record' in query:
                record = query["record"]
            if 'db' in query:
                db = query["db"]
                if 'alist' == action:
                    # return list of annotators

                    t["annotator"] = []
                    t["annotator"].append({"name": "atr", "desc": "reference beat, rhythm, and signal quality annotations"})
                    t["success"] = True
                elif 'rlist' == action:
                    # return list of records for db

                    t["record"] = []
                    t["record"].append("207")
                    t["success"] = True
                elif 'fetch' == action and len(record) > 0:
                    if 'dt' in query:
                        dt = int(query["dt"])
                    fetch = {}
                    if 'annotator' in query:
                        annotator = query["annotator"]
                        fetch["annotator"] = []
                        ta = {"name":annotator}
                        ta["annotation"] = []
                        # loop through beat info appending to annotation
                        for time, symbolAnnotation in lightwave_io.Annotations(record, db):
                            # for time, symbolAnnotation in zip(x,y):
                                ta["annotation"].append({"t":time, "a": lightwave_io.symbolLetter(symbolAnnotation), "s":0,"c":0,"n":0,"x":None})
                        ta["description"] = "" # get description from somewhere?
                        fetch["annotator"].append(ta)
                    elif 'signal' in query:
                        if 't0' in query:
                            t0 = int(float(query["t0"]))
                        else:
                            t0 = 0
                        tfreq = int(lightwave_io.RecordFreq(record, db)[0])
                        t0 = t0 * tfreq
                        tf = dt * tfreq + t0
                        print(type(t0), type(tf))
                        samp = lightwave_io.RecordSample(record, db)[t0: tf]
                        samp.insert(0, 0)
                        signal = {}
                        signal["name"] = "Unspecified"
                        signal["units"] = "mV"
                        signal["t0"] = t0
                        signal["tf"] = tf
                        signal["gain"] = 1
                        signal["base"] = 1024
                        signal["tps"] = 1
                        signal["scale"] = 1
                        signal["samp"] = [samp[x] - samp[x-1] for x in range(1, len(samp))]
                        fetch["signal"] = [signal]
                    else:
                        t["success"] = False
                    if 'success' not in t:
                        t["fetch"] = fetch
                        t["success"] = True
                else:
                    info = {"db": db, "record": record, "start": None, "end": None}
                    info["db"] = db
                    info["record"] = record
                    tfreq, duration = lightwave_io.RecordInfo(record, db)
                    info["tfreq"] = tfreq[0]
                    duration = duration/tfreq[0]
                    dmin = int(duration/60)
                    dsec = int(duration - dmin*60)
                    dmsec = round((duration - dmin*60 - dsec)*1000)
                    info["duration"] = "%d:%02d.%d" % (dmin, dsec, dmsec)
                    info["signal"] = [{"name": "Unspecified", "tps": 1, "units": None, "gain": 1, "adcres": 11, "adczero": 1024, "baseline": 1024}]
                    info["note"] = []
                    t["info"] = info
                    t["success"] = True
            else:
                t["success"] = False
                t["error"] = "Your request did not specify a database"
        if 'success' in t and t["success"]: t["version"] = "0.68"
    else:
        t["success"] = False
        t["error"] = "Your request did not specify a database"
    return Response(json.htmlsafe_dumps(t), mimetype='application/javascript; charset=uft-8')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=env.get('PORT', 5000))

