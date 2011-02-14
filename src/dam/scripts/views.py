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
from dam.mprocessor.models import *
from dam.eventmanager.models import Event, EventRegistration
from dam.workspace.models import Workspace
from dam.core.dam_repository.models import Type
from httplib import HTTP
from django.db import IntegrityError


def _get_scripts_info(script):
        
    return {'id': script.pk, 
            'name': script.name, 
            'description': script.description, 
#            'is_global': script.is_global,  
             
            'already_run': script.component_set.all().count() > 0,
            'workspace_id': script.workspace.pk
            
            }

@login_required
def get_scripts(request):
    workspace = request.session.get('workspace')
    
    scripts = Pipeline.objects.filter(workspace = workspace).distinct()
    resp = {'scripts': []}
            
    for script in scripts:
        info =  _get_scripts_info(script)
        resp['scripts'].append(info)
        
    resp['scripts'].append(info)
    
    return HttpResponse(simplejson.dumps(resp))


@login_required
def get_script_actions(request):
    script_id = request.POST['script']
    media_type = request.POST.getlist('media_type', Type.objects.all().values_list('name', flat = True))
    
    
    resp = {'actions': tmp['media_type'], 'already_run': script.component_set.all().count() > 0}
    return HttpResponse(simplejson.dumps(resp))

    

@login_required
def get_actions(request):  
    import os, settings
    from mediadart.config import Configurator
    
    
    c = Configurator()
    actions_modules =  c.get("MPROCESSOR", "plugins")
    src_dir = '/'.join(settings.ROOT_PATH.split('/')[:-1]) #removing dam dir, it ends with src dir
    actions_dir = actions_modules.replace('.', '/')
    all_files = os.listdir(os.path.join(src_dir, actions_dir))
    
    resp = {'scripts':[]}
    modules_to_load = []
    try:
        for file in all_files:
            if file.endswith('.py'):
                modules_to_load.append(file.split('.py')[0])
                
        top_module = __import__(actions_modules, fromlist=modules_to_load)
        logger.debug('modules_to_load %s'%modules_to_load)
        for module in modules_to_load:
            try:
                logger.debug(module)
                
                module_loaded = getattr(top_module, module, None)
                if module_loaded:
                    logger.debug(module_loaded)
                    logger.debug('aaaa %s'%hasattr(module_loaded, 'inspect'))
                    
                    if hasattr(module_loaded, 'inspect'):
                        tmp = module_loaded.inspect()
                        tmp.update({'name': module})
                        resp['scripts'].append(tmp)
                        media_type = request.POST.get('media_type') # if no media_type all actions will be returned
            except Exception, ex:
                logger.error(ex)
                continue
        
    except Exception, ex:
        logger.exception(ex)
        raise ex        
    return HttpResponse(simplejson.dumps(resp))

def _new_script(name = None, description = None, workspace = None, pipeline = None, events = [], script = None,  is_global = False):
    
    if script:        
        if pipeline:
            ActionList.objects.filter(script = script).delete()
        if name:
            script.name = name
        if description:
            script.description = description
        script.save()
    else:
        script = Script.objects.create(name = name, description = description, workspace = workspace,  is_global = is_global)
 
        
    if pipeline:
        pipeline = simplejson.loads(pipeline)
    
        for media_type, actions in pipeline.items():
            if actions.get('actions'):
                source_variant_name = actions.get('source_variant',  'original')
                logger.debug('media_type %s'%media_type)
                logger.debug('actions %s'%actions)
                
                logger.debug('source_variant_name %s' %source_variant_name)
                source_variant = Variant.objects.get(name = source_variant_name, auto_generated = False )
                ActionList.objects.create(script = script, media_type = Type.objects.get(name = media_type), actions = simplejson.dumps(actions), source_variant = source_variant)

    
#    EventRegistration.objects.filter( script = script, workspace = workspace).delete()
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
    
#    if script.is_global:        
#        return HttpResponse(simplejson.dumps({'error': 'script is not editable'}))
        
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
    
#    if script.is_global:        
#        return HttpResponse(simplejson.dumps({'error': 'script is not editable'}))
#        
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



def _run_script(script, items = None,   run_again = False):
    if run_again:
        items = [c.item for c in script.component_set.all()]
    logger.debug('items %s'%items)
    logger.debug('script %s'%script)
    logger.debug('script.actionlist_set.all() %s'%script.actionlist_set.all())
    script.execute(items)
    
    
@login_required
def run_script(request):
    from dam.repository.models import Item
    script_id = request.POST['script_id']
    script = Script.objects.get(pk = script_id)
    
    run_again = request.POST.get('run_again')
   
    if not run_again:
        items = request.POST.getlist('items')
        items = Item.objects.filter(pk__in = items)
    else:
        items = []
        
    _run_script(script,  items,  run_again)
   
    return HttpResponse(simplejson.dumps({'success': True}))


@login_required
def get_available_actions(request):
    resp =  {'actions': [{
                'name': 'adapt_image',
                'params': {}
            }
                         
                         
            ]}
    return HttpResponse(simplejson.dumps(resp))

def _script_monitor(workspace):
    import datetime    
    processes = workspace.get_active_processes()
    processes_info = []
    for process in processes:
        try:

            if not process.last_show_date:
                process.last_show_date = datetime.datetime.now()
                process.save()
    #                status = 'in progress'
                
            elif process.is_completed() and (datetime.datetime.now() - process.last_show_date).days > 0:
                
                process.delete()
                continue
    #            else:
    #                status = 'in progress'
            
            items_completed =  process.get_num_target_completed()
            items_failed =  process.get_num_target_failed()
            total_items = process.processtarget_set.all().count()
            if total_items == 0:
                progress = 0
            else:
                progress =  round(float(items_failed + items_completed)/float(total_items)*100)
              
            processes_info.append({
                'id': process.pk,
                 'name':process.pipeline.name,
    #                 'status': status,                 
                 'total_items':total_items,
                 'items_completed': items_completed,
                 'progress':progress,
                 'type': process.pipeline.type,
                 'start_date': process.start_date.strftime("%d/%m/%y %I:%M:%S"),
                 'end_date': process.end_date.strftime("%d/%m/%y %I:%M"),
                 'launched_by': process.launched_by.username,
                 'items_failed': items_failed
                 })
        except:
            continue
        
    return processes_info
        
    


@login_required
def script_monitor(request):   
    
    try:
        workspace = request.session['workspace']
        processes_info = _script_monitor(workspace)
        
        return HttpResponse(simplejson.dumps({
            'success': True,
            'scripts':processes_info
        }))
    except Exception, ex:
        logger.exception(ex)
        return HttpResponse(simplejson.dumps({'success': False}))
    
    
