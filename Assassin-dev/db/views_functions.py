import numpy as np

def signedIn(request):
    try:
        name = request.session['signedIn']
        return True
    except Exception:
        return False
    
def convertTo64(num):
    newnum = str(np.int64(num))
    zeros = 8-len(newnum)
    for x in range(zeros):
        newnum = "0"+newnum

    return newnum

def convertFrom64(num):
    cont = True
    while(cont):
        if num[0] == "0":
            num = num[1:]
        else:
            cont = False

    return int(np.int64(num))

def getUser(request):
    try:
        return request.session['user']
    except Exception:
        return None
