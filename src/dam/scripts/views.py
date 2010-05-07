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

from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from dam.scripts.models import *
from dam.eventmanager.models import Event, EventRegistration
from dam.workspace.models import Workspace
from dam.framework.dam_repository.models import Type
from httplib import HTTP

@login_required
def get_actions(request):    
    actions = {'actions':[]}    
    
    for action in BaseAction.__subclasses__():
      
            
            actions['actions'].append({                                
                    'name':action.__name__.lower(),
                    'media_type': action.media_type_supported,
                    'parameters': action.required_parameters                    
            })
                
    return HttpResponse(simplejson.dumps(actions))
         
def new_script(request):
    pipeline = simple_json.loads(request.POST['actions'])
    name = request.POST['name']
    description = request.POST.get('description')
    workspace_id = request.POST['workspace_id']
    workspace = Workspace.objects.get(pk = workspace_id)  
    events = request.POST.getlist('event')
    
    script = Script.objects.create(name = name, description = description, workspace = workspace, pipeline = pipeline)
    
    for event_name in events:
        event = Event.objects.get(name = event_name)
        EventRegistration.objects.create(event = event, listener = script)
        
    return HttpResponse(simplejson.dumps({'success': True}))


def edit_script(request):
    script_id = request.POST['script_id']
    script = Script.objects.get(pk = script_id)
    
    pipeline_str = request.POST.get('actions')
    if pipeline_str:        
        script.pipeline = pipeline_str
        
    name = request.POST.get('name')
    if name:
        script.name = name
        
    description = request.POST.get('description')
    if description:
        script.description = description
    
    events = request.POST.getlist('event')
    
    for event_name in events:
        event = Event.objects.get(name = event_name)
        EventRegistration.objects.get_or_create(event = event, listener = script)
    
    script.save()
    return HttpResponse(simplejson.dumps({'success': True}))
        
        
        
         
             