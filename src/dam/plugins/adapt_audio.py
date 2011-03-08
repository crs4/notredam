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


AUDIO_PRESETS = {
     'MP3': 'audio/mpeg',
    'AAC':'audio/x-mp4',
    'WAV':'audio/x-wav',
    'OGG': 'audio/ogg',
}

def run(*args, **kw_args):
    deferred = defer.Deferred()
    adapt_method = Proxy('Adapter').adapt_audio
    adapter = AdaptAV(deferred, adapt_method, AUDIO_PRESETS)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred

class AdaptAudio:
   
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
                output_preset,   # a mime type
                **preset_params   # json encoded dictionary
                ):

	log.info('AdaptAudio.execute')
	log.debug('preset_params %s'%preset_params)		
	log.debug('self.AUDIO_PRESETS %s'%self.AUDIO_PRESETS)
	if output_preset not in self.AUDIO_PRESETS:
		raise  Exception('Unsupported output_preset for audio adaptation %s' % output_preset)
	else:
	    preset = self.AUDIO_PRESETS[output_preset]
	#~ preset_params = loads(preset_params)
	try:
		output_type = Type.objects.get_or_create_by_mime(output_preset)
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
            output_preset =  'WAV',
            audio_rate=44100   # per esempio
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
