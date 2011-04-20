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
from dam.mprocessor.models import Pipeline, TriggerEvent
from dam.supported_types import mime_types_by_type
from dam.logger import logger

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
    
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_actions(request):  
    import os, settings
    from mediadart.config import Configurator
    workspace = request.session.get('workspace')
    
    c = Configurator()
    actions_modules =  c.get("MPROCESSOR", "plugins")
    src_dir = '/'.join(settings.ROOT_PATH.split('/')[:-1]) #removing dam dir, it ends with src dir
    actions_dir = actions_modules.replace('.', '/')
    all_files = os.listdir(os.path.join(src_dir, actions_dir))
    
    resp = {'scripts':[]}
    modules_to_load = []
    try:
        for filename in all_files:
            if filename.endswith('.py') and not filename.endswith('_idl.py'):
                modules_to_load.append(filename.split('.py')[0])
                
        top_module = __import__(actions_modules, fromlist=modules_to_load)
        logger.debug('modules_to_load %s'%modules_to_load)
        for module in modules_to_load:
            try:
                logger.debug(module)
                
                module_loaded = getattr(top_module, module, None)
                if module_loaded:
                    logger.debug(module_loaded)
                    
                    
                    if hasattr(module_loaded, 'inspect'):
                        tmp = module_loaded.inspect(workspace)
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


def _edit_script(pk, name, params,workspace, media_types, events):
    if pk: #editing an existing script
        pipeline = Pipeline.objects.get(pk = pk)
        pipeline.triggers.remove(*pipeline.triggers.all())
        pipeline.media_type.remove(*pipeline.media_type.all())
    else:
        pipeline = Pipeline()
        
        pipeline.workspace = workspace
        
    pipeline.name = name    
    pipeline.params = params

    pipeline.save()
    
    for m in media_types:
        if m not in mime_types_by_type:
            continue
        for subm in mime_types_by_type[m]:
            t = Type.objects.get_or_create_by_mime('%s/%s' % (m, subm))
            pipeline.media_type.add(t)

    existing_events = [e.name for e in TriggerEvent.objects.all()]
    for e in events:
        if e not in existing_events:
            continue
        pipeline.triggers.add(TriggerEvent.objects.get(name = e))
    
    return pipeline

@login_required
def edit_script(request):
    from mprocessor.pipeline import DAG, DAGError
    pk = request.POST.get('pk')
    name = request.POST['name']
    params =  request.POST['params']
    media_types = request.POST.getlist('media_types')
    events = request.POST.getlist('events')
    workspace = request.session['workspace']
    
    try:
        dag = DAG(simplejson.loads(params))
        logger.debug('params %s'%params)
        logger.debug(dag.show())
        pipeline = _edit_script(pk, name, params, workspace, media_types, events)
    except IntegrityError:
        return HttpResponseServerError(simplejson.dumps({'success': False, 'errors': [{'name': 'script_name', 'msg': 'script named %s already exist'%name}]}))
    except DAGError:
        return HttpResponseServerError(simplejson.dumps({'success': False,  'errors': 'Cyclic graph'}))

    return HttpResponse(simplejson.dumps({'success': True, 'pk': pipeline.pk}))  

@login_required
def delete_script(request):        
    script_id = request.POST['pk']
    script = Pipeline.objects.get(pk = script_id)
    script.delete()
    return HttpResponse(simplejson.dumps({'success': True}))



def _run_script(pipe, user, workspace, items = None, run_again = False):
    if run_again:
        pass
    process = None
    for item in items:        
#        logger.debug('item.type'%item.type)
        if pipe.is_compatible(item.type):
            if not process:
                process = Process.objects.create(pipeline=pipe, 
                    workspace=workspace, 
                    launched_by=user)
            process.add_params(target_id=item.pk)
    if process:
        process.run()
    
