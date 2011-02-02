import os
import sys
import mimetypes
import shutil

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.utils import simplejson
from django.contrib.auth.models import User
from dam.mprocessor.models import new_processor, Pipeline
from dam.workspace.models import DAMWorkspace
from dam.core.dam_repository.models import Type
from dam.repository.models import Item
from dam.variants.models import Variant
from mediadart.storage import new_id
from dam.upload.views import guess_media_type


actions = {'thumbnail_image':{
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'height':100,
            'width': 100,
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_format' : 'jpeg'        
            },
         'in': ['fakethumb'],
         'out':['fakethumbout']    
        
        
    },
    'preview_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'height':300,
            'width': 300,
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_format' : 'jpeg'        
            },
         'in': ['fakepreview'],
         'out':['fakepreviewout']    
        },
        
    
    'fullscreen_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'height':800,
            'width': 600,
            'source_variant': 'original',
            'output_variant': 'fullscreen',
            'output_format' : 'jpeg'        
            },
         'in': ['fakefull'],
         'out':['fakefullout']    
    },
    
}

class DoTest:
    def __init__(self):
        self.ws = DAMWorkspace.objects.get(pk = 1)
        self.user = User.objects.get(username='admin')

    def create_item(self, filepath):
        guess = guess_media_type(filepath)
        media_type = Type.objects.get(name=guess)
        item = Item.objects.create(owner = self.user, uploader = self.user, type=media_type)
        item.add_to_uploaded_inbox(self.ws)
        item.workspaces.add(self.ws)
        return item

    def create_variant(self, item, variant, filepath):
        fname, ext = os.path.splitext(filepath)
        res_id = new_id() + ext
        comp = item.create_variant(variant, self.ws)
        if variant.auto_generated:
            comp.imported = True
        comp.file_name = filepath
        comp._id = res_id
        mime_type = mimetypes.guess_type(filepath)[0]
        comp.format = mime_type.split('/')[1]
        comp.save()
        return comp

    def register(self, name, type, description, pipeline_definition):
        preview = Pipeline.objects.create(name = name, type = type, description='', params = simplejson.dumps(pipeline_definition), workspace = self.ws)
        print 'registered pipeline %s, pk = %s' % (name, preview.pk)

    def upload(self, filepath):
        item = self.create_item(filepath)
        print ('created item %s' % item.pk)
        variant = Variant.objects.get(name = 'original')
        comp = self.create_variant(item, variant, filepath)
        imported_filepath = os.path.join(settings.MEDIADART_STORAGE, comp._id)
        shutil.copyfile(filepath, imported_filepath)
        print('file moved to %s' % imported_filepath)
        uploader = new_processor('upload', self.user, self.ws)
        uploader.add_params(item.pk)
        uploader.run()



usage="""
Usage: script_test.py <action> <arguments>
 where action is
 
  register [pipeline_definition]  (default register actions)

  upload <filename>
"""


def main(argv):
    test = DoTest()
    if len(argv) < 2: 
        argv.append('register')
    task = argv[1]

    if task == 'register':
        if len(argv) < 3:
            argv.append('actions')
        pipeline_def = globals()[argv[2]]
        test.register('upload rendition generation', 'upload', '', pipeline_def)
    elif task == 'upload':
        test.upload(argv[2])
    else:
        print usage
    
if __name__=='__main__':
    main(sys.argv)

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
