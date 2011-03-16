import os
from twisted.internet import defer, reactor
from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy

from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models

get_models()

from dam.repository.models import *
from dam.variants.models import Variant    
from dam.workspace.models import DAMWorkspace
from dam.plugins.common.utils import get_source_rendition, get_ext_by_type
from dam.core.dam_repository.models import Type
#from dam.plugins.adapt_magick_idl import inspect
from dam.plugins.common.utils import splitstring

from uuid import uuid4

def run(*args, **kw_args):
    deferred = defer.Deferred()
    adapter = AdaptImage(deferred)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred

class AdaptImage:
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
                workspace, 
                item_id, 
                source_variant,
                output_variant,
                output_extension,
                cmdline
                ):

        log.info('AdaptImage.execute')
        item, source = get_source_rendition(item_id, source_variant, workspace)
        media_type = Type.objects.get_or_create_by_filename('foo%s' % output_extension)
        output_variant = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant, workspace, media_type)
        output_component.source = source
        output_component.uri = get_storage_file_name(item.ID, workspace.pk, output_variant.name, media_type.ext)
        output_component.save() 
                
        argv = splitstring(cmdline)
        d = self.adapter_proxy.adapt_image_magick('%s[0]' % source.uri, output_component.uri, argv)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_component])
        return self.deferred
    

def test():
    print 'test'
    item = Item.objects.get(pk=1)
    workspace = DAMWorkspace.objects.get(pk = 1)
    
    d = run( 
            workspace,
            item.pk,
            source_variant = 'original',
            output_variant='thumbnail',
            output_extension = '.jpg',
            cmdline="-resize 100x100 -annotate 90x90 'ME    FOX'",
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
