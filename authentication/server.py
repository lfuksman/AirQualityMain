from functools import wraps
import json
from os import environ as env

import dotenv
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, redirect, render_template, session, url_for
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
import pyodbc

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


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=env.get('PORT', 5000))

