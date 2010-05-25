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

from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from django.views.generic.simple import redirect_to
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from dam.repository.models import Item, Component
from dam.core.dam_repository.models import Type
from dam.metadata.models import MetadataDescriptorGroup, MetadataDescriptor, MetadataValue, MetadataProperty
from dam.variants.models import Variant
from dam.treeview.models import Node
from dam.batch_processor.models import MachineState, Machine, Action
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.decorators import permission_required
from dam.upload.models import UploadURL
from dam.upload.uploadhandler import StorageHandler
from dam.eventmanager.models import EventRegistration
from dam.preferences.views import get_metadata_default_language

from mediadart.storage import Storage

import logger

import mimetypes
import os.path, traceback
import time
import tempfile

def _get_upload_url(user, workspace, number):

    """
    FIX: API NEED FIXING!!
    """

    urls = []

    for i in xrange(int(number)):
        urls.append(UploadURL.objects.create(user=user, workspace=workspace).url)

    return urls

@login_required
def get_upload_url(request):
    """
    Generate unique upload urls (workaround for flash cookie bug)
    """
    n = request.POST['n']

    workspace = request.session.get('workspace')
    user = User.objects.get(pk = request.session['_auth_user_id'])

    urls = _get_upload_url(user, workspace, n)

    resp = simplejson.dumps({'urls': urls})
    return HttpResponse(resp)
    
def _get_uploaded_info(upload_file):

    file_name = upload_file.name

    type = guess_media_type(file_name)
    
    upload_file.rename()
    
    res_id = upload_file.get_res_id()

    return (file_name, type, res_id)

    
def _save_uploaded_component(request, res_id, file_name, variant, item, user, workspace):
    """
    Create component for the given item and generate mediadart tasks. 
    Used only when user uploaded an item's variant
    """
    comp = item.create_variant(variant, workspace)
    
    if variant.auto_generated:
        comp.imported = True

    logger.debug('comp._id %s'%comp._id)
    logger.debug('res_id %s'%res_id)
    comp.file_name = file_name
    comp._id = res_id
    
    mime_type = mimetypes.guess_type(file_name)[0]
        
    ext = mime_type.split('/')[1]
    comp.format = ext
    comp.save()

    default_language = get_metadata_default_language(user)
    
    for key in request.POST.keys():
        if key.startswith('metadata'):
            value = request.POST[key]
            metadata_id = key.split('_')[-1]
            descriptor = MetadataDescriptor.objects.get(pk = metadata_id)
            MetadataValue.objects.save_descriptor_values(descriptor, item, value, workspace, 'original', default_language)

    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    orig=MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=comp,  value=mime_type)

    try:
        generate_tasks(comp)
        
        if not variant.auto_generated:
            for ws in item.workspaces.all():
                EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})
        
    except Exception, ex:
        print traceback.print_exc(ex)
        raise    
    
def _save_uploaded_item(request, upload_file, user, workspace):

    variant = Variant.objects.get(name = 'original')

    file_name, type, res_id = _get_uploaded_info(upload_file)
    
    item_ctype = ContentType.objects.get_for_model(Item)

    media_type = Type.objects.get(name=type)
    
    item = Item.objects.create(owner = user, uploader = user,  type = media_type)
    item_id = item.pk
    item.add_to_uploaded_inbox(workspace)

    item.workspaces.add(workspace)


    variant = Variant.objects.get(name = 'original')
    _save_uploaded_component(request, res_id, file_name, variant, item, user, workspace)
#    EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})
    
def _save_uploaded_variant(request, upload_file, user, workspace):
    variant_id = request.POST['variant_id']
    item_id = request.POST['item_id']

    variant =  Variant.objects.get(pk = variant_id)
    logger.debug('***************************************VARIANT %s******************'%variant)
    item = Item.objects.get(pk = item_id)
    
    file_name, type, res_id = _get_uploaded_info(upload_file)
                
    _save_uploaded_component(request, res_id, file_name, variant, item, user, workspace)
    
def upload_item(request):

    """
    Used for uploading a new item. Save the uploaded file using the custom handler dam.upload.uploadhandler.StorageHandler
    """

    try:
        request.upload_handlers = [StorageHandler()]
        
        url = request.POST['unique_url']
        upload_file = request.FILES['Filedata']
        
        user, workspace = UploadURL.objects.get_user_ws_from_url(url)
    
        _save_uploaded_item(request, upload_file, user, workspace)
    
        resp = simplejson.dumps({})
        return HttpResponse(resp)
    except Exception, ex:
        logger.exception(ex)
        raise ex

def upload_variant(request):
    """
    Used for uploading/replacing an item's variant. Save the uploaded file using the custom handler dam.upload.uploadhandler.StorageHandler
    """

    request.upload_handlers = [StorageHandler()]

    url = request.POST['unique_url']    
    upload_file = request.FILES['Filedata']
    
    user, workspace = UploadURL.objects.get_user_ws_from_url(url)

    _save_uploaded_variant(request, upload_file, user, workspace)        

    resp = simplejson.dumps({})
    return HttpResponse(resp)

