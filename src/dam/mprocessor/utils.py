import os

def normpath(path):
    ret = os.path.normpath(path)
    if ret.startswith('//'):
        return ret[1:]
    else:
        return ret
