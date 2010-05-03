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
from django.utils import simplejson

from dam.settings import ROOT_PATH
from dam.variants.models import Variant, ImagePreferences, AudioPreferences, VideoPreferences,  DocPreferences,  VariantAssociation,  ImagePreferencesForm, VideoPreferencesForm, AudioPreferencesForm,  DocPreferencesForm,  SourceVariant,  _create_parameters_json,  Preset
from dam.framework.dam_repository.models import Type
from dam.repository.models import Component
from dam.workspace.models import Workspace
from dam.workspace.decorators import permission_required
from dam.repository.models import Component,  Item
from dam.metadata.views import _get_formatted_descriptors, save_variants_rights, _get_ws_groups
from dam.application.views import get_component_url
from dam.batch_processor.models import Machine

import os
import logger
import os, time

@login_required
@permission_required('admin')
def new_variant(request):
    workspace = request.session['workspace']
    media_type = request.POST['media_type']
    name = request.POST.get('name',  'new variant')
    is_source = request.POST.get('is_source',  False)
    logger.debug('is_source %s'%is_source)
    
    prefs = {'image': ImagePreferences,  'audio': AudioPreferences,  'movie': VideoPreferences}
    v = Variant.objects.create(name = name,  media_type = Type.objects.get(name = media_type),  is_global = False,  auto_generated =  not is_source)
    va = VariantAssociation.objects.create(variant = v,  workspace = workspace,)
    if not is_source:
        va.preferences = preferences = prefs[media_type].objects.create() 
        va.save()
    return HttpResponse(simplejson.dumps({'success': True}))
    

@login_required
@permission_required('admin')
def edit_variant(request):
    workspace = request.session['workspace']
    variant_id = request.POST['variant_id']
    v = Variant.objects.get(pk = variant_id)    
    name = request.POST['name']
    v.name = name
    v.save()
    return HttpResponse(simplejson.dumps({'success': True}))
    
@login_required
@permission_required('admin')
def delete_variant(request):     
	
	variant_id = request.POST['variant_id']
	var =  Variant.objects.get(pk = variant_id )
	if not var.is_global:
		var.delete()	
	else:
		raise Exception('global variant cannot be deleted, sorry')

	return HttpResponse(simplejson.dumps({'success':True}))

def get_variant_media_type(item_id,  variant_name, workspace):
    try:
        item = Item.objects.get(pk = item_id)
        logger.debug('variant_name %s' %variant_name)
        if variant_name == 'original' or variant_name ==  'edited':
            logger.debug('original or edited')
            return item.type.name
        logger.debug('item %s' %item)
        logger.debug('variant name %s' %variant_name)
        
        v = Variant.objects.get(Q(workspace = workspace) | Q(workspace__isnull = True), variant_name = variant_name, media_type = item.type)
        
        logger.debug('item_id %s' %item_id)
        
        logger.debug('workspace%s' %workspace)
        logger.debug('varaiant %s' %v)
        
        vp = v.ImagePreferences_set.all()[0]
        media_type = vp.media_type.name
        return media_type
    except Exception,  ex:
        logger.exception(ex)
        raise ex

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
    
def _create_variant(variant,  item, ws):
    logger.debug('variant %s'%variant)
    logger.debug('item.type %s'%item.type.name)
    logger.debug('ws %s'%ws)
#    if variant_name =='original':
#        variant,  created = Variant.objects.get_or_create(variant_name = 'original')        
#    else:        

#    variant = Variant.objects.get(name = variant_name)
    
    try:
        if variant.shared:
            comp = Component.objects.get(item = item, variant= variant)
            comp.workspace.add(ws)
            comp.workspace.add(*item.workspaces.all())
        else:
            comp = Component.objects.get(item = item, variant= variant,  workspace = ws)
        comp.metadata.all().delete()
        comp.save()
        
    except Component.DoesNotExist:
        logger.debug('variant does not exist yet')
        comp = Component.objects.create(item = item, variant= variant)
        comp.workspace.add(ws)
        if variant.shared:
            comp.workspace.add(*item.workspaces.all())
    
    return comp
    

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

    
    available_sources =  Variant.objects.filter(auto_generated = False,  default_url__isnull = True,  variantassociation__workspace = workspace, media_type__name = media_type)

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
    media_type = request.POST['media_type']
    type = request.POST.get('type',  'generated')
    logger.debug('type %s'%type)
    if media_type == 'video': #sigh
        media_type = 'movie'
        
    vas = VariantAssociation.objects.filter(variant__media_type__name = media_type,  variant__auto_generated =  (type == 'generated'),  workspace = workspace,  variant__default_url__isnull = True, variant__editable = True)
    
    
    resp = {'variants':[]}
    for va in vas:
        variant = va.variant