@login_required
def run_script(request):
    from dam.repository.models import Item
    script_id = request.POST['script_id']
    script = Pipeline.objects.get(pk = script_id)
    
    run_again = request.POST.get('run_again')
   
    if not run_again:
        items = request.POST.getlist('items')
        items = Item.objects.filter(pk__in = items)
    else:
        items = []
        
    _run_script(script, request.user, request.session['workspace'], items,  run_again)
   
    return HttpResponse(simplejson.dumps({'success': True}))

def _script_monitor(workspace):
    import datetime, settings    
    processes = workspace.get_active_processes()
    processes_info = []
    for process in processes:
        try:

            if not process.last_show_date:
                process.last_show_date = datetime.datetime.now()
                process.save()
    #                status = 'in progress'
                
            elif settings.REMOVE_OLD_PROCESSES and process.is_completed() and (datetime.datetime.now() - process.last_show_date).days > 0:
                
                process.delete()
                logger.debug('process %s deleted'%process.pk)
                continue
    #            else:
    #                status = 'in progress'
            
            items_completed =  process.get_num_target_completed()
            items_failed =  process.get_num_target_failed()
            total_items = process.processtarget_set.all().count()
            if total_items == 0:
                progress = 0
            else:
                progress =  round(float(items_completed)/float(total_items)*100)
                            
            tmp = {
                'id': process.pk,
                 'name':process.pipeline.name,
    #                 'status': status,                 
                 'total_items':total_items,
                 'items_completed': items_completed,
                 'progress':progress,
                 'type': ','.join([trigger.name for trigger in process.pipeline.triggers.all()]),                 
                 'start_date': process.start_date.strftime("%d/%m/%y %I:%M:%S"),
                 'launched_by': process.launched_by.username,
                 'items_failed': items_failed
                 }
        
            if process.end_date:
                tmp['end_date'] = process.end_date.strftime("%d/%m/%y %I:%M:%S")
                
            processes_info.append(tmp)
        except Exception, ex:
            logger.exception(ex)
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


@login_required
def get_events(request):
    script_id = request.POST.get('script_id')

    if script_id:
        pipeline = Pipeline.objects.get(pk = script_id)
        pipeline_triggers = pipeline.triggers.all()
    else:
        pipeline_triggers = TriggerEvent.objects.none()
    
    resp = {'events':[], 'success':True,}
    for t in TriggerEvent.objects.all():
        resp['events'].append({'id':t.pk, 'text':t.name, 'checked':(t in pipeline_triggers)})
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_media_types(request):
    script_id = request.POST.get('script_id')

    if script_id:
        pipeline = Pipeline.objects.get(pk = script_id)
        pipeline_media_types = [x.name for x in pipeline.media_type.all()]
    else:
        pipeline_media_types = []
    
    resp = {'types':[], 'success':True,}
    for t in mime_types_by_type.keys():
        resp['types'].append({'value': t, 'text': t, 'checked':(t in pipeline_media_types)})
    return HttpResponse(simplejson.dumps(resp))


@login_required
def editor(request, script_id = None):
    
    from django.template import RequestContext
    from django.shortcuts import render_to_response
    script_id = script_id or request.POST.get('pk')
    logger.debug('script_id %s'%script_id)

    if script_id:
        pipeline = Pipeline.objects.get(pk = script_id)
        workspace = pipeline.workspace
        params = pipeline.params
        name = pipeline.name
    else:
        workspace_id  = request.GET['workspace']
        workspace = Workspace.objects.get(pk = workspace_id)
        params = ''
        name = '' 
        pk = ''
    logger.debug('params: %s'%params)
    return render_to_response('script_editor.html', RequestContext(request,{'params':params,  'name': name, 'pk': script_id, 'workspace': workspace }))

@login_required
def get_failures_info(request):
    process_id = request.POST['process_id']
    process = Process.objects.get(pk = process_id)
    resp = ''
    for process_target in process.processtarget_set.filter(actions_failed__gt = 0):
        resp += '<p>item pk:<b>%s</b></p>'%(process_target.target_id)
        resp += '<p>Errors:</p>'
        resp += '<p>' +  process_target.result + '</p>'

    return HttpResponse(resp)

