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

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic.simple import redirect_to
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import IntegrityError
from django.utils import simplejson

from dam.settings import ROOT_PATH, SERVER_PUBLIC_ADDRESS
from dam.variants.models import Variant
from dam.core.dam_repository.models import Type
from dam.repository.models import Component
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.decorators import permission_required
from dam.repository.models import Component,  Item
from dam.metadata.views import _get_ws_groups
from dam.batch_processor.models import Machine

import os
import logger
import os, time

class MediaTypeNotFound(Exception):
    pass

def _edit_variant(variant_id,name, workspace, media_type):
    if not media_type:
        raise MediaTypeNotFound
    if not variant_id:
        v = Variant.objects.create(name = name,  workspace = workspace, auto_generated =  True)
        v.media_type = []
        v.media_type.add(*media_type)
    else:
        v = Variant.objects.get(pk = variant_id, workspace = workspace)    
        if name:
            v.name = name
        if media_type:
            v.media_type = []
            v.media_type.add(*media_type)
        v.save()
    return v
    

@login_required
@permission_required('admin')
def edit_variant(request):
    workspace = request.session['workspace']
    
    
    media_type =  Type.objects.filter(name__in = request.POST.keys())
    logger.debug('media_type %s'%media_type)
    name = request.POST.get('name')
    variant_id = request.POST.get('variant_id')
    
    try:
        v = _edit_variant(variant_id,name, workspace, media_type)
    except Variant.DoesNotExist:
        return HttpResponse(simplejson.dumps({'success': False, 'msg':'variant does not exist or is not editable'}))
    except MediaTypeNotFound:
        return HttpResponse(simplejson.dumps({'success': False, 'msg':'no media type selected'}))
    except IntegrityError:
        return HttpResponse(simplejson.dumps({'success': False, 'errors':[{'id': 'name', 'msg':'a variant with the same name already exists'}]}))
    return HttpResponse(simplejson.dumps({'success': True, 'pk': v.pk}))
    

#@login_required
#@permission_required('admin')
#def edit_variant(request):
#    workspace = request.session['workspace']
#    variant_id = request.POST['variant_id']
#    v = Variant.objects.get(pk = variant_id)    
#    name = request.POST['name']
#    v.name = name
#    v.save()
#    return HttpResponse(simplejson.dumps({'success': True}))
    
@login_required
@permission_required('admin')
def delete_variant(request):     
	
	variant_id = request.POST['variant_id']
	var =  Variant.objects.get(pk = variant_id )
	if var.workspace:
		var.delete()	
	else:
		HttpResponse(simplejson.dumps({'success':False}))

	return HttpResponse(simplejson.dumps({'success':True}))

@login_required
@permission_required('admin')
def force_variant_generation(request,  variant_id,  item_id):
    from dam.upload.views import generate_tasks
    
    workspace = request.session['workspace']
    variant = Variant.objects.get(pk = variant_id)
        
    component = variant.component_set.get(workspace = workspace,  item__pk = item_id)
    component.imported = False
    component.save()
    item = component.item
    try:
        
#        variant = component.variant
#        component = variant.get_component(workspace,  item)
#        component.new_md_id()
        generate_tasks(variant, workspace,  item,  force_generation = True)    
    except Exception,  ex:
        logger.exception(ex)
    
    return HttpResponse(simplejson.dumps({'success': True}))

