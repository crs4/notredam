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

#from dam.scripts.models import Pipeline
from dam.mprocessor.models import Pipeline, Process
from dam.repository.models import Item, Component, Watermark, new_id, get_storage_file_name
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
#from dam.mprocessor.models import MAction

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


        


def _create_item(user, workspace, res_id, media_type):
    item = Item.objects.create(owner = user, uploader = user,  _id = res_id, type=media_type)    
    item.add_to_uploaded_inbox(workspace)    
    item.workspaces.add(workspace)
    return item

#def _get_media_type(file_name):
#    type = guess_media_type(file_name)
#    media_type = Type.objects.get(name=type)
#    return media_type

def _create_variant(file_name, uri, media_type, item, workspace, variant):
    logger.debug('file_name %s'%file_name)
    logger.debug('uri %s'%uri)
    
    comp = item.create_variant(variant, workspace, media_type)        
    if not item.type:
        item.type = media_type
    if variant.auto_generated:
        comp.imported = True
        
    comp.file_name = file_name
    comp.uri = uri        
    #mime_type = mimetypes.guess_type(file_name)[0]
    #ext = mime_type.split('/')[1]
    comp.format = media_type.ext   # bad bad
    comp.save()    
    return comp

def _get_filepath(file_name):
    fname, ext = os.path.splitext(file_name)
    res_id = new_id() + ext
    fpath = os.path.join(settings.MEDIADART_STORAGE, res_id)
    
    return fpath, res_id

def _upload_loop(filenames, trigger, variant_name, user, workspace, split_file=False):
    """
       Parameters:
       <filenames> is a list of tuples (filename, original_filename, res_id).
       <trigger> is a string, like 'upload'
       <variant_name> is the name of a registered variant
       <user> and <workspace> are two objects as usual.
       <split_file> = True means the names in filenames have the structure:
          <res_id>_<original_file_name>

       Creates a new item for each filename;
       Create a component with variant = variant_name;
       Find all the pipelines associated to the trigger;
       Associates each item to all pipelines thata accept that type of item;
       Launches all pipenes;
       Returns the list of process_id launched;
    """
    pipes = Pipeline.objects.filter(triggers__name=trigger)
    for pipe in pipes:
        pipe.__process = False
    for filename in filenames:
        if split_file:
            tmp = filename.split('_')
            res_id = l[0]
            original_filename = '_'.join(tmp[1:])
        else:
            res_id = new_id()
            original_filename = filename
        variant = Variant.objects.get(name = variant_name)
        fpath, ext = os.path.splitext(filename)
        res_id = new_id()
        media_type = Type.objects.get_or_create_by_filename(filename)
        item = _create_item(user, workspace, res_id, media_type)
        found = 0
        for pipe in pipes:
            if pipe.is_compatible(media_type):
                if not pipe.__process:
                    pipe.__process = Process.objects.create(pipeline=pipe, 
                                                            workspace=workspace, 
                                                            launched_by=user)
                pipe.__process.add_params(item.pk)
                found = 1
                log.debug('item %s added to %s' % (item.pk, pipe.name))
        if not found:
            logger.debug( ">>>>>>>>>> No action for %s" % filename)
        final_file_name = get_storage_file_name(res_id, workspace.pk, variant.name, ext)
        final_path = os.path.join(settings.MEDIADART_STORAGE, final_file_name)
        _create_variant(original_file_name, final_file_name, media_type, item, workspace, variant)
        shutil.copyfile(filename, final_path)
    ret = []
    for pipe in pipes:
        if pipe.__process:
            print 'Launching process %s-%s' % (str(pipe.__process.pk), pipe.name)
            pipe.__process.run()
            ret.append(pipe.__process.pk)
    return ret


def import_dir(dir_name, user, workspace, session):
    logger.debug('########### INSIDE import_dir')
    files =os.listdir(dir_name)
    ret = _upload_loop(files, 'upload', 'original', user, workspace, True)
    logger.debug('Launched %s' % ' '.join(ret))


