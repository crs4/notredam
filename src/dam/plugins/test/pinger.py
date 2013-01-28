import os
from mprocessor import log
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
    ping_method = FIXME  # Was: Proxy('Adapter').ping
    pinger = Pinger(ping_method)
    result = pinger.execute()
    return result


class Pinger:
    def __init__(self, method):
        self.method = method

    def ok(self, result):
        return result

    def ko(self, result):
        pass

    def execute(self):
        try:
            result = self.method()
            return self.ok(result)
        except:
            self.ko(None)
            raise

#
# Stand alone test
#
def test():
    print 'test'
    print run()
