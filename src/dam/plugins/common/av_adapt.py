#
# Common class for implementing adapt_audio e adapt_video
#
import os
from json import loads
from twisted.python.failure import Failure
from mediadart import log

from dam.variants.models import Variant    
from dam.plugins.common.utils import get_source_rendition
from dam.core.dam_repository.models import Type
from dam.repository.models import get_storage_file_name

class AdaptAV:
    VIDEO_PRESETS = {
        'MATROSKA_MPEG4_AAC': 'video/x-m4v',
        'MP4_H264_AACLOW': 'video/mp4',
        'FLV': 'video/flv',
        'AVI': 'video/x-msvideo',
        'FLV_H264_AAC': 'video/flv',
        'MPEGTS': 'video/ts',
        'THEORA': 'video/ogg',
    }
    def __init__(self, deferred, adapter, presets):    
        self.deferred = deferred
        self.adapter_method = adapter
        self.presets = presets
    
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
                output_preset,   # a mime type or a Mediadart PRESET
                **preset_params  # additional parameters (see adapter server for explanation)
                ):

        log.info('%s.execute' % self)
        log.info('output_preset %s'%output_preset)
        log.info('self.presets %s'%self.presets)
        if output_preset not in self.presets:
            raise  Exception('%s: unsupported output_preset' % (self, output_preset))

        try:
            output_type = Type.objects.get_or_create_by_mime(self.presets[output_preset])
            item, source = get_source_rendition(item_id, source_variant, workspace)
            output_variant_obj = Variant.objects.get(name = output_variant)
            output_component = item.create_variant(output_variant_obj, workspace, output_type)
            output_component.source = source
            output_file = get_storage_file_name(item.ID, workspace.pk, output_variant_obj.name, output_type.ext)
        except Exception, e:
            self.deferred.errback(Failure(e))
            return
                
        d = self.adapter_method(source.uri, output_file, output_preset, preset_params)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_component])
        return self.deferred
