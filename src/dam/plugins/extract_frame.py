from twisted.internet import defer, reactor
from twisted.python.failure import Failure
from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy
import os

from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models

get_models()

from dam.repository.models import *
from dam.variants.models import Variant    
from dam.core.dam_repository.models import Type
from dam.workspace.models import DAMWorkspace
from dam.plugins.common.utils import get_source_rendition
from dam.plugins.extract_frame_idl import inspect
from dam.repository.models import Item, Component, Watermark, new_id, get_storage_file_name

from uuid import uuid4

def new_id():
    return uuid4().hex

def run(*args, **kw_args):
    deferred = defer.Deferred()
    frame_extractor = FrameExtractor(deferred)
    reactor.callLater(0, frame_extractor.execute, *args, **kw_args)
    return deferred

class FrameExtractor:
    def __init__(self, deferred):    
        self.deferred = deferred
        self.adapter_proxy = Proxy('Adapter')
    
    def handle_result(self, result, output_file, component):
        log.debug('handle_result %s' % str(result))
        log.debug("[save_component] component %s" % component.pk)        
        
        directory, name = os.path.split(output_file)
        component.uri = name
        component.save()
        self.deferred.callback(output_file)
        
    def handle_error(self, result):
        self.deferred.errback('error %s' % str(result))
    
    def execute(self,
                item_id, 
                workspace, 
                source_variant,
                output_variant,
                output_extension,  # with the leading '.'
                frame_w = None,
                frame_h = None,
                position = None):

        log.info('executing action extract_frame')
        try:
            item, source = get_source_rendition(item_id, source_variant, workspace)
            output_type = Type.objects.get_or_create_by_filename('foo%s' % output_extension)
            output_variant_obj = Variant.objects.get(name = output_variant)
            output_component = item.create_variant(output_variant_obj, workspace, output_type)
            output_component.source = source
            output_file = get_storage_file_name(item.ID, workspace.pk, output_variant_obj.name, output_type.ext)
        except Exception, e:
            self.deferred.errback(Failure(e))
            return
        
        d = self.adapter_proxy.extract_video_thumbnail(source.uri, output_file, (frame_w, frame_h), position)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_file, output_component])

    
#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a video comp.)
#
def test():
    print 'test'
    item = Item.objects.get(pk=1)
    workspace = DAMWorkspace.objects.get(pk = 1)
    
    d = run(4,
            workspace,
            source_variant = 'original',
            output_variant='thumbnail',
            output_format = 'image/png',
            frame_w = 100,
            frame_h = 100,
            position = 30,
            )
    print 'addBoth'
    d.addBoth(print_result)
    print 'dopo addBoth'
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
