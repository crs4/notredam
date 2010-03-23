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
from django.http import HttpResponse,  HttpResponseServerError
from django.utils import simplejson
from django.views.generic.simple import redirect_to
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from dam.settings import MEDIADART_CONF
from dam.repository.models import Item, Component,  _new_md_id
from dam.metadata.views import  get_metadata_default_language, save_descriptor_values, save_variants_rights
from dam.metadata.models import MetadataDescriptorGroup, MetadataDescriptor, MetadataValue, MetadataProperty
from dam.variants.models import Variant,  ImagePreferences as VariantsPreference,  VariantAssociation
from dam.treeview.models import Node
from dam.treeview.views import _add_node
from dam.batch_processor.models import MDTask, MachineState, Machine, Action

from dam.workspace.models import Workspace
from dam.workspace.decorators import permission_required
from dam.application.views import get_component_url
from dam.application.models import Type
from dam.variants.views import _create_variant
import logger

import mimetypes
import os.path, traceback
import time

def _uploaded_item(item,  workspace):
    uploaded = Node.objects.get(depth = 1,  label = 'Uploaded',  type = 'inbox',  workspace = workspace)
    time_uploaded = time.strftime("%Y-%m-%d", time.gmtime())
    node = Node.objects.get_or_create(label = time_uploaded,  type = 'inbox',  parent = uploaded,  workspace = workspace,  depth = 2)[0]
    node.items.add(item)

def adobe_air_upload(request):

    from mediadart.storage import Storage

    workspace = Workspace.objects.all()[0]

    print workspace

    file_name = request.POST['file_name']
    user = User.objects.all()[0]
    type = guess_media_type(file_name)

    storage = Storage('/tmp/prova/')
    res_id = storage.add('/tmp/prova/imports/'+file_name)
    
    new_keywords = False

    item_ctype = ContentType.objects.get_for_model(Item)
    
    item = Item.objects.create(uploader = user,  type = type)
    item_id = item.pk
    _uploaded_item(item,  workspace) 

    item.workspaces.add(workspace)
        
    variant = Variant.objects.get(name = 'original',  media_type__name = item.type)
            
    comp = _create_variant(variant,  item, workspace)
    
    comp.file_name=file_name
    comp._id = res_id
    
    logger.debug('comp._id %s'%comp._id )
    mime_type = mimetypes.guess_type(file_name)[0]
    
    ext = mime_type.split('/')[1]
    comp.format= ext
    comp.save()
    
    logger.debug('mime_type  %s'%mime_type )
    
    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    metadata_mimetype = MetadataValue.objects.get_or_create(schema=metadataschema_mimetype, object_id=item.ID, content_type=item_ctype, value=mime_type)
    orig=MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=comp,  value=mime_type)
    try:
        generate_tasks(variant, workspace, item)
    except Exception, ex:
        traceback.print_exc(ex)
        raise
#    resp = simplejson.dumps({'new_keywords':new_keywords})
    resp = simplejson.dumps({})
    return HttpResponse(resp)


