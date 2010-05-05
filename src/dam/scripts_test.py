from django.core.management import setup_environ
import settings
setup_environ(settings)




from scripts.models import *

from workspace.models import *
from eventmanager.models import *
from django.utils import simplejson



pipeline = {
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
pipeline_json = simplejson.dumps(pipeline)
#script = Script.objects.create(name = 'variant_generation', description = 'variant generation', pipeline = pipeline_json, workspace = ws )

script = Script.objects.get(pk =  1)
script.pipeline = pipeline_json
script.save()

#upload = Event.objects.create(name = 'upload')
#EventRegistration.objects.create(event = upload, listener = script)



#script.execute(Item.objects.all())
