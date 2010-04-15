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
    actions = models.ManyToManyField('Action', through = 'Action2Script')
    workspace = models.ForeignKey('workspace.Workspace')
    event = models.ForeignKey('eventmanager.EventRegistration',  null = True,  blank = True)
    state = models.ForeignKey('workflow.State',  null = True,  blank = True)
    
class Action(models.Model):
    name = models.CharField(max_length = 50)
    previous_action = models.ForeignKey('self',  null = True,  blank = True)
    command = models.CharField(max_length = 200)
    


class ActionParameter(models.Model):
    name = models.CharField(max_length = 50)
    caption = models.CharField(max_length = 100)
    
class Action2Script(models.Model):
    action = models.ForeignKey('Action')
    script = models.ForeignKey('Script')
    parameters = models.ManyToManyField('Parameter2Action')
    
    
class Parameter2Action(models.Model):
    parameter = models.ForeignKey('ActionParameter')
    action2script = models.ForeignKey('Action2Script')
    value = models.CharField(max_length = 50)
    
    
    