def _upload_item(file_name, file_raw,  variant, user, session, workspace, session_finished = False):
    if not isinstance(file_name, unicode):
            file_name = unicode(file_name, 'utf-8')        
    tmp_dir = '/tmp/'+ session
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
        
    #~ if file_counter == 1:
        #~ if os.path.exists(tmp_dir):
            #~ os.rmdir(tmp_dir)
        #~ 
        #~ os.mkdir(tmp_dir)
        
    logger.debug('tmp_dir %s'%tmp_dir)	
    file_name = new_id() + '_' + file_name
    file = open(os.path.join(tmp_dir, file_name), 'wb')
    file.write(file_raw)
    file.close() 
    if session_finished:  
        import_dir(tmp_dir, user, workspace, session)
        os.rmdir(tmp_dir)	

@login_required
def upload_item(request):

    """
    Used for uploading a new item. Save the uploaded file using the custom handler dam.upload.uploadhandler.StorageHandler
    """
    
    try:  
        workspace = request.session['workspace']
        variant_name = request.GET['variant']
        variant = Variant.objects.get(name = variant_name)
        session = request.GET['session']
        file_counter = int(request.GET['counter'])
        total = int(request.GET['total'])
        user = request.user  
        file_name = request.META['HTTP_X_FILE_NAME']
        _upload_item(file_name,request.raw_post_data, variant, request.user, session, workspace)        
        resp = simplejson.dumps({'success': True})
        
    except Exception, ex:
        logger.exception(ex)
        raise ex        
    
    return HttpResponse(resp)

def _upload_variant(item, variant, workspace, user, file_name, file_raw):   
    #TODO: refresh url in gui, otherwise old variant will be shown
    if not isinstance(file_name, unicode):
        file_name = unicode(file_name, 'utf-8')
        
    ext = os.path.splitext(file_name)[1]
    res_id = item.ID
    
    final_file_name = get_storage_file_name(res_id, workspace.pk, variant.name, ext)
    final_path = os.path.join(settings.MEDIADART_STORAGE, final_file_name)
    file = open(final_path, 'wb')
    file.write(file_raw)
    file.close()
    media_type = Type.objects.get_or_create_by_filename(file_name)
     
    _create_variant(file_name, final_file_name,media_type, item, workspace, variant)    
    uploaders = []
    if variant.name == 'original':
        triggers_name = 'upload'
    else:
        triggers_name = 'upload_variant'
    
    for p in Pipeline.objects.filter(triggers__name=triggers_name):
        logger.debug('Using pipeline %s' % p.name)        
        uploader = Process.objects.create(pipeline=p, workspace=workspace, launched_by=user)
                
        if uploader.is_compatible(media_type):            
            uploader.add_params(item.pk)        
            logger.debug('running pipeline')
            uploader.run()

@login_required
def upload_variant(request):  
    workspace = request.session['workspace']
    variant_name = request.GET['variant']
    logger.debug('--- variant_name %s'%variant_name)
    
    variant = Variant.objects.get(name = variant_name)
    item_id = request.GET.get('item')        
    user = request.user  
    item = Item.objects.get(pk = item_id)
    file_name = request.META['HTTP_X_FILE_NAME']
    _upload_variant(item, variant, workspace, request.user, file_name, request.raw_post_data)

    
    
#    upload_process = new_processor('upload', user, workspace)
#    upload_process.add_params(item.pk)
#    upload_process.run()
    
    resp = simplejson.dumps({'success': True})        
   
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

def upload_session_finished(request):
    session = request.POST['session']
    workspace = request.session.get('workspace')
    user = User.objects.get(pk = request.session['_auth_user_id'])
    
    tmp_dir = '/tmp/'+ session
    logger.debug('tmp_dir %s'%tmp_dir)
    
    if os.path.exists(tmp_dir):
        import_dir(tmp_dir, user, workspace, session)
        os.rmdir(tmp_dir)
        return HttpResponse(simplejson.dumps({'success': True}))
    else:
        return HttpResponse(simplejson.dumps({'success': False}))
    
        
