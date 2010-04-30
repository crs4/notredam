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
        
        
     }
     
     
     
     
   ]
}

ws = Workspace.objects.get(pk = 1)
pipeline_json = simplejson.dumps(pipeline)
#script = Script.objects.create(name = 'prova', description = 'prova', pipeline = pipeline_json, workspace = ws )

script = Script.objects.get(pk =  1)
script.pipeline = pipeline_json
script.save()

#upload = Event.objects.create(name = 'upload')
#EventRegistration.objects.create(event = upload, listener = script)



#script.execute(Item.objects.all())
