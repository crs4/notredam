from twisted.internet import defer, reactor
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
from dam.workspace.models import DAMWorkspace

from uuid import uuid4

def new_id():
    return uuid4().hex

def inspect(workspace):
    from django.db.models import Q
    variants = [[variant.name] for variant in Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False)]
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
                'description': 'input-variant',
                
                'help': ''
            },
            
            {   
                'name': 'output_variant',
                'fieldLabel': 'Output Rendition',
                'xtype': 'select',
                'values': variants,
                'description': 'output-variant',
                'default': 0,
                'help': ''
            },
            {
             'xtype':'fieldsetcontainer',
             'items':[{
              'xtype': 'movablecbfieldset',
              'title': 'Resize',
              'name': 'resize',
              
             
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
              'xtype': 'movablecbfieldset',
              'title': 'Watermark',
              'name': 'watermark',
              'items':[
                       {
                        'xtype': 'compositefield',
                        'items':[
                                 {
                                    'id': 'wm_id',
                                    'width': 160,
                                    'xtype':'textfield',
                                    'name': 'wm_id',
                                    'fieldLabel': 'image',                    
                                    'description': 'image',
                                    
                #                    'value': 100,
                                    'help': ''
                                },
                                {
                                 'xtype': 'watermarkbrowsebutton',
                                 'text': 'Browse',
                                 'values': variants
                                 
                                   
                                }
                        ]
                        },
                        {
                         'xtype': 'watermarkposition'
                         
                         },
                        
              ]
              },
              ]
             
             },
                         

              
              {   
                'name': 'output_format',
                'fieldLabel': 'format',
                'xtype': 'select',
                'values': [['jpeg'], ['bmp'], ['gif'], ['png']],
                'description': 'output_format',
                
                'help': ''
            }
              
        ]
        
    } 

theProxy = None

def run(*args, **kw_args):
    #log.debug('adapt_image')
    #global theProxy
    #log.debug('adapt_image1')
    #log.debug('adapt_image1 %s' % str(theProxy))
    #log.debug('adapt_image2')
    #if theProxy is None:
        #log.debug('### new instance of Proxy')
    #    theProxy = Proxy('Adapter')
    #else:
    #    log.debug('### reusing proxy instance %s' % str(theProxy))
    deferred = defer.Deferred()
    adapter = Adapter(deferred, theProxy)
    reactor.callLater(0, adapter.execute, *args, **kw_args)
    return deferred

class Adapter:
    def __init__(self, deferred, proxy):    
        self.deferred = deferred
        self.adapter_proxy = Proxy('Adapter') #proxy
    
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

        log.info('executing adaptation')
        item = Item.objects.get(pk = item_id)
        source = Component.objects.get(workspace=workspace, variant__name=source_variant, item=item)
        
        output_variant = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant, workspace)
                
        log.debug("[adapt_resource] from original component %s" % output_component.source)
        
        output_component.source = source
        argv = [] #for calling imagemagick
    
        for action in actions:
            if action == 'resize':
                argv +=  ['-resize', '%dx%d' % (resize_w, resize_h)]
                
            elif action == 'crop':
                if crop_ratio:
                    x, y = crop_ratio.split(':')
                    argv += ['-gravity', 'center', '-crop', '%dx%d%%+0+0' % (int(100./float(x)), int(100./float(y)))]
                else:
                    crop_x = crop_x or 0   # here None means 0
                    crop_y = crop_y or 0
                    argv += ['-crop', '%sx%s+%s+%s' % (int(crop_w), int(crop_h), int(crop_x), int(crop_y))]

            elif action == 'watermark':
                pos_x = int(pos_x_percent * source.width/100.)
                pos_y = int(pos_y_percent * source.height/100.)
                argv += ['cache://' + wm_id, '-geometry', '+%s+%s' % (pos_x,pos_y), '-composite']
        
        log.debug("calling adapter")
        dest_res_id = get_storage_file_name(item.ID, workspace.pk, output_variant.name, output_format)
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
            output_format = 'jpg',
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

    
    
    
