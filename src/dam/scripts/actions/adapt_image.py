from twisted.internet import defer
from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy
import os

from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models

get_models()

from dam.repository.models import Component
from dam.variants.models import Variant
from dam.repository.models import Item    
from dam.workspace.models import DAMWorkspace

from uuid import uuid4

def new_id():
    return uuid4().hex

def inspect():
    return {
        'name': __name__,
        'parameter_groups':{
        'resize':['width', 'height'],
        'crop':['ratio'],
            'watermark': ['pos_x_percent','pos_y_percent', 'component_id']
            
            
            },
            'width': {
            'type': 'int',
            'description': 'width',
            'default': 100,
            'help': ''
            
            
        },     
        'actions':{
            'type': 'list',
            'available_values':['resize', 'crop', 'watermark']
                 
        },
        'height': {
            'type': 'int',
            'description': 'height',
            'default': 100,
            'help': ''
                       
        }, 
         'ratio':{
            'type': 'string',
            'description': 'ratio',
            'default': '1:1',
            'help': ''
                       
        },
        
        'wm_id':{
            'type': 'component_id',
            'description': 'component',
            'default': '',
            'help': ''
                       
        },
         'pos_x_percent':{
            'type': 'string',
            'description': 'pos_x_percent',
            'default': 0,
            'help': ''
                       
        },
        
         'pos_y_percent':{
            'type': 'string',
            'description': 'pos_y_percent',
            'default': 0,
            'help': ''
                       
        },
    
        'output_variant': {
            'type': 'output-variant',
            'description': 'output-variant',
            'default': 0,
            'help': ''
        },
#        'source_variant': {
#            'type': 'input-variant',
#            'description': 'input-variant',
#            'default': 0,
#            'help': ''
#        }      
        
         
        } 

def run(item_id, workspace, source_variant, output_variant, output_format, actions, height = None, width = None, ratio = None, pos_x_percent = None, pos_y_percent = None, wm_id = None):
    return Adapter().execute(item_id, workspace, source_variant, output_variant, output_format, actions, height, width, ratio, pos_x_percent, pos_y_percent, wm_id)

class Adapter:

    def __init__(self):    
        self.deferred = defer.Deferred()
    
    def handle_result(self, result, component):
        log.debug('result %s'%result)
        log.debug("[save_component] component %s" % component.pk)        
        
        if result:
            dir, name = os.path.split(result)
            component._id = name
            component.save()
        else:
            log.error('Empty result passed to save_and_extract_features')
        self.deferred.callback(result)
        
    def handle_error(self, result, component):
        self.deferred.errcallback('error')
    
    def execute(self,item_id, workspace, source_variant, output_variant, output_format, actions, height, width, ratio, pos_x_percent, pos_y_percent, wm_id):
        log.info('executing adaptation')
        item = Item.objects.get(pk = item_id)
        source_variant = Variant.objects.get(name = source_variant)
        source = item.get_variant(workspace, source_variant)
        
        log.debug('item %s'%item)
        log.debug('workspace %s'%workspace)
        log.debug('source_variant %s'%source_variant)

        
        output_variant = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant, workspace)
                
        log.debug("[adapt_resource] from original component %s" % output_component.source.ID)
        
        orig = output_component.source
        dest_res_id = new_id()
        
        args ={}
        argv = [] #for calling imagemagick
    
    
       
        source_width = source.width
        source_height = source.height
        for action in actions:
            if action == 'resize':
                log.debug('source.width %s'%source.width)
                log.debug('source.height %s'%source.height)
                width = min(width,  source.width)
                height = min(height,  source.height)
                
                
                
                argv +=  ['-resize', '%dx%d' % (width, height)]
                
                aspect_ratio = source.height/source.width 
                alfa = min(width/source.width, height/source.height)
                source_width = alfa*source.width
                source_height = alfa*source.height
                
            elif action == 'crop':
                
                x_ratio, y_ratio = ratio.split(':')
                y_ratio = int(y_ratio)
                x_ratio = int(x_ratio)
                final_width = min(source_width, source_height*x_ratio/y_ratio)
                final_height = final_width*y_ratio/x_ratio
                log.debug('ratio=(%s,%s), final(h,w)=(%s, %s), original(h,w)=(%s, %s)'%(
                       x_ratio, y_ratio, final_height, final_width, source_height, source_width))
                ul_y = (source_height - final_height)/2
                ul_x = 0
                lr_y = ul_y + final_height
                lr_x = final_width 
    #            else:
    #                lr_x = int(int(action['parameters']['lowerright_x'])*component.source.width/100)
    #                ul_x = int(int(action['parameters']['upperleft_x'])*component.source.width/100)
    #                lr_y = int(int(action['parameters']['lowerright_y'])*component.source.height/100)
    #                ul_y = int(int(action['parameters']['upperleft_y'])*component.source.height/100)
                
                source_width = lr_x -ul_x 
                source_height = lr_y - ul_y
                log.debug('orig(h,w)=(%s, %s)' % (source.height, source.width))
                argv +=  ['-crop', '%dx%d+%d+%d' % (source_width, source_height,  ul_x, ul_y)]
                log.debug('argv %s'%argv)
            
            elif action == 'watermark':
                pos_x = int(pos_x_percent)*source_width/100
                pos_y = int(int(pos_y_percent)*source_height/100)
                argv += ['cache://' + watermark_id, '-geometry', '+%s+%s' % (pos_x,pos_y), '-composite']
        
        adapter_proxy = Proxy('Adapter')
        
        dest_res_id = dest_res_id + '.' + output_format
        d = adapter_proxy.adapt_image_magick('%s[0]' % orig.ID, dest_res_id, argv)
        d.addCallbacks(self.handle_result, self.handle_error, [output_component])
        
        return self.deferred
    

def test():
    print 'test'
    
    item = Item.objects.all()[0]
    workspace = DAMWorkspace.objects.get(pk = 1)
    source_variant = 'original'
    
    actions = ['resize'] 
    height = width = 100
    output_variant = 'fullscreen'
    output_format = 'jpg'
    d = run(item, workspace, source_variant, output_variant,output_format, actions, height, width)
    d.addBoth(print_result)
    
def print_result(result):
    
    print result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
