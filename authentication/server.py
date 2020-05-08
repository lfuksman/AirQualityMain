from functools import wraps
import json
from os import environ as env
from scipy.io import loadmat

import dotenv
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, redirect, render_template, session, url_for, request, Response, json
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
import pyodbc
from flask_table import Table, Col, LinkCol
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, SelectField
from flask_cors import cross_origin

import lightwave_io
import pickle

DATABASE_NAME = 'ECG_Database' # the name of the SQL Server Database in SSMS


app = Flask(__name__)
AUTH0_AUDIENCE = 'https://dev-92zb026a.auth0.com/userinfo' # Configure based on the domain of Auth0 web application
app.secret_key = 'secret_key'
JWT_PAYLOAD = 'jwt_payload'
PROFILE_KEY = 'profile'
conn_string = (
    r'DRIVER={ODBC Driver 17 for SQL Server};' # Change the value based on local machine
    r'SERVER=DANICOMPUTER;' # Change the value based on local machine
    r'DATABASE=ECG_Database;'
    r'Trusted_Connection=yes;'
)
# When establishing a connection, pyodbc defaults to autocommit=False in accordance with Python's DB-API spec. Therefore when the first SQL statement is executed, 
# ODBC begins a database transaction that remains in effect until the Python code does a .commit() or a .rollback() on the connection.
# SQL Server does not allow CREATE DATABASE to be executed within such a transaction, so we need to have the connection in autocommit mode before issuing such statements.
# That can be accomplished when the connection is opened.
conn = pyodbc.connect(conn_string, autocommit=True)
cursor = conn.cursor()

oauth = OAuth(app)

