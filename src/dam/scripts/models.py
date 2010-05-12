#########################################################################
#
# NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
# Web: www.notre-dam.org
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################
from django.db import models
from django.utils import simplejson
from django.contrib.contenttypes import generic
from upload.views import generate_tasks
from variants.models import Variant
from repository.models import Component
from dam.framework.dam_repository.models import Type
import logger

variant_generation_pipeline = {
    'event': 'upload',
    'state': '', 
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


class ScriptException(Exception):
    pass
  
class MissingActionParameters(ScriptException):
    pass

class WrongInput(ScriptException):
    pass

class ActionError(ScriptException):
    pass

class MediaTypeNotSupported(ScriptException):
    pass

class PresetUnknown(ScriptException):
    pass


class Script(models.Model):
    name = models.CharField(max_length= 50)
    description = models.CharField(max_length= 200)
    pipeline = models.TextField()
    workspace = models.ForeignKey('workspace.Workspace')
    event = generic.GenericRelation('eventmanager.EventRegistration')
    state = models.ForeignKey('workflow.State',  null = True,  blank = True)
    media_type = models.ManyToManyField(Type)
    is_global = models.BooleanField(default = False)
    
    def save(self, *args, **kwargs):
        super(Script, self).save(*args, **kwargs)
        pipeline = simplejson.loads(self.pipeline)
        media_type = pipeline['media_type'].keys()
        
        media_type = Type.objects.filter(name__in = media_type)
        self.media_type.remove(*self.media_type.all())
        self.media_type.add(*media_type)
         
    
    def __unicode__(self):
        return unicode(self.name)
    
    
    def execute(self, items):
        pipeline = simplejson.loads(str(self.pipeline)) #cast needed, unicode keywords in Pipe.__init__ will not work
        
        media_types = pipeline.get('media_type', {})
                             
        actions_available = {}       
       
        for subclass in BaseAction.__subclasses__():
            actions_available[subclass.__name__.lower()] = subclass
        
        actions = {
            'image':[],
            'video':[],
            'audio':[],
            'doc':[]
            }
        
        logger.debug('media_types %s'%media_types)
        for media_type, info in media_types.items():
            logger.debug('info %s '%info)            
            logger.debug('media_type %s'%media_type)
            source_variant = info['source_variant']
            for action_dict in info['actions']:
                
                type = action_dict['type'].lower()
                params = action_dict['parameters']
                params['workspace'] = self.workspace
                params['media_type'] = media_type
                params['source_variant'] = source_variant
                logger.debug('action_dict %s'%action_dict)
                try:                    
                    action = actions_available[type](**params)                
                except Exception, ex:              
                    logger.exception(ex)                
                    raise ActionError('action %s does not exist'%type)
                actions[media_type].append(action)
  
        
        
        logger.debug('actions %s'%actions)
        for item in items:
            adapt_parameters = {}   
            media_type = item.type.name
            if media_type == 'movie':
                media_type = 'video'
                
            for action in actions[media_type]:
                if isinstance(action, SaveAs):
                    action.execute(item,adapt_parameters)
                else:
                    tmp_adapt_parameters = action.get_adapt_params()
                    logger.debug('tmp_adapt_parameters %s'%tmp_adapt_parameters)
                    if tmp_adapt_parameters:
                        adapt_parameters.update(tmp_adapt_parameters)
            
    class Meta:
        unique_together = ('name', 'workspace')
 
    
    
class BaseAction(object):
    
    media_type_supported = ['image', 'video', 'audio', 'doc']
    required_parameters = []
    def __init__(self, media_type, source_variant, workspace, **params):   
        
#        if media_type not in self.media_type_supported:
#            raise MediaTypeNotSupported('media_type %s not supported by action %s'%(media_type, self.__class__.__name__))
        
        
        if media_type == 'video':
            media_type = 'movie'# sigh
        self.media_type = media_type
        logger.debug('self.media_type %s'%self.media_type)
        self.source_variant = source_variant
        self.workspace = workspace
        if params:
            self.parameters = params
        else:
            self.parameters = {}
            
    def get_adapt_params(self):
        return self.parameters


class SaveAs(BaseAction):
    media_type_supported = ['image', 'video',  'doc', 'audio']
    required_parameters = ['output_variant', 'output_format']
    def __init__(self, media_type, source_variant, workspace, output_variant, output_format):  
        super(SaveAs, self).__init__(media_type, source_variant, workspace)
        
        self.output_variant = output_variant
        self.output_format = output_format
    
    def execute(self, item, adapt_parameters):     
        logger.debug('self.output_variant %s'%self.output_variant)
        logger.debug('self.media_type %s'%self.media_type)
        variant = Variant.objects.get(name = self.output_variant, media_type__name = self.media_type)          
        
        component = variant.get_component(self.workspace,  item)    
         
        if self.media_type == 'movie' or self.media_type == 'audio':
            adapt_parameters['preset_name'] = self.output_format
        else:
            adapt_parameters['codec'] = self.output_format
        
        logger.debug('adapt_parameters %s'%adapt_parameters)    
        component.set_parameters(adapt_parameters) 
        
        
        source_variant = Variant.objects.get(name = self.source_variant, media_type__name = self.media_type) 
        source= source_variant.get_component(self.workspace, item)                 
        component.source = source
        component.save() 
        logger.debug('generate task')
        generate_tasks(variant, self.workspace, item)



class Resize(BaseAction): 
    media_type_supported = ['image', 'video',  'doc']
    required_parameters = ['max_height','max_width']
    def __init__(self, media_type, source_variant, workspace,  max_height, max_width):
        super(Resize, self).__init__(media_type, source_variant, workspace)
        if media_type == 'video' or media_type == 'movie':
            self.parameters['video_height'] = max_height
            self.parameters['video_width'] = max_width
        else:
            self.parameters['max_height'] = max_height
            self.parameters['max_width'] = max_width
                

class Crop(BaseAction): 
    media_type_supported = ['image',]
    required_parameters = ['upperleft_x', 'upperleft_y', 'lowerright_x', 'lowerright_y']
    def __init__(self, media_type, source_variant, workspace,  upperleft_x, upperleft_y, lowerright_x, lowerright_y):
        params = {'upperleft_x':upperleft_x, 'upperleft_y':upperleft_y, 'lowerright_x':lowerright_x, 'lowerright_y':lowerright_y }
        
        super(Crop, self).__init__(media_type, source_variant, workspace, **params)
     
class Watermark(BaseAction): 
    media_type_supported = ['image', 'video']
    required_parameters = ['filename', 'pos_x', 'pos_y', 'pos_x_percent', 'pos_y_percent', 'alpha']
    
    def __init__(self, media_type, source_variant, workspace, filename, pos_x = None, pos_y = None, pos_x_percent = None, pos_y_percent = None, alpha = None):
        
        super(Watermark,  self).__init__(media_type, source_variant, workspace)
        self.parameters['watermark_filename'] = filename
        
         
        
        if self.media_type == 'image':
            if not (pos_x and pos_y):
                raise MissingActionParameters('pos_x or pos_y parameter is missing: they are required')
            
            self.parameters['alpha'] = alpha
            self.parameters['pos_x'] = pos_x
            self.parameters['pos_y'] = pos_y
            
        else:
            if not ((pos_x and pos_y) or (pos_x_percent and pos_y_percent)):
                raise MissingActionParameters('no coordinates for watermark are passed (pos_x, pos_y or pos_x_percent, pos_y_percent): they are required')
            
            if (pos_x and pos_y):
                self.parameters['watermark_top'] = pos_x
                self.parameters['watermark_left'] = pos_y
            else:
                self.parameters['watermark_top_percent'] = pos_x_percent
                self.parameters['watermark_left_percent'] = pos_y_percent
                
                
            
        
#        TODO: watermark corner
        

preset = {'movie':
                   {'matroska_mpeg4_aac': 'mpeg4',
                   'mp4_h264_aaclow': 'mpeg4',
                   'flv': 'flv',
                   'avi': 'avi',
                   'flv_h264_aac': 'flv',
                   'theora': 'ogg'}
     
}

        
class VideoEncode(BaseAction):
    """default bitrate in kb""" 
    media_type_supported = ['video']
    def __init__(self, media_type, source_variant, workspace, bitrate, framerate):
        params = {'bitrate':bitrate,  'framerate': framerate}
        super(VideoEncode, self).__init__(media_type, source_variant, workspace, **params)
        
       
        if self.parameters.has_key('bitrate'):
#            if self.parameters['output_format'] in ['flv', 'avi', 'mpegts']:
#                self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate')*1000)
#            else:
#                 self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate'))
            self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate'))       
        
        if self.parameters.has_key('framerate'): 
            self.parameters['video_framerate'] = self.parameters.pop('framerate')
                
class AudioEncode(BaseAction):
    """default bitrate in kb"""
    media_type_supported = ['video', 'audio']
    
    def __init__(self, media_type, source_variant, workspace, rate, bitrate):
        super(AudioEncode, self).__init__(media_type, source_variant, workspace)
        

        self.parameters['audio_bitrate'] = int(bitrate)            
        self.parameters['audio_rate'] = int(rate)
                

class ExtractVideoThumbnail(BaseAction):
    media_type_supported = ['movie']
    def __init__(self, media_type, source_variant, workspace, max_height,  max_width):
        params = {'max_height': max_height,  'max_width':max_width}
        super(ExtractVideoThumbnail, self).__init__(media_type, source_variant, workspace, **params)
    

