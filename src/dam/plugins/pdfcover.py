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
from dam.repository.models import get_storage_file_name
from dam.plugins.common.av_adapt import AdaptAV
from dam.plugins.adapt_audio_idl import inspect

#
# External interface
# 
def run(*args, **kw_args):
    deferred = defer.Deferred()
    adapter = PdfCover(deferred)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred


class PdfCover:
    def __init__(self, deferred):
        self.deferred = deferred
        self.adapter_proxy = Proxy('Adapter')

    def handle_result(self, result, outfile, component):
        log.debug('handle_result'   # result is empty on success
        
        directory, name = os.path.split(outfile)
        component.uri = name
        component.save()
        self.deferred.callback(outfile)
        
    def handle_error(self, result):
        self.deferred.errback('error %s' % str(result))
    
    def execute(self,
                item_id, 
                workspace, 
                source_variant,
                output_variant,
                output_extension,  # extension (with the '.') or "same_as_source"
                max_size,          # largest dimension
                ):

        log.info('AdaptImage.execute')
        item, source = get_source_rendition(item_id, source_variant, workspace)
        output_variant_obj = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant_obj, workspace, media_type)

        try:
            output_type = Type.objects.get_or_create_by_filename('foo%s' % output_extension)
            item, source = get_source_rendition(item_id, source_variant, workspace)
            output_variant_obj = Variant.objects.get(name = output_variant)
            output_component = item.create_variant(output_variant_obj, workspace, output_type)
            output_component.source = source
            output_file = get_storage_file_name(item.ID, workspace.pk, output_variant_obj.name, output_type.ext)
        except Exception, e:
            self.deferred.errback(Failure(e))
            return
                
        d = self.adapter_proxy.adapt_doc(source.uri, output_file, max_size)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_file, output_component])
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
            output_variant=  'preview',
            output_extension = '.jpg',
            max_size = 100,
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
