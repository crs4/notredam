from repository.models import Component
from uuid import uuid4
from twisted.internet import defer
from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy


def new_id():
    return uuid4().hex

def inspect(input_params):
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
    
        'output': {
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

    
def run(item, workspace, source_variant, actions, height, width, ratio, pos_x_percent, pos_y_percent, wm_id, output):
    source = item.get_variant(workspace, source_variant)
    component = item.create_variant(output, workspace)
    
    log.debug("[adapt_resource] from original component %s" % component.source.ID)
    
    orig = component.source
    dest_res_id = new_id()
    
    args ={}
    argv = [] #for calling imagemagick


    log.debug('script %s'%script)
    source_width = source.width
    source_height = source.height
    for action in actions:
        if action == 'resize':
            width = min(width,  source.width)
            height = min(height,  source.height)
            argv +=  ['-resize', '%dx%d' % (width, height)]
            
            aspect_ratio = source.height/source.width 
            alfa = min(action['parameters']['max_width']/source.width, action['parameters']['max_height']/source.height)
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
    transcoding_format = vp.get('codec', orig.format) #change to original format
    dest_res_id = dest_res_id + '.' + transcoding_format
    d = adapter_proxy.adapt_image_magick('%s[0]' % orig.ID, dest_res_id, argv)
    return d

#
#def next_action():
#    pass
#    
#
#def h_ok(status, result):
#    pass
#
#d = adapt_image.run(**params)
#d.addCallbacks(h_ok, h_error)
