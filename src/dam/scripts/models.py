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
        
        pipes = pipeline.get('pipes', [])
        
        for pipe_kwargs in pipes:
           
            try:
                Pipe(self.workspace, **pipe_kwargs).execute(items)
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


class Pipe:
    def __init__(self,workspace, actions = [], media_type = None, source_variant = None, output_variant = None ):
        
        
        actions_available = {}
        self.adaptation_task = False
        self.workspace = workspace
        for subclass in BaseMDAction.__subclasses__():
            actions_available[subclass.__name__.lower()] = subclass
    
            
        if media_type == 'video':
            media_type = 'movie'# sigh
        
        self.media_type = media_type
        self.source_variant = source_variant
        self.output_variant = output_variant
        
        
        
        self.actions = []
        logger.debug('actions %s'%actions)
        logger.debug('actions_available %s'%actions_available)
        for action_dict in actions:
            
            type = action_dict['type'].lower()
            try:
                
                params = action_dict['parameters']
                if self.source_variant: 
                    params['source_variant'] = self.source_variant
                
                action = actions_available[type](self.media_type,**params)
                if isinstance(action, BaseMDAction):
                    self.adaptation_task = True
            except Exception, ex:
                logger.debug('self.media_type %s'%self.media_type)
                logger.debug('type %s'%type)
                logger.exception(ex)
                
                raise ActionError('action %s does not exist'%type)
            self.actions.append(action)
            
        
    def execute(self, items):
        
        adaptation_task = False
        adapt_parameters = {}
        logger.debug('self.media_type %s'%self.media_type)
        variant = Variant.objects.get(name = self.output_variant, media_type__name = self.media_type)
        for item in items:
            
            try:
                component = variant.get_component(self.workspace,  item)    
                    
            except Component.DoesNotExist:
                component = Component.objects.create(variant = variant,  item = item)
                component.workspace.add(self.workspace)
            
            for action in self.actions:
                    logger.debug('action %s'%action.__class__)
                    logger.debug('isinstance(action, BaseMDAction) %s'%isinstance(action, BaseMDAction))
                                   
                    if isinstance(action, BaseMDAction):
                        tmp = action.get_adapt_params()
                        logger.debug('tmp %s'%tmp)
                        if tmp:
                            adapt_parameters.update(tmp)
                    else:
                        action.execute(item, variant)
                        
                
            logger.debug('self.adaptation_task %s'%self.adaptation_task)
            logger.debug('adapt_parameters %s'%adapt_parameters)
            if self.adaptation_task and adapt_parameters:
                component.set_parameters(adapt_parameters) 
                
                component.source = Variant.objects.get(name = self.source_variant, media_type__name = self.media_type).get_component(self.workspace, item)
                component.save() 
                               
                generate_tasks(variant, self.workspace, item)

class BaseAction(object):
    required_params = []
  
    def __init__(self, **parameters):
        logger.debug('parameters %s'%parameters)
        if self.required_params:
            if parameters.keys().sort() != self.required_params.sort():
                raise MissingActionParameters('action parameters are: %s; parameters passed are %s'%(self.required_params, parameters))
    
                    
        self.parameters = parameters
       
    def execute(self, item, variant):
        pass

    
class BaseMDAction(BaseAction):
    media_type_supported = []
    def __init__(self, media_type, **parameters):   
        
        if media_type not in self.media_type_supported:
            raise MediaTypeNotSupported
        
        super(BaseMDAction, self).__init__(**parameters)
        if media_type == 'video':
            media_type = 'movie'# sigh
        self.media_type = media_type
        logger.debug('self.media_type %s'%self.media_type)
        
    
    def get_adapt_params(self):
        return self.parameters


class Resize(BaseMDAction): 
    media_type_supported = ['image', 'movie']
#    image params: max_dim
    
#        TODO: check parameters in init
    
    
    
class Transcode(BaseMDAction):
    media_type_supported = ['image', 'movie', 'doc', 'audio']
#    image params: codec
   
#        TODO: check parameters init

    

class Watermark(BaseMDAction):
    media_type_supported = ['image', 'movie', 'doc']
    required_params = ['file']
    def get_adapt_params(self):
        return {'watermark':self.parameters['file']}

class ExtractVideoThumbnail(BaseMDAction):
    media_type_supported = ['movie']
#    required_params = ['max_dim']
    
    def get_adapt_params(self):
        return {'thumb_size':self.parameters['max_dim']}



class PresetAction(BaseMDAction):
    required_params = ['preset_name']
    

class AdaptVideo(BaseMDAction):
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