@login_required
@permission_required('add_item')
def upload_finished(request):

    """
    Create item, components and save metadata after upload and generate MediaDART tasks for the new uploaded item
    """
    workspace = request.session.get('workspace')
    variant_id = request.POST.get('variant_id',  None)
    item_id = request.POST.get('item_id')
    file_name = request.POST['file_name']
    job_id = request.POST['job_id']
    user = User.objects.get(pk = request.session['_auth_user_id'])
    type = request.POST['type']
    
    new_keywords = False

    item_ctype = ContentType.objects.get_for_model(Item)
    
    if not item_id:
        item = Item.objects.create(uploader = user,  type = type)
        item_id = item.pk
        _uploaded_item(item,  workspace) 
        
        
        metadata_list = {}

        for key in request.POST.keys():
            if key.startswith('metadata'):
                value = request.POST[key]   
                metadata_id = key.split('_')[-1]
                logger.debug('metadata_id %s'%metadata_id )
                descriptor = MetadataDescriptor.objects.get(pk = metadata_id)
                default_language = get_metadata_default_language(user)
                save_descriptor_values(descriptor, item, value, workspace, 'original', default_language)

        item.workspaces.add(workspace)

        uploaded_by_schema = MetadataProperty.objects.filter(uploaded_by=True)
        for s in uploaded_by_schema:
            m_value = MetadataValue.objects.get_or_create(schema=s, object_id=item.ID, content_type=item_ctype)
            m_value[0].value = item.uploader.username
            m_value[0].save()
    
        uploaded_on = MetadataProperty.objects.filter(creation_date=True)
        for s in uploaded_on:
            m_value = MetadataValue.objects.get_or_create(schema=s, object_id=item.ID, content_type=item_ctype)
            m_value[0].value = str(item.creation_time)
            m_value[0].save()
    
        file_name_schema = MetadataProperty.objects.filter(file_name_target=True)
        for s in file_name_schema:
            m_value = MetadataValue.objects.get_or_create(schema=s, object_id=item.ID, content_type=item_ctype)
            m_value[0].value = file_name
            m_value[0].save()
            
        owner = MetadataProperty.objects.filter(item_owner_target=True)
        for s in owner:
            m_value = MetadataValue.objects.get_or_create(schema=s, object_id=item.ID, content_type=item_ctype)
            my_ws = item.workspaces.all()[0]
            if my_ws.creator:
                creator = my_ws.creator.username
            else:
                my_ws.members.all()[0]
                creator = my_ws.members.all()[0].username
    
            m_value[0].value = creator
            m_value[0].save()
    
    else:            
        item = Item.objects.get(pk = item_id)
        
    if not variant_id:
        variant = Variant.objects.get(name = 'original',  media_type__name = item.type)
    else:
        variant =  Variant.objects.get(pk  = variant_id)     
            
    comp = _create_variant(variant,  item, workspace)
    
    comp.file_name=file_name
    comp._id = request.POST['res_id']
    
    logger.debug('comp._id %s'%comp._id )
    mime_type = mimetypes.guess_type(file_name)[0]
    
    ext = mime_type.split('/')[1]
    comp.format= ext
    comp.save()
    
    logger.debug('mime_type  %s'%mime_type )
    
    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    metadata_mimetype = MetadataValue.objects.get_or_create(schema=metadataschema_mimetype, object_id=item.ID, content_type=item_ctype, value=mime_type)
    orig=MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=comp,  value=mime_type)
    
    generate_tasks(variant, workspace, item,   upload_job_id=job_id, )
#    resp = simplejson.dumps({'new_keywords':new_keywords})
    resp = simplejson.dumps({})
    return HttpResponse(resp)

def _get_upload_url(res_id,  fsize, ext):
    """
    Get a MediaDART upload url
    """

    from mediadart import toolkit

    t = toolkit.Toolkit(MEDIADART_CONF)
    s = t.get_storage()
    
    logger.debug('fsize %s'%fsize) 
    logger.debug('ext %s'%ext) 
    up_resp = s.get_upload_url(res_id, False, fsize, ext)
    if up_resp:
        resp = up_resp
        resp['res_id'] = res_id
        resp.pop('service_load')
        resp.pop('id')

        
        job_id = resp['job_id']
        return (resp,  job_id)
        
    else:
        raise Exception

