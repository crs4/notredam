import os
from json import loads
from twisted.internet import defer, reactor
from twisted.python.failure import Failure
from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy

# This is due to a bug in Django 1.1
from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models
get_models()

from dam.repository.models import *
from dam.variants.models import Variant    
from dam.workspace.models import DAMWorkspace
from dam.plugins.common.utils import get_source_rendition
from dam.plugins.adapt_audio_idl import inspect
from dam.core.dam_repository.models import Type
from uuid import uuid4

def new_id():
    return uuid4().hex

def run(*args, **kw_args):
    deferred = defer.Deferred()
    adapter = AdaptAudio(deferred)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred

class AdaptAudio:
    AUDIO_PRESETS = {
        'audio/mpeg': 'MP3',
        'audio/x-mp4':'AAC',
        'audio/x-wav': 'WAV',
        'audio/ogg':  'OGG',
    }
    def __init__(self, deferred):    
        self.deferred = deferred
        self.adapter_proxy = Proxy('Adapter')
    
    def handle_result(self, result, component):
        log.debug('handle_result %s' % str(result))
        log.debug("[save_component] component %s" % component.pk)        
        
        if result:
            directory, name = os.path.split(result)
            component.uri = name
            component.save()
        else:
            log.error('Empty result passed to save_and_extract_features')
        self.deferred.callback(result)
        
    def handle_error(self, result):
        self.deferred.errback('error %s' % str(result))
    
    def execute(self,
                item_id,         # item pk
                workspace,       # workspace object
                source_variant,  # name of the variant
                output_variant,  # name of the variat
                output_format,   # a mime type
                preset_params,   # json encoded dictionary
                ):

        log.info('AdaptAudio.execute')
        if output_format not in self.AUDIO_PRESETS:
            raise  Exception('Unsupported output_format for audio adaptation %s' % output_format)
        else:
            preset = self.AUDIO_PRESETS[output_format]
        preset_params = loads(preset_params)
        try:
            output_type = Type.objects.get_or_create_by_mime(output_format)
            item, source = get_source_rendition(item_id, source_variant, workspace)
            output_variant_obj = Variant.objects.get(name = output_variant)
            output_component = item.create_variant(output_variant_obj, workspace, output_type)
            output_component.source = source
            output_file = get_storage_file_name(item.ID, workspace.pk, output_variant_obj.name, output_type.ext)
        except Exception, e:
            self.deferred.errback(Failure(e))
            return
                
        d = self.adapter_proxy.adapt_audio(source.uri, output_file, preset, preset_params)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_component])
        return self.deferred

#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
def test():
    print 'test'
    item = Item.objects.get(pk=2)
    workspace = DAMWorkspace.objects.get(pk = 1)
    
    d = run(item.pk,
            workspace,
            source_variant = 'original',
            output_variant=  'fullscreen',
            output_format =  'audio/mpeg',
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

    
    
    
