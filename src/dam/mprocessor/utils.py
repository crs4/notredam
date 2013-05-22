import os
import sys
import urllib
import types
from subprocess import PIPE, Popen
from threading  import Thread
from Queue import Queue, Empty

from . import log

def normpath(path):
    ret = os.path.normpath(path)
    if ret.startswith('//'):
        return ret[1:]
    else:
        return ret

class RunProcError(Exception): 
    pass

MAX_BUFFER_SIZE = 8*1024
def _enqueue_data_and_close(fd, queue, logging=False):
    if logging:
        log.debug('starting enqueuing thread')

    while True:
        data = fd.read(MAX_BUFFER_SIZE)
        if data == '':
            # Signal EOF by enqueuing None
            if logging:
                log.debug('EOF reached')
            queue.put(None)
            break
        if logging:
            log.debug('enqueuing %d bytes' % (len(data), ))
        queue.put(data)

    if logging:
        log.debug('closing file descriptor and terminating enqueuing thread')
    fd.close()

class RunProc(object):
    """
    Wrapper for calling an external process.

    Parameters:
        exe: name of the executable
        argv: list of arguments
        env: dictionary of the environment settings to add to the existing environment
             if env contains the key "md_overwrite_env" the environment replaces the
             existing.
        cb:  callback(data, *cbargv) to receive the stdout of the process.
        cbargv: additional arguments to the callback
        do_log: verbose logging
    """
    @classmethod
    def run(cls, exe, argv=[], env={}, cb=None, cbargv=[], do_log=1):
        self = cls()
        self.exe = str(getattr(exe, 'exe', exe))
        self.argv = getattr(exe, 'argv', argv)
        if type(self.argv) in [types.UnicodeType, types.StringType]:
            self.argv = self.argv.split()
        self.argv = map(str, self.argv)
        if env.has_key('md_overwrite_env'):
            self.env = {}
        else:
            self.env = os.environ
        self.env.update(getattr(exe, 'env', env))
        self._log = do_log
        if self._log:
            log.debug('starting: %s %s' % (self.exe, ' '.join(self.argv)))
            if self._log > 1:
                log.debug('Environment: %s' % self.env)

        self._cb = cb     # called with the bytes received
        self._cbargv = cbargv  # additional arguments passed to the callback

        # spawn the process at low priority
        # FIXME: handle (unlikely) "nice" launch failure here
        self._proc = Popen(['nice', '-n', '20', 'ionice', '-n', '7', '-t',
                            self.exe] + self.argv, stdout=PIPE, env=self.env)
        self._queue = Queue()

        self.pid = self._proc.pid
        if self._log:
            log.debug('started subprocess - pid: %d' % (self.pid, ))

        self._iothread = Thread(target=_enqueue_data_and_close,
                                args=(self._proc.stdout, self._queue,
                                      self._log))
        self._iothread.start()
        
        while True:
            data = self._queue.get()
            if data is not None:
                if self._log:
                    log.debug('dequeued %d bytes' % (len(data), ))
                if self._cb is not None:
                    self._cb(data, *self._cbargv)
            self._queue.task_done()
            if data is None:
                # End of file reached --- see _enqueue_data_and_close()
                if self._log:
                    log.debug('received EOF - not waiting for more data')
                break

        # After the queue ends closed and the loop above
        # terminates, let's wait for the subprocess to end
        self._proc.wait()

        if self._proc.returncode != 0:
            raise RunProcError('error executing "%s %s" (return code: %s)'
                               % (self.exe, ' '.join(self.argv),
                                  self._proc.returncode))
        elif self._log:
            log.debug('subprocess at pid %d terminated correctly'
                      % (self.pid, ))
        return self

def doHTTP(url):
    # Open the given HTTP URL using 'GET' method, and return all data
    with urllib.urlopen(url) as f:
        ret = f.read()
    return ret
