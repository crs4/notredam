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
        'source_variant': {
            'type': 'input-variant',
            'description': 'input-variant',
            'default': 0,
            'help': ''
        }      
        
         
        } 

def run(item, workspace, source_variant, output_variant, output_format, dim_x, dim_y):
    
    return Adapter().execute(item, workspace, source_variant, output_variant, output_format, dim_x, dim_y)

def save_component(self, result):   # era save_and_extract_features
    log.debug("[save_component] component %s" % component.ID)
    component = self.maction.component
    if result:
        dir, name = os.path.split(result)
        component._id = name
        component.save()
    else:
        log.error('Empty result passed to save_and_extract_features')
    return result    

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
        reactor.stop()
        return result
        
    
    def handle_error(self, result, component):
        self.deferred.callback('error')
        reactor.stop()
    
    def execute(self,item, workspace, source_variant, output_variant, output_format, dim_x, dim_y):
        dest_res_id = new_id()
        dest_res_id = dest_res_id + '.' + output_format
        
        source_variant = Variant.objects.get(name = source_variant)
        source = item.get_variant(workspace, source_variant)
        
        output_variant = Variant.objects.get(name = output_variant)
        output_component = item.create_variant(output_variant, workspace)
        
        adapter_proxy = Proxy('Adapter')
        d = adapter_proxy.extract_video_thumbnail(source.ID, dest_res_id, thumb_size=(dim_x, dim_y))
        d.addCallbacks(self.handle_result, self.handle_error, [output_component])
        
        return self.deferred
    

def test():
    print 'test'
    
    item = Item.objects.all()[2]
    workspace = DAMWorkspace.objects.get(pk = 1)
    source_variant = 'original'
    
    actions = ['resize'] 
    dim_x = dim_y = 100
    output_variant = 'thumbnail'
    output_format = 'jpg'
    
    d = run(item, workspace, source_variant, output_variant, output_format, dim_x, dim_y)
    d.addBoth(print_result)
    
def print_result(result):
   
    print result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
