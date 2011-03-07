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
from dam.plugins.common.utils import get_source_rendition, get_variants, get_ext_by_type
from dam.core.dam_repository.models import Type

from uuid import uuid4

def new_id():
    return uuid4().hex

def inspect(workspace):
   
    media_types = get_ext_by_type('image')
    variants = get_variants(workspace, 'image')
    output_variants = get_variants(workspace, 'image', auto_generated = True)
#    source_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = False)]
#    output_variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), auto_generated = True, hidden = False)]
     
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
             'xtype':'fieldsetcontainer',
             'order_field_name': 'actions',
             'items':[{
              'xtype': 'movablecbfieldset',
              'title': 'Resize',
              'name': 'resize',
              'order_field_name': 'actions',
              'order_field_value': 'resize',
            
             
              'items':[{
                    'xtype':'numberfield',
                    'name': 'resize_h',
                    'fieldLabel': 'height',                    
                    'description': 'height',
                    'minValue':0,
#                    'value': 100,
                    'help': 'height of resized image in pixels'
                },
                {
                    'xtype':'numberfield',
                    'name': 'resize_w',
                    'fieldLabel': 'width',                    
                    'description': 'width',
#                    'value': 100,
                    'minValue':0,
                    'help': 'width of resized image in pixels'
                },
                
              ]
              },
               {
              'xtype': 'movablecbfieldset',
              'title': 'Crop',
              'name': 'crop',
             
              'order_field_name': 'actions',
              'order_field_value': 'crop',
              'items':[{
                    'xtype':'numberfield',
                    'name': 'crop_h',
                    'fieldLabel': 'height',                    
                    'description': 'height',
                    'minValue':0,
#                    'value': 100,
                    'help': 'heigth of crop area, default till bottom edge of image'
                },
                {
                    'xtype':'numberfield',
                    'name': 'crop_w',
                    'fieldLabel': 'width',                    
                    'description': 'width',
#                    'value': 100,
                    'minValue':0,
                    'help': 'width of crop area, default till right edge of image'
                },
                
                
              ]
              },
              {
              'xtype': 'watermarkfieldset',
              'title': 'Watermark',
              'name': 'watermark',
              'order_field_name': 'actions',
              'order_field_value': 'watermark',                            
               'renditions': variants
              },
              ]
             
             },
                         

              
              {   
                'name': 'output_format',
                'fieldLabel': 'format',
                'xtype': 'select',
                'values': media_types,
                'description': 'output_format',
                'value': '.jpg',
                'help': ''
            }
              
        ]
        
    } 


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
                item_id, 
                workspace, 
                source_variant,
                output_variant,
                output_format,
                actions,
                resize_h = None,
                resize_w = None,
                crop_w = None,
                crop_h = None,
                crop_x = None,
                crop_y = None,
                crop_ratio = None,
                pos_x_percent = None,
                pos_y_percent = None,
                wm_id = None):

        log.info('AdaptImage.execute')
        item, source = get_source_rendition(item_id, source_variant, workspace)
        if output_format == 'same_as_source':
            media_type = source.media_type
        else:
            media_type = Type.objects.get_or_create_by_filename('foo%s' % output_format)
        output_variant = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant, workspace, media_type)
                
        log.debug("[adapt_resource] from original component %s" % output_component.source)
        
        output_component.source = source
        argv = [] #for calling imagemagick
    
        for action in actions:
            if action == 'resize':
                argv +=  ['-resize', '%sx%s' % (resize_w, resize_h)]
                
            elif action == 'crop':
                if crop_ratio:
                    x, y = crop_ratio.split(':')
                    argv += ['-gravity', 'center', '-crop', '%sx%s%%+0+0' % (int(100./float(x)), int(100./float(y)))]
                else:
                    crop_x = crop_x or 0   # here None means 0
                    crop_y = crop_y or 0
                    argv += ['-gravity', 'center', '-crop', '%sx%s+%s+%s' % (int(crop_w), int(crop_h), int(crop_x), int(crop_y))]

            elif action == 'watermark':
                pos_x = int(pos_x_percent * source.width/100.)
                pos_y = int(pos_y_percent * source.height/100.)
                argv += ['cache://' + wm_id, '-geometry', '+%s+%s' % (pos_x,pos_y), '-composite']
        
        log.debug("calling adapter")
        extension = media_type.ext
        dest_res_id = get_storage_file_name(new_id(), workspace.pk, output_variant.name, extension)
        output_component.uri = dest_res_id
        output_component.save() 
        
        d = self.adapter_proxy.adapt_image_magick('%s[0]' % source.uri, dest_res_id, argv)
        d.addCallbacks(self.handle_result, self.handle_error, callbackArgs=[output_component])
        return self.deferred
    

def test():
    print 'test'
    item = Item.objects.get(pk=1)
    workspace = DAMWorkspace.objects.get(pk = 1)
    
    d = run(item.pk,
            workspace,
            source_variant = 'original',
            output_variant='fullscreen',
            output_format = '.jpg',
            actions = ['crop', 'resize'],
            resize_h=100,
            resize_w=100,
            crop_ratio="2:2",
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