@login_required
def get_variant_sources(request):
    workspace = request.session['workspace']
    variant_id = request.POST.get('variant_id')
    resp = {'variants':[]}
    
    
    if variant_id:
        variant = Variant.objects.get(pk = variant_id)
        sources = SourceVariant.objects.filter(destination = variant,  workspace = workspace)
        media_type = variant.media_type.name
        
        source_ids = []
        for source in sources:
            source_variant= source.source
            source_ids.append(source_variant.pk)
            resp['variants'].append({'pk': source_variant.pk,  'name': source_variant.name,  'rank': source.rank,  'original':  source_variant.is_global and source_variant.name == 'original',  'is_global':source_variant.is_global})
        
        
    else: #new variant
        variant = None
        media_type = request.POST['media_type']
        orig = Variant.objects.get(name = 'original',  media_type__name = media_type)
        resp['variants'].append({'pk': orig.pk,  'name': orig.name,  'rank': 1,  'original':  True,   'is_global': True})

    
    available_sources =  Variant.objects.filter(auto_generated = False, workspace = workspace, media_type__name = media_type)

    if variant:
        available_sources = available_sources.exclude(pk__in = source_ids)
    else:
        available_sources = available_sources.exclude(pk =  orig.pk)
    

    for source in available_sources:          
        resp['variants'].append({'pk': source.pk,  'name': source.name,  'rank': 0,  'is_global':source.is_global})
 
    return HttpResponse(simplejson.dumps(resp))
        
    
@login_required
def get_variants_list(request):
    workspace = request.session['workspace']
#    workspace = Workspace.objects.get(pk = 1)
#    media_type = request.POST['media_type']
    type = request.POST.get('type',  '')
    logger.debug('type %s'%type)
    if type == '':
        
        vas = Variant.objects.filter(Q(workspace = workspace)| Q(workspace__isnull = True), hidden = False)
    else:
        vas = Variant.objects.filter(Q(workspace = workspace)| Q(workspace__isnull = True), auto_generated =  (type == 'generated'),  hidden = False)
    
    
    resp = {'variants':[]}
    for variant in vas:
        
        resp['variants'].append({'pk':variant.pk,  'name': variant.name, 'is_global': variant.workspace is None })
    
    return HttpResponse(simplejson.dumps(resp))


@login_required
@permission_required('admin')
def get_variant_info(request):
    
    variant_id = request.POST['variant_id']
    variant = Variant.objects.get(pk = variant_id)
    
    resp = {'data':{'name': variant.name}, 'success': True}
    
    variant_media_type = variant.media_type.all()
    for media_type in Type.objects.all():
        if media_type in variant_media_type:
            resp['data'][media_type.name] = True  
     
    resp = simplejson.dumps(resp)
    return HttpResponse(resp)


@login_required
def get_variants(request):
    
    workspace = request.session['workspace']
    item_id = request.POST.get('items')
    logger.debug('item_id %s'%item_id)
    item = Item.objects.get(pk = item_id)
    logger.debug('before comps')
    user = User.objects.get(pk=request.session['_auth_user_id'])
    
    item_variants = Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True), media_type = item.type, hidden = False).distinct()
    logger.debug('item_variants %s'%item_variants)

    now = time.time()
    resp = {'variants':[]}
    for v in item_variants:
        auto_generated = v.auto_generated     
        try:
            logger.debug('variant  %s'%v)
            comp = Component.objects.get(item = item,  workspace = workspace,  variant = v)
            
            work_in_progress = Machine.objects.filter(current_state__action__component = comp).count() > 0
#            resource_url = "/resources/%s/%s/"% (comp.id, workspace.pk)
            resource_url = comp.get_component_url()
            abs_resource_url = SERVER_PUBLIC_ADDRESS + resource_url
#            resource_url = "/redirect_to_component/%s/%s/?t=%s"% (item_id,  v.name,  now)
#            resource_url = comp.get_component_url(True)
            info_list = []
            if comp.media_type.name== 'image':
                extension = comp.format
            else:
                if comp.format in ['flv',  'mp3',  'mp4',  'mpeg',  'mpg',  'x-flv']:
                    extension = comp.format
                else:
                    extension = None
                    
           
            media_type = comp.media_type.name 
            imported = comp.imported
            
            basic_group = _get_ws_groups(workspace, 'specific_basic')[0]
            full_group = _get_ws_groups(workspace, 'specific_full')[0]
            
            info_list = comp.get_formatted_descriptors(basic_group,  user, workspace)
            info_list_full = comp.get_formatted_descriptors(full_group,  user, workspace)
            
