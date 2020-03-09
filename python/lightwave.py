from flask import Flask, request, json, Response, render_template
from flask_cors import cross_origin

import lightwave_io

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/')
@app.route('/index')
def index():
    return "Fix this hehehe"

@app.route("/lightwave/")
def lightwaveclient():
    return render_template("lightwave/lightwave.html")

# @app.route('/lightwave/<string:page_name>/')
# def render_static(page_name):
#     print(page_name)
#     return render_template('%s' % page_name)

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
            t["database"].append({"name":"mit-bit", "desc":"idk"})
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
                        # t:
                        # a:symbol
                        # s: 0
                        # c: 0
                        # n: 0
                        # x: null?
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
app.run()