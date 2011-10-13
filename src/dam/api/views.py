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

import mimetypes
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse,  Http404
from django.shortcuts import render_to_response
from django.core import serializers

from django.utils import simplejson as json
from django.db.models.query import QuerySet
from django.db.models import Q

from django_restapi.resource import Resource,  HttpMethodNotAllowed
from django_restapi.authentication import *
from django_restapi.responder import *

from django.contrib.auth.models import Permission
from decimal import *

from dam.repository.models import Item,  Component, _get_resource_url, new_id
from dam.core.dam_repository.models import Type
from dam.core.dam_metadata.models import XMPStructure
from dam.workspace.models import DAMWorkspace
from dam.core.dam_workspace.models import WorkspacePermissionAssociation, WorkspacePermission
from dam.workflow.models import State, StateItemAssociation
from dam.treeview.models import Node, NodeMetadataAssociation,  SmartFolder, SmartFolderNodeAssociation
from dam.treeview.models import InvalidNode,  WrongWorkspace,  NotMovableNode,  NotEditableNode
#from dam.variants.models import VariantAssociation,  Variant,  PresetPreferences,  Preset,  SourceVariant, ImagePreferences,  AudioPreferences,  VideoPreferences
from dam.mprocessor.models import Pipeline 
from dam.workspace.views import _add_items_to_ws, _search
from dam.api.models import Secret,  Application
from dam.metadata.models import MetadataValue,  MetadataProperty,  MetadataLanguage
from dam.upload.views import _upload_variant, _upload_resource_via_raw_post_data, _upload_resource_via_post
from dam.workflow.views import _set_state 
from dam.scripts.views import _edit_script, _get_scripts_info
from dam.settings import SERVER_PUBLIC_ADDRESS
from dam.plugins import extract_basic

from dam.api.decorators import *
from dam.api.exceptions import *
from dam.workspace.forms import AdminWorkspaceForm
from dam.variants.views import _edit_variant
#~ from dam.upload.uploadhandler import StorageHandler
from django.contrib.auth import authenticate,  login

#from django.contrib.sessions.backends.db import SessionStore


import logging
logger = logging.getLogger('dam')

import os.path
from mimetypes import guess_type

from django.template.loader import render_to_string
from twisted.test.test_jelly import SimpleJellyTest

def _check_parent(values):
    if  Node.objects.get(pk = values['parent_id']).depth  == 0:
        values['parent_id'] = None
    return values    

class ModResource(Resource):
    """
    This class permits to use post in alternative to http methods 'DELETE' and 'PUT' 
    """
    
    def __init__(self, private = False,   *args,  **kwargs):
        super(ModResource,  self).__init__( *args,  **kwargs)
        #logger.debug('_private %s'%private)
        self.private = private
        
    def get_json_request(self,  request):
        try:
            json_request = json.loads(request.raw_post_data)
            logger.debug('json_request %s'%json_request)
        except Exception,  ex:
            logger.exception(ex) 
            raise MalformedJSON
        return json_request
        
    def dispatch(self, request, target, *args, **kwargs):
        """
        """
        request_method = request.method.upper()
        logger.debug('request_method %s'%request_method)
        logger.debug('self.permitted_methods %s'%self.permitted_methods)
        if request_method not in self.permitted_methods:
            raise HttpMethodNotAllowed
        
        if request_method == 'GET':
            return target.read(request, *args, **kwargs)
        elif request_method == 'POST':
#            return target.create(request, *args, **kwargs)
            return target.update(request, *args, **kwargs)
        elif request_method == 'PUT':
            return target.update(request, *args, **kwargs)
#            load_put_and_files(request)
            return target.update(request, *args, **kwargs)
        elif request_method == 'DELETE':
            return target.delete(request, *args, **kwargs)
        else:
            raise Http404

def _check_app_permissions(ws, user_id,  perm_list):
    """
    ws: a single workspace or a QuerySet of them
    """
    logger.debug('user_id %s'%user_id)
    user = User.objects.get(pk = user_id)
    if isinstance(ws,  QuerySet):
        logger.debug('passed queryset')
        
        raise_error = True
        logger.debug('ws %s'%ws)
        for el in ws:
            
            try:
                _check_app_permissions(el, user_id,  perm_list)
                raise_error = False
                break
            except Exception, ex:
                logger.exception('el: %s. ex: %s'%(el, ex))
                pass
        
        if raise_error:
             if not user.is_superuser:
                logger.exception('no permission')
                raise InsufficientPermissions
            
    else:
        logger.debug('passed ws')
        logger.debug('ws.get_permissions(user) %s'%ws.get_permissions(user))
        if ws.get_permissions(user).filter(codename__in = perm_list).count()  == 0:
            logger.debug('no permission')
            if not user.is_superuser:
                 raise InsufficientPermissions('no permission')
            
def _update_ws(ws, attr_dict):
    form = AdminWorkspaceForm(ws, attr_dict)
    if form.is_valid():
        for attr in attr_dict.keys():
            ws.__dict__[attr] = form.cleaned_data[attr]
    return form
    
def _check_permissions_for_item(user_id,  item, perm_list =  ['admin',  'edit_metadata']):
    user = User.objects.get(pk = user_id)
    wss = item.workspaces.filter(members = user)          
    
    if wss.count() == 0:
         if not user.is_superuser:
             raise InsufficientPermissions            
    logger.debug('checking permissions')        
    _check_app_permissions(wss,  user_id,  perm_list)
    
    
class WorkspaceResource(ModResource):   
    metadata = ['name',  'description',  'creator']    
    
    @exception_handler
    @api_key_required    
    def set_creator(self,  request,  workspace_id = None):
        """ 
        Allows to get informations about all DAM users. This is a private method, only for admin users.
        - Method: POST
            - parameters: 
                - user_id: the id of the new creator
        -returns: empty string
        """
        
        u = User.objects.get(pk = request.POST['user_id'])
        if not u.is_superuser:
            raise InsufficientPermissions
        
        ws = Workspace.objects.get(pk = workspace_id)
        user_id = request.POST.get('creator_id')
        user = User.objects.get(pk = user_id)
        ws.creator = user
        ws.save()
        
        return HttpResponse('')         
    
    @exception_handler
    @api_key_required
    def set_name(self,  request,  workspace_id):
        """
        Allows to edit the name of workspace
        - method POST
            - parameters:
                - name: the new name for the given workspace        
        - returns: empty string
        """
      
        
        if not request.POST.has_key('name') :
            raise MissingArgs
        
        user_id = request.POST.get('user_id')
        ws = Workspace.objects.get(pk = workspace_id)
        
        user = User.objects.get(pk = user_id)        
        _check_app_permissions(ws,  user_id,  ['admin'])
        
        name = request.POST['name']
        form = _update_ws(ws,  {'name': name,})
        if not form.is_valid():
            logger.exception('invalid form:\n %s' %form.errors)            
            raise ArgsValidationError(form.errors  )        
        ws.name = name
        ws.save()
        return HttpResponse('')        
    
    @exception_handler
    @api_key_required
    def set_description(self,  request,  workspace_id):
        """
        Allows to edit the description of the workspace
        - method POST
            - parameters:
                - description: the new description for the given workspace        
        - returns: empty string
        """
        
        
        if not request.POST.has_key('description') :
            raise MissingArgs
            
        user_id = request.POST['user_id']
        user = User.objects.get(pk = user_id)        
        
        ws = Workspace.objects.get(pk = workspace_id)
        
        _check_app_permissions(ws,  user_id,  ['admin'])
        ws.description = request.POST['description']
        ws.save()
        return HttpResponse('')            

    def _get_collections(self, workspace_id):
        ws = Workspace.objects.get(pk = workspace_id)
        
        kws = []
        nodes= Node.objects.filter(type = 'collection',  depth = 1,  workspace = ws)            
        logger.debug('COLLECTIONS %s'%nodes)            

        coll_resource = CollectionResource()
        for node in nodes:
            kws.append(coll_resource.get_info(node))
            
        
        tax = {'collections': kws}
        logger.debug('collections %s'%kws )
        
        return tax
    
    @exception_handler
    @api_key_required
    def get_collections(self,  request,  workspace_id):
        """
        - Method: GET
            - No parameters.
        - Returns:
            information about the workspace collections, for example:{"collections": [{'items': [], 'label': 'test_with_item', 'parent_id': None, 'workspace': 1, 'id': 19, 'children': []}]}
        """
        tax = WorkspaceResource()._get_collections(workspace_id)
        resp = json.dumps(tax)

        return HttpResponse(resp)        
    
    def _get_members(self, workspace_id):
        ws = Workspace.objects.get(pk = workspace_id)
        resp = {'members':[]}
        members = ws.members.all()
        for member in members:
            tmp = {'username': member.username}
            permissions = ws.get_permissions(member)
            tmp['permissions'] = [perm.name for perm in permissions]            
            resp['members'].append(tmp)
            
        return resp
    
    @exception_handler
    @api_key_required
    def get_members(self,  request, workspace_id):
        """
        Allows to get the members of a workspace.
        - method: GET
            - parameters: none
        - returns: a list of members and their permissions, for example: {'members': [{'username': 'test', 'permissions': ['admin']}]})
        """
        
        resp = WorkspaceResource()._get_members(workspace_id)
        resp = json.dumps(resp)
        return HttpResponse(resp)
  

    def _set_permissions(self, ws, users, permissions_list):
        
        for perm_name in permissions_list:
            permission = WorkspacePermission.objects.get(name = perm_name)
            wspa, created = WorkspacePermissionAssociation.objects.get_or_create(permission  = permission, workspace = ws)
            wspa.users.add(*users)
            
    
    @exception_handler
    @api_key_required
    def add_members(self,  request, workspace_id):
        """
        Allows to add members to a given workspace, specifying permissions.
        
        - method: POST
            - params:
                - users: username of the users to add as members
                - permissions: a list of permissions to assign to the new members (for example 'admin', 'add item', 'edit metadata' etc.)
         -returns: empty string         
                
        """
        ws = Workspace.objects.get(pk = workspace_id)
        user_id = request.POST['user_id']
        _check_app_permissions(ws, user_id, ['admin'])
        user_names = request.POST.getlist('users')
        permissions = request.POST.getlist('permissions')        
        
        users = User.objects.filter(username__in = user_names)
        ws.members.add(*users)
        self._set_permissions(ws, users, permissions)
            
        
        return HttpResponse('')


    @exception_handler
    @api_key_required
    def remove_members(self,  request, workspace_id):
        """
        Allows to remove members from a given workspace.
        
        - method: POST
            - params:
                - users: username of the users to remove
         -returns: empty string         
                
        """
    
        ws = Workspace.objects.get(pk = workspace_id)
        user_id = request.POST['user_id']
        _check_app_permissions(ws, user_id, ['admin'])
        user_names = request.POST.getlist('users')        
        
        users = User.objects.filter(username__in = user_names) 
        admins = ws.members.filter(workspacepermissionassociation__workspace = ws, workspacepermissionassociation__permission__name = 'admin')
        admins_to_change = admins.filter(username__in = user_names)
        if admins_to_change.count() > 0:
            if admins.count() == 1:
                raise WorkspaceAdminDeletion
        
        ws.members.remove(*users)
        wspa =  WorkspacePermissionAssociation.objects.filter(users__in = users, workspace = ws).delete()
        
        return HttpResponse('')

    
    
    @exception_handler
    @api_key_required
    def set_permissions(self,  request, workspace_id):
        """
        Allows to set permissions for a list of workspace members.
        
        - method: POST
            - params:
                - users: username of the users
                - permissions: a list of permissions (for example 'admin', 'add item', 'edit metadata' etc.)
                
         -returns: empty string         
                
        """
    
        ws = Workspace.objects.get(pk = workspace_id)
        user_id = request.POST['user_id']
        _check_app_permissions(ws, user_id, ['admin'])
        user_names = request.POST.getlist('users')    
        permissions = request.POST.getlist('permissions')            
        
        users = User.objects.filter(username__in = user_names)
        self._set_permissions(ws, users, permissions)
        
        return HttpResponse('')

    
    def  _get_list(self, wss):
        
        wss_list = []
        
        for ws in wss:
            tmp = {'id':ws.pk,  'name': ws.name,  'description':ws.description,  }
            if  ws.creator:
                tmp['creator'] = ws.creator.username
            else:
                tmp['creator']  = None
            wss_list.append(tmp)
        
        return wss_list
    
    @exception_handler
    @api_key_required
    def get_list(self,  request):
        """
        Allows to get all the workspaces to whom the user is associated.
        - Method: GET
            - No parameters.
        - returns: list of workspaces, for example [{'id':2,  'name': 'test',  'description':'', 'creator': 'test_ws'}] 
        """
                
        user_id = request.GET['user_id']
        user = User.objects.get(pk = user_id)        
        
        if user.is_superuser:
            wss = Workspace.objects.all()
        else:
            wss = user.workspaces.all()

        wss_list = WorkspaceResource()._get_list(wss)    

        logger.debug('wss_list %s'%wss_list)
        resp = json.dumps(wss_list)            
        return HttpResponse(resp)        
        
        
        
    @exception_handler
    @api_key_required
    def get_keywords(self, request,  workspace_id):    
        """
        Allows. to get the keywords of a workspace.
        - Method: GET
            - No parameters.
        - returns:
            - JSON example:{
                                    'keywords':[
                                                    'id':1
                                                    'label':'People'
                                                    parent_id: null                                                    
                                                    ]
                                    }        
        """
        ws = Workspace.objects.get(pk = workspace_id)  

        user_id = request.GET['user_id']
        user = User.objects.get(pk = user_id)   
        if not user.is_superuser:     
            if ws.members.filter(pk = user.pk).count() == 0:
                raise InsufficientPermissions
        