#            info_list.append({'caption': 'File Size', 'value': '%s' % comp.format_filesize()})
        except Exception,  ex:
            logger.exception(ex)
            work_in_progress =  True
          
            resp['variants'].append({'pk': v.pk, 
                                     'variant_name': v.name, 
                                     'item_id': item_id,  
                                     'auto_generated':auto_generated,  
                                     'media_type': media_type, 
                                      'work_in_progress':work_in_progress})
            continue
            
            #logger.exception(ex)
#            pk = None
#            prefs = v.variantassociation_set.get(workspace = workspace).preferences
#            if prefs:
#                media_type = prefs.media_type.name
#            else:
#                media_type = item.type.name
#            imported = False
#            work_in_progress = False
#            info_list = []
#            info_list_full = []
#            resource_url = ''
#            auto_generated = v.auto_generated
#            extension = None
            
        resp['variants'].append({'data_basic': info_list, 
                                 'data_full':info_list_full,
                                 'variant_name': v.name,
                                 'resource_url': resource_url,
                                 'abs_resource_url': abs_resource_url,  
                                 'pk': v.pk,  
                                 'imported':imported, 
                                 'item_id': item_id,  
                                 'auto_generated':auto_generated,  
                                 'media_type': media_type,  
                                 'extension':extension,  
                                 'work_in_progress':work_in_progress,  
                                 'width': str(comp.width), 
                                  'height': str(comp.height )})
    
    return HttpResponse(simplejson.dumps(resp))

def get_variant_metadata(request):
    try:
        workspace = request.session['workspace']
        component_id= request.POST.get('component_id')
        component = Component.objects.get(pk = component_id )
#        item = Item.objects.get(component = component)
        
        metadata  = []
        for data in component.metadata.all().distinct():
            
            metadata.append({ 
                                        'name':data.schema.field_name, 
                                        'namespace':data.schema.namespace.prefix,
                                        'caption':data.schema.caption,
                                        'value': data.value})
        
        result = {'metadata':metadata}
        return HttpResponse(simplejson.dumps(result))
        
        
    except Exception,  ex:
        logger.exception(ex)
        raise ex
    

@login_required
@permission_required('admin')
def save_sources(request):
    logger.debug(request.POST)
    try:
        resp = {'success': True}
        workspace = request.session['workspace']
        variants = request.POST['variants']
        media_type = request.POST['media_type']
        variants = simplejson.loads(variants)
        existing_variant_ids = []
        for v in variants:
            if v['pk']:
                existing_variant_ids.append(v['pk'])
                variant = Variant.objects.get(pk = v['pk'])
                if not variant.is_global:
                    if v['name']!= variant.name:
                        variant.name = v['name']
                        variant.save()
                        
            else:
                logger.debug('creating variant %s'%v['name'])
                variant = Variant.objects.create(name = v['name'],  is_global = False,  workspace = workspace, auto_generated = False,  media_type = Type.objects.get(name= media_type))
#                VariantAssociation.objects.create(variant= variant,  workspace = workspace)
                existing_variant_ids.append(variant.pk)
                
        variant_to_delete = Variant.objects.filter(is_global = False,  auto_generated = False,  workspace = workspace).exclude(pk__in = existing_variant_ids)
        variant_to_delete.delete()
        
    except Exception,  ex:
        logger.exception(ex)
        raise ex
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_variants_menu_list(request):
    """
    Returns the list of variants of the current workspace
    """
    workspace = request.session['workspace']
    
    vas = Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False).exclude(name='original').order_by('name').values_list('name', flat=True)  
    
    vas = set(vas)
    
    resp = {'variants':[]}
    for va in vas:
        resp['variants'].append({'variant_name': va})
    return HttpResponse(simplejson.dumps(resp))
