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
from dam.core.dam_repository.models import Type
from httplib import HTTP
from django.db import IntegrityError

@login_required
def get_scripts(request):
    workspace = request.session.get('workspace')
    media_type = request.POST.getlist('media_type')
    if not media_type:
        media_type =  Type.objects.all().values_list('name', flat = True)
    scripts = Script.objects.filter(workspace = workspace, actionlist__media_type__name__in = media_type).distinct()
    resp = {'scripts': []}
    for script in scripts:
        actions_media_type = {}
        for action in script.actionlist_set.all():                        
            actions_media_type[action.media_type.name] = simplejson.loads(action.actions)
             
        resp['scripts'].append({'id': script.pk, 'name': script.name, 'description': script.description, 'actions_media_type': actions_media_type})
    
    return HttpResponse(simplejson.dumps(resp))


@login_required
def get_script_actions(request):
    script_id = request.POST['script']
    media_type = request.POST.getlist('media_type', Type.objects.all().values_list('name', flat = True))
    script = Script.objects.get(pk = script_id)
    tmp = simplejson.loads(script.pipeline)
    resp = {'actions': tmp['media_type']}
    return HttpResponse(simplejson.dumps(resp))

    

@login_required
def get_actions(request):  
    media_type = request.POST.get('media_type') # if no media_type all actions will be returned
    workspace = request.session.get('workspace')
    logger.debug('media_type %s'%media_type)  
    actions = {'actions':[]}    
    classes = []
    classes.extend(BaseAction.__subclasses__())
    classes.extend(SaveAction.__subclasses__())
    
    for action in classes:
            if action == SaveAction:
                continue
                
            if media_type:
                if media_type in action.media_type_supported:
                    add_action = True
                else:
                    add_action = False
            else:
                add_action = True
            
            if add_action:
               
                tmp = {                                 
                        'name':action.verbose_name.lower(),
                        'media_type': action.media_type_supported,
                        'parameters': action.required_parameters(workspace)                    
                }
                actions['actions'].append(tmp)
    logger.debug('actions %s'%actions)        
    return HttpResponse(simplejson.dumps(actions))

def _new_script(name = None, description = None, workspace = None, pipeline = None, events = [], script = None):
    
    if script:        
        if pipeline:
            ActionList.objects.filter(script = script).delete()
    else:
        script = Script.objects.create(name = name, description = description, workspace = workspace)
    
    if pipeline:
        pipeline = simplejson.loads(pipeline)
    
        for media_type, actions in pipeline.items():
            source_variant_name = actions.get('source_variant',  'original')
            source_variant = Variant.objects.get(name = source_variant_name, auto_generated = False )
            ActionList.objects.create(script = script, media_type = Type.objects.get(name = media_type), actions = simplejson.dumps(actions), source_variant = source_variant)

    
    EventRegistration.objects.filter( script = script, workspace = workspace).delete()
    for event_name in events:
        event = Event.objects.get(name = event_name)
        EventRegistration.objects.create(event = event, listener = script, workspace = workspace)

    return script

@login_required
def new_script(request):
    
    no_actions = simplejson.dumps({'image':[], 'audio': [], 'video': [], 'doc': []})
    pipeline = request.POST.get('actions_media_type', no_actions)
    name = request.POST['name']
    description = request.POST.get('description')
    workspace = request.session.get('workspace')
      
    events = request.POST.getlist('event')
    try:
        script = _new_script(name, description, workspace, pipeline, events)
    except IntegrityError:
        return HttpResponse(simplejson.dumps({'success': False, 'errors': [{'id': 'script_name', 'msg': 'A script named %s already exist'%name}]}))
    
    return HttpResponse(simplejson.dumps({'success': True, 'id': script.pk}))

@login_required
def edit_script(request):
    script_id = request.POST['script']
    script = Script.objects.get(pk = script_id)
    
    if script.is_global:        
        return HttpResponse(simplejson.dumps({'error': 'script is not editable'}))
        
    pipeline = request.POST.get('actions_media_type')
    workspace = request.session.get('workspace')
    name = request.POST.get('name')
    description = request.POST.get('description')
    events = request.POST.getlist('event')
    try:
        _new_script(name, description, workspace, pipeline, events, script)
    except IntegrityError:
        return HttpResponse(simplejson.dumps({'success': False, 'errors': [{'name': 'name', 'msg': 'script named %s already exist'%name}]}))
    
#    items = [c.item for c in script.component_set.all()]
#    script.execute(items)
        
    return HttpResponse(simplejson.dumps({'success': True}))

@login_required
def rename_script(request):
    script_id = request.POST['script']
    script = Script.objects.get(pk = script_id)
    
    if script.is_global:        
        return HttpResponse(simplejson.dumps({'error': 'script is not editable'}))
        
    workspace = request.session.get('workspace')
    name = request.POST['name']
    description = request.POST['description']
    script.name = name
    script.description = description
    script.save()
    
    return HttpResponse(simplejson.dumps({'success': True}))



@login_required
def delete_script(request):        
    script_id = request.POST['script']
    script = Script.objects.get(pk = script_id)
    if not script.is_global:
        script.delete()
    else:
        return HttpResponse(simplejson.dumps({'error': 'script is not editable'}))
    return HttpResponse(simplejson.dumps({'success': True}))

@login_required
def run_script(request):
    from dam.repository.models import Item
    script_id = request.POST['script_id']
    items = request.POST.getlist('items')
    items = Item.objects.filter(pk__in = items)
    
    script = Script.objects.get(pk = script_id)
    script.execute(items)
    return HttpResponse(simplejson.dumps({'success': True}))
    
  