#        kws = list(Node.objects.get(workspace = ws,  depth = 0,  type = 'keyword').get_branch().values('id',  'label',  'parent_id'))
#        
#        kws[0].pop('parent_id')
#        tax = {'keywords': kws}
#        logger.debug('keywords %s'%kws )
                    
#        resp = json.dumps(tax)            
#        return HttpResponse(resp)        
        return KeywordsResource()._read(user, workspace_id)
    
    @exception_handler
    @api_key_required
    def edit(self,  request,  workspace_id):
        """
        Allows to edit the name of workspace
        - method POST
            - parameters:
                - name: the new name for the given workspace  
                - description      
        - returns: empty string
        """
      
        
#        if not request.POST.has_key('name') :
#            raise MissingArgs
        
        user_id = request.POST.get('user_id')
        ws = Workspace.objects.get(pk = workspace_id)
        
        user = User.objects.get(pk = user_id)        
        _check_app_permissions(ws,  user_id,  ['admin'])
        
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name:
            form = _update_ws(ws,  {'name': name,})
            if not form.is_valid():
                logger.exception('invalid form:\n %s' %form.errors)            
                raise ArgsValidationError(form.errors  )        
            ws.name = name
        if description:
            ws.description = description
            
        ws.save()
        return HttpResponse('')        
        
#        TODO: check args everywhere
    
    
    @exception_handler
    @api_key_required   
    def get_items_complete(self,  request,  workspace_id):   
        """
        """ 
        
        items = Item.objects.filter(workspaces__pk = workspace_id)
        workspace = Workspace.objects.get(pk = workspace_id)
        resp = {'items': []}
        variants = request.GET.getlist('variants')
        
        for item in items:
            tmp = {'pk': item.pk}
            component_list = Component.objects.filter(item = item, workspace__pk =workspace_id)
        
            for c in component_list:
                v = c.variant
                if v.name in variants:
#                    if v.name == 'thumbnail':
#                        url = '/files/thumbs/%s.jpg'%item.ID
#                    else:
                    va = v.variantassociation_set.get(workspace__pk = workspace_id)
                    logger.debug('v %s'%v)
                    url = c.get_component_url()
                    tmp[v.name] = url
        
            resp['items'].append(tmp)
        json_resp = json.dumps(resp)
        return HttpResponse(json_resp)
    
    @exception_handler
    @api_key_required
    def set_description(self,  request,  workspace_id):
        """
        Allows to edit the description of the workspace
        - method POST
            - parameters:
                - description: the new description for the given workspace        
        - returns: empty string
        """
        
        
        if not request.POST.has_key('description') :
            raise MissingArgs
            
        user_id = request.POST['user_id']
        user = User.objects.get(pk = user_id)        
        
        ws = Workspace.objects.get(pk = workspace_id)
        
        _check_app_permissions(ws,  user_id,  ['admin'])
        ws.description = request.POST['description']
        ws.save()
        return HttpResponse('')            
        
    @exception_handler
    @api_key_required   
    def get_states(self,  request,  workspace_id):
        workspace = Workspace.objects.get(pk = workspace_id)
        states = State.objects.filter(workspace = workspace)
        resp = {'states':[]}
        for state in states:
            resp['states'].append({'id':state.pk, 'name':state.name}) 
            
        json_resp = json.dumps(resp)        
        return HttpResponse(json_resp)
    
    def _get_variants(self, workspace_id):
        vas = Variant.objects.filter(Q(workspace__pk = workspace_id) |Q (workspace__isnull = True), hidden = False)
        resp = {'renditions':[]}
        workspace = Workspace.objects.get(pk = workspace_id)
        
        
        for va in vas:           
            tmp = VariantsResource().get_info(va,  workspace)
            resp['renditions'].append( tmp)
        
        return resp
    
    @exception_handler
    @api_key_required   
    def get_variants(self,  request,  workspace_id):
        """
        Allows to get informations about the renditions of the workspace.
        - method: GET
            - parameters: none
        - returns: information on renditions for example: {"renditions": [{"caption": "Original", "auto_generated": false, "id": 1, "media_type": ["image", "video", "doc", "audio"], "name": "original"}, {"caption": "edited", "auto_generated": false, "id": 2, "media_type": ["image", "video", "doc", "audio"], "name": "edited"}, {"caption": "Thumbnail", "auto_generated": true, "id": 3, "media_type": ["image", "video", "doc"], "name": "thumbnail"}, {"caption": "Preview", "auto_generated": true, "id": 4, "media_type": ["image", "video", "doc", "audio"], "name": "preview"}, {"caption": "Fullscreen", "auto_generated": true, "id": 5, "media_type": ["image"], "name": "fullscreen"}, {"caption": "mail", "auto_generated": true, "id": 6, "media_type": ["image", "video", "doc", "audio"], "name": "mail"}]}
 
        
        """
        resp = WorkspaceResource()._get_variants(workspace_id)
                
        json_resp = json.dumps(resp)
        logger.debug(json_resp)
        return HttpResponse(json_resp)
        
    def _get_items(self, workspace_id):
        items = Item.objects.filter(workspaces__pk = workspace_id)
        resp = [i.pk for i in items]            
        
        return resp
        
    def _read(self, workspace_id):
        ws = Workspace.objects.get(pk = workspace_id)        
        resp = {'id': workspace_id}
        if ws.creator:
            resp['creator'] = ws.creator.username
        else:
            resp['creator'] = None
        resp['name'] = ws.name
        resp['description'] = ws.description
        
        return resp
        
    @exception_handler
    @api_key_required   
    def read(self,  request,  workspace_id):        
        """
        Returns info about a given workspace.
        - method GET
            - parameters: none
        - returns:
            - JSON example:{'creator': 'test', 'description': '', 'name': 'test workspace', 'id': '2'}
        """
        
        user = User.objects.get(pk = request.GET.get('user_id'))
        if not user.is_superuser:
            if ws not in user.workspaces.all() :
                raise InsufficientPermissions
        
        resp = WorkspaceResource()._read(workspace_id)
        
        json_resp = json.dumps(resp)
        return HttpResponse(json_resp)
    
    @exception_handler
    @api_key_required    
    def create(self,  request):
        """
        Allows to create a new workspace.
        - method: POST
            - parameters:            
                - name 
                - description 
        - returns: information about the new workspace, for example {"description": "", "id": 2, "name": "test_1"}
        """
        
        logger.debug('args %s'%request.POST)
        if not request.POST.has_key('name'):
            raise MissingArgs
        
        if request.POST.has_key('creator'):
            user = User.objects.get(username = request.POST.get('creator'))
        else:
            user_id = request.POST.get('user_id')
            user = User.objects.get(pk = user_id)
        name = request.POST .get('name')
        description = request.POST .get('description', '')

        ws = Workspace()
        form = _update_ws(ws,  {'name': name,  'description': description})
        
        if not form.is_valid():
            logger.exception('invalid form:\n %s' %form.errors)            
            raise ArgsValidationError(form.errors  )
        
        
        logger.info("name:%s,Description:%s,user:%s" %(name, description, user))
        if (len(DAMWorkspace.objects.filter(name = name, creator = user))>0):
            logger.info("ESISTE GIAAAAAA!!!!")
            raise
        else:
            logger.info("NON ESISTE!!!!")
        
        ws = DAMWorkspace.objects.create_workspace(name, description, user)

        resp = {'id': ws.pk, 'name': ws.name,  'description': ws.description}
        json_resp = json.dumps(resp)
        logger.debug('json_resp %s'% json_resp)
        return HttpResponse(json_resp )    
    
    @exception_handler
    @api_key_required
    def delete(self,  request,  workspace_id,  ):      
        """
        Allows to delete a given workspace
        - method: GET
            - parameters: none
        - returns: empty response
        """ 
        
        ws = Workspace.objects.get(pk = workspace_id)        
        user_id = request.GET['user_id']
        _check_app_permissions(ws,  user_id,  ['admin'])
        logger.debug('deleting ws %s' % ws.pk)
        ws.delete()        
        return HttpResponse('')
        
    def _get_smartfolders(self, workspace_id):
        sms = SmartFolder.objects.filter(workspace__pk = workspace_id)            
                   
        resp = {'smartfolders':[]}
        sm_resource = SmartFolderResource()
        for sm in sms:
            resp['smartfolders'].append(sm_resource.get_info(sm))
        
        return resp
    
    @exception_handler
    @api_key_required
    def get_smartfolders(self,  request,  workspace_id,  ):      
        """
        Allows to delete a given workspace
        - method: GET
            - parameters: none
        - returns: a json string containig information about smart folders belonging to the given workspace. Here an example:
         {'smart_folders': [{'and_condition': True, 'id': 1, 'label': 'test', 'workspace_id': 1, 'queries': [{'negated': False, 'type': 'keyword', 'id': 17}]}]}
            
        """ 
        resp = WorkspaceResource()._get_smartfolders(workspace_id)
        return HttpResponse(simplejson.dumps(resp))
        
        
    @exception_handler
    @api_key_required
    def get_scripts(self,  request,  workspace_id,  ):      
        """
        """ 
        
        scripts = Pipeline.objects.filter(workspace__pk = workspace_id)            
                   
        resp = {'scripts':[]}
        for script in scripts:
           resp['scripts'].append(_get_scripts_info(script))
        
        return HttpResponse(simplejson.dumps(resp))

    @exception_handler
    @api_key_required
    def get_items(self,  request, workspace_id):        
        """
        Allows to retrieve items according to a given query.
        The query can contains one or more words, each one can be formatted in this way:
            {metadata_schema}_{metadata_name}={value}
            
        For example 'dc:title=test' will find all items with dublin core title metadata equal to 'test'.
        Obviously, you can search just with simple words, so if query is equal to 'test', a full text search on all searchable metadata will be performed.
        
        """
        
        start = request.GET.get('start')
        limit = request.GET.get('limit')
        
        
        metadata = request.GET.getlist('metadata')
        media_type = request.GET.getlist('media_type')
        logger.debug('metadata %s'%metadata)
        
        workspace = Workspace.objects.get(pk = workspace_id)
        variants = request.GET.getlist('renditions')
        logger.debug('variants %s'%variants)
        
        items = Item.objects.filter(workspaceitem__workspace__pk = workspace_id)
        logger.debug('---------items %s'%items)
        items, total_count = _search(request.GET,  items, media_type, start, limit,  workspace)
     
        resp = {'items': []}
        
                
        #state = request.GET.get('state')
        #logger.debug('state %s'%state)
        #if state:
            #items = items.filter(stateitemassociation__state__name = state)
        #
     #
        items = items.distinct()    
        item_res = ItemResource()

        for item in items:
            logger.debug(item)
            try:
                resp['items'].append(item_res._get_item_info(item, workspace, variants, metadata))
            except Exception,ex:
                logger.error(ex)
    
        resp['totalCount'] = total_count
        json_resp = json.dumps(resp)
        return HttpResponse(json_resp)
        
