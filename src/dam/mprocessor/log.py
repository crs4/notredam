import os
import sys
import inspect
import codecs
import time
import traceback
from dam.mprocessor.config import Configurator

def conf_get(func, name, default):
    try:
        ret = func('LOG', name)
    except:
        ret = default
    return ret

c = Configurator()
__levels = {'error': 0, 'warning':1, 'info':2, 'debug':3}
__main_name =os.path.basename(getattr(sys.modules['__main__'], '__file__', 'unknown')).split('.')[0]
__rootdir = inspect.getsourcefile(conf_get)[:-len('log/__init__.py')]
__rootlen = len(__rootdir)
__level = __levels[conf_get(c.get, 'level', 'error').lower()]
__console = conf_get(c.getboolean, 'console', True)
__maxsize = conf_get(c.getint, 'max_file_size', 100)*1000000
__logdir = conf_get(c.get, 'logdir', None)
__basetime = None
__f, __fname, __fnum = None, None, 0


def __check_dir(curhead):
    "Check that directory curhead exists, creating recursively the whole tree if needed"
    if not os.path.exists(curhead):
        head, _ = os.path.split(curhead)
        if not os.path.exists(head):
            __check_dir(head)
        os.mkdir(curhead)

def __check_logfile():
    global __f, __fname, __main_name, __console, __logdir, __fnum
    if __f: 
        if __f.tell() < __maxsize:
            return
        else:
            __f.close()
            __f = None
            __fnum += 1
    if not __fname:
        __check_dir(os.path.abspath(__logdir))
        __fname = '%s-%s' % (__main_name, time.strftime('%b%d-%H:%M', time.localtime()))
    if not __f:
        __f = codecs.open(os.path.join(__logdir, '%s-%03d.log' % (__fname, __fnum)), encoding='latin-1', mode='w')
        if __fnum == 0:
            start_msg = '------ Logging starts at: %s\n' % time.ctime()
            __f.write(start_msg)
            if __console:
                print(start_msg)

def __log(tag, msg):
    global __rootdir, __rootlen, __logdir, __f, __console, __basetime
    filename, linenum = traceback.extract_stack()[-3][:2]
    filename = os.path.basename(filename)
    if not __basetime:
        __basetime = time.time()
    elapsed = '%04.1f' % (time.time() - __basetime)
    msg = '%s|%s|%s:%d| %s\n' % (tag[:3], elapsed, filename, linenum, msg.replace('\\n', '\n'))
    if __logdir:
        __check_logfile()
        __f.write(msg)
        __f.flush()
    if __console:
        print msg,

debug = info = warning = error = lambda msg : None
if __level >= 3:
    debug = lambda msg: __log('DEBUG', msg)

if __level >= 2:
    info = lambda msg: __log('INFO', msg)

if __level >= 1:
    warning = lambda msg: __log('WARNING', msg)

error = lambda msg: __log('ERROR', msg)

    
