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
from dam.framework.dam_repository.models import Type
from dam.metadata.views import get_metadata_default_language, save_descriptor_values, save_variants_rights
from dam.metadata.models import MetadataDescriptorGroup, MetadataDescriptor, MetadataValue, MetadataProperty
from dam.variants.models import Variant
from dam.treeview.models import Node
from dam.batch_processor.models import MachineState, Machine, Action

from dam.workspace.models import Workspace
from dam.workspace.decorators import permission_required
from dam.application.views import get_component_url
from dam.variants.views import _create_variant
from dam.upload.models import UploadURL
from dam.upload.uploadhandler import StorageHandler
from eventmanager.models import EventRegistration
from mediadart.storage import Storage

import logger

import mimetypes
import os.path, traceback
import time
import tempfile

def _uploaded_item(item,  workspace):

    uploaded = Node.objects.get(depth = 1,  label = 'Uploaded',  type = 'inbox',  workspace = workspace)
    time_uploaded = time.strftime("%Y-%m-%d", time.gmtime())
    node = Node.objects.get_or_create(label = time_uploaded,  type = 'inbox',  parent = uploaded,  workspace = workspace,  depth = 2)[0]
    node.items.add(item)

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
    
def save_uploaded_component(request, res_id, file_name, variant, item, user, workspace):
    """
    Create component for the given item and generate mediadart tasks. 
    Used only when user uploaded an item's variant
    """
    comp = _create_variant(variant,  item, workspace)
    
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
            save_descriptor_values(descriptor, item, value, workspace, 'original', default_language)

    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    orig=MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=comp,  value=mime_type)

    try:
        generate_tasks(variant, workspace, item, 1)
    except Exception, ex:
        print traceback.print_exc(ex)
        raise    
    
def save_uploaded_item(request, upload_file, user, workspace):

    type = guess_media_type(upload_file.name)
    
    fname, extension = os.path.splitext(upload_file.name)

    upload_file.rename(extension)

    uploaded_fname = upload_file.get_filename()
    path, res_id = os.path.split(uploaded_fname)
    file_name = upload_file.name
    
    item_ctype = ContentType.objects.get_for_model(Item)

    media_type = Type.objects.get(name=type)
    
    item = Item.objects.create(owner = user, uploader = user,  type = media_type)
    item_id = item.pk
    _uploaded_item(item, workspace) 

    item.workspaces.add(workspace)

    variant = Variant.objects.get(name = 'original',  media_type__name = type)
    save_uploaded_component(request, res_id, file_name, variant, item, user, workspace)
    EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})
    

def save_uploaded_variant(request, upload_file, user, workspace):

    variant_id = request.POST['variant_id']
    item_id = request.POST['item_id']

    variant =  Variant.objects.get(pk = variant_id)
    item = Item.objects.get(pk = item_id)
    
    fname, extension = os.path.splitext(upload_file.name)

    upload_file.rename(extension)

    uploaded_fname = upload_file.get_filename()
    path, res_id = os.path.split(uploaded_fname)
    file_name = upload_file.name    
            
    save_uploaded_component(request, res_id, file_name, variant, item, user, workspace)

def get_user_ws_from_url(url):
    """
    Retrieve user and workspace from the unique upload url
    """

    find_url = UploadURL.objects.get(url=url)
    user = find_url.user
    workspace = find_url.workspace

    find_url.delete()

    return (user, workspace)
    
def upload_item(request):

    """
    Used for uploading a new item. Save the uploaded file using the custom handler dam.upload.uploadhandler.StorageHandler
    """

    try:
        request.upload_handlers = [StorageHandler()]
        
        url = request.POST['unique_url']
        upload_file = request.FILES['Filedata']
        
        user, workspace = get_user_ws_from_url(url)
    
        save_uploaded_item(request, upload_file, user, workspace)
    
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
    
    user, workspace = get_user_ws_from_url(url)

    save_uploaded_variant(request, upload_file, user, workspace)        

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
    It tries to guess the media type of the uploaded file (image, movie, audio or doc)
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
        if media_type == 'video':
            media_type = 'movie'
        
#        if media_type == 'application':
#            media_type = 'doc'        
    
        if media_type not in [type.name for type in Type.objects.all()]:
            raise Exception
            
    except Exception, ex:
        media_type = 'media_type sconociuto'
        logger.debug('raise ex')
        raise Exception('unsupported media type')

    return media_type

def  copy_metadata(comp,  comp_source):
    """
    Copies metadata from comp_source to comp
    """
    for metadata in comp_source.metadata.all():
        MetadataValue.objects.create(schema = metadata.schema, xpath=metadata.xpath, content_object = comp,  value = metadata.value, language=metadata.language)



def _generate_tasks(variant, workspace, item,  component, force_generation,  check_for_existing):
    
    """
    Generates MediaDART tasks
    """

    logger.debug('_generate_tasks')
    from dam.framework.dam_repository.models import Type
    
#    variant_source = workspace.get_source(media_type = Type.objects.get(name = item.type),  item = item)
    if variant.auto_generated:
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
               
        try:
            comp = variant.get_component(item = item,  workspace= workspace)
        except Component.DoesNotExist, ex:
            comp = _create_variant(variant,  item, workspace)
            
        end = MachineState.objects.create(name='finished')
#        save_rights_action = Action.objects.create(component=comp, function='save_rights')
#        save_rights_state = MachineState.objects.create(name='comp_save_rights', action=save_rights_action, next_state=end)    
        fe_action = Action.objects.create(component=comp, function='extract_features')
        fe_state = MachineState.objects.create(name='comp_fe', action=fe_action, next_state=end)
        
        if comp.imported:
            logger.debug('----------source_machine %s'%source_machine)             
            Machine.objects.create(current_state=fe_state, initial_state=fe_state, wait_for=source_machine)  
        
        else:
            logger.debug('adaptation task')
            adapt_action = Action.objects.create(component=comp, function='adapt_resource')
            adapt_state = MachineState.objects.create(name='comp_adapt', action=adapt_action, next_state=fe_state)
            
            Machine.objects.create(current_state=adapt_state, initial_state=adapt_state, wait_for=source_machine)        
                
    else:
        source = component
                
        end = MachineState.objects.create(name='finished')
        feat_extr_action = Action.objects.create(component=source, function='extract_features')
        feat_extr_orig = MachineState.objects.create(name='source_fe', action=feat_extr_action, next_state=end)
        
        source_machine = Machine.objects.create(current_state=feat_extr_orig, initial_state=feat_extr_orig)
#        ms_mimetype=MetadataProperty.objects.get(namespace__prefix='dc',field_name="format")

         

            
def generate_tasks(variant, workspace, item, upload_job_id = None, url = None,  force_generation = False,  check_for_existing = False):
    
    """
    Generate MediaDART Tasks for the given variant, item and workspace
    """
    logger.debug('generate_tasks')
    component = variant.get_component(workspace,  item)
#    try:
#        component = variant.get_component(workspace,  item)    
#        
#    except Component.DoesNotExist:
#        component = Component.objects.create(variant = variant,  item = item)
#        component.workspace.add(workspace)
        
    if upload_job_id:
        component.imported = True
        component.save()
        
    
    if variant.shared and not variant.auto_generated and not check_for_existing: #the original... is shared by all the ws
        wss = item.workspaces.all()
    else:
        wss = [workspace]
    
    for ws in wss:
        _generate_tasks(variant, ws, item,  component, force_generation,  check_for_existing)            