class ItemResource(ModResource): 
    
    @exception_handler
    @api_key_required
    def generate_variants(self,  request,  item_id):
        """
        It allows to generate variants of a given  item        
        
        - method: POST
            - parameters: 
                - workspace_
        - returns: empty response
        """       
        
        item  = Item.objects.get(pk = item_id)
        
        orig = Component.objects.get(item = item, variant__variant_name = 'original')
        
        if self.private:
            media_type = request.POST.get('media_type') 
            if media_type:
                if not media_type in ['image',  'video',  'audio',  'doc']:
                    raise ArgsValidationError
                logger.debug('media_type %s' %media_type)
                item.type = media_type
                item.save()

        user_id = request.POST ['user_id']
        logger.debug('user_id %s'% user_id)
        _check_permissions_for_item(user_id,  item)
        
        workspace_id = request.POST .get('workspace_id')
        if not workspace_id:
            raise MissingArgs
            
        workspace = Workspace.objects.get(pk = workspace_id)
        
        generate_variants(orig, workspace, upload = False, api=True)
        
        return HttpResponse('')
        
        
#    @exception_handler
#    @api_key_required
    def upload_variant(self,  request,  item_id):
#    TODO:FINISH DOC
        """ 
        Allows to upload a variant of a item.
        - method: POST
            - params:
                - workspace_id
                - variant_id
                - Filedata: the file to upload
            
        - returns: empty string

        """       
       
        try:
            file = _upload_resource_via_post(request, False)
            logger.debug('file %s'%file)
            logger.debug('request.FILES %s'%request.FILES)
            file = request.FILES['files_to_upload']
            file_name = file.name
            
            
            
            ws_id = request.POST.get('workspace_id')
            if not ws_id:
                raise MissingArgs
            
            ws = DAMWorkspace.objects.get(pk = ws_id)   
            user_id = request.POST ['user_id']
            user = User.objects.get(pk = user_id)
            logger.debug('----------user %s'%user)
            variant_id = request.POST['rendition_id']
            variant = Variant.objects.get(id = variant_id)
            logger.debug('item_id %s'%item_id)
            item = Item.objects.get(pk = item_id)                       
            _upload_variant(item, variant, ws, user, file_name, file)            
            os.rmdir(file.dir)
            
        except Exception,ex:
            logger.exception(ex)
            raise ex  
        return HttpResponse('')

       
#    @exception_handler
#    @api_key_required
    def add_component(self,  request,  item_id):
        """ 
        Allows to add new component with url must to do.
        - method: POST
            - params:
                - workspace_id
                - rendition_id
                - url url of file
            
        - returns: empty string

        """       
        try:
            if not request.POST.has_key('workspace_id'):
                raise MissingArgs
            if not  request.POST.has_key('uri'):
                raise MissingArgs
            if not  request.POST.has_key('rendition_id'):
                raise MissingArgs
            if not  request.POST.has_key('file_name'):
                raise MissingArgs
             
            logger.debug("request.POST: %s" %request.POST)
            variant_id = request.POST['rendition_id']
            variant =  Variant.objects.get(pk = variant_id)
            item = Item.objects.get(pk = item_id)
            workspace_id = request.POST['workspace_id']
            if len(request.POST['uri']) >0:
                media_type = Type.objects.get_or_create_by_filename(request.POST['uri'])
            else:
                media_type = Type.objects.get_or_create_by_filename(request.POST['file_name'])
            comp = item.create_variant(variant, workspace_id, media_type)
            if variant.auto_generated:
                comp.imported = True
            comp.file_name = request.POST['file_name']
            uri = request.POST['uri']
            res_id = uri.split('/')
            res_id.reverse()
            logger.debug("\n\n res_id[] %s, len: %s" %(res_id[0], len(res_id[0])))
            comp._id = res_id[0]
            comp.uri = res_id[0]            
            logger.debug('res_id[0] %s' %res_id[0])
            mime_type = mimetypes.guess_type(res_id[0].lower())[0]
            if mime_type == None:
                mime_type = str(Type.objects.get_or_create_by_filename(res_id[0].lower()))
            logger.debug('mime_type %s' %mime_type)    
            ext = mime_type.split('/')[1]
            comp.format = ext
            comp.save()
             
        except Exception,ex:
            logger.exception(ex)
            raise ex 
        
        return HttpResponse('')
        
    @exception_handler
    @api_key_required
    def delete(self,  request,  item_id):
        """
        Delete the item from the given workspace  

        - method: GET
        - args: 
            - workpace_id   
        - returns: empty response
        """ 

        if not  request.GET.has_key('workspace_id'):
            raise MissingArgs

        ws_id = request.GET['workspace_id']            
        ws = DAMWorkspace.objects.get(pk = ws_id)        
        item = Item.objects.get(pk = item_id)
        
        user_id = request.GET['user_id']        
        
        
        _check_app_permissions(ws,  user_id,  ['admin',  'remove_item'])
        item.workspaceitem_set.filter(workspace = ws).delete()
        if item.workspaces.all().count() == 0:
            item.delete()
        return HttpResponse('')        
    
    
    @exception_handler
    @api_key_required
    def set_metadata(self,  request,  item_id,):      
        """
        - method: POST
            - parameters: 
                workspace_id
                - metadata: JSON dictionary containing metadata schemas and relative values to the item. Example: {'dc:title': {'en-US': 'test'},  'dc:identifier': 'test',  'dc:subject': ['test', 'test2']}
        - returns: empty response
        
        """
        try:
            
            return self._set_metadata(request,  item_id)   
        except Exception, ex:
            logger.exception(ex)
            raise ex
        
    def _set_metadata(self,  request,  item_id,):      
#        workspace = Workspace.objects.get(pk = request.POST['workspace_id'])
        logger.debug('request.POST %s'%request.POST)
        if not request.POST.has_key('metadata'):
            raise MissingArgs
        # logger.debug("request.POST.get('metadata') %s"%request.POST.get('metadata') )
        metadata = json.loads(request.POST.get('metadata'))
        
        user_id = request.POST['user_id']
        
        item  = Item.objects.get(pk = item_id)        
        _check_permissions_for_item(user_id,  item)
        
        ctype = ContentType.objects.get_for_model(item)
        
        new_metadata = {}
        for data in metadata.keys():         
            logger.debug('data %s'%data) 
            try:  
                property_namespace,   property_field_name = data.split('_')
            except:
                raise ArgsValidationError({'metadata': ['metadata schema are not formatted properly' % data]})
            try:
                property = MetadataProperty.objects.get(namespace__prefix = property_namespace,  field_name = property_field_name)
            except MetadataProperty.DoesNotExist:
                raise ArgsValidationError({'metadata': ['metadata schema %s unknown' % data]})
                
            if property.type == 'lang':
                if not isinstance(metadata[data],  dict):
                    raise ArgsValidationError({'metadata': ['format of metadata %s is invalid; it must be a dictionary (ex: {"en-US":"value"})' % data]})
                
                new_metadata[str(property.pk)]  = []
                for lang in metadata[data].keys():
                    
                    if lang not in MetadataLanguage.objects.all().values_list('code',  flat = True):
                        raise ArgsValidationError({'metadata': ['invalid language %s for metadata %s' % (lang, data)]})
                    
                    new_metadata[str(property.pk)] .append([metadata[data][lang],  lang])
                
#                dict

            elif property.type in XMPStructure.objects.all().values_list('name',  flat = True):
#                list of dict
                
                if not isinstance(metadata[data],  list):
                    raise ArgsValidationError({'metadata': ['format of metadata %s is invalid; it must be a list of dictionaries' % data]})
                
                structure = XMPStructure.objects.get(name = property.type)
                structure_list = []
                
                for _structure in metadata[data]:
                    if not isinstance(_structure ,  dict):
                        raise ArgsValidationError({'metadata': ['format of metadata %s is invalid; it must be a list of dictionaries' % data]})
                    
                    tmp_dict = {}
                    for el in _structure.keys():
                        property_namespace,   property_field_name = el.split('_')
                        try:
                            el_property = MetadataProperty.objects.get(namespace__prefix = property_namespace,  field_name = property_field_name)
                        except MetadataProperty.DoesNotExist:
                            raise ArgsValidationError({'metadata': ['metadata schema %s unknown' % el]})
                        logger.debug('structure %s'%structure)
                        if el_property not in structure.properties.all():
                            raise ArgsValidationError({'metadata': ['unexpected property %s' % el]})
                        
                        tmp_dict[str(el_property.pk)] = _structure[el]
                    
                    structure_list.append(tmp_dict)                    
                        
                new_metadata[str(property.pk)] = structure_list

            elif property.is_array != 'not_array':                
#                list of str
                
                if not isinstance(metadata[data],  list):
                    raise ArgsValidationError({'metadata': ['format of metadata %s is invalid; it must be a list of strings' % data]})
                for el in metadata[data]:
                    if not isinstance(el,  basestring):
                        raise ArgsValidationError({'metadata': ['format of metadata %s is invalid; it must be a list of strings' % data]})
                
                new_metadata[str(property.pk)] = metadata[data]
            else:
#                str
                if not isinstance(metadata[data],  basestring) and not isinstance(metadata[data],  int) and not isinstance(metadata[data],  float):
#                    logger.debug('metadata[data] %s'%metadata[data])
#                    logger.debug('-------------------------------------metadata[data].__class__ %s'%metadata[data].__class__)
                    raise ArgsValidationError({'metadata': ['format of metadata %s is invalid; it must be a string' % data]})
                
                new_metadata[str(property.pk)] = metadata[data]
                
        logger.debug('new_metadata %s' %new_metadata)
        MetadataValue.objects.save_metadata_value([item], new_metadata,  'original', item.workspaces.all()[0]) #workspace for variant metadata, not supported yet
        