auth0 = oauth.register( # Connection to Auth0 api, configure to match the values in Auth0 web application
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
    #print("redirected here")
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
    user_id = userinfo['sub']
    #print(username)
    query = "SELECT UserRoleId FROM Users WHERE Username = ?" # get the userRoleId associated with the username of the user that logged in 
    cursor.execute(query, username)
    userRole = cursor.fetchone() # UserRoleId
    ### if the user doesn't exist - add the user and re-query 
    if userRole is None:
        addUser(user_id, username)
        #requery 
        cursor.execute(query, username)
        userRole = cursor.fetchone()
    print(userRole.UserRoleId)

    #############this is where we can get the result from the ML algorithm and put it in the database using pickle.    ###############################################
    
    #queryUserId = "SELECT UserId FROM Users WHERE Username = ?"                      # get the UserId of the User the annotated signal is tied to
    #cursor.execute(queryUserId, username)
    #USER = cursor.fetchone()                                                         # UserId
    #USERID = USER.UserId
    #r = loadmat("../sampleRecMitdb207.mat")                                          # the ML algorithm will send back 'r' so we just need a way to store in the db
    #rec = pickle.dumps(r)                                                            # the loadmat function was used just for test data 
    #addRecord(rec, USERID)                                                           # compress the file with pickle.dumps, associate with user and insert into db

    ##################################################################################################################################################################
    
    if userRole.UserRoleId == 1:
        return redirect('/adminDashboard')
    #this is where we redirect to lightwave...
    else:
        return redirect('/dashboard')



@app.route('/adminDashboard')
def adminDashboard():
    cursor.execute('SELECT * FROM Users') # Get a list of all users
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    table = Results(results)
    table.border = True
    return render_template('adminDashboard.html', table=table)


class Results(Table): # Table of all users that displays on the admin dashboard
    Username = Col('Username')
    UserRoleId = Col('UserRoleId')
    edit = LinkCol('Edit', 'edit', url_kwargs=dict(Username= 'Username'))


class EditableForm(Form): # Form to allow admin to edit user roles
    roles_options = [('1', '1'), ('2', '2'), ('3', '3')]
    Username = StringField('Username')                              #edit the username 
    UserRoleId = SelectField('UserRoleId', choices=roles_options)


@app.route('/edit/<string:Username>', methods=['GET', 'POST']) # Renders the editable form
def edit(Username):
    form = EditableForm(request.form)
    form.Username.data=Username
    return render_template('editableForm.html', form=form) 


@app.route('/updateInfo', methods=['GET', 'POST'])
def updateInfo(): # Update user information in database
    Username = request.form.get("Username")
    UserRoleId= request.form.get("UserRoleId")
    cursor.execute('UPDATE Users SET UserRoleId =? WHERE Username =?', (UserRoleId, Username))
    return redirect('/adminDashboard')


@app.route('/login')
def login(): # Login page
    return auth0.authorize_redirect(redirect_uri='http://localhost:5000/callback') 


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            # Redirect to Login page here
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


#this is where we could redirect to lightwave with the user credentials
@app.route('/dashboard')
@requires_auth
def dashboard():    
    return redirect('/lightwave/')
    #return render_template('dashboard.html',
                            #userinfo=session['profile'],
                            #userinfo_pretty=json.dumps(session['jwt_payload'], indent=4))


@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('home', _external=True), 'client_id': '90ycfYTmNMgEpY7x4a2fquPoW5iB0N77'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@app.route("/lightwave/")
def lightwaveclient(): #Redirect to lightwave
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
            #t["database"].append({"name":"ECG-Database", "desc":"static database with only one static file as record"})
            #Can change the name of RECORDS later on.... 
            userinfo=session['profile']
            username=userinfo['name']
            queryUser = "SELECT UserId FROM Users WHERE Username = ?"
            cursor.execute(queryUser, username)
            USER = cursor.fetchone()
            USERID = USER.UserId  
            
            queryUserRole = "SELECT UserRoleId FROM Users WHERE Username = ?"  # get the UserRoleId of the user
            cursor.execute(queryUserRole, username)
            UserRole = cursor.fetchone()

            ##### The if statement below executes if the user is a doctor #####
            if UserRole.UserRoleId == 3: # if the user is a doctor then query database for users that the doctor is linked to 
                queryPatients = "SELECT Username FROM Users WHERE DoctorId = ?" 
                cursor.execute(queryPatients, USERID)
                patients = cursor.fetchall()
                #print(patients)
                for row in patients:
                    #print(row[0])  
                    t["database"].append({"name":DATABASE_NAME, "desc":"Patient: " + str(row[0])})  #cast to list because Row instance isn't JSON Serialiazable       

            else: #if the user is a patient only show their records
                t["database"].append({"name":DATABASE_NAME, "desc":"Records"}) 
            t["success"] = True
           # print(t)
        else:
            if 'record' in query:
                record = query["record"]
            if 'db' in query:
                db = query["db"]
                #print(query)
                if 'alist' == action:
                    # return list of annotators
                    t["annotator"] = []
                    t["annotator"].append({"name": "atr", "desc": "reference beat, rhythm, and signal quality annotations"})
                    t["success"] = True
                elif 'rlist' == action:
                    # return list of records for db
                    t["record"] = []
                    #print(query)
                    #this is where we decide what records the user can see...                  
                    #get the automatically created UserId from the database to use to narrow records results on lightwave page
                    userinfo=session['profile']
                    username=userinfo['name']

                    queryUserRole = "SELECT UserRoleId FROM Users WHERE Username = ?"  # get the UserRoleId of the user
                    cursor.execute(queryUserRole, username)
                    UserRole = cursor.fetchone()

                    queryUser = "SELECT UserId FROM Users WHERE Username = ?"
                    cursor.execute(queryUser, username)
                    USER = cursor.fetchone()
                    USERID = USER.UserId 
                    # print(UserRole.UserRoleId)      
                    # select the userId and query for their records 
                    if UserRole.UserRoleId == 3:
                        queryRecords = """SELECT RecordId, ROW_NUMBER() OVER(ORDER BY [RecordId] ASC) AS Record#, FORMAT ([Record_DateTime], 'MM/dd/yyyy  hh:mm tt') as Date FROM Records AS rec JOIN dbo.Users usr ON usr.UserId = rec.UserId WHERE usr.DoctorId = ? ORDER BY Date ASC"""
                    else:                               
                        queryRecords = "SELECT RecordId, ROW_NUMBER() OVER(ORDER BY [RecordId] ASC) AS Record#, FORMAT ([Record_DateTime], 'MM/dd/yyyy  hh:mm tt') as Date FROM Records WHERE UserId = ? ORDER BY Date ASC"
                    cursor.execute(queryRecords, USERID)
                    records = cursor.fetchall()                   
                    for row in records:
                        #row = list(row)
                        t["record"].append((row[0], "R" + str(row[1]) + " - " + str(row[2])))  # this is how we format what is displayed in the drop down to the user                 
                    t["success"] = True                                                        # lightwave.js line 620+ was modified to display the format above correctly
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
                #this is where the record clicked in the drop down is passed to lightwave_io to be read and processed
                else:
                    info = {"db": db, "record": record, "start": None, "end": None}
                    #print(record)
                    info["db"] = db
                    info["record"] = record
                    #this is where we get the pickle object record to pass 
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

# check if all the necessary tables exist in the database. For each table that doesn't exist, one is created with the necessary properities to work with this project
def checkTablesExist():
    cursor.execute("USE " + DATABASE_NAME)
    if cursor.tables(table='Users', tableType='TABLE').fetchone():
        print("Users table exists")     
    else:
        addUsersTable()
    if cursor.tables(table='Records', tableType='TABLE').fetchone():
       print("Records Table exists")
    else:
        addRecordsTable()
    if cursor.tables(table='UserRoles', tableType='TABLE').fetchone():
        print("UserRoles table exists")        
    else:
        addUserRolesTable()

# Add user to the database with the username associated with the Auth0 sign-up
def addUser(user_id, username):
    newUserName = username
    USER_ID = user_id
    cursor.execute('''
                INSERT INTO Users (Auth0_UserId, Username, UserRoleId)      
                VALUES
                (?,?,'')
                ''', USER_ID, newUserName)     # USER_ID is the id given by Auth0, UserRoleId defaults to 0 
    conn.commit()    # the Users table has a Primary Key that is auto-generated each time a new user is entered into the database. 

# check if the database exists on the local machine, if not one is created.
def checkDB_Exists():
    database = DATABASE_NAME
    query = "SELECT * FROM sys.databases WHERE name = ?"
    cursor.execute(query, database)
    if cursor.fetchone() is None:
        query = "CREATE DATABASE " + DATABASE_NAME
        cursor.execute(query)
        conn.commit()        
        query = "ALTER DATABASE " + DATABASE_NAME + " SET AUTO_UPDATE_STATISTICS ON"
        cursor.execute(query)
        conn.commit() 
        query = "ALTER DATABASE " + DATABASE_NAME + "  SET TRUSTWORTHY ON "
        cursor.execute(query) 
        conn.commit()  
        query = "ALTER DATABASE " + DATABASE_NAME + " SET  READ_WRITE"
        cursor.execute(query)  
        conn.commit()
    else:
        print('Database EXISTS')

# add Users table if it does not exist
def addUsersTable():
    # create the table
    query = """CREATE TABLE [dbo].[Users](
	[UserId] [int] IDENTITY(1,1) NOT NULL,
	[Auth0_UserId] [nvarchar](50) NULL,
	[Username] [varchar](50) NOT NULL,
	[UserRoleId] [int] NULL,
	[DoctorId] [int] NULL,
    PRIMARY KEY CLUSTERED 
    ([UserId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]"""
    cursor.execute(query)
    conn.commit()
    query = "ALTER TABLE [dbo].[Users] ADD  CONSTRAINT [DF_Users_UserRoleId]  DEFAULT ((0)) FOR [UserRoleId]"     # default UserRoleId is 0 
    cursor.execute(query)
    conn.commit()

#add the Records table if it does not exist
def addRecordsTable():
    query = """CREATE TABLE [dbo].[Records](
	[RecordId] [int] IDENTITY(1,1) NOT NULL,
	[UserId] [int] NOT NULL,
	[RecordString] [varbinary](max) NOT NULL,
	[Record_DateTime] [datetime] NULL,
    CONSTRAINT [PK_RECORDS] PRIMARY KEY CLUSTERED 
    ([RecordId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]"""
    cursor.execute(query)
    conn.commit()
    query = "ALTER TABLE [dbo].[Records] ADD  CONSTRAINT [DF_RECORDS_Record_DateTime]  DEFAULT (getdate()) FOR [Record_DateTime]"
    cursor.execute(query)
    conn.commit()
    query = "ALTER TABLE [dbo].[Records]  WITH CHECK ADD  CONSTRAINT [FK_RECORDS_RECORDS] FOREIGN KEY([RecordId])REFERENCES [dbo].[Records] ([RecordId])"
    cursor.execute(query)
    conn.commit()
    query = "ALTER TABLE [dbo].[Records] CHECK CONSTRAINT [FK_RECORDS_RECORDS]"
    cursor.execute(query)
    conn.commit()

#add the UserRoles Table if it does not exist
def addUserRolesTable():
    query = """CREATE TABLE [dbo].[UserRoles](
	[UserRoleId] [int] NOT NULL,
	[UserRole] [varchar](50) NOT NULL,
    CONSTRAINT [PK_UserRoles] PRIMARY KEY CLUSTERED 
    ([UserRoleId] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]"""
    cursor.execute(query)
    conn.commit()
 
  
#add the pickled object to the database corresponding to this user 
def addRecord(data_string, user_id):
    cursor.execute('''
                INSERT INTO Records (UserId, RecordString)
                VALUES
                (?,?)
                ''', user_id, data_string)
    conn.commit()

# main function
if __name__ == "__main__":
    checkDB_Exists()
    checkTablesExist()
    app.run(host='127.0.0.1', port=env.get('PORT', 5000))

