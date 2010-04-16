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

class Script(models.Model):
    name = models.CharField(max_length= 50)
    actions = models.ManyToManyField('Action', through = 'ActionScriptAssociation')
    workspace = models.ForeignKey('workspace.Workspace')
    event = models.ForeignKey('eventmanager.EventRegistration',  null = True,  blank = True)
    state = models.ForeignKey('workflow.State',  null = True,  blank = True)
    
    def __unicode__(self):
        return unicode(self.name)
        
    
class Action(models.Model):
  
    name = models.CharField(max_length = 50)
    command = models.CharField(max_length = 200)
    media_type = models.ManyToManyField('application.Type')
    
    def __unicode__(self):
        return unicode(self.name)

class Parameter(models.Model):
    name = models.CharField(max_length = 50)
    caption = models.CharField(max_length = 100)
    
    def __unicode__(self):
        return unicode(self.name)

class ActionScriptAssociation(models.Model):
    action = models.ForeignKey('Action')
    script = models.ForeignKey('Script')
    action_position = models.SmallIntegerField()
    parameters= models.ManyToManyField('ParameterToAction',  related_name = 'parameter_values',  null = True,  blank = True)
    
    class Meta:
        unique_together = ('script', 'action_position' )
    
class ParameterToAction(models.Model):
    parameter = models.ForeignKey('Parameter')
    ActionScriptAssociation = models.ForeignKey('ActionScriptAssociation')
    value = models.CharField(max_length = 50)
    
    def __unicode__(self):
        return unicode(self.parameter.name)
