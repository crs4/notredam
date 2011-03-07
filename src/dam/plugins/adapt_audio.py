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
# Interface definition: used by the GUI
#
def inspect(workspace):
    variants = get_variants(workspace, 'audio')
    output_variants = get_variants(workspace, 'audio', auto_generated = True)
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
    
    
    width = 200
    audio_rate = {
                  'xtype': 'select',
                  'fieldLabel': 'Sample Rate (Hz)',
                  'name': 'audio_rate',                  
                  'width': 200,
                  'value':44100,
                  'values': [[44100],[48000],[59000] ]
    }
    
    
    bit_rate_b = {
                  'xtype': 'select',
                  'fieldLabel': 'Bit Rate (kbps)',
                  'name': 'audio_bitrate_b',
                  'width': 200,
                  'values': [[64, 64000], [80, 80000], [96, 96000], [112, 112000],[128, 128000], [160, 16000], [192, 192000], [224, 224000], [256, 256000], [590, 59000]],
                  'value': 128000,
                  'fields': ['kbps', 'bps'],                  
                  'valueField': 'bps',
                  'displayField': 'kbps',
                  'hiddenName': 'audio_bitrate_b'
    }
    
    bit_rate_kb = {
                  'xtype': 'select',
                  'fieldLabel': 'Bit Rate (kbps)',
                  'name': 'audio_bitrate_kb',
                  'width': 200,
                  'values': [[64], [80], [96], [112],[128], [160], [192], [224], [256], [590]],
                  'value': 128
    }
    
    
    
    return {
        'name': __name__,
       
        
        'params':[
            {   
                'name': 'source_variant',
                'fieldLabel': 'Source Rendition',
                'xtype': 'select',
                'values': variants,
                'value': variants[0],
                'description': 'input-variant',
                
                'help': ''
            },
            
            {   
                'name': 'output_variant',
                'fieldLabel': 'Output Rendition',
                'xtype': 'select',
                'values': output_variants,
                'value': output_variants[0],
                'description': 'output-variant',
                'default': 0,
                'help': ''
            },
             
                {
                 'xtype':'selectfieldset',
                 'fieldLabel': 'Name',
                 'title': 'Preset',
                 'select_name': 'preset',
                 'select_value': 'MP3',
                 'values':{
                    'MP3':[
                       audio_rate,
                       bit_rate_kb
                    ],
                    
                    'AAC':[
                       audio_rate,
                       bit_rate_b
                    ],
                    
                    'OGG':[
                           audio_rate,
                           {
                        'xtype': 'numberfield',
                        'name': 'audio_quality',    
                        'fieldLabel': 'Audio Quality',
                        'minValue': 0,
                        'maxValue': 1,
                        'allowDecimals': True,                    
                        'width': width,
                        'value': 0.9
                    }],
                    'WAV': [audio_rate]
                    
                      
                }
                 
             }
                      
            
        ]
                    
   } 

    

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

    
    
    
