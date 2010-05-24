from django.core.management import setup_environ
import settings
setup_environ(settings)




from scripts.models import *
from scripts.views import _new_script
from workspace.models import *
from eventmanager.models import *
from django.utils import simplejson



pipeline_thumb = {
    
        
                  
    
        'image':{
            'source_variant': 'original',
            'actions': [
                {'type': 'resize',
                'parameters':{
                    'max_height': 100,
                    'max_width': 100
                    
                }
                        
                },
               
                {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'jpeg',
                    'output_variant': 'thumbnail'
                }
                        
            }    
        ],
                 
                 
        },
#        'audio':{},
        'video':{
            'source_variant': 'original',
            'actions':[{
                'type': 'extractvideothumbnail',
                'parameters':{
                'max_height': 100,
                'max_width': 100,
                }
            },
            {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'jpeg',
                    'output_variant': 'thumbnail'
                }
                            
            }]
        },
        'doc':{
            'source_variant': 'original',
            'actions': [
            {
               'type': 'resize',
               'parameters':{                        
                    'max_height': 100,
                    'max_width': 100,
                }
            
            },
            {
            'type': 'saveas',
            'parameters':{
                'output_format': 'jpeg',
                'output_variant': 'thumbnail'
            }
                        
            }]
        }
    
}


pipeline_preview = {
    
        
                  
    
        'image':{
            'source_variant': 'edited',
            'actions': [
                {
                 'type': 'resize',
                'parameters':{
                   'max_height': 300,
                   'max_width': 300,
                }
                        
                },
                {
                     'type': 'setrights',
                     'parameters':{
                        'rights': 'creative commons by'
                     }
                 },
                {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'jpeg',
                    'output_variant': 'preview'
                    
#                    'output_variant': 'preview'
                }
                        
            }    
        ],
                 
                 
        },
        'audio':{
                 'source_variant': 'original',
                 'actions':[{
                   'type': 'audioencode',
                   'parameters':{                        
                        'bitrate':128,
                        'rate':44100
                        }
                    },
                    {
                    'type': 'saveas',
                    'parameters':{
                        'output_format': 'mp3',
                        'output_variant': 'preview'
                    }
                            
                }]
                 
                 
                 
                 },
        'video':{
            'source_variant': 'original',
            'actions':[
                    
                 {
                'type': 'resize',
                'parameters':{
                    'max_height': 300,
                    'max_width': 300
                    }
                },
                {
                   'type': 'videoencode',
                   'parameters':{
                        'framerate':'25/2',
                        'bitrate':640
                    }
                
                },                
                {
                   'type': 'audioencode',
                   'parameters':{                        
                        'bitrate':128,
                        'rate':44100
                    }
                
                },
#                {
#                   'type': 'watermark',
#                   'parameters':{
#                    'filename':'14c5c8e95751401db5dd6253817b6a6d.gif',
#                    'pos_x_percent': 20,
#                    'pos_y_percent':20,
#                  
#                                 
#                    }
#                   
#                },
                
#                {
#                'type': 'sendbymail',
#                'parameters':{
#                    'output_format': 'flv',
#                    'mail': 'mdrio@tiscali.it'
#                }
#                            
#                },
                {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'flv',
                    'output_variant': 'preview'
                }
                            
                }]
                 
        },
        
        'doc':{
            'source_variant': 'original',
            'actions': [
            {
               'type': 'resize',
               'parameters':{                        
                    'max_height':300,
                    'max_width':300,
                }
            
            },
            {
            'type': 'saveas',
            'parameters':{
                'output_format': 'jpeg',
                'output_variant': 'preview'
            }
                        
            }]
        }
        
    
}






pipeline_fullscreen = {
   
    
        'image':{
            'source_variant': 'original',
            'actions': [
                {
                 'type': 'resize',
                'parameters':{
                    'max_height': 800,
                    'max_width': 800,
                }
                        
                },
#                {
#                 'type': 'crop',
#                 'parameters':{
#                    'upperleft_x': 20, 
#                    'upperleft_y':20,
#                    'lowerright_x':2000,
#                    'lowerright_y': 2000           
#                }
#                 
#                 },
                
#                {
#                   'type': 'watermark',
#                   'parameters':{
#                    'filename':'14c5c8e95751401db5dd6253817b6a6d.gif',
#                    'pos_x': 20,
#                    'pos_y':20,
#                    'alpha': 255
#                                 
#                    }
#                   
#                },
                {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'jpeg',
                    'output_variant': 'fullscreen'
                }
                        
            },
#                {
#                 'type': 'crop',
#                 'parameters':{
#                    'upperleft_x': 20, 
#                    'upperleft_y':20,
#                    'lowerright_x':200,
#                    'lowerright_y': 200           
#                }
#                 
#                 },
#                 {
#                'type': 'saveas',
#                'parameters':{
#                    'output_format': 'jpeg',
#                    'output_variant': 'fullscreen'
#                }
#                        
#            }
                 
                
    
        ],
                 
                 
        },
    
}

    

ws = DAMWorkspace.objects.get(pk = 1)
upload = Event.objects.create(name = 'upload')

pipeline_json = simplejson.dumps(pipeline_thumb)
_new_script(name = 'thumb_generation', description = 'thumbnail generation', workspace = ws, pipeline = pipeline_json, events = ['upload'])
ScriptDefault.objects.create(name = 'thumb_generation', description = 'thumbnail generation', pipeline = pipeline_json, )


_new_script(name = 'preview_generation', description = 'preview generation', workspace = ws, pipeline = pipeline_json, events = ['upload'])
ScriptDefault.objects.create(name = 'preview_generation', description = 'preview generation', pipeline = pipeline_json)

pipeline_json = simplejson.dumps(pipeline_fullscreen)

_new_script(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json, workspace = ws, events = ['upload'])
ScriptDefault.objects.create(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json)

#
#script_thumb = Script.objects.create(name = 'thumb_generation', description = 'thumbnail generation', pipeline = pipeline_json, workspace = ws, is_global = True )
#
#script_thumb = Script.objects.create(name = 'thumb_generation', description = 'thumbnail generation', pipeline = pipeline_json, workspace = ws, is_global = True )
#
#
#
#script_thumb = Script.objects.get(pk =  1)
#script_thumb.pipeline = pipeline_json
#script_thumb.save()


#EventRegistration.objects.create(event = upload, listener = script_thumb, workspace = ws)



#script_preview = Script.objects.get(pk =  2)
#script_preview.pipeline = pipeline_json
#script_preview.save()

#upload = Event.objects.create(name = 'upload')
#upload = Event.objects.get(name = 'upload')
#EventRegistration.objects.create(event = upload, listener = script_preview, workspace = ws)

#pipeline_json = simplejson.dumps(pipeline_fullscreen)
#
#script_fullscreen = Script.objects.create(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json, workspace = ws, is_global = True)
#ScriptDefault.objects.create(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json)

#script_preview = Script.objects.get(pk =  3)
#script_preview.pipeline = pipeline_json
#script_preview.save()

#upload = Event.objects.create(name = 'upload')
#upload = Event.objects.get(name = 'upload')
#EventRegistration.objects.create(event = upload, listener = script_fullscreen, workspace = ws)