#        prefs = va.preferences.get_form()
#        resp['variants'].append({'pk':variant.pk,  'name': variant.name,  'prefs': prefs})
        resp['variants'].append({'pk':variant.pk,  'name': variant.name, 'is_global': variant.is_global })
    return HttpResponse(simplejson.dumps(resp))


@login_required
@permission_required('admin')
def get_variant_prefs(request):
    workspace = request.session['workspace']
    variant_id = request.POST.get('variant_id')
    form_classes = {'image':ImagePreferencesForm,  'doc': DocPreferencesForm,  'movie': VideoPreferencesForm,  'audio': AudioPreferencesForm}
    if variant_id:
        va = VariantAssociation.objects.get(variant__pk = variant_id,  workspace = workspace)
    #    resp = {'success': True,  'data': prefs}
        
        form_class = form_classes[va.preferences.media_type.name]        
            
        prefs = {'success': True,  'data': form_class(va.preferences).get_form()}
    else:
        media_type = request.POST['media_type']
        form_class = form_classes[media_type]
        prefs = {'success': True,  'data': form_class().get_form()}
    logger.debug('form_class %s'%form_class)
    logger.debug(form_class)
    resp = simplejson.dumps(prefs)
    return HttpResponse(resp)


@login_required
@permission_required('admin')
def save_prefs(request):
    from upload.views import generate_tasks

    try:
        workspace = request.session['workspace']
        variant_id = request.POST.get('variant')
        is_source = request.POST.get('is_source',  False)
        rights_change = request.POST.get('rights_type_id',  False)

        
        resp = {'success': True}
        if variant_id:    
            variant = Variant.objects.get(pk = variant_id)
            media_type = variant.media_type.name
            va = VariantAssociation.objects.get(variant__pk = variant_id,  workspace = workspace)
        else:
            media_type = request.POST['media_type']
            name = request.POST['name']
            
            
            
            
            logger.debug('is_source %s'%is_source)
            prefs = {'image': ImagePreferences,  'audio': AudioPreferences,  'movie': VideoPreferences,  'doc': DocPreferences}
            variant = Variant.objects.create(name = name,  media_type = Type.objects.get(name = media_type),  is_global = False,  auto_generated =  not is_source)
            
            resp['pk'] = variant.pk
            preset = request.POST.get('preset')
            if preset:
                prefs = prefs[media_type].objects.create(preset = Preset.objects.get(pk = preset)) 
            else:
                prefs = prefs[media_type].objects.create() 
            va = VariantAssociation.objects.create(variant = variant,  workspace = workspace, preferences = prefs)
            if not is_source:
                sources = Variant.objects.filter(is_global = True,  auto_generated = False,  default_url__isnull = True,  media_type__name = media_type)
                for source in sources:
                    SourceVariant.objects.create(workspace = workspace,  destination = variant,  rank = source.default_rank,  source = source)    
            
        if not is_source:
            prefs = va.preferences
            prefs.save_func(request.POST)


            sources = request.POST['sources']
            sources = simplejson.loads(sources)
            
            logger.debug("SourceVariant.objects.filter(destination = variant,workspace= workspace).exclude(source__name = 'original',  source__is_global = True) %s"%SourceVariant.objects.filter(destination = variant,workspace= workspace).exclude(source__name = 'original',  source__is_global = True) )
            SourceVariant.objects.filter(destination = variant,workspace= workspace).exclude(source__name = 'original',  source__is_global = True).delete()
            for source in sources:
                logger.debug('source["pk"] %s'%source["pk"])
                source_variant = Variant.objects.get(pk = source['pk'])
                if not source_variant.is_original():
                    SourceVariant.objects.create(destination = variant,  source =  source_variant,  workspace= workspace,  rank = source['rank'])
                else:
                    orig = SourceVariant.objects.get(destination = variant,  source =  source_variant,  workspace= workspace)
                    orig.rank = source['rank']
                    orig.save()
            
            
            logger.debug('now lets generate tasks!')
            for item in workspace.items.filter(type = media_type):
                generate_tasks(variant, workspace,  item)
                if rights_change:
                    save_variants_rights(item, workspace, variant)
        
    except Exception, ex:
        logger.exception(ex)
        raise ex
    
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_variants(request):
    
    workspace = request.session['workspace']
    item_id = request.POST.get('items')
    logger.debug('item_id %s'%item_id)
    item = Item.objects.get(pk = item_id)
    logger.debug('before comps')
    user = User.objects.get(pk=request.session['_auth_user_id'])
    
    item_variants = Variant.objects.filter(variantassociation__workspace = workspace,  media_type = item.type,  default_url__isnull = True).distinct()

    print item_variants

    now = time.time()
    resp = {'variants':[]}
    for v in item_variants:
                
        try:
            comp = Component.objects.get(item = item,  workspace = workspace,  variant = v)
            work_in_progress = Machine.objects.filter(current_state__action__component = comp).count() > 0
            resource_url = "/redirect_to_component/%s/%s/?t=%s"% (item_id,  v.name,  now)
            info_list = []
            if comp.media_type.name== 'image':
                extension = comp.format
            else:
                if comp.format in ['flv',  'mp3',  'mp4',  'mpeg',  'mpg',  'x-flv']:
                    extension = comp.format
                else:
                    extension = None
                    
            auto_generated = v.auto_generated
            media_type = comp.media_type.name 
            imported = comp.imported
            
            basic_group = _get_ws_groups(workspace, 'specific_basic')[0]
            full_group = _get_ws_groups(workspace, 'specific_full')[0]
            
            basic_descriptors = comp.get_descriptors(basic_group)
            full_descriptors = comp.get_descriptors(full_group)
            
            info_list = _get_formatted_descriptors(basic_descriptors,  user, workspace)
            info_list_full = _get_formatted_descriptors(full_descriptors,  user, workspace)
            
