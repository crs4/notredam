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
        
        actions = pipeline.get('actions', [])
        
        for action_params in actions:
           
            try:
                ActionFactory().get_action(**action_params).execute(items, self.workspace)
            except Exception, ex:
                logger.exception(ex)
                                
            
        
        
            
    class Meta:
        unique_together = ('name', 'workspace' )
  

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

class ActionFactory:
    def get_action(self, **action_params):
        if action_params['type'] == 'adaptation':
            action_params.pop('type')
            return Adaptation(**action_params)
        else:
            return None
    
    
class BaseAction(object):
    required_params = []
  
    def __init__(self, **parameters):
        logger.debug('parameters %s'%parameters)
        if self.required_params:
            if parameters.keys().sort() != self.required_params.sort():
                raise MissingActionParameters('action parameters are: %s; parameters passed are %s'%(self.required_params, parameters))
    
                    
        self.parameters = parameters
       
    def execute(self, items, workspace):
        pass


preset = {'movie':
                   {'matroska_mpeg4_aac': 'mpeg4',
                   'mp4_h264_aaclow': 'mpeg4',
                   'flv': 'flv',
                   'avi': 'avi',
                   'flv_h264_aac': 'flv',
                   'theora': 'ogg'}
     
}


class Adaptation(BaseAction):
    def __init__(self,actions, media_type, source_variant, output_variant, output_format):
        
        
       
        if media_type == 'video':
            media_type = 'movie'# sigh
#        
#            if self.output_format  not in preset[media_type].keys():
#                raise PresetUnknown('Preset %s unknown. Presets available are: %s.'%(self.output_format,','.join(preset[media_type].keys()))) 
#                
#            self.extension = preset[media_type][output_format]
#            
#        else:
#            self.extension = self.output_format
       
        
        self.media_type = media_type
        self.source_variant = source_variant.lower()
        self.output_variant = output_variant.lower()
        self.output_format = output_format.lower()     
        
        actions_available = {}       
       
        for subclass in BaseAdaptAction.__subclasses__():
            actions_available[subclass.__name__.lower()] = subclass
    
       
                
        
        self.actions = []
        
        for action_dict in actions:
            
            type = action_dict['type'].lower()
            try:
                
                params = action_dict['parameters']
                if self.source_variant: 
                    params['source_variant'] = self.source_variant
                if self.output_format:
                    params['output_format'] = self.output_format
                
                
                action = actions_available[type](self.media_type,**params)
                
            except Exception, ex:
              
                logger.exception(ex)
                
                raise ActionError('action %s does not exist'%type)
            self.actions.append(action)
            
        
    def execute(self, items, workspace):
               
        adapt_parameters = {}
       
        variant = Variant.objects.get(name = self.output_variant, media_type__name = self.media_type)
        for item in items:
            
            try:
                component = variant.get_component(workspace,  item)    
                    
            except Component.DoesNotExist:
                component = Component.objects.create(variant = variant,  item = item)
                component.workspace.add(workspace)
            
            for action in self.actions:
                    logger.debug('action %s'%action.__class__)
                    logger.debug('isinstance(action, BaseAdaptAction) %s'%isinstance(action, BaseAdaptAction))       
                    tmp = action.get_adapt_params()                        
                    adapt_parameters.update(tmp)
                    
            
            
            if self.media_type == 'movie' or self.media_type == 'audio':
                adapt_parameters['preset_name'] = self.output_format
            else:
                adapt_parameters['codec'] = self.output_format
            
            logger.debug('adapt_parameters %s'%adapt_parameters)    
            component.set_parameters(adapt_parameters) 
            
            component.source = Variant.objects.get(name = self.source_variant, media_type__name = self.media_type).get_component(workspace, item)
            component.save() 
            generate_tasks(variant, workspace, item)


class BaseAdaptAction(BaseAction):
    media_type_supported = []
    def __init__(self, media_type, **parameters):   
        
        if media_type not in self.media_type_supported:
            raise MediaTypeNotSupported('media_type %s not supported by action %s'%(media_type, self.__class__.__name__))
        
        super(BaseAdaptAction, self).__init__(**parameters)
        if media_type == 'video':
            media_type = 'movie'# sigh
        self.media_type = media_type
        logger.debug('self.media_type %s'%self.media_type)
        
    
    def get_adapt_params(self):
        return self.parameters