#        for data in metadata:            
#            logger.debug('metadata %s '%metadata )
#            logger.debug('data %s '%data )
#            if not isinstance(data,  dict):
#                raise MalformedJSON('metadata must be a list of dictionary')
#            if not data.has_key('namespace') or not data.has_key('name') or not data.has_key('value'):
#                raise MalformedJSON('a metadata entry does not have the three keys required: "namespace", "name", "value"')
#            
#            schema_namespace = data['namespace']
#            schema_name= data['name']
#            value = data['value']                
##            logger.debug('value %s' % value)            
#            schema_obj = MetadataProperty.objects.get(namespace__prefix = schema_namespace ,  field_name = schema_name)                     
#            if schema_obj.is_array == 'alt' and schema_obj.type == 'lang':
##                    TODO: gestire default lang
#                lang = data.get('lang')
#            else:
#                lang = None
#            
#            if schema_obj.is_array != 'not_array' and schema_obj.is_array  != 'alt':
#                if not isinstance(value,  list):
#                    value = [value]                  
#                
#                for el in value:
##                    logger.debug('el value %s'%el)
#                    metadata = MetadataValue.objects.create(schema = schema_obj, object_id  = item.pk,  content_type = ctype,  language = lang)
#                    metadata.value = el
#                    metadata.save()
#            else:
#                metadata = MetadataValue.objects.get_or_create(schema = schema_obj, object_id  = item.pk,  content_type = ctype,  language = lang)[0]                
#                metadata.value = value 
#                metadata.save()
        
        return HttpResponse('')
        
        
    def _get_metadata(self,  item):
        def convert_property(metadata):
            
            property_id = metadata.keys()[0]
            property = MetadataProperty.objects.get(pk = property_id)
            
            converted_metadata = {}
            property_key = '%s_%s'%(property.namespace.prefix , property.field_name)            
            
            values = metadata[property_id]
            if isinstance(values,  unicode) or isinstance(values,  str) or isinstance(values,  dict):
                converted_metadata[property_key] = values
            
            if isinstance(values,  list):
                if isinstance(values[0],  str) or isinstance(values[0],  unicode):
                    converted_metadata[property_key] = values
                    
                else:
                    converted_metadata[property_key] = []
                    for value in values:
                        inner_dict = {}
                        for key  in value.keys():
                            inner_property = MetadataProperty.objects.get(pk = key)            
                            
                            inner_property_key = '%s_%s'%(inner_property.namespace.prefix , inner_property.field_name)            
                            inner_dict[inner_property_key] = value[key]
                            
                        converted_metadata[property_key].append(inner_dict)
                    
                    
                      
            logger.debug('converted_metadata %s'%converted_metadata)    
            return converted_metadata
        
        resp = {}
        metadata_list = item.get_metadata_values()
        for metadata in metadata_list:
            resp.update(convert_property(metadata))
            
        logger.debug('resp %s'%resp)
        return resp
            
        
        
    
    def _get_item_info(self, item, workspace, variants, metadata):
        media_type = item.type.name            
        tmp = {'pk': item.pk, 'media_type': media_type}
    
        for m in metadata:
            if m == '*':                
                properties = MetadataProperty.objects.all()
                for metadata_value in MetadataValue.objects.filter(item = item):
                    tmp[str(metadata_value.schema)] = metadata_value.value
                break
                
            property_namespace, property_field_name = m.split(':')
                
            try:
                property = MetadataProperty.objects.get(namespace__prefix__iexact = property_namespace,  field_name__iexact = property_field_name)
                mv = MetadataValue.objects.get(schema = property, item = item)                
                tmp[m] = mv.value
            except Exception, ex:
                #logger.error('skipping %s'%ex)
                pass
                
                    
                
                    
            
        
#        component_list = Component.objects.filter(item = item, workspace = workspace)
        for variant in variants:
            component = Component.objects.get(item = item,  workspace = workspace,  variant__name = variant)               
            url  = component.get_url()                
            tmp[variant] = url
                
        return tmp
    
    
    
    @exception_handler
    @api_key_required
    def add_to_collection(self,  request,  item_id):
        """
        - method: POST
        - args: 
            - collection_id: the id of the collection to whom add the item
        -returns: empty response
        """
        
        
        if not request.POST.has_key('collection_id'):
            raise MissingArgs
        
        collection_node_ids = request.POST.getlist('collection_id')
        for i in range(len(collection_node_ids)): 
            collection_node_id = collection_node_ids[i]                
            collection_node = Node.objects.get(pk = collection_node_id)
            if i == 0:
                ws = collection_node.workspace
                user_id = request.POST['user_id']
                _check_app_permissions(ws,  user_id,  ['admin',  'edit_collection'])
            
            collection_node.save_collection_association([item_id])
        
        return HttpResponse('')
        
    @exception_handler
    @api_key_required
    def remove_from_collection(self,  request,  item_id):
        """
        Allows to remove association between an item and collections
        
        - method: POST
        - args: 
            - collection_id: the ids of the collections
        -returns: empty response
        """        
        
        if not request.POST.has_key('collection_id'):
            raise MissingArgs
        
        collection_node_ids = request.POST.getlist('collection_id')
        for i in range(len(collection_node_ids)):
            collection_node_id = collection_node_ids[i]
            collection_node = Node.objects.get(pk = collection_node_id)
            if  i == 0:                 
                ws = collection_node.workspace
                user_id = request.POST ['user_id']
                logger.debug('user_id %s'% user_id)
                _check_app_permissions(ws,  user_id,  ['admin',  'edit_collection'])
            
            collection_node.remove_collection_association([item_id])        
        
        return HttpResponse('')    
    
    @exception_handler
    @api_key_required
    def add_keywords(self, request,  item_id):  
        """
        - method: POST
        - args: 
            - keywords: a list of id
        - returns: empty response
        
        - JSON request example:
        {'keywords':
            ['bla',
            'blablabla'           
            ]
        }
        """
        return self._add_keywords(request,  item_id)
        
    def _add_keywords(self, request,  item_id):    
        
        if not request.POST.has_key('keywords'):
            raise MissingArgs
        node_ids = request.POST.getlist('keywords')
        for node_id in node_ids:
            node = Node.objects.get(pk = node_id)
            node.save_keyword_association([item_id])
            
        return HttpResponse('')    
        
        
    @exception_handler
    @api_key_required
    def remove_keywords(self, request,  item_id):
        """
        - method: POST
        - args: 
            - keywords: a list of keywords to be removed
        - returns: empty response
        
       
        }
        """
        self._remove_keywords(request,  item_id)
        return HttpResponse('')
        
    def _remove_keywords(self, request,  item_id):       
        if not request.POST.has_key('keywords'):
            raise MissingArgs
        node_ids = request.POST.getlist('keywords')
        for node_id in node_ids:
            node = Node.objects.get(pk = node_id)
            node.remove_keyword_association([item_id])
        
    @exception_handler
    @api_key_required
    def remove_metadata(self,  request,  item_id,): 
        """
        - method: POST
            - parameters: 
                - metadata
        - returns: empty response
            
        JSON request examples:
        It cleans the metadata dc:title
        
        {'metadata': 
            [
                {'namespace': 'dc', 
                'name': 'title', 
               ]
        }
        
        It removes an element of the metadata dc:subject
        {'metadata': 
            [
                {'namespace': 'dc', 
                'name': 'title', 
                'value':'test'
                }, 
                {
                'namespace': 'dc', 
                'name': 'subject', 
                'value':['a', 'b']
                },                                                 
            ]
        }
        
        """
        return self._remove_metadata(request,  item_id,)
    def _remove_metadata(self,  request,  item_id,): 
        
        
        if not request.POST.has_key('metadata'):
            raise MissingArgs
        metadata = json.loads(request.POST.get('metadata'))
        
        user_id = request.POST ['user_id']
        logger.debug('user_id %s'% user_id)
        item  = Item.objects.get(pk = item_id)
        _check_permissions_for_item(user_id,  item)
      
        
        ctype = ContentType.objects.get_for_model(item)
        for data in metadata:
            if  not data.has_key('namespace') or not data.has_key('name'):
                raise ArgsValidationError
            m = MetadataValue.objects.filter(schema__namespace__prefix = data['namespace'],  schema__field_name =  data['name'],  item= item)
            
            if data.has_key('value'):                
                logger.debug('filtering for value %s' %data['value'])
                m = m.filter(value = data['value'])
            
            m.delete()        
            return HttpResponse('')    
    
    @exception_handler
    @api_key_required
    def add_to_ws(self,  request,  item_id):
        """
        - method: POST
            - parameters: 
                - workspace_id: the id of the workspace to whom the item will be added
        - returns: empty response
        
        - JSON request example:
            {'workspace_id':1}
        """
        if not request.POST.has_key('workspace_id'):
            raise MissingArgs
        user_id = request.POST.get('user_id')
        
        workspace_id = request.POST['workspace_id']        
        ws = DAMWorkspace.objects.get(pk = workspace_id)        
        item = Item.objects.get(pk = item_id)
        _check_app_permissions(ws,  user_id,  ['admin',  'add_item'])        
        current_ws = item.workspaces.exclude(pk = ws.pk)[0]
        _add_items_to_ws(item, ws, current_ws)        
        return HttpResponse('')        
    
    def _read(self, user, item_id, flag, ws_id = None, variants = None):
        item = Item.objects.get(pk = item_id)         
        
        keywords = list(item.keywords())
        colls = item.node_set.filter(type = 'collection')
        collection_ids = list(item.collections())
            
        wss = item.workspaces.all()
        logger.debug('wss %s'%wss)
        resp = {'id': item.pk,  'workspaces':[ws.pk for ws in wss ],  'keywords':keywords,  'collections': collection_ids,  'media_type': str(item.type)}
        try:
            upload_workspace = Node.objects.get(type = 'inbox', parent__label = 'Uploaded', items = item).workspace
            resp['upload_workspace']= upload_workspace.pk
        except Node.DoesNotExist:
            pass
        
        try:    
            metadata = self._get_metadata(item)            
            resp['metadata'] = metadata
            
        except:
            resp['metadata'] = {}        
        
        
#            request.POST.['get_variant_urls'] = workspace
        if flag:
            self.get_variant_urls(user,  item, ws_id, variants )
            
            logger.debug(item.variants)
            resp['renditions'] = {}
                
            for variant_name,  value in item.variants.items():
                tmp = {}
                try:
                    file_name = item.component_set.get(variant__name = variant_name, workspace__pk = ws_id).file_name
                    tmp['file_name'] = file_name
                except Exception, ex:
                    logger.exception(ex)
                    
                tmp['url'] = value
                v = Variant.objects.get(name = variant_name)
                c = v.get_component(Workspace.objects.get(pk = ws_id),item)
                try:
                    tmp['metadata_list'] = item.get_metadata_values()
                except Exception, ex:
                    tmp['metadata_list'] = {}
                    logger.exception(ex)

                resp['renditions'] [variant_name] = tmp
        
        return resp
    
    @exception_handler
    @api_key_required
    def read(self,  request, item_id):
        """
        - method: GET
            - parameters: 
                - variants_workspace: the workspace id for whom retrieve the variants' info
                - variants: optional, list of variants to get
        - returns: 
            - JSON example:
            {
            'id': 1, 
            'workspaces':[1,2],  
            'keywords':[5,6], 
            'collections': [3,4],
            'metadata':[
                            {
                            'namespace':'dc',
                            'name':'title',
                            value:'foo'
                            }
                            ],
            "variants urls": {"fullscreen": "http://127.0.1.1:7000/resources/7551515e84958f0ff70b22b8f43131af2209bf15/resource.jpg", "preview": "http://127.0.1.1:7000/resources/f64b97087bdbef164116789bc7e1d1d6964cc943/resource.jpg", "original": "http://127.0.1.1:7000/resources/e121aad2baa81693eaf498f00aa477facdb275fa/resource.jpg", "thumbnail": "http://127.0.1.1:7000/resources/413f4dfbe508b0730fb62c806175326abb259bed/resource.jpg"}
            
            }
        """
        
        
        user_id = request.GET.get('user_id')        
        user = User.objects.get(pk = user_id)
        if not user.is_superuser:
            if item.workspaces.filter(members = user).count() == 0:
                raise  InsufficientPermissions            
        flag = request.GET.__contains__('renditions_workspace')
        if flag:
            ws_id = request.GET.get('renditions_workspace')
            variants = request.GET.getlist('renditions')
        else:
            ws_id = None
            variants = None
        
        resp = ItemResource()._read(user, item_id, flag, ws_id, variants)
        
        logger.debug('resp %s'% resp)
        json_resp = json.dumps(resp)
        return HttpResponse(json_resp)
        
    def get_variant_urls(self, user,  item, workspace_id, variants_to_get = None):
