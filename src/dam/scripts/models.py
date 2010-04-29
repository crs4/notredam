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


"""   
{
    action

}



 
  pipeline =   {
        
    event: upload, optional
    state: boh, optional
    pipes:[
    
        {
            id: preview_image,
            media_type: 'image',
            source_variant: 'original',
            
            actions: [
                {
                type: resize,
                parameters:{
                    height:100 
                }        
            
                },
                {
                type: watermark,
                parameters:{
                    file: /p/a/t/h
                },
        
                
                },                
                {
                type: save_as_variant
                parameters:{
                    variant: preview
                    }
                    
                
                }
            
            ],
           
        }
        
        
        ]
        }
    

 {
        
   
    
    media_type: image,
    source: original,
    output: preview,
    actions: [
        {
        type: resize,
        parameters:{
            height:100 
        }        
    
        },
        {
        type: watermark,
        parameters:{
            file: /p/a/t/h
        },
        {
         type:set_rights,
         parameters:{
             right: cc
         }
        
        },
        
        }
    
    ],
   
}


""" 

pipeline = {
        
    'event': 'upload',
    'state': 'boh', 
    'pipes':[
    
        {
            
            'media_type': 'image',
            'source_variant': 'original',
            'output_variant': 'preview',
            
            'actions': [
                {
                'type': 'resize',
                'parameters':{
                    'max_dim':200 
                }        
            
                },
            
            
            ],
           
        }
        
        
        ]
        }




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
                logger.error(ex)
                                
            
        
        
            
    class Meta:
        unique_together = ('name', 'workspace' )
  
  
class MissingActionParameters(Exception):
  pass

class WrongInput(Exception):
  pass

class ActionError(Exception):
    pass


class Pipe:
    def __init__(self,workspace, actions = [], media_type = None, source_variant = None, output_variant = None ):
        
        
        actions_available = {}
        self.adaptation_task = False
        self.workspace = workspace
        for subclass in BaseMDAction.__subclasses__():
            actions_available[subclass.__name__.lower()] = subclass
    
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
                
                action = actions_available[type](**params)
                if isinstance(action, BaseMDAction):
                    self.adaptation_task = True
            except Exception, ex:
                logger.error(ex)
                
                raise ActionError('action %s does not exist'%type)
            self.actions.append(action)
            
        
    def execute(self, items):
        
        adaptation_task = False
        adapt_parameters = {}
        variant = Variant.objects.get(name = self.output_variant, media_type__name = self.media_type)
        for item in items:
            
            try:
                component = variant.get_component(self.workspace,  item)    
                    
            except Component.DoesNotExist:
                component = Component.objects.create(variant = variant,  item = item)
                component.workspace.add(self.workspace)
            
            for action in self.actions:               
                                    
                    tmp = action.execute(item, variant)
                    logger.debug('tmp %s'%tmp)
                    if tmp:
                        adapt_parameters.update(tmp)
                    
                
            logger.debug('self.adaptation_task %s'%self.adaptation_task)
            logger.debug('adapt_parameters %s'%adapt_parameters)
            if self.adaptation_task and adapt_parameters:
                component.set_parameters(adapt_parameters) 
                
                component.source = Variant.objects.get(name = self.source_variant, media_type__name = self.media_type).get_component(self.workspace, item)
                component.save() 
                               
                generate_tasks(variant, self.workspace, item)

class BaseAction(object):
    required_params = []
    input_number = 1
    output_number = 1
    def __init__(self, **parameters):
        if parameters.keys().sort() != self.required_params.sort():
            raise MissingActionParameters('action parameters are: %s; parameters passed are %s'%(self.required_params, parameters))
#        if isinstance(inputs, list):
#            if len(inputs) > self.input_number:
#                raise WrongInput('expected %s inputs, %s given'%self.input_number, len(inputs)) 
                
        self.parameters = parameters
       
    def execute(self, item, variant):
        pass
    
class BaseMDAction(BaseAction):
    def get_adapt_parameters(self):
        pass

class Resize(BaseMDAction):
    required_params = ['max_dim']
    
    def execute(self, item, variant):                
        return {'max_dim': self.parameters['max_dim']}
    
class Transcoding(BaseMDAction):
    required_params = ['format']
    
    def get_adapt_parameters(self):
        return {'output_file': self.input + '.' + self.parameters['format']}

class Watermark(BaseMDAction):
    required_params = ['file']
    def get_adapt_parameters(self):
        return {'watermark':self.parameters['file']}

class ExtractVideoThumbnail(BaseMDAction):
    pass

    
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
