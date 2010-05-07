from django.core.management import setup_environ
import settings
setup_environ(settings)




from scripts.models import *

from workspace.models import *
from eventmanager.models import *
from django.utils import simplejson



#pipeline = {
#    'event': 'upload',
#    'state': '',
#    'media_type': 'image',
#    'source_variant': 'original', 
#    'actions':[
#        {
#            'type': 'resize',
#            'parameters':{
#                'max_dim': 100
#            }
#                    
#        },
#        {
#            'type': 'saveas',
#            'parameters':{
#                'output_format': 'jpeg',
#                'output_variant': 'thumbnail'
#            }
#                    
#        }
#        
#               
#    ]
#    
#    }

pipeline_thumb = {
    'event': 'upload',
    'state': '',
    'source_variant': 'original', 
    'actions':{
        'image':[
            {
                'type': 'resize',
                'parameters':{
                    'max_dim': 100
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
        'audio':[],
        'video':[{
            'type': 'extractvideothumbnail',
            'parameters':{
            'max_dim': 100}
        },
        {
            'type': 'saveas',
            'parameters':{
                'output_format': 'jpeg',
                'output_variant': 'thumbnail'
            }
                        
        }],
        'doc':[
            {
               'type': 'resize',
               'parameters':{                        
                    'max_dim':100,
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
    'event': 'upload',
    'state': '',   
    'source_variant': 'original', 
    'actions':{
        'image':[
            {
                'type': 'resize',
                'parameters':{
                    'max_dim': 300
                }
                        
            },
            {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'jpeg',
                    'output_variant': 'preview'
                }
                        
            }    
        ],
        'audio':[{
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
                        
            }
                
                
                
                ],
        'video':[
                 {
                'type': 'resize',
                'parameters':{
                    'height': 300,
                    'width': 300
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
                {
            'type': 'saveas',
            'parameters':{
                'output_format': 'flv',
                'output_variant': 'preview'
            }
                        
        }],
        'doc':[
            {
               'type': 'resize',
               'parameters':{                        
                    'max_dim':300,
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
    'event': 'upload',
    'state': '',   
    'source_variant': 'original', 
    'actions':{
        'image':[
            {
                'type': 'resize',
                'parameters':{
                    'max_dim': 800
                }
                        
            },
            {
                'type': 'saveas',
                'parameters':{
                    'output_format': 'jpeg',
                    'output_variant': 'fullscreen'
                }
                        
            }    
        ],
        
        
    }
}





#    
#    {
#           'type': 'audioencode',
#           'parameters':{                        
#                'bitrate':128,
#                'rate':44100
#            }
#                
#        },
#        {
#            'type': 'saveas',
#            'parameters':{
#                'output_format': 'mp3',
#                'output_variant': 'preview'
#            }
#                    
#        }
    
    
    
    
    





pipeline3 = {
    'event': 'upload',
    'state': 'boh', 
    'actions':[
               
#               {
#        #metadata        
#        },
        {
         'type':'adaptation',
        'media_type': 'image',
        'source_variant': 'original',
        'output_variant': 'preview',
        'output_format': 'jpeg',
        'actions':[{
            'type': 'resize',
            'parameters':{
                'max_dim': 200
            }
                    
        }]
         
         },
         
         {
        'type':'adaptation',
        'media_type': 'image',
        'source_variant': 'original',
        'output_variant': 'thumbnail',
        'output_format': 'jpeg',
        'actions':[{
            'type': 'resize',
            'parameters':{
                'max_dim': 100
            }
                    
        }]
         
         },
         {
        'type':'adaptation',
        'media_type': 'image',
        'source_variant': 'original',
        'output_variant': 'fullscreen',
        'output_format': 'jpeg',
        'actions':[{
            'type': 'resize',
            'parameters':{
                'max_dim': 800
            }
                    
        }]
         
         },
         
        {
        'type':'adaptation',
        'media_type': 'video',
        'source_variant': 'original',
        'output_variant': 'thumbnail',
        'output_format': 'jpeg',
        'actions':[{
            'type': 'extractvideothumbnail',
            'parameters':{
                'max_dim': 100
            }
                    
        }]
         
         },
         
        {
            'type':'adaptation',
            'media_type': 'video',
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_format': 'flv',
            'actions':[{
                'type': 'resize',
                'parameters':{
                    'max_height': 320,
                    'max_width': 200
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
                {
                'type': 'watermark', 
                'parameters':{
                    'uri': 'c2ed4e4af0874b8ea72e88d91c706359', 
                    'position':1
                    }
                
                }
                
                        
            ]
         
        },
        {
            'type':'adaptation',
            'media_type': 'audio',
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_format': 'mp3',
            'actions':[
                {
                   'type': 'audioencode',
                   'parameters':{                        
                        'bitrate':128,
                        'rate':44100
                    }
                }
            ]
                     
        }, 
        {
            'type':'adaptation',
            'media_type': 'doc',
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_format': 'jpeg',
            'actions':[
                {
                   'type': 'resize',
                   'parameters':{                        
                        'max_dim':100,
                    }
                
                } 
  
    ]
    }, 
    
    {
            'type':'adaptation',
            'media_type': 'doc',
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_format': 'jpeg',
            'actions':[
                {
                   'type': 'resize',
                   'parameters':{                        
                        'max_dim':200,
                    }
                
                } 
  
    ]
    }
    
       ]          
             
}

pipeline2 = {
        
    'event': 'upload',
    'state': '', 
    'pipes':[
             {
            
            'media_type': 'image',
            'source_variant': 'original',
            'output_variant': 'preview',
            
            'actions': [{
                'type': 'resize',
                'parameters':{
                    'max_dim':200 
                    },
                },
                {
                 'type': 'transcode',
                 'parameters':{
                    'codec':'jpeg'           
                    }
                 
                 }       
            
            ],
           
    },{
         'media_type': 'image',
         'source_variant': 'original',
         'output_variant': 'thumbnail',
         
         'actions': [{
             'type': 'resize',
             'parameters':{
                 'max_dim':100 
             }        
         
        },
        {
         'type': 'transcode',
         'parameters':{
            'codec':'jpeg'           
            }
         
         }       
        
        
        ],
        
        
     },
     {
         'media_type': 'image',
         'source_variant': 'original',
         'output_variant': 'fullscreen',
         
         'actions': [{
             'type': 'resize',
             'parameters':{
                 'max_dim':800 
             }        
         
        },
        {
         'type': 'transcode',
         'parameters':{
            'codec':'jpeg'           
            }
         
         }
        
        ],
        
        
     },
     
     {
         'media_type': 'video',
         'source_variant': 'original',
         'output_variant': 'thumbnail',
         
         'actions': [{
             'type': 'extractvideothumbnail',
             'parameters':{
                 'max_dim':100 
             }        
         
        }],
        
        
     },
     
     {
         'media_type': 'video',
         'source_variant': 'original',
         'output_variant': 'preview',
         
         'actions': [{
             'type': 'resize',
             'parameters':{
                 'max_size':800 
             }        
         
        },
        {
         'type': 'transcode',
         'parameters':{
            'preset_name':'flv'           
            }
         
         }
         
         ],
        
        
     }
     
     
     
     
   ]
}

ws = Workspace.objects.get(pk = 1)

pipeline_json = simplejson.dumps(pipeline_thumb)
script_thumb = Script.objects.create(name = 'thumb_generation', description = 'thumbnail generation', pipeline = pipeline_json, workspace = ws )

#script_thumb = Script.objects.get(pk =  1)
#script_thumb.pipeline = pipeline_json
#script_thumb.save()

upload = Event.objects.create(name = 'upload')
EventRegistration.objects.create(event = upload, listener = script_thumb)

pipeline_json = simplejson.dumps(pipeline_preview)

script_preview = Script.objects.create(name = 'preview_generation', description = 'preview generation', pipeline = pipeline_json, workspace = ws )

#script_preview = Script.objects.get(pk =  2)
#script_preview.pipeline = pipeline_json
#script_preview.save()

#upload = Event.objects.create(name = 'upload')
#upload = Event.objects.get(name = 'upload')
EventRegistration.objects.create(event = upload, listener = script_preview)

pipeline_json = simplejson.dumps(pipeline_fullscreen)

script_fullscreen = Script.objects.create(name = 'fullscreen_generation', description = 'fullscreen generation', pipeline = pipeline_json, workspace = ws )

#script_preview = Script.objects.get(pk =  3)
#script_preview.pipeline = pipeline_json
#script_preview.save()

#upload = Event.objects.create(name = 'upload')
upload = Event.objects.get(name = 'upload')
EventRegistration.objects.create(event = upload, listener = script_fullscreen)