#        TODO: gestire not available
        logger.debug(' workspace_id %s' %workspace_id)
        try:
            ws = Workspace.objects.get(pk = workspace_id)        
        except Workspace.DoesNotExist,  ex:
            logger.exception(ex)
            raise ex
        
        logger.debug(' app.user.workspaces.filter(pk = workspace_id) %s' %user.workspaces.filter(pk = workspace_id))
        logger.debug('%s user.pk' %user.pk)
        if not user.is_superuser:
            if user.workspaces.filter(pk = workspace_id).count()  == 0:
                logger.exception('no permission')
                raise InsufficientPermissions
        
        
        item.variants = {}
        workspace = Workspace.objects.get(pk = workspace_id)
        component_list = Component.objects.filter(item = item, workspace__pk =workspace_id)
        logger.debug('-----------------------------------variants_to_get %s'%variants_to_get)
        if variants_to_get:
            component_list = component_list.filter(variant__name__in = variants_to_get)
        
        for c in component_list:
            v = c.variant
                            
            
            logger.debug('v %s'%v)
            url  = c.get_url()        
#            item.variants[va.pk] = url
            if url:
                item.variants[v.name] = 'http://' + SERVER_PUBLIC_ADDRESS + url
            else:
                item.variants[v.name] = ""

    def get_type(self, request):
        """
        return type about a file name
        - method: POST
        - args:
            - filename : filename.extention
        - returns:
            - JSON example:
            {
            'media_type': 'image/jpg',
            }
        
        """        

        if not request.POST.has_key('file_name'):
            raise MissingArgs
        
        try:
            logger.info(request.POST['file_name'])
            file_name = str(request.POST['file_name'].lower())
            media_type = Type.objects.get_or_create_by_filename(file_name)
            resp = {'media_type': str(media_type)}
            json_resp = json.dumps(resp)
        except Exception, ex:
            logger.exception(ex)
        
        return HttpResponse(json_resp)           
        
                        
    @exception_handler
    @api_key_required
    def create(self,  request):
        """
        Create a new item in the given workspace
        - method: POST
        - args:
            - workspace_id : the id of the workspace to whom the item will be added
            - media_type: image, video, audio. Optional, default: image
        - returns:
            - JSON example:
            {
            'id': 1,
            'workspace_id':1
            
            }
        
        """        
        
        if not request.POST.has_key('workspace_id'):
            raise MissingArgs
        
        media_type = request.POST['media_type']
            
        user_id = request.POST ['user_id']
        logger.debug('user_id %s'%user_id)
        user = User.objects.get(pk = user_id)
        
        ws_id = request.POST ['workspace_id']            
        ws = DAMWorkspace.objects.get(pk = ws_id)
        
        _check_app_permissions(ws,  user_id,  ['admin',  'add_item'])        

        
        item = Item.objects.create(ws, uploader = user,_id = new_id(),  type = Type.objects.get_or_create_by_mime(media_type))
             
        
        resp = {'id': item.pk,   'workspace_id':ws_id}
        json_resp = json.dumps(resp)

        return HttpResponse(json_resp)   


    @exception_handler
    @api_key_required   
    def get_collections(self, request, item_id):
        """
        """
                
        if not request.GET.has_key('workspace_id'):
            raise MissingArgs, "workspace id and item id are both mandatory parameters"
        
        workspace_id = request.GET['workspace_id']
        
        try:
            ws = Workspace.objects.get(id=workspace_id)
        except:
            raise WorkspaceDoesNotExist
        
        item = Item.objects.get(pk = item_id)
        logger.info("\n\n\n item_id %s \n\n\n")
        parent = request.GET.get('parent')
        if parent:
            parent_node = Node.objects.get(pk = parent)
            sub_tree = parent_node.get_branch()
            collections = sub_tree.filter(items = item)
        
        else:        
            collections = item.collections()
        
        collections = list(collections.values('id', 'label'))
        return HttpResponse(simplejson.dumps({'collections': collections}))

    
    @exception_handler
    @api_key_required   
    def get_keywords(self, request, item_id):
        """
        """
                
        if not request.GET.has_key('workspace_id'):
            raise MissingArgs, "workspace id and item id are both mandatory parameters"
        
        workspace_id = request.GET['workspace_id']
        
        try:
            ws = Workspace.objects.get(id=workspace_id)
        except:
            raise Workspace.DoesNotExist
        
        item = Item.objects.get(pk = item_id)
        parent = request.GET.get('parent')
        if parent:
            parent_node = Node.objects.get(pk = parent)
            sub_tree = parent_node.get_branch()
            keywords = sub_tree.filter(items = item)
        
        else:        
            keywords = item.keywords()
        logger.debug('---------- %s'%keywords)
        keywords = list(keywords.values('id', 'label'))
        return HttpResponse(simplejson.dumps({'keywords': keywords}))
        
        

    
    @exception_handler
    @api_key_required   
    def get_state(self, request, item_id):
        """
        Allows to get the state of an item in a given workspace
         - method: POST
         - parameters: 
            - workspace_id
         - returns: empty string if no state has been found, otherwise a json string similar to:
         {'name': 'test'}
          
        
        """
        item = Item.objects.get(pk = item_id)
        if not request.POST.has_key('workspace_id'):
            raise MissingArgs, "workspace id and item id are both mandatory parameters"
        
        workspace_id = request.POST['workspace_id']
        
        try:
            ws = Workspace.objects.get(id=workspace_id)
        except:
            raise Workspace.DoesNotExist
        
        
        
        try:
            state = item.stateitemassociation_set.get(state__workspace = ws).state
            resp = {'name': state.name, 'id': state.pk}
        except Exception, ex:
            logger.exception(ex)
            resp = ''
        
            

        json_resp = json.dumps(resp)
        return HttpResponse(json_resp)
            
    @exception_handler
    @api_key_required
    def get_all_states(self, request, item):
        resp = dict()
        
        try:
            for sa in StateItemAssociation.objects.filter(item=item):
                resp[str(sa.workspace)] = str(sa.state)

                json_resp = json.dumps(resp)
        except:
            pass
            
        return HttpResponse(json_resp)
             
   
    @exception_handler
    @api_key_required       
    def set_state(self, request, item_id):
        """
        Allows to set a state to an item in a workspace
         - method: POST
         - parameters:
             - workspace_id
             - state: name of the state
         - returns: empty string         
        
        """
        
        items = Item.objects.filter(pk = item_id)
        state_name = request.POST.get('state')
        if not state_name:
            raise MissingArgs({'args': ['no state passed']})
        
        ws_id = request.POST.get('workspace_id')
        if not ws_id:
            raise MissingArgs({'args': ['no workspace_id passed']})
        
        state = State.objects.get(name = state_name)
        
        user_id = request.POST.get('user_id')
        workspace = Workspace.objects.get(pk = ws_id)
        _check_app_permissions(workspace,  user_id,  ['admin', 'set_state'])
        _set_state(items, state) 
        return HttpResponse('')   



class CollectionResource(ModResource):    
    
    @exception_handler
    @api_key_required
    def create(self,  request):
        """
        Allows to create a new collections.
        - method: POST
            - parameters: 
                - label (required)
                - workspace_id: optional, it allows to create a collection at the top level
                - parent_id optional, required if no workspace_id is passed
            
        - returns: information about the new collection
            JSON example: {'id': 2,'label': 'test', 'parent_id': 1, 'workspace_id': 1  }                   
        """        
#        TODO: metadata adding  test and doc
        logger.debug('creating...')
          
        user_id = request.POST.get('user_id')
        ws_id = request.POST.get('workspace_id')
        parent_id = request.POST.get('parent_id')
        label = request.POST.get('label')        
        
        if not label:
            raise MissingArgs
        if  ws_id:           
            workspace = DAMWorkspace.objects.get(pk = ws_id)
            parent_node = Node.objects.get(workspace = workspace, type = 'collection', depth= 0)
        else:
            if not parent_id:
                raise MissingArgs
            parent_node = Node.objects.get(pk = parent_id)
            workspace = parent_node.workspace        
            
        _check_app_permissions(workspace,  user_id,  ['admin',  'add_collection'])     
        node = Node.objects.add_node(parent_node,label, workspace)            
        json_response = json.dumps({'model': 'collection',  'id': node.pk, 'label': label, 'parent_id': parent_id, 'workspace_id': workspace.id,  })
        logger.debug('add: json_response %s'%json_response )
        return HttpResponse(json_response) 
    
    def get_info(self, node):
        tmp_values = {
            'id': node.pk,  
            'label': node.label,   
            'workspace':node.workspace.pk, 
            'items':[]
        }
        if  node.parent.depth == 0:
            tmp_values['parent_id'] = None
        else:
            tmp_values['parent_id'] = node.parent.pk
        items = node.items.all()
        tmp_values['items'] = [i.pk for i in items] 
        
        tmp_values['children'] = []
        for child in node.children.all():                    
            tmp_values['children'].append(self.get_info(child))
        
        return tmp_values
    
        
    @exception_handler
    @api_key_required
    def read(self,  request,  collection_id = None):
        """
        Allows to get informations about a given collection or about all collection of a workspace
        @param collection_id: optional, required if no workspace_id is passed via GET
        
        - method: GET
            - parameters:
                - workspace_id: optional, required if no collection_id is passed. Use it to get all the collections of the given workspace
        - returns: 
            JSON example: {'id': 1,'label': 'test', 'parent_id': null, 'workspace_id': 1, items: [1,2]  }                   
        """   
        
        user_id = request.GET.get('user_id')        
        user = User.objects.get(pk = user_id)
        
        if collection_id:
            node = Node.objects.get(pk = collection_id)
            if node.depth < 1:
                raise InvalidNode
            
            
            
            
            
            tmp_values = self.get_info(node)
            resp = json.dumps(tmp_values)
        else:

            if not request.GET.has_key('workspace_id'):
                raise MissingArgs
            workspace_id = request.GET.get('workspace_id')
            ws = Workspace.objects.get(pk = workspace_id)
            
            kws = []
            nodes= Node.objects.filter(type = 'collection',  depth = 1,  workspace = ws)            
            logger.debug('COLLECTIONS %s'%nodes)            

            for node in nodes:
                kws.append(self.get_info(node))
                
            
            tax = {'collections': kws}
            logger.debug('collections %s'%kws )
            resp = json.dumps(tax)

