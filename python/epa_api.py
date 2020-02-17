import requests
import pickle
from typing import Dict
from progress.bar import Bar

codeToState = {} # Stores the codes used by the API as keys and the values are the State's names
params = ['62101', '62201', '61101', '42101', '44201', '42401', '42602', '81104'] # list of param to request from EPA API
byear = 2019 # start year to gather data from
eyear = 2019 # end year to gather data from (inclusive)

# base function for request calls
def callAPI(url: str, params: dict):
    r = requests.get(url=url, params=params)
    return r.json() if r.ok else r

# wrapper function to add the email and key to the params dictionary
def addCredsAndCallAPI(url: str, params: dict):
    params["email"] = "test@aqs.api"
    params["key"] = "test"
    return callAPI(url, params)

# Simple call to get list of available states as parameters
def getStateList():
    return addCredsAndCallAPI('https://aqs.epa.gov/data/api/list/states', {})

# wrapper to set the url for request with params
def getDataByStateParams(params: dict):
    return addCredsAndCallAPI("https://aqs.epa.gov/data/api/dailyData/byState", params)

# Convert parameters to dict object for request
def getDataByState(param: str, bdate: str, edate: str, state: str):
        params = {}
        params['param'] = param
        params['bdate'] = bdate
        params['edate'] = edate
        params['state'] = state
        return getDataByStateParams(params)

# parses the state list response to local variable
def setStateList():
    response = getStateList()

    for k1 in response["Data"]:
        v = list(k1.values())
        codeToState[v[0]] = v[1]

# Loops through each state using the parameters passed in
def getDataForEachState(param: str, bdate: str, edate:str):
    t = []
    for k in codeToState:
        r = getDataByState(param, bdate, edate, k)
        bar.next() # increament the progress bar
        if "Data" in r:
            t.append(r["Data"])
    return t

# Helper function to build list of tuples for parameter years to be in the format EPA API accepts
def buildDates(byear: int, eyear: int):
    t = []
    for year in range(byear, eyear + 1):
        bdate = str(year) + "0101"
        edate = str(year) + "1231"
        t.append((bdate, edate))
    return t

# Loops through each year passed, calling getDataForEachState
def getDataForYears(param: str, byear: int, eyear: int):
    t = []
    for bdate, edate in buildDates(byear, eyear):
        t.append(getDataForEachState(param, bdate, edate))
    return t

# Helper function to loop though each param (EPA API parameter to determine data type for request)
def getData(params: list, byear: int, eyear: int):
    t = []
    for param in params:
        t.append(getDataForYears(param, byear, eyear))
    return t

setStateList() # Required

bar = Bar('Progress', max=len(codeToState)*len(params)*(eyear-byear+1))

# using a pickle file for storage
pickle.dump(getData(params, byear, eyear), open('output.p', 'wb'))

# mark the progress bar as complete
bar.finish()


