from scipy.io import loadmat

def convertNumpyArrayToList(np):
    t = []
    for a in np.tolist():
        # print(type(a))
        for b in a:
            # print(type(b))
            for c in b.tolist():
                for i in c:
                    # print(i)
                    t.append(i)
    return t
        
def symbolLetter(a):
    switcher={
        0:"N",
        1:"V",
        2:"A"
    }
    return switcher.get(int(a),"")

def Annotations(record, db):
    r = loadmat("../sampleRecMitdb"+record+".mat") # temporary, need to switch to database
    if 'rec_info' in r:
        rec_info = r["rec_info"]
        return zip(convertNumpyArrayToList(rec_info["ecg_locs"]), convertNumpyArrayToList(rec_info["beat_type"]))
    return []

def RecordInfo(record, db):
    r = loadmat("../sampleRecMitdb"+record+".mat") # temporary
    if 'rec_info' in r:
        rec_info = r["rec_info"]
        return (convertNumpyArrayToList(rec_info["Fs"]), len(convertNumpyArrayToList(rec_info["denoised_ecg"]))) # freq, duration, signal_info?

def RecordFreq(record, db):
    r = loadmat("../sampleRecMitdb"+record+".mat") # temporary
    if 'rec_info' in r:
        rec_info = r["rec_info"]
        return convertNumpyArrayToList(rec_info["Fs"])

def RecordSample(record, db):
    r = loadmat("../sampleRecMitdb"+record+".mat") # temporary
    if 'rec_info' in r:
        rec_info = r["rec_info"]
        return convertNumpyArrayToList(rec_info["denoised_ecg"])


tfreq, duration = RecordInfo("207", "")
duration = duration/tfreq[0]
dmin = int(duration/60)
dsec = int(duration - dmin*60)
dmsec = round((duration - dmin*60 - dsec)*1000)
print("%d:%02d.%d" % (dmin, dsec, dmsec))

# print(Annotations("207", ""))
# print(RecordInfo("207", ""))

# for x, y in Annotations("207", ""):
#     if isinstance(x, list) and isinstance(y, list):
#         print("are list")
#         for a, b in zip(x, y):
#             a = a.tolist()
#             b = b.tolist()
#             for i in range(len(a)):
#                 print(a[i], b[i])
#             # if isinstance(a, list) and isinstance(b, list):
#             #     print("is list again")
#             #     for c, d in zip(a, b):
#             #         # print(c,d)
#             #         for time, symbolAnnotation in zip(c, d):
#             #             print(time, symbolAnnotation)
#             # else:
#             #     for time, symbolAnnotation in zip(a, b):
#             #         print(time, symbolAnnotation)
#     else:
#         for time, symbolAnnotation in zip(x,y):
#             print(time, symbolAnnotation)