#       TODO: check
#        if ws.members.filter(pk = user.pk).count() == 0:
#            raise InsufficientPermissions        
        return HttpResponse(resp)   
      
    @exception_handler
    @api_key_required
    def edit(self,  request,  collection_id):
        """
        Allows to rename a given collection
        - method: POST
        - args: 
            - label (required): the new label
            
        - returns : empty response
        """     
        
        node  = Node.objects.get(pk = collection_id)
        ws = node.workspace   
        user_id = request.POST.get('user_id')       
        _check_app_permissions(ws, user_id,  ['admin',  'edit_collection'])        
        
        if request.POST.has_key('label'):
            label = request.POST['label']
            logger.debug('label %s' %label)
            node.rename_node(label,  ws)   
            return HttpResponse('') 
        else:
            raise MissingArgs
            
    @exception_handler
    @api_key_required
    def move(self,  request,  collection_id):
        """
        Allows to move a collection in the hierarchy, associating it to a new parent
        - method: GET
        - args: 
            - parent_id: the id of the new parent. Optional, if not passed, the collection will be moved to the top level
            
        - returns : empty response
        
        """
      
        user_id = request.POST.get('user_id')
        node_source = Node.objects.get(pk = collection_id)
        ws = node_source.workspace
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_collection'])
        
        if not request.POST.has_key('parent_id'):
                    
            node_dest = Node.objects.get(type = 'collection',  depth = 0,  workspace = ws)
        else:
            node_dest = Node.objects.get(pk = request.POST['parent_id'])  
        
        logger.debug('moving...')        
        node_source.move_node(node_dest,  ws)
        return HttpResponse('')         
        
    @exception_handler
    @api_key_required
    def delete(self,  request,  node_id):
        """
        Allows to delete a collection.
        - method: GET
        -  returns : empty response
        
        """
        user_id = request.GET.get('user_id')
        node = Node.objects.get(pk = node_id)
        ws = node.workspace
        _check_app_permissions(ws,  user_id,  ['admin',  'remove_collection'])        
        node.delete()
        return HttpResponse('')       



    @exception_handler
    @api_key_required
    def add_items(self, request,  collection_id):
        """
        Allows to associate items to a given collection.
        - method: POST
        - args:
            - items: a list of item ids to whom add the given collection
        - JSON request example:
        {
            'items':[1,2,3]
        }
        
        -  returns : empty response
        
        """
        
          
        if  not request.POST.has_key('items'):
            raise MissingArgs        
                
        node = Node.objects.get(pk = collection_id)
        ws = node.workspace                
        user_id = request.POST.get('user_id')       
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_collection'])        
        
        item_ids = request.POST.getlist('items') 
        node.save_collection_association(item_ids)
        return HttpResponse('')        
    
    @exception_handler
    @api_key_required
    def remove_items(self, request,  collection_id):
        """
        Allows to remove associations to items and a given collection
        - method: POST
        - args:
            - items: a list of item ids to remove
        - JSON request example:
        {
            'items':[1,2,3]
        }
        
        -  returns : empty response
        
        """
               
          
        if  not request.POST.has_key('items'):
            raise MissingArgs        
                
        node = Node.objects.get(pk = collection_id)
        ws = node.workspace                
        user_id = request.POST.get('user_id')       
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_collection'])        
        
        item_ids = request.POST.getlist('items') 
        logger.debug('item_ids %s'%item_ids)
        logger.debug('nodes %s'%node.items.all())
        node.remove_collection_association(item_ids)  
        logger.debug('nodes %s'%node.items.all())      
        
        return HttpResponse('')
            
class KeywordsResource(ModResource):    
    
#    @exception_handler
    def _read(self, user, workspace_id, node_id  = None, flag = False):
        def get_info(kw,  get_branch = False):
            kw_info = {
                'id': kw.pk,  
                'label': kw.label,   
                'workspace':kw.workspace.pk, 
                'type': kw.cls, 
                'associate_ancestors': kw.associate_ancestors,  
                'metadata_schema': [],  
                'items':[]
            }
            if  kw.parent.depth == 0:
                kw_info['parent_id'] = None
            else:
                kw_info['parent_id'] = kw.parent.pk
                
            for kw_metadata in kw.metadata_schema.all():
                kw_info['metadata_schema'].append({
                    'id': kw_metadata.pk, 
                    'name': kw_metadata.field_name, 
                    'namespace': kw_metadata.namespace.name, 
                    'value': NodeMetadataAssociation.objects.get(node = kw,  metadata_schema = kw_metadata).value
                    
                    })
            
            kw_info['items'] = [i.pk for i in kw.items.all()] 
            
            if get_branch:
                kw_info['children'] = []
                for child in kw.children.all():                    
                    kw_info['children'].append(get_info(child,  True))
            else:
                kw_info['children'] = [i.pk for i in kw.children.all()] 
            
            logger.info('\n\n\n kw_info %s' %kw_info)
            return kw_info
        
#        user_id = request.GET.get('user_id')        
#        user = User.objects.get(pk = user_id)
        
        
        logger.debug('workspace_id %s'%workspace_id)        
        if node_id:
            node = Node.objects.get(pk = node_id)
            logger.debug('node %s'%node)
            if node.depth < 1:
                raise InvalidNode
            
            ws = node.workspace
            if not user.is_superuser:
                if ws.members.filter(pk = user.pk).count() == 0:
                    raise InsufficientPermissions       
                
            resp = get_info(node,  True)
        else:

#            if not request.GET.has_key('workspace_id'):
#                raise MissingArgs
#            workspace_id = request.GET.get('workspace_id')
            ws = Workspace.objects.get(pk = workspace_id)
            
            if not user.is_superuser:
                if ws.members.filter(pk = user.pk).count() == 0:
                    raise InsufficientPermissions       
            
            kws = []          
            
            tmp_kws = Node.objects.filter(type = 'keyword',  depth = 1,  workspace = ws).order_by('depth')
            for kw in tmp_kws:
                kw_info = get_info(kw, True)    
                kws.append(kw_info)
                
            tax = {'keywords': kws}
            logger.debug('keywords %s'%kws)
            
            resp = tax
        
        if(flag):
            return resp 
        else:
            resp = json.dumps(resp)
            return HttpResponse(resp)
        
        
        
    @exception_handler
    @api_key_required
    def read(self,  request,  node_id = None):
        """
        Returns information about a given keyword or all keywords of a workspace
        @param node_id:optional, required if no workspace_id is passed
        - method: GET
            - parameters: 
                
                - workspace_id: optional, required if no node_id is passed. Use it to get all the keywords of the given workspace
        
        - returns :
            JSON example: {
                                    'id': 1,
                                    'label': 'test', 
                                    'parent_id': null, 
                                    'workspace': 1  
                                    'associate_ancestors': false,
                                    'metadata_schemas': ['id': 22, 'name': 'test', 'namespace': 'test'],
                                    items: ['123', '345']
                                    }                   
        """   
                
        user_id = request.GET.get('user_id')
        logger.debug('user_id %s'%user_id)       
        user = User.objects.get(pk = user_id)
        return self._read(user, None, node_id)
   
    
    
    def _prepare_metadata_schema(self,  request):        
        tmp_metadata_schema = request.POST.get('metadata_schema')
        if not tmp_metadata_schema:
            return []
            
        tmp_metadata_schema = simplejson.loads(tmp_metadata_schema)        
        
        logger.debug('----------tmp_metadata_schema %s'%tmp_metadata_schema)
        metadata_schema = []
        for metadata in tmp_metadata_schema:
            namespace = metadata['namespace']
            name = metadata['name']
            value = metadata['value']
            
            metadata_schema.append({'id': MetadataProperty.objects.get(field_name = name, namespace__name__iexact = namespace).pk,  'value': value })            
        logger.debug('----------metadata_schema %s'%metadata_schema)                
        return metadata_schema
    
    @exception_handler
    @api_key_required
    def create(self,  request):
        """
        Allows to create a new keyword.
        - method: POST
            - parameters: 
                - label (required)
                - workspace_id: optional, it allows to create a keyword at the top level
                - parent_id optional, required if no workspace_id is passed
                - type: 'category' or 'keyword'
                - associate_ancestors: boolean, valid only if type is 'keyword'
                - metadata_schema: optional. JSON list of dictionaries containing namespace, name and value for the metadata schemas  to associate to the new keyword. Example: [{"namespace": 'dublin core','name': 'title',   "value": 'test'}]
                
        
        - returns : JSON dictionary containing the id of the new keyword.Example: {'id':23}
        
        """        
        
        logger.debug('creating...')
      
      
        type = request.POST.get('type')
        if not type:
            raise MissingArgs
        
        
        if not request.POST.has_key('label'):
               raise MissingArgs
        if request.POST.has_key('parent_id'):
            node_parent = Node.objects.get(pk = request.POST['parent_id'])                        
            ws = node_parent.workspace        
            
        elif request.POST.has_key('workspace_id'):
            ws = DAMWorkspace.objects.get(pk = request.POST['workspace_id'])
            node_parent = Node.objects.get(type = 'keyword',  depth = 0,  workspace = ws)
        else:
            raise MissingArgs        
        
        if type not in ['keyword',  'category']:
            raise ArgsValidationError
            
        if type == 'keyword':
            if request.POST.has_key('associate_ancestors'):
                associate_ancestors = True
            else:
                associate_ancestors = False
#            associate_ancestors= request.POST.get('associate_ancestors',  False)
           
#            if associate_ancestors is None:
#                raise MissingArgs
            
#            associate_ancestors = simplejson.loads(associate_ancestors)
#            if not isinstance(associate_ancestors,  bool):
#                raise ArgsValidationError
        
        
            metadata_schema = self._prepare_metadata_schema(request)
                
            
            
            
        else:
            associate_ancestors = False
            metadata_schema = []
        
        user_id = request.POST.get('user_id') 
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_taxonomy'])
        
        new_node = Node.objects.filter(parent = node_parent, label = request.POST['label'])
        if new_node.count() > 0:
            new_node = new_node[0]
        else:
            new_node = Node.objects.add_node(node_parent, request.POST['label'],  ws, type, associate_ancestors)   
            if len(metadata_schema) > 0:
                new_node.save_metadata_mapping(metadata_schema)
        
        items  = request.POST.getlist('items')
