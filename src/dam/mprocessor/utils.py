import os
import types
from twisted.internet import defer, reactor, protocol
from twisted.python.failure import Failure
from twisted.internet import defer, reactor
from twisted.web.client import HTTPClientFactory
from . import log

def normpath(path):
    ret = os.path.normpath(path)
    if ret.startswith('//'):
        return ret[1:]
    else:
        return ret

class RunProcError(Exception): 
    pass

class RunProc(protocol.ProcessProtocol):
    """
    Wrapper for calling an external process in a twisted-approved way.

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
        # spawn the process at low priority
        self._proc = reactor.spawnProcess(self, 'nice', ['nice', '-n', '20', 'ionice', '-n', '7', '-t', self.exe] + self.argv, env=self.env)
        if self._proc is None:
            raise RunProcError('failed to launch %s' % self._script.exe )
        else:
            self.pid = str(self._proc.pid) or 'unavailable'
        if self._log > 1:
            log.debug('started proc %s' % (self.pid))
        self._cb = cb     # called with the bytes received
        self._cbargv = cbargv  # additional arguments passed to the callback
        return self

    def __init__(self):
        self.__stdout = ""
        self.__stderr = ""
        self._max_stdout = 8*1024
        self._max_stderr = 8*1024
        self.__requests = []

    def getResult(self):
        """
        Return a Deferred which will fire with the result of L{parseChunks}
        when the child process exits.
        """
        d = defer.Deferred()
        self.__requests.append(d)
        return d

    def _fireResultDeferreds(self, result):
        """
        Callback all Deferreds returned up until now by L{getResult}
        with the given result object.
        """
        requests = self.__requests
        self.__requests = None
        for d in requests:
            d.callback(result)

    def _fireErrorDeferreds(self, result):
        """
        Callback all Deferreds returned up until now by L{getResult}
        with the given result object.
        """
        requests = self.__requests
        self.__requests = None
        for d in requests:
            d.errback(Failure(result))

    def outReceived(self, data):
        """
        Accumulate output from the child process in a list.
        """
        if self._cb:
            self._cb(data, *self._cbargv)
        else:
            self.__stdout = self.__stdout[-self._max_stdout:] + data

    def errReceived(self, data):
        log.error('proc %s(echoing stderr): %s' % (self.pid, data.strip()))
        self.__stderr = self.__stderr[-self._max_stderr:] + data

    def processEnded(self, reason):
        """
        Handle process termination by parsing all received output and firing
        any waiting Deferreds.
        """
        if reason.value.exitCode == 0:
            self._fireResultDeferreds({'exitCode':0, 'data':''.join(self.__stdout)})
        else:
            self._fireErrorDeferreds({'exitCode':reason.value.exitCode, 'data':self.__stderr})

def doHTTP(url, data='', method='POST', headers = {}, followRedirect=False):
    factory = HTTPClientFactory(url=str(url), method=method, postdata=data,
               headers=headers, followRedirect=followRedirect)
    reactor.connectTCP(factory.host, factory.port, factory)
    return factory