@login_required
def get_metadata_upload(request):
    """
    Get metadata schemas for upload 
    """
    user = request.session['_auth_user_id']
    workspace = request.session['workspace']
    metadata = {'schemas': []}
    if workspace.get_permissions(user).filter(Q(codename = 'edit_metadata') | Q(codename = 'admin')).count() > 0:
        group = MetadataDescriptorGroup.objects.get(upload=True)
        
        for ms in group.descriptors.all():
            metadata['schemas'].append({'pk':ms.pk,  'name':ms.name.capitalize()})
    
    resp = simplejson.dumps(metadata)
    return HttpResponse(resp)

def guess_media_type (file):

    """
    It tries to guess the media type of the uploaded file (image, video, audio or doc)
    """
    
#    mimetypes.init()
    mimetypes.add_type('video/flv','.flv')
    mimetypes.add_type('video/ts','.ts')
    mimetypes.add_type('video/mpeg4','.m4v')
    mimetypes.add_type('doc/pdf','.pdf')
    mimetypes.add_type('image/nikon', '.nef')
    mimetypes.add_type('image/canon', '.cr2')
    mimetypes.add_type('image/digitalnegative', '.dng')
    
    media_type = mimetypes.guess_type(file)
    
    try:
        media_type = media_type[0][:media_type[0].find("/")]
        
#        if media_type == 'application':
#            media_type = 'doc'        
    
        if media_type not in [type.name for type in Type.objects.all()]:
            raise Exception
            
    except Exception, ex:
        media_type = 'media_type sconociuto'
        logger.debug('raise ex')
        raise Exception('unsupported media type')

    return media_type

def _generate_tasks( component, force_generation,  check_for_existing):
    
    """
    Generates MediaDART tasks
    """

    logger.debug('_generate_tasks')
    from dam.core.dam_repository.models import Type
    variant = component.variant
#    variant_source = workspace.get_source(media_type = Type.objects.get(name = item.type),  item = item)
    
    if variant and not variant.auto_generated:
     
                
        end = MachineState.objects.create(name='finished')     
            
        feat_extr_action = Action.objects.create(component=component, function='extract_features')
        feat_extr_orig = MachineState.objects.create(name='source_fe', action=feat_extr_action, next_state=end)
        
        source_machine = Machine.objects.create(current_state=feat_extr_orig, initial_state=feat_extr_orig)
    else:
        source = component.source
        if not source:            
            if component.imported:
                source = None
            else:
                logger.debug('impossible to generate variant, no source found')
                return 
        

        end = MachineState.objects.create(name='finished')

                
        feat_extract_orig = MachineState.objects.filter(action__component = source, action__function = 'extract_features')
        logger.debug('feat_extract_orig %s'%feat_extract_orig)
        
        if feat_extract_orig.count(): 
            source_machine = feat_extract_orig[0].machine_set.all()[0]  
        else:
            source_machine = None
        
#        source_machine = None
        logger.debug('source_machine %s'%source_machine)
               
        end = MachineState.objects.create(name='finished')
        logger.debug('----------------- VARIANT %s'%variant)
#        if not variant:
        if  variant.name == 'mail':
            
            send_mail_action = Action.objects.create(component=component, function='send_mail')
            send_mail_state = MachineState.objects.create(name='send_mail', action=send_mail_action, next_state=end) 
            end_state = send_mail_state
        else:
            end_state = end
        
        fe_action = Action.objects.create(component=component, function='extract_features')
        fe_state = MachineState.objects.create(name='comp_fe', action=fe_action, next_state=end_state)
        
        if component.imported:
            logger.debug('----------source_machine %s'%source_machine)             
            Machine.objects.create(current_state=fe_state, initial_state=fe_state, wait_for=source_machine)  
        
        else:
            logger.debug('adaptation task')
            adapt_action = Action.objects.create(component=component, function='adapt_resource')
            adapt_state = MachineState.objects.create(name='comp_adapt', action=adapt_action, next_state=fe_state)
            
            Machine.objects.create(current_state=adapt_state, initial_state=adapt_state, wait_for=source_machine)        
                
  
        
#        ms_mimetype=MetadataProperty.objects.get(namespace__prefix='dc',field_name="format")

def generate_tasks(component, upload_job_id = None, url = None,  force_generation = False,  check_for_existing = False):
    
    """
    Generate MediaDART Tasks for the given variant, item and workspace
    """
    logger.debug('generate_tasks')
#    component = variant.get_component(workspace,  item)
#    try:
#        component = variant.get_component(workspace,  item)    
#        
#    except Component.DoesNotExist:
#        component = Component.objects.create(variant = variant,  item = item)
#        component.workspace.add(workspace)
        
    if upload_job_id:
        component.imported = True
        component.save()
        
    variant = component.variant
#    if variant and  variant.shared and not variant.auto_generated and not check_for_existing: #the original... is shared by all the ws
#        wss = component.item.workspaces.all()
#    else:
#        wss = [workspace]
#    for ws in wss:
#        _generate_tasks( ws,  component, force_generation,  check_for_existing)            

    _generate_tasks(component, force_generation,  check_for_existing)
