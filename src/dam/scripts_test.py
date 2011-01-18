from django.core.management import setup_environ
import settings
setup_environ(settings)




from dam.scripts.models import *
from dam.scripts.views import _new_script
from dam.workspace.models import *
from dam.eventmanager.models import *
from dam.variants.models import Variant
from django.utils import simplejson


actions = {'adapt_image':{ 
    'params':{
        'actions':['resize'],
        'height':300,
        'width': 300,
        'source_variant': 'original',
        'output_variant': 'thumbnail',
        'output_format' : 'jpeg'        
        },
     'in': ['fake'],
     'out':['fakeout']    
    }
    
}
ws = DAMWorkspace.objects.get(pk = 1)
preview = Pipeline.objects.create(name = 'thumbnail generation', description='', params = simplejson.dumps(actions), workspace = ws)

#pipeline_thumb = {
#    
#        
#                  
#    
#        'image':{
#            'source_variant': 'original',
#            'actions': [
#                {'type': 'resize',
#                'parameters':{
#                    'max_height': 100,
#                    'max_width': 100
#                    
#                }
#                        
#                },
#               
#                {
#                'type': 'save',
#                'parameters':{
#                    'output_format': 'jpeg',
#                    'output': Variant.objects.get(name = 'thumbnail').pk,
#                    'embed_xmp': False
#                }
#                        
#            }    
#        ],
#                 
#                 
#        },
#        'audio':{},
#        'video':{
#            'source_variant': 'original',
#            'actions':[{
#                'type': 'extractvideothumbnail',
#                'parameters':{
#                'max_height': 100,
#                'max_width': 100,
#                   'output_format': 'jpeg',
#                    'output': Variant.objects.get(name = 'thumbnail').pk
#                }
#            },
##            {
##                'type': 'save',
##                'parameters':{
##                    'output_format': 'jpeg',
##                    'output': 'thumbnail'
##                }
##                            
##            }
#            ]
#        },
#        'doc':{
#            'source_variant': 'original',
#            'actions': [
#            {
#               'type': 'resize',
#               'parameters':{                        
#                    'max_height': 100,
#                    'max_width': 100,
#                }
#            
#            },
#            {
#            'type': 'save',
#            'parameters':{
#                'output_format': 'jpeg',
#                'output': Variant.objects.get(name = 'thumbnail').pk
#            }
#                        
#            }]
#        }
#    
#}
#
#
#pipeline_preview = {
#    
#        
#                  
#    
#        'image':{
#            'source_variant': 'original',
#            'actions': [
#                {
#                 'type': 'resize',
#                'parameters':{
#                   'max_height': 300,
#                   'max_width': 300,
#                }
#                        
#                },
##                {
##                     'type': 'set rights',
##                     'parameters':{
##                        'rights': 'creative commons by'
##                     }
##                 },
#                {
#                'type': 'save',
#                'parameters':{
#                    'output_format': 'jpeg',
#                    'output': Variant.objects.get(name = 'preview').pk,
#                     'embed_xmp': False
#                    
##                    'output': 'preview'
#                }
#                        
#            }    
#        ],
#                 
#                 
#        },
#        'audio':{
#                 'source_variant': 'original',
#                 'actions':[{
#                   'type': 'audio encode',
#                   'parameters':{                        
#                        'bitrate':128,
#                        'rate':44100
#                        }
#                    },
#                    {
#                    'type': 'save',
#                    'parameters':{
#                        'output_format': 'mp3',
#                        'output': Variant.objects.get(name = 'preview').pk
#                    }
#                            
#                }]
#                 
#                 
#                 
#                 },
#        'video':{
#            'source_variant': 'original',
#            'actions':[
#                    
#                 {
#                'type': 'resize',
#                'parameters':{
#                    'max_height': 300,
#                    'max_width': 300
#                    }
#                },
#                {
#                   'type': 'video encode',
#                   'parameters':{
#                        'framerate':'25/2',
#                        'bitrate':640
#                    }
#                
#                },                
#                {
#                   'type': 'audio encode',
#                   'parameters':{                        
#                        'bitrate':128,
#                        'rate':44100
#                    }
#                
#                },
##                {
##                   'type': 'watermark',
##                   'parameters':{
##                    'filename':'14c5c8e95751401db5dd6253817b6a6d.gif',
##                    'pos_x_percent': 20,
##                    'pos_y_percent':20,
##                  
##                                 
##                    }
##                   
##                },
#                
##                {
##                'type': 'sendbymail',
##                'parameters':{
##                    'output_format': 'flv',
##                    'mail': 'mdrio@tiscali.it'
##                }
##                            
##                },
#                {
#                'type': 'save',
#                'parameters':{
#                    'output_format': 'flv',
#                    'output': Variant.objects.get(name = 'preview').pk
#                }
#                            
#                }]
#                 
#        },
#        
#        'doc':{
#            'source_variant': 'original',
#            'actions': [
#            {
#               'type': 'resize',
#               'parameters':{                        
#                    'max_height':300,
#                    'max_width':300,
#                }
#            
#            },
#            {
#            'type': 'save',
#            'parameters':{
#                'output_format': 'jpeg',
#                'output': Variant.objects.get(name = 'preview').pk
#            }
#                        
#            }]
#        }
#        
#    
#}
#
#
#
#
#
#
#pipeline_fullscreen = {
#   
#    
#        'image':{
#            'source_variant': 'original',
#            'actions': [
#                {
#                 'type': 'resize',
#                'parameters':{
#                    'max_height': 800,
#                    'max_width': 800,
#                }
#                        
#                },
##                {
##                 'type': 'crop',
##                 'parameters':{
##                    'upperleft_x': 20, 
##                    'upperleft_y':20,
##                    'lowerright_x':2000,
##                    'lowerright_y': 2000           
##                }
##                 
##                 },
#                
##                {
##                   'type': 'watermark',
##                   'parameters':{
##                    'filename':'14c5c8e95751401db5dd6253817b6a6d.gif',
##                    'pos_x': 20,
##                    'pos_y':20,
##                    'alpha': 255
##                                 
##                    }
##                   
##                },
#                {
#                'type': 'save',
#                'parameters':{
#                    'output_format': 'jpeg',
#                    'output': Variant.objects.get(name = 'fullscreen').pk,
#                     'embed_xmp': False
#                }
#                        
#            },
##                {
##                 'type': 'crop',
##                 'parameters':{
##                    'upperleft_x': 20, 
##                    'upperleft_y':20,
##                    'lowerright_x':200,
##                    'lowerright_y': 200           
##                }
##                 
##                 },
##                 {
##                'type': 'save',
##                'parameters':{
##                    'output_format': 'jpeg',
##                    'output': 'fullscreen'
##                }
##                        
##            }
#                 
#                
#    
#        ],
#                 
#                 
#        },
#    
#}
#
#    
#
#ws = DAMWorkspace.objects.get(pk = 1)
#
#Event.objects.create(name = 'upload')
#Event.objects.create(name = 'item copy')
#
#pipeline_json = simplejson.dumps(pipeline_thumb)
#_new_script(name = 'thumb_generation', description = 'thumbnail generation', workspace = ws,  pipeline = pipeline_json, events = ['upload', 'item copy'],  is_global = True)
#ScriptDefault.objects.create(name = 'thumb_generation', description = 'thumbnail generation', pipeline = pipeline_json, )
#
#
#pipeline_json = simplejson.dumps(pipeline_preview)
#_new_script(name = 'preview_generation', description = 'preview generation', workspace = ws, pipeline = pipeline_json, events = ['upload', 'item copy'], is_global = True)
#ScriptDefault.objects.create(name = 'preview_generation', description = 'preview generation', pipeline = pipeline_json)
#
#pipeline_json = simplejson.dumps(pipeline_fullscreen)
#
#_new_script(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json, workspace = ws, events = ['upload', 'item copy'], is_global = True)
#ScriptDefault.objects.create(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json)
