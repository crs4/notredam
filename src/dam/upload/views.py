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
from django.db import transaction
import shutil, os
from mediadart.storage import new_id
from django.conf import settings

from dam.scripts.models import Script, ScriptExecution, ScriptItemExecution
from dam.repository.models import Item, Component, Watermark
from dam.core.dam_repository.models import Type
from dam.metadata.models import MetadataDescriptorGroup, MetadataDescriptor, MetadataValue, MetadataProperty
from dam.variants.models import Variant
from dam.treeview.models import Node
#from dam.batch_processor.models import MachineState, Machine, Action
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.decorators import permission_required
from dam.upload.models import UploadURL
from dam.upload.uploadhandler import StorageHandler
from dam.eventmanager.models import EventRegistration
from dam.preferences.views import get_metadata_default_language
from dam.mprocessor.models import MAction

from mediadart.storage import Storage

from dam import logger
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
    if not isinstance(upload_file.name, unicode):
        file_name = unicode(upload_file.name, 'utf-8')
    else:
        file_name = upload_file.name

    type = guess_media_type(file_name)
    
    upload_file.rename()
    
    res_id = upload_file.get_res_id()

    return (file_name, type, res_id)


@transaction.commit_manually
def _save_uploaded_component(request, res_id, file_name, variant, item, user, workspace):
    """
    Create component for the given item and generate mediadart tasks. 
    Used only when user uploaded an item's variant
    """
    try:
        logger.debug('############### _save_uploaded_component: %s' % variant.pk)
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
        transaction.commit()
       
        generate_tasks(comp, workspace)
        
#-        if not variant.auto_generated:
#-            for ws in item.workspaces.all():
#-                EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})
        
    except Exception, ex:
        print traceback.print_exc(ex)
        transaction.rollback()
        raise    
    transaction.commit()
    
    
def _save_uploaded_item(request, upload_file, user, workspace):

    variant = Variant.objects.get(name = 'original')

    file_name, type, res_id = _get_uploaded_info(upload_file)
    
    item_ctype = ContentType.objects.get_for_model(Item)

    media_type = Type.objects.get(name=type)
    
    item = Item.objects.create(owner = user, uploader = user,  type = media_type)
    item_id = item.pk
    item.add_to_uploaded_inbox(workspace)

    item.workspaces.add(workspace)

    _save_uploaded_component(request, res_id, file_name, variant, item, user, workspace)
#    EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})
    
def _save_uploaded_variant(request, upload_file, user, workspace):
    variant_id = request.POST['rendition_id']
    item_id = request.POST['item_id']

    variant =  Variant.objects.get(pk = variant_id)
    logger.debug('***************************************VARIANT %s******************'%variant)
    item = Item.objects.get(pk = item_id)
    
    file_name, type, res_id = _get_uploaded_info(upload_file)
                
    _save_uploaded_component(request, res_id, file_name, variant, item, user, workspace)

def add_resource(file_path, user, workspace, variant, item, script_session):
    path, file_name = os.path.split(file_path)    
    mime_type = mimetypes.guess_type(file_name)[0]        
    ext = mime_type.split('/')[1]
    
    type = guess_media_type(file_name)    
    res_id = new_id()
    new_name = res_id + '.' + ext
    new_file_path = os.path.join(settings.MEDIADART_STORAGE, new_name)  
    shutil.copy(file_path, new_file_path)    
    
    if not item:
        media_type = Type.objects.get(name=type)    
        item = Item.objects.create(owner = user, uploader = user,  type = media_type)
        item_id = item.pk
        item.add_to_uploaded_inbox(workspace)
        item.workspaces.add(workspace)
    
    comp = item.create_variant(variant, workspace)
    
    if variant.auto_generated:
        comp.imported = True

    logger.debug('comp._id %s'%comp._id)
    logger.debug('res_id %s'%res_id)
    comp.file_name = file_name
    comp._id = res_id
    
    comp.format = ext
    comp.save()
    launch_upload_script(user, item, script_session)

def launch_upload_script(user, item, script_session):
    try:
        script = Script.objects.get(pk = 1)
        script_execution, created = ScriptExecution.objects.get_or_create(script = script, session = script_session, launched_by = user)
        ScriptItemExecution.objects.create(script = script_execution, item = item)
    except Exception, ex:
        logger.exception(ex)
        

@login_required
def upload_resource(request):

    """
    Used for uploading a new item. Save the uploaded file using the custom handler dam.upload.uploadhandler.StorageHandler
    """
    
    try:
        workspace = request.session['workspace']
        variant_name = request.POST['variant']
        session = request.POST['session']
        item_id = request.POST.get('item')
        if item_id:
            item = Item.objects.get(pk = item_id)
        else:
            item = Item.objects.none()
        
        user = request.user        
        
        request.upload_handlers = [StorageHandler()]
        upload_file = request.FILES['Filedata']   
        
        variant = Variant.objects.get(name = variant_name)
        add_resource(upload_file.name, user, workspace, variant, item, script_session)
        
        resp = simplejson.dumps({})
    except Exception, ex:
        logger.exception(ex)
        raise ex
        
    
    return HttpResponse(resp)

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

def upload_watermark(request):
    """
    Used for uploading/replacing the watermark for the given workspace. Save the uploaded file using the custom handler dam.upload.uploadhandler.StorageHandler
    """
       
    request.upload_handlers = [StorageHandler()]
    url = request.POST['unique_url']    
    upload_file = request.FILES['Filedata']

    user, workspace = UploadURL.objects.get_user_ws_from_url(url)

    file_name, type, res_id = _get_uploaded_info(upload_file)

    logger.debug('file_name %s' % file_name)
    logger.debug('res_id %s' % res_id)

    comp= Watermark.objects.create(type = Type.objects.get(name=type), workspace=workspace)

    comp.file_name = file_name
    comp._id = res_id
    comp.save()
    
    resp = simplejson.dumps({'res_id': res_id})
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



def _generate_tasks( component, workspace, force_generation,  check_for_existing, embed_xmp):
    """
    Generates MediaDART tasks
    """
    def _cb_start_upload_events(status_ok, result, userargs):
        logger.debug('_generate_tasks: starting upload events: %s' % result)
        item = component.item
        for ws in item.workspaces.all():
            EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})

    logger.debug('############ _generate_tasks')
    from dam.core.dam_repository.models import Type
    variant = component.variant

    maction = MAction()
    maction.add_component(component)
    
    if variant and not variant.auto_generated:    # The component is a source component
        maction.append_func('extract_features')
        maction.append_func('extract_xmp', component.get_extractor())
        callback = _cb_start_upload_events
    else:                                         # The component is derived from a source component
        if not component.imported:
            maction.append_func('adapt_resource')
        maction.append_func('extract_features')
        
        if embed_xmp:
            maction.append_func('embed_xmp')
                
        if  variant.name == 'mail':
            maction.append_func('send_mail')
        callback = lambda a, b, c: None
    maction.activate(callback)
#    maction.activate(None)
#    callback(None, None,None)
    
def generate_tasks(component, workspace, upload_job_id = None, force_generation = False,  check_for_existing = False, embed_xmp = False):
    
    """
    Generate MediaDART Tasks for the given variant, item and workspace
    """
    logger.debug('generate_tasks')

    if upload_job_id:
        component.imported = True
        component.save()
        
    
    #Action.objects.filter(component=component).delete()

    _generate_tasks(component, workspace, force_generation,  check_for_existing, embed_xmp)