@login_required
@permission_required('add_item')
def get_upload_url(request):

    """
    Checks if file media type is supported and get a new upload url from MediaDART
    """
    
    try:
        file_name = request.POST['file_name']
        file_size = request.POST['file_size']
        logger.debug('file_name %s'%file_name)
        logger.debug('file_size %s'%file_size)
        
        
        try:
            type = guess_media_type(file_name)
            logger.debug('----type: %s'%type)
        except Exception,  ex:
            return HttpResponseServerError(ex)
       
        logger.debug('type from guess_media_type %s'%type)
        sname, ext = os.path.splitext(file_name)
        
        res_id = _new_md_id()
        resp,  job_id = _get_upload_url(res_id,  file_size, ext)
        resp['type'] = type
        resp = simplejson.dumps(resp)
        

        logger.debug('resp %s'%resp)
        return HttpResponse(resp)
    except:
        logger.exception(traceback.format_exc())
        raise

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
    It tries to guess the media type of the uploaded file (image, movie or audio)
    """
    
#    mimetypes.init()
    logger.debug('file %s'%file)
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

    logger.debug('media type %s'%media_type)
    return media_type

def  copy_metadata(comp,  comp_source):
    """
    Copies metadata from comp_source to comp
    """
    for metadata in comp_source.metadata.all():
        logger.debug('metadata to cp %s'%metadata )
        MetadataValue.objects.create(schema = metadata.schema, xpath=metadata.xpath, content_object = comp,  value = metadata.value, language=metadata.language)

def create_initial_state(state_def):
    if state_def.get('action'):
        new_action = Action.objects.create(**state_def.get('action'))
        new_state = MachineState.objects.create(name=state_def.get('name'), action=new_action)        
    else:
        new_state = MachineState.objects.create(name=state_def.get('name'))        

    return new_state
    
def _generate_tasks(variant, workspace, item,  component,  register_task,  force_generation,  check_for_existing):
    """
    Generates MediaDART tasks
    """

    from dam.application.models import Type
#    variant_source = workspace.get_source(media_type = Type.objects.get(name = item.type),  item = item)
    logger.debug('VARIANT.pk %s'%variant.pk)
    logger.debug('VARIANT %s'%variant)
    logger.debug('ITEM.pk %s'%item.pk)
    if variant.auto_generated:
        variant_source = variant.get_source(workspace,  item)
        logger.debug('SOURCE VARIANT %s'%variant_source)
        if variant_source:
            source = variant_source.get_component(workspace = workspace,  item = item) 
        else:
            if component.imported:
                source = None
            else:
                logger.debug('impossible to generate variant, no source found')
                return 
        variants_to_generate = [variant]
        feat_extr_orig = metadata_orig =  None

        initial_state = {'name':'fake_state'}
        
    else:
        logger.debug('SOURCE VARIANT %s'%variant)
        source = component
        dests = Variant.objects.filter(destinations__workspace = workspace, destinations__source = variant)
        logger.debug('DESTS %s'%dests)
        variants_to_generate = []
        for dest in dests:
            variant_source = dest.get_source(workspace,  item)
            logger.debug('variant_source %s'%variant_source)
            logger.debug('variant.sources.get(workspace = workspace, destination = dest).rank %s'%variant.sources.get(workspace = workspace, destination = dest).rank)
            logger.debug('variant_source.sources.get(workspace = workspace, destination = dest).rank %s'%variant_source.sources.get(workspace = workspace, destination = dest).rank)
            
            # if source has been re-imported, do not add imported components to variants_to_generate
            
            try:
                comp = dest.get_component(item = item,  workspace= workspace)
                if comp.imported:
                    continue
            except:
                pass

            if variant_source == None or (variant.sources.get(workspace = workspace, destination = dest).rank  <= variant_source.sources.get(workspace = workspace, destination = dest).rank):
                variants_to_generate.append(dest)
        logger.debug('REGISTER TASK %s'%register_task)

        feat_extr_action = {'component':source, 'function':'extract_features'}
        feat_extr_orig = {'name':'source_fe', 'action':feat_extr_action}
                
        initial_state = feat_extr_orig
        
#        feat_extr_orig = MDTask.objects.create(component = source, task_type='feature_extraction', wait_for=register_task)
#        metadata_orig = MDTask.objects.create(component = source, task_type='extract_metadata', wait_for=feat_extr_orig)    
#         if source.variant.name == 'thumbnail':
#             save_thumb = MDTask.objects.create(component=source, task_type="save_thumb", wait_for=register_task)
        
    logger.debug('component %s'%component )    
    logger.debug('variants_to_generate  %s'%variants_to_generate )
    
#    feat_extr_orig = MDTask.objects.create(component = source, task_type='feature_extraction', wait_for=register_task)    
#    metadata_orig = MDTask.objects.create(component = source, task_type='extract_metadata', wait_for=feat_extr_orig)    


    ms_mimetype=MetadataProperty.objects.get(namespace__prefix='dc',field_name="format")
    for v in variants_to_generate:       
        logger.debug('v = %s'%v)       
        logger.debug('ws %s'%workspace)
        variant_association = VariantAssociation.objects.get(workspace = workspace,  variant = v) 
        
        logger.debug('variant association %s'%(variant_association.pk))
        vp = variant_association.preferences    
        try:
            comp = v.get_component(item = item,  workspace= workspace)
            logger.debug('comp %s'%comp)
            if comp.imported:

                end = MachineState.objects.create(name='finished')
                save_rights_action = Action.objects.create(component=comp, function='save_rights')
                save_rights_state = MachineState.objects.create(name='comp_save_rights', action=save_rights_action, next_state=end)
                fe_action = Action.objects.create(component=comp, function='extract_features')
                fe_state = MachineState.objects.create(name='comp_fe', action=fe_action, next_state=save_rights_state)
                
                my_cs = create_initial_state(initial_state)
                my_cs.next_state = fe_state
                my_cs.save()
                
                Machine.objects.create(current_state=my_cs, initial_state=my_cs)

#                feat_extr_task = MDTask.objects.create(component=comp, task_type="feature_extraction", wait_for=register_task)
#                extract_metadata = MDTask.objects.create(component=comp, task_type="extract_metadata", wait_for=feat_extr_task)
#                rights = MDTask.objects.create(component=comp, task_type="set_rights", wait_for=extract_metadata)
        
#                 if comp.variant.name == 'thumbnail':
#                     save_thumb = MDTask.objects.create(component=comp, task_type="save_thumb", wait_for=register_task)
                
                continue
                
            if not force_generation:
                logger.debug('NOT FORCE GENERATION!!!!!!!!!')
            
#                Just checking if same variants already exist
            
                logger.debug('comp.source_id %s'%comp.source_id)
                logger.debug('source._id %s'%source._id)
                if comp.preferences and comp.preferences == vp and comp.source_id == source._id:
    #            variant already exists
                    logger.debug('variant already exists!!!!!!!!!!!!!!!!!!!!!!!!!')
                    comp.save()
                    continue
        
    #    Searching for some variant in others ws
                
                found_same_prefs = False
                if v.is_global:
                    for item_ws in item.workspaces.exclude(pk = workspace.pk):
                        
                        ws_prefs = v.variantassociation_set.get(workspace = item_ws ).preferences                    
    #                        
                        ws_comp = Component.objects.get(variant = v,  workspace = item_ws,  item = item)
                        
    #                    if comp.preferences and comp.preferences == ws_prefs and source._id == ws_comp.source_id:
                        
                        if vp  == ws_prefs and source._id == ws_comp.source_id:
        #            variant already exists
                            logger.debug('variant found in a other ws!!!')
                            logger.debug('item_ws %s'%item_ws)
                            logger.debug('ws_comp._id %s'%ws_comp._id)
                            
                            
                            comp._id = ws_comp._id
                            copy_metadata(comp,  ws_comp)
                            comp.format = ws_comp.format
                            comp.save()
                            found_same_prefs = True
                            break
                if found_same_prefs:
                    comp.save()
                    continue
        
                
                elif (comp.imported or comp.uri) :
                    comp.save()
                    continue
                    
                else:
                    comp.new_md_id()
                    comp.metadata.all().delete()
                    comp.save()

            
            else:
                logger.debug('forcing generation')
                comp.new_md_id()
                
#                    TODO: cancellare solo quelli che verranno ri estratti
                comp.metadata.all().delete()
#                save_variants_rights(comp, item, workspace, v)
                comp.save()
    
        except Component.DoesNotExist, ex:
            logger.debug('+++++++++++++++++++++++++++++++++++--------------------------------------------------------------------------creating variant %s %d'%(v, v.pk))
            comp = _create_variant(v,  item, workspace)
            #comp = Component.objects.create(item = item,  variant =v)
            #comp.workspace.add(workspace)
            #            save_variants_rights(comp, item, workspace, v)
        
        type= vp.mime_type.name
        if type =='image' or type =='doc':
            ext=vp.codec
        elif type  =='movie':
            type = 'video'
            
            ext=vp.preset.extension
        elif type  =='audio':
            ext=vp.preset.extension
        
        comp.format = ext
        comp.save()
        
        mime_type=type+'/'+ext        
        MetadataValue.objects.create(schema=ms_mimetype, content_object = comp, value=mime_type)
        
        if vp.media_type.name == 'image' and v.media_type == 'image' and vp.cropping and feat_extr_orig:
            previous_task = feat_extr_orig
            logger.debug('cropping!')
        else:
            previous_task = register_task

        end = MachineState.objects.create(name='finished')

        save_rights_action = Action.objects.create(component=comp, function='save_rights')
        save_rights_state = MachineState.objects.create(name='comp_save_rights', action=save_rights_action, next_state=end)

        fe_action = Action.objects.create(component=comp, function='extract_features')
        fe_state = MachineState.objects.create(name='comp_fe', action=fe_action, next_state=save_rights_state)

        adapt_action = Action.objects.create(component=comp, function='adapt_resource')
        adapt_state = MachineState.objects.create(name='comp_adapt', action=adapt_action, next_state=fe_state)

        my_cs = create_initial_state(initial_state)
        my_cs.next_state = adapt_state
        my_cs.save()
        
        Machine.objects.create(current_state=my_cs, initial_state=my_cs)
 
#        variant_task = MDTask.objects.create(component=comp, task_type="adaptation", wait_for=previous_task)
#        feat_extr_task = MDTask.objects.create(component=comp, task_type="feature_extraction", wait_for=variant_task)
#        extract_metadata = MDTask.objects.create(component=comp, task_type="extract_metadata", wait_for=feat_extr_task)
#        rights = MDTask.objects.create(component=comp, task_type="set_rights", wait_for=extract_metadata)

        logger.debug('added tast adapt, fe')

#         if comp.variant.name == 'thumbnail':
#             save_thumb = MDTask.objects.create(component=comp, task_type="save_thumb", wait_for=variant_task)
        
        comp.preferences = vp.copy()
        comp.source_id = source._id
        comp.save()
            
def generate_tasks(variant, workspace, item,  upload_job_id = None, url = None,  force_generation = False,  check_for_existing = False):
    
    """
    Generate MediaDART Tasks for the given variant, item and workspace
    """
    
    try:
        component = variant.get_component(workspace,  item)    
        
    except Component.DoesNotExist:
        logger.debug('Component.DoesNotExist')
        component = Component.objects.create(variant = variant,  item = item)
        component.workspace.add(workspace)
    
    logger.debug('component._id %s'%component._id)
    
    logger.debug('upload_job_id %s'%upload_job_id)
    
    if upload_job_id:
        component.imported = True
        component.save()
        register_task = MDTask.objects.create(component=component, task_type='wait_for_upload', job_id=upload_job_id)  
    elif url:
        s = storage.Storage()
        local_dir = s.get_local_data_directory()
        filepath = url
        component.uri = url
        component.save()
        register_task = MDTask.objects.create(component=component, task_type='register', filepath=filepath)
    else:
        register_task = None       
      
    
    if variant.shared and not variant.auto_generated and not check_for_existing: #the original... is shared by all the ws
        wss = item.workspaces.all()
    else:
        wss = [workspace]
        
    logger.debug('wss %s'%wss)
    
    for ws in wss:
        _generate_tasks(variant, ws, item,  component,  register_task,  force_generation,  check_for_existing)            
