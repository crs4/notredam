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
from dam.variants.models import Variant
from dam.repository.models import Component
from dam.core.dam_repository.models import Type
from django.db.models import Q
from dam import logger
from django.contrib.auth.models import User

INPROGRESS= 'in_progress'
FAILED = 'failed'
FINISHED = 'finished'

class Script(models.Model):
    name = models.CharField(max_length= 50)
    description = models.TextField(blank=True)
    # upload etc, used to group pipelines that must be run in succession at certain points
    type = models.CharField(max_length=32, blank=True, default="") 
    params = models.TextField()
    workspace = models.ForeignKey('workspace.DAMWorkspace')
#    
#    def run(self, user,items, session = None):
#        process = Process.objects.create(script = self, session = session, launched_by = user)
#        for item in items:
#            target = ProcessTarget.objects.create(process = process, target_id = item.pk)
            
def inspect_actions():
    from settings import INSTALLED_ACTIONS
    import sys
    
    actions = []
    
    for action in INSTALLED_ACTIONS:
        __import__(action)   
        m = sys.modules[action]
        name = m.__name__.split('.')[-1]
        actions.append({'name': name, 'parameters': m.inspect()})

    return actions
        



#class ScriptItemExecution(models.Model):
#    script_execution = models.ForeignKey('ScriptExecution')
#    item = models.ForeignKey('repository.Item')
#    status = models.TextField(default = INPROGRESS)
#
#class ScriptExecution(models.Model):
#    script = models.ForeignKey('Script')
#    session = models.CharField(max_length=256,null = True, blank = True)
#    start_date = models.DateTimeField(auto_now_add = True)
#    end_date = models.DateTimeField(null = True, blank = True)
##    event =  models.ForeignKey('eventmanager.Event', null = True, blank = True)    
#    launched_by = models.ForeignKey(User)
#    items = models.ManyToManyField('repository.Item', through = ScriptItemExecution)  
#    
#    def get_status(self):
#        if self.items.filter(status = INPROGRESS).count() > 0:
#            return INPROGRESS
#        return FINISHED
#         
#    def get_items_in_progress(self):
#        return self.items.filter(status = INPROGRESS)
#    
#    def get_items_finished(self):
#        return self.items.filter(status = FINISHED)
#    
#    def get_items_failed(self):
#        return self.items.filter(status = FAILED)
#    
#    def get_time_elapsed(self):
#        pass
