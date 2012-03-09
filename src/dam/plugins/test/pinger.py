import os
from twisted.internet import defer, reactor
from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy

# This is due to a bug in Django 1.1
from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models
get_models()

from dam.variants.models import Variant    
from dam.plugins.common.av_adapt import AdaptAV
from dam.plugins.adapt_audio_idl import inspect



def run(workspace, target):
    deferred = defer.Deferred()
    ping_method = Proxy('Adapter').ping
    pinger = Pinger(deferred, ping_method)
    reactor.callLater(0, pinger.execute)
    return deferred


class Pinger:
    def __init__(self, deferred, method):
        self.deferred = deferred
        self.method = method

    def ok(self, result):
        self.deferred.callback(result)

    def ko(self, result):
        self.deferred.errback(result)

    def execute(self):
        d = self.method()
        d.addCallbacks(self.ok, self.ko)
        

#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    d = run( )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
