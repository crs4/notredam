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

from dam.plugins.common.av_adapt import AdaptAV
from dam.plugins.adapt_audio_idl import inspect

VIDEO_PRESETS = {
    'MATROSKA_MPEG4_AAC': 'video/x-m4v',
    'MP4_H264_AACLOW': 'video/mp4',
    'FLV': 'video/flv',
    'AVI': 'video/x-msvideo',
    'FLV_H264_AAC': 'video/flv',
    'MPEGTS': 'video/ts',
    'THEORA': 'video/ogg',
}

def run(*args, **kw_args):
    deferred = defer.Deferred()
    adapt_method = Proxy('Adapter').adapt_video
    adapter = AdaptAV(deferred, adapt_method, VIDEO_PRESETS)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred

#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=2)
    workspace = DAMWorkspace.objects.get(pk = 1)
    
    d = run(item.pk,
            workspace,
            source_variant = 'original',
            output_variant=  'fullscreen',
            output_preset =  'audio/mpeg',
            preset_params =  u'{"audio_bitrate_kb": "128"}',   # per esempio
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