class Resize(BaseAdaptAction): 
    media_type_supported = ['image', 'movie',  'doc']

class Doc2Image(BaseAdaptAction): 
    media_type_supported = ['doc']
    required_parameters = ['max_dim']

class Watermark(BaseAdaptAction): 
    media_type_supported = ['image', 'movie']
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
        
        
class VideoEncode(BaseAdaptAction):
    """default bitrate in kb""" 
    media_type_supported = ['movie']
    def __init__(self, media_type, **parameters):
        
        super(VideoEncode, self).__init__(media_type, **parameters)
        if self.parameters.has_key('bitrate'):
            if self.parameters['output_format'] in ['flv', 'avi', 'mpegts']:
                self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate')*1000)
            else:
                 self.parameters['video_bitrate'] = int(self.parameters.pop('bitrate'))       
        
        if self.parameters.has_key('framerate'): 
            self.parameters['video_framerate'] = self.parameters.pop('framerate')
                
class AudioEncode(BaseAdaptAction):
    """default bitrate in kb"""
    media_type_supported = ['movie', 'audio']
    
    def __init__(self, media_type, **parameters):
        super(AudioEncode, self).__init__(media_type, **parameters)
        if self.parameters.has_key('bitrate'):
            if self.parameters['output_format'] in ['mp4_h264_aaclow', 'aac']:
                self.parameters['audio_bitrate'] = int(self.parameters.pop('bitrate')*1000)
            else:
                self.parameters['audio_bitrate'] = int(self.parameters.pop('bitrate'))
            
            self.parameters['audio_rate'] = int(self.parameters.pop('rate'))
                

class ExtractVideoThumbnail(BaseAdaptAction):
    media_type_supported = ['movie']
#    required_params = ['max_dim']
    
    def get_adapt_params(self):
        return {'thumb_size':self.parameters['max_dim']}



class PresetAction(BaseAdaptAction):
    required_params = ['preset_name']
    

class AdaptVideo(BaseAdaptAction):
    required_params = ['preset_name']
       

    
    
#    
#class Action(models.Model):
#    component = models.ForeignKey('Component')
#    function = models.CharField(max_length=64)
#
#    def __str__(self):
#        return "%s %s"  % (self.component.get_variant().name, self.function )
#
#class MachineState(models.Model):
#    name = models.CharField(max_length=64)
#    action = models.ForeignKey(Action, null=True, blank=True)
#    next_state =  models.ForeignKey('self', null=True, blank=True)
#
#    def copy(self):
#        initial = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields if not isinstance(f, models.AutoField) and not f in self._meta.parents.values()])
#        return self.__class__(**initial)
#        
#class Machine(models.Model):
#    initial_state = models.ForeignKey(MachineState, related_name='initial')
#    current_state = models.ForeignKey(MachineState)
#    wait_for = models.ForeignKey('self', null=True, blank=True)

        
    
#class Action(models.Model):  
#    name = models.CharField(max_length = 50)
#    command = models.CharField(max_length = 200)
#    media_type = models.ManyToManyField('application.Type')
#    parameters = models.ManyToManyField('Parameter')
#    
#    def __unicode__(self):
#        return unicode(self.name)
#
#class Parameter(models.Model):
#    name = models.CharField(max_length = 50)
#    caption = models.CharField(max_length = 100)
#    
#    def __unicode__(self):
#        return unicode(self.name)
#
#class ActionScriptAssociation(models.Model):
#    action = models.ForeignKey('Action')
#    script = models.ForeignKey('Script')
#    action_position = models.SmallIntegerField()
#    parameters= models.ManyToManyField('ParameterToAction',  related_name = 'parameter_values',  null = True,  blank = True)
#    
#    class Meta:
#        unique_together = ('script', 'action_position' )
#    
#class ParameterToAction(models.Model):
#    parameter = models.ForeignKey('Parameter')
#    ActionScriptAssociation = models.ForeignKey('ActionScriptAssociation')
#    value = models.CharField(max_length = 50)
#    
#    def __unicode__(self):
#        return unicode(self.parameter.name)
