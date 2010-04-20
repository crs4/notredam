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


"""    
    {
    variant: original, can be a list
    output: preview, optional
    event: upload, optional
    state: boh, optional
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
    }
    
    }
]}
""" 



class Script(models.Model):
    name = models.CharField(max_length= 50)
    description = models.CharField(max_length= 200)
    pipeline = models.TextField()
    workspace = models.ForeignKey('workspace.Workspace')
    event = models.ForeignKey('eventmanager.EventRegistration',  null = True,  blank = True)
    state = models.ForeignKey('workflow.State',  null = True,  blank = True)
    
    def __unicode__(self):
        return unicode(self.name)
    
    def create_state_machine(self, items):
        pipeline = simplejson.loads(self.pipeline)
        adapt_parameters = {}
        actions_available = {}
        
        variant = pipeline['variant']
        for subclass in BaseMDAction.__subclasses__():
            actions_available[subclass.__name__.lower()] = subclass
        for action in pipeline['actions']:
            
            type = action['type'].lower()            
            if type in actions_available.keys():
                pass
            
    class Meta:
        unique_together = ('name', 'workspace' )
  
  
class MissingActionParameters(Exception):
  pass

class WrongInput(Exception):
  pass

class BaseMDAction(object):
    required_params = []
    input_number = 1
    output_number = 1
    def __init__(self, inputs,parameters):
        if self.parameters.keys().sort() != required_params:
            raise MissingActionParameters('action parameters are: %s; parameters passed are %s'%(self.required_params, parameters))
        if isinstance(inputs, list):
            if len(inputs) > self.input_number:
                raise WrongInput('expected %s inputs, %s given'%self.input_number, len(inputs)) 
        
        self.input = input        
        self.parameters = parameters
    
    def validate(self):
        pass
    
class Resize(BaseMDAction):
    required_params = ['max_dim']
    
    def validate(self):                
        return {'max_dim': self.parameters['max_dim']}
    
class Transcoding(BaseMDAction):
    required_params = ['format']
    
    def validate(self):
        return {'output_file': self.input + '.' + self.parameters['format']}

class Watermark(BaseMDAction):
    required_params = ['file']
    def validate(self):
        return {'watermark':self.parameters['file']}


    
    
class Action(models.Model):
    component = models.ForeignKey(Component)
    function = models.CharField(max_length=64)

    def __str__(self):
        return "%s %s"  % (self.component.get_variant().name, self.function )

class MachineState(models.Model):
    name = models.CharField(max_length=64)
    action = models.ForeignKey(Action, null=True, blank=True)
    next_state =  models.ForeignKey('self', null=True, blank=True)

    def copy(self):
        initial = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields if not isinstance(f, models.AutoField) and not f in self._meta.parents.values()])
        return self.__class__(**initial)
        
class Machine(models.Model):
    initial_state = models.ForeignKey(MachineState, related_name='initial')
    current_state = models.ForeignKey(MachineState)
    wait_for = models.ForeignKey('self', null=True, blank=True)

        
    
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
