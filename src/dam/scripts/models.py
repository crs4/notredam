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
    
    def __unicode__(self):
        return unicode(self.name)
    
    def execute(self, items):
        pipeline = simplejson.loads(str(self.pipeline)) #cast needed, unicode keywords in Pipe.__init__ will not work
        
        action_for_media_type = pipeline.get('actions', {})
        source_variant = pipeline['source_variant'].lower()
         
                             
        actions_available = {}       
       
        for subclass in BaseAction.__subclasses__():
            actions_available[subclass.__name__.lower()] = subclass
        
        actions = {
            'image':[],
            'video':[],
            'audio':[],
            'doc':[]
            }
        
        
        for media_type in action_for_media_type.keys():
            for action_dict in action_for_media_type[media_type]:
                
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
                    if tmp_adapt_parameters:
                        adapt_parameters.update(tmp_adapt_parameters)
            
    class Meta:
        unique_together = ('name', 'workspace' )
 
    
    
class BaseAction(object):
    
    media_type_supported = ['image', 'video', 'audio', 'doc']
    required_parameters = []
    def __init__(self, media_type, source_variant, workspace):   
        
#        if media_type not in self.media_type_supported:
#            raise MediaTypeNotSupported('media_type %s not supported by action %s'%(media_type, self.__class__.__name__))
        
        
        if media_type == 'video':
            media_type = 'movie'# sigh
        self.media_type = media_type
        logger.debug('self.media_type %s'%self.media_type)
        self.source_variant = source_variant
        self.workspace = workspace
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
        generate_tasks(variant, self.workspace, item)



class Resize(BaseAction): 
    media_type_supported = ['image', 'video',  'doc']
    required_parameters = ['max_dim',  'height','width']
    def __init__(self, media_type, source_variant, workspace, max_dim = None, height = None, width = None):
        super(Resize, self).__init__(media_type, source_variant, workspace)
        if not max_dim and not height and not width:
            raise MissingActionParameters('action resize need at least max_dim or height or width')
        if max_dim:
            self.parameters['max_dim'] = max_dim
        if height:
            self.parameters['max_height'] = height
        if width:
            self.parameters['max_width'] = width
                

class Doc2Image(BaseAction): 
    media_type_supported = ['doc']
    required_parameters = ['max_dim']

class Watermark(BaseAction): 
    media_type_supported = ['image', 'video']
    required_parameters = ['watermark_uri',  'watermark_position']
    def __init__(self, media_type, **parameters):
        """
        parameters: 
            watermark_uri
            watermark_position(1,2,3,4,5,6,7,8,9)
        
        Mediadart API
        video:
            watermark_uri
            watermark_top
            watermark_left
            watermark_top_percent
            watermark_left_percent
        
        image:
            watermark_filename
            watermark_corner
        """
        super(Watermark,  self).__init__(media_type,  **parameters)
        
        self.parameters['watermak_filename'] = self.parameters.pop('uri')
        
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
        super(VideoEncode, self).__init__(media_type, source_variant, workspace)
        
       
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
        if self.parameters.has_key('bitrate'):
#            if self.parameters['output_format'] in ['mp4_h264_aaclow', 'aac']:
#                self.parameters['audio_bitrate'] = int(self.parameters.pop('bitrate')*1000)
#            else:
            self.parameters['audio_bitrate'] = int(bitrate)            
            self.parameters['audio_rate'] = int(rate)
                

class ExtractVideoThumbnail(BaseAction):
    media_type_supported = ['movie']
    def __init__(self, media_type, source_variant, workspace, max_dim):
        super(ExtractVideoThumbnail, self).__init__(media_type, source_variant, workspace)
        self.parameters['max_dim'] = max_dim

    
    def get_adapt_params(self):
        return {'thumb_size':self.parameters['max_dim']}



class PresetAction(BaseAction):
    required_params = ['preset_name']
    

class AdaptVideo(BaseAction):
    required_params = ['preset_name']
       