#            info_list.append({'caption': 'File Size', 'value': '%s' % comp.format_filesize()})
        except Exception,  ex:
            #logger.exception(ex)
            pk = None
            prefs = v.variantassociation_set.get(workspace = workspace).preferences
            if prefs:
                media_type = prefs.media_type.name
            else:
                media_type = item.type.name
            imported = False
            work_in_progress = False
            info_list = []
            info_list_full = []
            resource_url = ''
            auto_generated = v.auto_generated
            extension = None
            
        resp['variants'].append({'data_basic': info_list, 'data_full':info_list_full,  'variant_name': v.name,  'resource_url': resource_url,  'pk': v.pk,  'imported':imported, 'item_id': item_id,  'auto_generated':auto_generated,  'media_type': media_type,  'extension':extension,  'work_in_progress':work_in_progress,  'width': str(comp.width),  'height': str(comp.height )})
    
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
                variant = Variant.objects.create(name = v['name'],  is_global = False,  auto_generated = False,  media_type = Type.objects.get(name= media_type),  default_url = None)
                VariantAssociation.objects.create(variant= variant,  workspace = workspace)
                existing_variant_ids.append(variant.pk)
                
        variant_to_delete = Variant.objects.filter(is_global = False,  auto_generated = False,  default_url = None,  variantassociation__workspace = workspace).exclude(pk__in = existing_variant_ids)
        variant_to_delete.delete()
        
    except Exception,  ex:
        logger.exception(ex)
        raise ex
    return HttpResponse(simplejson.dumps(resp))



def get_preset_parameters(request):
    workspace = request.session['workspace']
    variant_id = request.POST.get('variant_id')
    preset_id = request.POST['preset_id']
    preset = Preset.objects.get(pk = preset_id)
    params = preset.parameters.all()
    
    if variant_id:
        variant = Variant.objects.get(pk = variant_id)
        prefs = VariantAssociation.objects.get(variant = variant,  workspace = workspace).preferences
        variant_resizable = variant.resizable
    else:
        prefs= None
        variant_resizable = True

    parameters = _create_parameters_json(params, prefs,  variant_resizable)
    return HttpResponse(simplejson.dumps(parameters))
    
    