#        TODO: test it
        if items:
            KeywordsResource().add_items(request, new_node.pk)
            
        
        return HttpResponse(simplejson.dumps({'id': new_node.pk}))        
    
    @exception_handler
    @api_key_required
    def edit(self,  request,  node_id):
        """
        Allows to edit a given keyword
        - method: POST
            - parameters: 
                - label                 
                - associate_ancestors: boolean, valid only if type is 'keyword'
                - metadata_schema: optional. JSON list of dictionaries containing namespace, name and value for the metadata schemas  to associate to the new keyword. Example: [{"namespace": 'dublin core','name': 'title',   "value": 'test'}]
                
        - returns : empty response
        """
        
        node  = Node.objects.get(pk = node_id)
        ws = node.workspace
        user_id = request.POST.get('user_id') 
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_taxonomy'])

        label = request.POST.get('label')
        associate_ancestors = request.POST.get('associate_ancestors',  None)
        if associate_ancestors is None:
            associate_ancestors = node.associate_ancestors
            
        metadata_schema = self._prepare_metadata_schema(request)
        
        
        node.edit_node(label,  metadata_schema, associate_ancestors,  ws)
        
        return HttpResponse('') 
    
    @exception_handler
    @api_key_required
    def move(self,  request,  node_id):
        """
        Allows to move a given keyword
        
        - method: GET
            - parameters: 
                - parent_id: the id of the new parent. Optional, if not passed the keyword will be moved at the top level
            
        - returns : empty response
        
        """

         
        user_id = request.POST.get('user_id') 
        node_source = Node.objects.get(pk = node_id)
        ws = node_source.workspace
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_taxonomy']) 
        
        if not request.POST.has_key('parent_id'):                  
            node_dest = Node.objects.get(type = 'keyword',  depth = 0,  workspace = ws)
        else:
            node_dest = Node.objects.get(pk = request.POST['parent_id'])  
        
        logger.debug('moving...')    
        logger.debug('ws %s'%ws)    
        node_source.move_node(node_dest,  ws)
        logger.debug('moved')                        
        
        return HttpResponse('') 
    
    @exception_handler
    @api_key_required
    def delete(self,  request,  node_id):
        """
        Allows to delete a given keyword
        - method: GET
            - parameters: none
        -  returns : empty response
        
        """
        
        user_id = request.GET.get('user_id')
        node = Node.objects.get(pk = node_id)
        ws = node.workspace
        _check_app_permissions(ws,  user_id,  ['admin',  'edit_taxonomy'])        
        node.delete()       
        return HttpResponse('')        
    
    @exception_handler
    @api_key_required
    def add_items(self, request,  node_id):
        """
        Allows to associate items to a given keyword.
        
        - method: POST
            -parameters:
                - items: a list of item ids to whom add the given keyword
        - JSON request example:
        {
            'items':[1,2,3]
        }
        
        -  returns : empty response
        
        """
        
          
        if  not request.POST.has_key('items'):
            raise MissingArgs
        
        node  = Node.objects.get(pk = node_id)
        ws = node.workspace        
        
        user_id = request.POST.get('user_id')       
        items = request.POST.getlist('items')
        keywords = node.pk
        new_post = request.POST.copy()
        new_post['keywords'] = keywords
        request.POST= new_post
        
        for item_id in items:
            ItemResource()._add_keywords(request,  item_id)
            
        return HttpResponse('')            
    
    
    
    
    @exception_handler
    @api_key_required
    def remove_items(self, request,  node_id):
        """
        Allows to remove the association between some items and a given keyword
        - method: POST
            - parameters:
                - items: a list of item ids to remove
        - JSON request example:
        {
            'items':[1,2,3]
        }
        
        -  returns : empty response
        
        """
        
        logger.debug('--------remove_items')
        
          
        if  not request.POST.has_key('items'):
            raise MissingArgs
        
        node  = Node.objects.get(pk = node_id)
        ws = node.workspace        
        
        user_id = request.POST.get('user_id')       
        items = request.POST.getlist('items')
        keywords = node.pk
        
        new_post = request.POST.copy()
        new_post['keywords'] = keywords
        request.POST= new_post
        
        for item_id in items:
            ItemResource()._remove_keywords(request,  item_id)
            
        return HttpResponse('')
    
    

class Auth(ModResource):
    @exception_handler
    def _login(self,  request):
        """
        Allows to log in a user through api. It returns user_id and secret necessary to any other api call
        - method: POST
        - parameters:
            - user_name
            - password
            - api_key
        - returns_ a json string similar to:
        {"secret": "ffbae16934db789f74b3d84494f133d4dcb34267", "user_id": 1, "workspace_id": 1, "session_id": "6a77bed80317ef052f0caf4580f9fb34"}
            
        """
        SESSION_KEY = '_auth_user_id'
        BACKEND_SESSION_KEY = '_auth_user_backend'
        
        user_name = request.POST.get('user_name')
        password = request.POST.get('password')
        api_key = request.POST.get('api_key')
        logger.debug('username password api_key %s %s %s' % (user_name,  password,  api_key))
        
        if not user_name or not password or not api_key:
            raise MissingArgs
                
        user = authenticate(username = user_name, password = password)

        if not user:
            logger.debug('login failed')
            raise LoginFailed
            
        
        try:
            app = Application.objects.get(api_key = api_key)
            secret,  created = Secret.objects.get_or_create(application = app, user = user)
        except Exception, ex:
            logger.exception('ex %s'%ex)
            raise invalidAPIKeyOrUserId
            
#        s = SessionStore()        
#        s[SESSION_KEY] = user.pk
#        s[BACKEND_SESSION_KEY] = user.backend
#        s.save()

        if user.is_active:
            login(request,  user)
        else:
            logger.debug('login failed')
            raise LoginFailed
        
        
        s = request.session
        wss = user.workspaces.all()
        resp_dict = {'user_id':user.pk,  'secret':secret.value,  'session_id': s.session_key, 'workspaces': [ws.id for ws in wss]}
       
        
        resp = json.dumps(resp_dict)    
        logger.debug('resp %s' %resp)
        return HttpResponse(resp)
        
    def _get_users(self):
        users = User.objects.all()
        resp = {'users':[]}
        for user in users:
            tmp = {'id': user.pk, 'username': user.username, 'is_superuser':user.is_superuser, 'password': user.password, 'email': user.email}
            resp['users'].append(tmp)
        
        logger.debug('resp %s'%resp)
        
        return resp    
    
    @exception_handler
    @api_key_required    
    def get_users(self,  request,  variant_id = None):
        """ 
        Allows to get informations about all DAM users. This is a private method, only for admin users. Note that the password is crypted
        - Method: GET
            - parameters: none
        -returns: {'users': [{'id':1, 'username': 'test', 'password': 'test', 'email': 'test@test.it', 'is_superuser': False}]}
        
        """
        u = User.objects.get(pk = request.GET['user_id'])
        if not u.is_superuser:
            raise InsufficientPermissions
        
        resp = Auth()._get_users()
        resp = json.dumps(resp)
        return HttpResponse(resp)

    @exception_handler
    @api_key_required    
    def add_user(self,  request):
        """ 
        Allows to add a user DAM users. This is a private method, only for admin users.
        - Method: POST
            - parameters:
                - username
                - password (crypted)
                - email
        -returns: id of the new user {'id':1}
        
        """
        u = User.objects.get(pk = request.POST['user_id'])
        if not u.is_superuser:
            raise 
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        
        if username is None:
            raise MissingArgs({'args': ['no username passed']}) 

        if password is None:
            raise MissingArgs({'args': ['no password passed']}) 

        if email is None:
            raise MissingArgs({'args': ['no email passed']}) 

        add_ws_permission = Permission.objects.get(codename='add_workspace')

        user = User.objects.create(username = username, password = password, email = email)
        user.user_permissions.add(add_ws_permission)
        user.save()
        
        create_ws = request.POST.get('create_workspace')
        if create_ws:
            ws = Workspace.objects.create_workspace(user.username, '', user)
        
        resp = {'id':user.pk}
        logger.debug('resp %s'%resp)    
        resp = json.dumps(resp)
        return HttpResponse(resp)
    

class VariantsResource(ModResource):   
    
    def get_info(self, variant,  workspace):
        logger.debug('variant %s'%variant)
        logger.debug('workspace %s'%workspace)
        
        resp = {
            'id': variant.pk, 
            'name': variant.name, 
            'caption': variant.caption, 
            'media_type': [media_type.name for media_type in variant.media_type.all()], 
            'auto_generated': variant.auto_generated,
        }

        if variant.workspace:
            resp['workspace_id'] = variant.workspace.pk
        
     
        logger.debug('resp %s'%resp)
        return resp
    
    @exception_handler
    @api_key_required    
    def read(self,  request,  variant_id = None):
        """
        Returns info about a specific variant or about variants of a workspace
        
         @param variant_id: optional. If passed, info about the given variant are returned, otherwise all variants for the workspace  are returned.
            - Method: GET
            - parameters:
                - workspace_id (optional, required if no variant_id is passed)
            - Returns:
            
                {'variants':  [{"caption": "Original", "auto_generated": false, "id": 1, "media_type": "image", "name": "original"}, {"caption": "edited", "auto_generated": false, "id": 2, "media_type": "image", "name": "edited"}, {"preferences": {"watermark_uri": null, "video_position": null, "container": "jpg", "watermarking_position": null, "codec": "jpg", "max_dim": 100, "cropping": false, "watermarking": false}, "sources": [{"id": 2, "name": "edited"}, {"id": 1, "name": "original"}], "id": 3, "caption": "Thumbnail", "media_type": "image", "auto_generated": true, "name": "thumbnail"}}
       
        """
        workspace_id = request.GET.get('workspace_id')
        if not workspace_id:
            raise MissingArgs({'args': ['no workspace id passed']})
        workspace = Workspace.objects.get(pk = workspace_id)
        
        if variant_id:
            variant = Variant.objects.get(pk = variant_id)
            resp = self.get_info(variant, workspace)
                
        else:            
            
            variants = workspace.get_variants().exclude(auto_generated = False)
            
            resp = {'variants':[]}
            for variant in variants:
                info = self.get_info(variant, workspace)
                resp['variants'].append(info)
#                try:
#                    info = self.get_info(variant, workspace)
#                    variant_id = info.pop('id')
#                    resp['variants'][variant_id] = info
#                except Exception,  ex:
#                    logger.exception(ex)
        
        return HttpResponse(simplejson.dumps(resp))


    
    
    @exception_handler
    @api_key_required
    def edit(self,  request, variant_id):
        """
        Allows to edit a variant
        
        @param variant_id: id of the variant to edit.

        - Method: POST
        - parameters: depends on the type of the variant.video ad audio variants use presets, while image and doc ones do not.
        - Returns: empty string
        
        """
        
      
        media_type = request.POST.getlist('media_type')
        media_type = Type.objects.filter(name__in = media_type)
        variant = Variant.objects.get(pk = variant_id)
      
        name = request.POST.get('name')
        if name:
            variant.name = name
            
            
        caption = request.POST.get('caption')
        if caption:
            variant.caption = caption
        
        variant.save()    
        
        if media_type:
            variant.media_type = []
            variant.media_type.add(*media_type)
        
        return HttpResponse('')
        
    
    def _edit(self,  request, variant_id):
      
        variant = Variant.objects.get(pk = variant_id)        
        if not variant.auto_generated:
            raise ImportedVariant
            
     
        return HttpResponse('')
    

    @exception_handler
    @api_key_required
    def create(self,  request):
        """
        Allows to  create a  new variant   

        - method: POST
        - parameters: depends on the type of the variant.video ad audio variants use presets, while image and doc ones do not.
            - workspace_id: workspace to whom the new variant belongs
        - returns: json string containing information about the new variant. For example:
        {"workspace_id": 1, "id": 17, "caption": "test", "media_type": "image", "auto_generated": false, "name": "test"}

        """
        
        
        
        workspace_id = request.POST.get('workspace_id')
        name = request.POST.get('name')
        caption = request.POST.get('caption')
        media_type = request.POST.get('media_type')
        
    
        
        workspace = DAMWorkspace.objects.get(pk = workspace_id)
        
        arg_dict = {'workspace_id': workspace_id, 'name': name, 'caption': caption, 'media_type': media_type}
        for arg in arg_dict.keys():
            if  arg_dict[arg] is None:
                raise MissingArgs({arg: ['argument %s is missing'%arg]})
                    
        
             
        variant = Variant.objects.create(name = name, caption = caption,  auto_generated = True, workspace = workspace)
        variant.media_type.add(*Type.objects.filter(name__in = media_type))
        
                   
        resp = simplejson.dumps(self.get_info(variant,  workspace))
        logger.debug('resp %s'%resp)
        return HttpResponse(resp)
        


