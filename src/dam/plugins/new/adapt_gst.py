from twisted.internet import defer, reactor
from dam.core.dam_repository.models import Type
from dam.variants.models import Variant
from dam.repository.models import get_storage_file_name
from dam.plugins.common.utils import get_source_rendition, splitstring
from dam.plugins.extract_basic import AVFeatures

from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy


from xadapt_video import pipelines, get_preset_params, TBD

def run(*args, **kw_args):
    deferred = defer.Deferred()
    remote = Proxy('GenericCmdline')
    adapter = AdaptVideo(deferred, remote)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred

class AdaptVideo:
    def __init__(self, deferred, adapter):    
        self.deferred = deferred
        self.adapter = adapter

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

    def finalize_params(self, params, source, **kwargs):
        "Override in derived classes to provide specialized param processing"
        av = AVFeatures(source)
        max_w, max_h = int(params.get('width', 0)), int(params.get('height', 0))
        w = w_orig = av.get_video_width()
        h = h_orig = av.get_video_height()
        alfa = min(float(max_w)/float(w_orig), float(max_h)/float(h_orig))
        if 0 < alfa < 1:
            w, h =  int((w_orig * alfa)/2)*2, int((h_orig * alfa)/2)*2

        params.update({'in_filename': source.uri, 
                       'out_filename': kwargs['output_file'],
                       'video_width': w,
                       'video_height': h, 
                       'video_duration': av.get_video_duration(),})
        return params


    def execute(self,
                workspace,       # workspace object
                item_id,         # item pk
                source_variant,  # name of the variant
                output_variant,  # name of the variat
                output_preset,   # a mime type or a Mediadart PRESET
                **preset_params  # additional parameters (appropriate pipeline for explanation)
                ):

        log.info('%s.execute' % self)
        log.info('output_preset %s'%output_preset)
        if output_preset not in pipelines:
            raise  Exception('%s: unsupported output_preset' % (self, output_preset))

        # get basic data (avoid creating stuff in DB)
        output_type = Type.objects.get_or_create_by_mime(pipelines[output_preset]['mime'])
        item, source_component = get_source_rendition(item_id, source_variant, workspace)
        output_file = get_storage_file_name(item.ID, workspace.pk, output_variant, output_type.ext)

        # load defaults
        params = get_preset_params(output_preset)
        params.update(preset_params)
        params.update(self.finalize_params(params, source_component, output_file=output_file))
        cmdline = pipelines[output_preset]['cmdline'] % params
        if TBD in cmdline:
            raise Exception('missing required parameter from preset')

        output_variant_obj = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant_obj, workspace, output_type)
        output_component.source = source_component

        args = splitstring(cmdline)
        print '######### args:\n', args
        #return self.deferred.callback('ok')
        env = {}
        proxy = Proxy(pipelines[output_preset]['server'])
        d = proxy.call('gst-launch-0.10', args)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_component])
        return self.deferred
    


#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from twisted.internet import defer, reactor
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=1)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant = 'original',
            output_variant=  'fullscreen',
            output_preset =  'FLV',
            preset_params =  {},   # per esempio
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