#    @exception_handler
#    @api_key_required
#    def upload_watermarking(self,  request):
#        """
#        Allows to get a valid watermarking uri. Once you get it, you first have to upload the resource, then you can edit or create a variant passing the watermarking uri and the its position.
#        Note that watermarking is available only for image a video resources (coming soon for doc ones)  
#        - method: POST
#        - parameters: 
#            - file_name: note that it must contain a valid extension, for example watermark.jpg
#            - fsize: dimension in bytes of the resource that will be used for watermarking
#        - returns: json formatted information for uploading a resource as watermarking
#         {"job_id": "e2f076bd89eac4f4397d5a89e0c32ef87f212158", "unique_key": "5bf3b0667a210bcafa4b38fa7f5453d75d0ae5ad", "ip": "127.0.0.1", "port": 10000, "chunk_size": 524288, "chunks": 1, "res_id": "c8230f4147cd45a55032405b5401a962ae42733c", "id": "d7faee99860c35f77e7c502bf47026c47d0cee10"}
#
#        """
#        file_name = request.POST.get('file_name')
#        fsize = request.POST.get('fsize')
#                
#        if not fsize:
#            raise MissingArgs({'args': ['no fsize passed']}) 
#        
#        if not file_name :
#            raise MissingArgs({'args': ['no file_name passed']}) 
#                
#        try:
#            ext = file_name.split('.')[1]
#        except:
#            raise ArgsValidationError({'args': ['invalid file_name, no valid extension found']})
#        
##         res_id = _new_md_id()
##         resp,  job_id = _get_upload_url(res_id,  fsize, ext)
#        
#        #TODO: replace _get_upload_url 
#        resp = []
#        
#        resp = simplejson.dumps(resp)
#        return HttpResponse(resp)
#        
#        

        


    @exception_handler
    @api_key_required
    def delete(self,  request, variant_id):
        """            
            @param variant_id: id of the variant to delete
            
            - Method: GET
                - No parameters
            
            - Returns:
                empty string
        """
        
        var =  Variant.objects.get(pk = variant_id)
        if  var.workspace:
            var.delete()	
        else:
            raise GlobalVariantDeletion
        
        return HttpResponse('')




class SmartFolderResource(ModResource):   
        
    def get_info(self, smart_folder):
                
        resp = {
            'id': smart_folder.pk, 
            'label': smart_folder.label,             
            'workspace_id': smart_folder.workspace.pk, 
            'and_condition': smart_folder.and_condition, 
            'queries': []
        }
        
        for node in smart_folder.nodes.all():
            resp['queries'].append({
                'id': node.pk, 
                'type': node.type, 
                'negated': SmartFolderNodeAssociation.objects.get(node = node, smart_folder = smart_folder).negated
            })
        
        return resp
        
    
    @exception_handler
    @api_key_required
    def read(self,  request,  sm_id):
        """ 
        """
    
        smart_folder = SmartFolder.objects.get(pk = sm_id)
        resp = self.get_info(smart_folder)
        return HttpResponse(simplejson.dumps(resp))

    @exception_handler
    @api_key_required
    def create(self,  request):
        """            
            - Method: POST
            - parameters:
                - workspace_id
                - label
                - and_condition: true for the intersection between queries, otherwise the union is used . Default is false.
                - queries: string in JSON format containing info (id and if the query is negated) about the queries of the smart folder to create. Example:{ id: 1,negated: false}                
            
            - Returns:
                {"and_condition": false, "workspace_id": 1, "id": 1, "label": "test"}
        """
                
        workspace_id = request.POST.get('workspace_id')
        workspace = DAMWorkspace.objects.get(pk = workspace_id)
        label = request.POST.get('label')
        queries = request.POST.get('queries')
        and_condition = request.POST.get('and_condition',  False)
        if  and_condition != 'true':
            and_condition = False
        
        if not workspace_id:
            raise MissingArgs({'args': ['no workspace id passed']})
        if not label:
            raise MissingArgs({'args': ['no label passed']})
        if not queries:
            raise MissingArgs({'args': ['no queries passed']})
        
        try:
            queries = simplejson.loads(queries)
        except:
            raise MalformedJSON
            
        sm = SmartFolder.objects.create(label = label,  workspace = workspace,  and_condition = and_condition)        
        for query in queries:            
            sm_ass = SmartFolderNodeAssociation.objects.create(smart_folder = sm,  node = Node.objects.get(pk = query['id']),  negated= query['negated'])
        
        resp = {'id': sm.pk,  'label': sm.label,  'workspace_id': sm.workspace.pk,  'and_condition': sm.and_condition}
        
        return HttpResponse(simplejson.dumps(resp))
        
        
    @exception_handler
    @api_key_required
    def delete(self,  request,  sm_id):
        """            
            @param sm_id: id of the smart folder to delete
            
            - Method: GET
                - No parameters
            
            - Returns:
                empty string
        """
        
        try:
            SmartFolder.objects.get(pk = sm_id) .delete()       
        except SmartFolder.DoesNotExist:
            raise SmartFolderDoesNotExist
        
        return HttpResponse('')

    @exception_handler
    @api_key_required
    def edit(self,  request,  sm_id):
        """            
            @param sm_id: id of the smart folder to edit
            
            - Method: POST
            - parameters:
                - label
                - and_condition: true for the intersection between queries, otherwise the union is used . Default is false.
                - queries: string in JSON format containing info (id and if the query is negated) about the queries of the smart folder to create. Example:{ id: 1,negated: false}                
            
            - Returns: empty string
               
        """
        
        try:
            sm = SmartFolder.objects.get(pk = sm_id)  
        except SmartFolder.DoesNotExist:
            raise SmartFolderDoesNotExist
            
        label = request.POST.get('label')
        queries = request.POST.get('queries')
        append_queries = request.POST.get('append_queries',  True)
        and_condition = request.POST.get('and_condition',  None)
        if and_condition is not None:
            sm.and_condition = simplejson.loads(and_condition)
        
        if label:
            sm.label = label
        if queries:
            if not append_queries:
                SmartFolderNodeAssociation.objects.all().delete()
            
            queries = simplejson.loads(queries)
            logger.debug('queries %s'%queries)
            
            for query in queries:            
                sm_ass, created = SmartFolderNodeAssociation.objects.get_or_create(smart_folder = sm,  node = Node.objects.get(pk = query['id']))
                sm_ass.negated = query['negated']
                sm_ass.save()
                
                
        
        sm.save()
        
        return HttpResponse('')

    @exception_handler
    @api_key_required
    def get_items(self,  request, sm_id):
        try:
            sm = SmartFolder.objects.get(pk = sm_id)  
        except SmartFolder.DoesNotExist:
            raise SmartFolderDoesNotExist
        
        workspace = sm.workspace
        items = Item.objects.filter(workspaces = workspace)
        new_post = request.POST.copy()
        new_post['query']= 'SmartFolders:"%s"'%sm.label
        request.POST = new_post
        items = _search(request.POST,  items, workspace = workspace).distinct()
        resp = {}
        resp['items'] = [i.pk for i in items.all()] 
        return HttpResponse(simplejson.dumps(resp))        

class ScriptResource(ModResource):  
    
    @exception_handler
    @api_key_required
    def create(self,  request):
       
        name = request.POST['name']
        description = request.POST['description']
        events = request.POST.getlist('events')
        params = request.POST.get('params')
        media_types = request.POST.getlist('media_types')
        workspace_id = request.POST.get('workspace_id')
        workspace = DAMWorkspace.objects.get(pk = workspace_id)        
        
        script  = _edit_script(None, name, params, workspace, media_types, events)
        return HttpResponse(simplejson.dumps({'id': script.pk,  'name': script.name,  'description': description}))
        
        
    @exception_handler
    @api_key_required
    def edit(self,  request,  script_id):
        name = request.POST['name']
        description = request.POST['description']
        params = request.POST['params']
        events = request.POST.getlist('events')
        media_types = request.POST.getlist('media_types')
        script = Pipeline.objects.get(pk = script_id)
        workspace = script.workspace        
        
        script  = _edit_script(script_id, name, params, workspace, media_types, events)
        return HttpResponse('')
        
    @exception_handler
    @api_key_required
    def run(self,  request,  script_id):
        from scripts.views import _run_script
       
        items = request.POST.getlist('items')
        logger.debug('items %s'%items)
        script = Pipeline.objects.get(pk = script_id)
        items = Item.objects.filter(pk__in = items)
        logger.debug('items %s'%items)
        user_id = request.POST['user_id']
        user = User.objects.get(pk = user_id)
        
        _run_script(script, user, script.workspace, items ,   False )
        return HttpResponse('')
    
    @exception_handler
    @api_key_required
    def run_again(self,  request,  script_id):
        from scripts.views import _run_script
        script = Pipeline.objects.get(pk = script_id)        
        _run_script(script, [] ,   True )
        return HttpResponse('')

    @exception_handler
    @api_key_required
    def delete(self,  request,  script_id):
        script = Pipeline.objects.get(pk = script_id)
        script.delete()
        
        return HttpResponse('')

    @exception_handler
    @api_key_required
    def read(self,  request,  script_id):
        script = Pipeline.objects.get(pk = script_id)
        info = _get_scripts_info(script)
        return HttpResponse(simplejson.dumps(info))

        
class StateResource(ModResource):  
    @exception_handler
    @api_key_required   
    def delete(self,  request,  state_id):
        state = State.objects.get(pk = state_id)
        workspace = state.workspace
        user_id = request.POST.get('user_id')
        _check_app_permissions(workspace,  user_id,  ['admin', 'set_state'])
        
        state.delete()
        return HttpResponse('')
    
    
    @exception_handler
    @api_key_required   
    def create(self,  request):
        from django.db import IntegrityError
        try:
            workspace_id = request.POST['workspace_id']
        except:
            raise MissingArgs({'args': ['no workspace_id passed']})
        workspace = DAMWorkspace.objects.get(pk = workspace_id)
        try: 
            name = request.POST['name']
        except:
            raise MissingArgs({'args': ['no state name passed']})
        
        user_id = request.POST.get('user_id')
        _check_app_permissions(workspace,  user_id,  ['admin', 'set_state'])
        try:
            state = State.objects.create(workspace = workspace, name = name)
        except IntegrityError:
            raise IntegrityError('a state named %s already exist'%(name))
            
        resp = json.dumps({'pk': state.pk, 'name': state.name})
        return HttpResponse(resp)
    
    @exception_handler
    @api_key_required   
    def edit(self,  request, state_id):
        from django.db import IntegrityError
        
        try: 
            name = request.POST['name']
        except:
            raise MissingArgs({'args': ['no state name passed']})
        
        state = State.objects.get(pk = state_id)
        workspace = state.workspace
        user_id = request.POST.get('user_id')
        _check_app_permissions(workspace,  user_id,  ['admin', 'set_state'])
        try:
            state.name = name
            state.save()
        except IntegrityError:
            raise IntegrityError('a state named %s already exist'%(name))
            
        return HttpResponse('')
    
    @exception_handler
    @api_key_required   
    def read(self,  request,  state_id):
        
        state = State.objects.get(pk = state_id)
        
        resp = {'id':state.pk, 'name':state.name, 'items':[sa.item.pk for sa in state.stateitemassociation_set.all()]}
            
        json_resp = json.dumps(resp)        
        return HttpResponse(json_resp)
    
    @exception_handler
    @api_key_required   
    def add_items(self,  request,  state_id):
        state = State.objects.get(pk = state_id)
        items = request.POST.getlist('items')
        items = Item.objects.filter(pk__in = items)
        _set_state(items, state)
                
        return HttpResponse('')
    
    @exception_handler
    @api_key_required   
    def remove_items(self,  request,  state_id):
        state = State.objects.get(pk = state_id)
        items = request.POST.getlist('items')
        workspace = state.workspace
        user_id = request.POST.get('user_id')
        _check_app_permissions(workspace,  user_id,  ['admin', 'set_state'])
        StateItemAssociation.objects.filter(item__pk__in = items, state = state).delete()
        return HttpResponse('')
        
    
