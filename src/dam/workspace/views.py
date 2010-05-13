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

from django.utils.encoding import smart_str
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader,  Template
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic.simple import redirect_to

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.contrib.auth.models import User
from django.utils import simplejson
from dam.basket.views import __inbasket
from dam.basket.models import Basket
from dam.repository.models import Item, Component
from dam.workspace.decorators import permission_required, membership_required
from dam.treeview import views as treeview
from dam.treeview.models import Node,  Category,  SmartFolder
from dam.workspace.models import Workspace, WorkSpacePermission, WorkspacePermissionsGroup, WorkSpacePermissionAssociation
from dam.variants.models import Variant      
from dam.upload.views import generate_tasks
from dam.application.views import get_component_url
from dam.workspace.forms import AdminWorkspaceForm, AdminWorkspaceGroupsForm, AddMembersForm, AddMembersToGroupForm, SetPermissionsForm, SetGroupsForm
from dam.framework.dam_repository.models import Type
from dam.geo_features.models import GeoInfo
from dam.batch_processor.models import MachineState, Machine
from dam.settings import GOOGLE_KEY, ROOT_PATH, DATABASE_ENGINE
from dam.application.views import NOTAVAILABLE
from dam.preferences.models import DAMComponentSetting
from dam.preferences.views import get_user_setting, get_user_setting_by_level
from dam.metadata.models import MetadataProperty
from dam.metadata.views import get_metadata_default_language
from dam.scripts.models import variant_generation_pipeline, Script
from dam.eventmanager.models import Event, EventRegistration

from django.utils.datastructures import SortedDict

import logger
import time
import operator
import re

from operator import and_, or_
import cPickle as pickle
import os.path
from settings import INSTALLATIONPATH, THUMBS_DIR, SERVER_PUBLIC_ADDRESS

#for django admin
#def admin_edit_user(request,  object_id):
#    return mod_admin_views.change_stage(request, 'auth', 'user',  object_id )
#
##for django admin
#def admin_edit_ws_group(request,  ):
#    return mod_admin_views.change_stage_ws_group(request, 'auth', 'user',  object_id )

#for django admin
@login_required
def get_ws_permissions(request,  user_id, workspace_id ): 
    wsp = WorkSpacePermission.objects.filter(workspacepermissionassociation__workspace__pk =  workspace_id, workspacepermissionassociation__users__pk = user_id)    
    return render_to_response('option_permission.html', RequestContext(request,{'permissions' : wsp}))

#for django admin
@login_required
def get_available_permissions(request,  user_id, workspace_id ):   
    wsp = WorkSpacePermission.objects.filter().exclude(workspacepermissionassociation__users__pk = user_id, workspacepermissionassociation__workspace__pk =  workspace_id,)  
    return render_to_response('option_permission.html', RequestContext(request,{'permissions' : wsp}))

@login_required
def is_workspace_member(request,  user_id, workspace_id ):   
    ws = Workspace.objects.get(pk = workspace_id)   
    try:
        result = ws.members.all().filter(pk = user_id).count() 
    except Exception,  ex:
        raise ex
    return HttpResponse(result)
    
#for django admin
@login_required
def get_groups(request,  user_id,  workspace_id ):
    user = User.objects.get(pk = user_id)
    f = forms.Form()
    ws_groups = forms.ModelMultipleChoiceField(queryset = WorkspacePermissionsGroup.objects.filter(workspace__pk = workspace_id),  initial = [perm.pk for perm in  WorkspacePermissionsGroup.objects.filter(users = user,  workspace__pk = workspace_id)])    
    ws_groups.widget.attrs  ={'id':'ws_groups',  'class':'vSelectMultipleField',}
    f.fields['ws_groups'] = ws_groups
    plus = '<a onclick="return showAddAnotherPopup(this);" id="add_ws_groups" class="add-another" href="../../../workspace/workspacepermissionsgroup/add/"> <img width="10" height="10" alt="Add Another" src="/media/img/admin/icon_addlink.gif"/></a>'
    return HttpResponse(str(f['ws_groups']) + plus)


@login_required
def update_available_workspaces(request, user_id,   name):    
    ws = Workspace.objects.get(name = name)
    d = {'id':ws.pk,  'name':ws.name}
    result = ws.members.all().filter(pk = user_id).count() 
    member = ''
    if result > 0:
        member = 'member:1'
    return HttpResponse('{name:"%s", id:%s, %s }'%(ws.name, ws.pk,  member) )

@login_required
def get_members(request,):
    try:
        ws_id = request.POST.get('ws_id')
        group_id = request.POST.get('group_id')
        ws = Workspace.objects.get(pk  = ws_id)
        members = ws.members.all()
        if group_id != None:
            group =  WorkspacePermissionsGroup.objects.get(pk = group_id)
            users = group.users.all()
            for member in members:
                if member in users:
                    member.selected = True
    except Exception,  ex:
            raise ex
    return render_to_response('option_permission.html', RequestContext(request,{'permissions' : members}))
    
#for django admin
@login_required
def get_user_ws_permissions(request, user_id,  workspace_id):   
    all_perm = WorkSpacePermission.objects.all()
    wsp = WorkSpacePermission.objects.filter(workspacepermissionassociation__workspace__pk =  workspace_id, workspacepermissionassociation__users__pk = user_id)    
    for perm in all_perm:
        if perm in wsp:
            perm.selected = True    
    return render_to_response('option_permission.html', RequestContext(request,{'permissions' : all_perm}))

#for django admin
@login_required    
def get_group_permissions(request, ):
    group_ids =request.POST.getlist('group_ids')
    perm =  WorkSpacePermission.objects.filter(workspacepermissionsgroup__pk__in = group_ids).distinct()   
    return render_to_response('option_permission.html', RequestContext(request,{'permissions' : perm}))

#for django admin
@login_required
def get_user_ws_groups(request, user_id,  workspace_id):   
    all_groups = WorkspacePermissionsGroup.objects.filter(workspace__pk = workspace_id)
    user = User.objects.get(pk = user_id)
    user_groups = user.workspacepermissionsgroup_set.all().filter(workspace__pk = workspace_id)
    for group  in all_groups:
        if group in user_groups:
            group.selected = True
    return render_to_response('option_permission.html', RequestContext(request,{'permissions' : all_groups}))

@login_required    
@permission_required('admin', False)
def admin_workspace_get_groups_count(request,  ws_id):
    ws = Workspace.objects.get(pk = ws_id)
    n_groups = ws.workspacepermissionsgroup_set.all().count()
    return HttpResponse(str(n_groups))
    
@login_required 
@permission_required('admin', False)
def admin_workspace(request,  ws_id):
    ws = Workspace.objects.get(pk = ws_id)
    return _admin_workspace(request,  ws)

def _create_workspace(ws, user):
    ws.creator = user 
    ws.save() 
    
    wspa = WorkSpacePermissionAssociation.objects.get_or_create(workspace = ws, permission = WorkSpacePermission.objects.get(name='admin'))[0]
    wspa.users.add(user)
    ws.members.add(user)
    image = Type.objects.get(name = 'image')
    movie = Type.objects.get(name = 'movie')
    audio = Type.objects.get(name = 'audio')
#    global_variants = Variant.objects.filter(is_global = True,  )
    
    
    try:
        
        global_scripts = Script.objects.filter(is_global = True)
        upload = Event.objects.get(name = 'upload')
        for glob_script in global_scripts:
            script = Script.objects.create(name = glob_script.name, description = glob_script.description, pipeline = glob_script.pipeline, workspace = ws )
            EventRegistration.objects.create(event = upload, listener = script, workspace = ws)
        
        logger.debug('workspace: %s'%ws)
        logger.debug('workspace.name %s'%ws.name)
        logger.debug('workspace.pk %s'%ws.pk)
        root = Node.objects.create(label = 'root', depth = 0,  workspace = ws,  editable = False,  type = 'keyword',  cls = 'keyword')
        col_root = Node.objects.create(label = 'root', depth = 0,  workspace = ws,  editable = False,  type = 'collection')
        inbox_root = Node.objects.create(label = 'root', depth = 0,  workspace = ws,  editable = False,  type = 'inbox')
        uploaded = Node.objects.create(parent = inbox_root, depth = 1, label = 'Uploaded', workspace = ws, editable = False,  type = 'inbox')
        imported = Node.objects.create(parent = inbox_root, depth = 1, label = 'Imported', workspace = ws, editable = False, type = 'inbox')

        for cat in Category.objects.all():
            Node.objects.create(workspace = ws, label = cat.label, depth = 1, type = root.type, parent = root,  is_drop_target = cat.is_drop_target,  is_draggable = cat.is_draggable,  editable = cat.editable,  cls = cat.cls)
#        return render_to_response('test_refactoring.html', RequestContext(request,{'ws':ws,  'keywords_root': keywords_root}))
    except Exception,  ex:
        logger.exception(ex)
        raise ex
    
    
    
    return ws

@login_required 
def create_workspace(request):
    user = User.objects.get(pk=request.session['_auth_user_id'])
    if not user.has_perm('workspace.add_workspace'):
        resp = simplejson.dumps({'failure': True})
        return HttpResponse(resp)
    else: 
    	return _admin_workspace(request,  None)

def _admin_workspace(request,  ws):
    user = User.objects.get(pk=request.session['_auth_user_id'])    
    logger.debug('ws %s'%ws)
    if ws == None:
        ws = Workspace()

    
    form = AdminWorkspaceForm(ws, request.POST)
    logger.debug(request.POST)
    if form.is_valid():
        name = form.cleaned_data['name']
        description = form.cleaned_data['description']
        logger.debug('form.cleaned_data %s'%form.cleaned_data)
        ws.name = name 
        ws.description = description             
        
        if ws.pk == None:
#                orig = Variant.objects.get(name = 'original',  is_global = True)
#                ws.default_source_variant = orig
            ws.save()                           
            ws = _create_workspace(ws, user)            
        else:
            ws.save()           
        
        resp = simplejson.dumps({'success': True,  'ws_id':ws.pk})
    else:
        logger.debug('form invalid')
        logged.debug(form._errors)        
        resp = simplejson.dumps({'failure': True})

#            TODO: form invalid

    
    return HttpResponse(resp)
#    else:
#        
#        form = AdminWorkspaceForm(ws)
#    return render_to_response('admin/workspace/general.html', RequestContext(request,{'form': form, 'ws':ws,  'type':'general'}))

@login_required
@permission_required('admin',  False)
def admin_workspace_groups(request, ws_id):
    ws = Workspace.objects.get(pk = ws_id)
    groups =  ws.workspacepermissionsgroup_set.all()
    return render_to_response('admin/workspace/group_list.html', RequestContext(request,{'groups':groups, 'ws':ws,  'type': 'groups',  }))

@login_required
@permission_required('admin',  False)
def admin_workspace_add_groups(request, ws_id,  group_id = None):    
    
    """
    It allows to add a permission group to a workspace
    @param ws_id: the id 
    """
    
    ws = Workspace.objects.get(pk=ws_id)
    if group_id:
        group = WorkspacePermissionsGroup.objects.get(pk = group_id)
    else:
        group = WorkspacePermissionsGroup()
    if request.method == 'POST':
        
        if request.POST.get('cmd') == 'delete':
            group.delete()
            return HttpResponseRedirect('/admin_workspace_permissions/groups/%s/'%ws_id)
        else:          
            form = AdminWorkspaceGroupsForm(ws, group,   request.POST)
            context = {'form': form, 'ws':ws,  'group':group,  'type':'groups' , }
            members_id = request.POST.getlist('members')
            members = User.objects.filter(pk__in = members_id)
            if form.is_valid():
                
                name = form.cleaned_data['name']
                permissions = form.cleaned_data['permissions']
                group.name = name
                group.workspace = ws
                group.save()
                group.permissions.remove(*group.permissions.all())
                group.permissions.add(*permissions)
                group.users.remove(*group.users.all())
                group.users.add(*members)
                ws.members.add(*members)
                context['members'] = group.users.all()
                return HttpResponseRedirect('/admin_workspace_get_groups/%s/'%ws.pk)
            else:
                context['members'] = members
                return render_to_response('admin/workspace/group.html', RequestContext(request, context))
            
    else:
        form = AdminWorkspaceGroupsForm(ws,  group)
        
    
    context = {'form': form, 'ws':ws,  'group':group,  'type':'groups' ,  }
    if group_id:
        context['members'] =group.users.all()
    return render_to_response('admin/workspace/group.html', RequestContext(request, context))

def admin_workspace_check_current_user_admin(request,  ws):    
   
    """
    Internal function for checking that the current user maintains the admin permission    
    """
    
    user = User.objects.get(pk = request.session['_auth_user_id'] )

    logger.debug('ws.pk %s'%ws.pk)
    admin = WorkSpacePermission.objects.get(codename = 'admin')
    perm = user.workspacepermissionassociation_set.filter(permission = admin, workspace = ws)
    groups =  user.workspacepermissionsgroup_set.filter(permissions = admin,  workspace = ws)
    logger.debug('perm.count() %s '%perm.count())
    logger.debug('groups.count() %s '%groups.count())
    
    if perm.count() == 0 and groups.count() == 0:
        try:
            wspa,  created =  WorkSpacePermissionAssociation.objects.get_or_create(permission = admin,  workspace = ws)
            wspa.users.add(user)
        except Exception, ex:
            logger.exception('ex in adding admin permission to the current user: %s'%  ex)
    

@login_required
@permission_required('admin',  False)
def admin_workspace_permissions(request, type,  ws_id):
    
    """
    Main  view for editing workspace members permissions.
    @type: a string that can assume two values, 'members' or 'groups'
    @params ws_id: the id of the workspace to edit     
    """
    
    ws = Workspace.objects.get(pk=ws_id)
   
    if type == 'members':
        members = ws.members.all()
        form = AddMembersForm(ws)
        for member in members:
            member.perm_groups  = member.workspacepermissionsgroup_set.all().filter(workspace = ws)
        
        return render_to_response('admin/workspace/permissions.html', RequestContext(request,{'members':members, 'ws':ws,  'type':type,'form':form  }))
        
    elif type == 'groups':
        groups =  ws.workspacepermissionsgroup_set.all()
        return render_to_response('admin/workspace/permissions.html', RequestContext(request,{'groups':groups, 'ws':ws,  'type': type,  }))
    else:
        raise Exception('invalid type %s' %type)

@login_required
@permission_required('admin',  False)
def admin_workspace_add_members(request, ws_id):
    
    """
    It allows to add  members to a workspace. Members area passed via POST.
    @params ws_id: the id of the workspace to edit
    """

    ws = Workspace.objects.get(pk=ws_id)
    div = 'member_list'
    if request.method == 'POST':
        form = AddMembersForm(ws,  request.POST)
        if form.is_valid():
            members_id = request.POST.getlist('members_to_add')         
            members = User.objects.filter(pk__in = members_id) 
            ws.members.add(*members)
        
        members = ws.members.all()
        form = AddMembersForm(ws)
        for member in members:
            member.perm_groups  = member.workspacepermissionsgroup_set.all().filter(workspace = ws)        

        return render_to_response('admin/workspace/member_list.html', RequestContext(request,{'members': members,  'form':form,  'ws': ws}))
        
    else:
        form = AddMembersForm(ws,)
        
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form,  'form_id': 'form_add',  'form_action': '/admin_workspace_add_members/',  'div':'member_list',  'notfieldset':1}))
        
@login_required
@permission_required('admin',  False)
def admin_workspace_add_members_to_group(request, ws_id, group_id = None ):
    
    """
    It allows to add members to a permission group    
    @param ws_id: the id of the workspace to edit
    @param group_id: the id of the group to whom members will be added. It is None when the group is being created
    """
    
    ws = Workspace.objects.get(pk=ws_id)
    div = 'member_list'
    if group_id:
        group = WorkspacePermissionsGroup.objects.get(pk = group_id)
    else:
        group = None
    form = AddMembersToGroupForm(group)
    
    return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'button_function':'add_user_to_group()',  'button_value':'add',  'notfieldset':1  }))
 
@login_required
@permission_required('admin',  False)
def admin_workspace_remove_members(request,  ws_id):
    
    """
    It allows to remove members from a workspace. Members area passed via POST.
    @params ws_id: the id of the workspace to edit
    """
    
    ws = Workspace.objects.get(pk = ws_id)
    user_pk = request.session['_auth_user_id']
   
    members_id = request.POST.getlist('members')
    members = User.objects.filter(pk__in = members_id).exclude(pk = user_pk)        
    ws.members.remove(*members)      
    wspas = WorkSpacePermissionAssociation.objects.filter(workspace = ws, users__pk__in = members_id)
    for wspa in wspas:
        wspa.users.remove(*members)
    for group in ws.workspacepermissionsgroup_set.filter(users__pk__in = members_id):
        group.users.remove(*members)
        
    members = ws.members.all()
    form = AddMembersForm(ws)
    for member in members:
        member.perm_groups  = member.workspacepermissionsgroup_set.all().filter(workspace = ws)        
    
    return render_to_response('admin/workspace/member_list.html', RequestContext(request,{'members': members,  'form':form}))

@login_required
@permission_required('admin',  False)
def admin_workspace_remove_user_from_groups(request, ws_id):
    ws = Workspace.objects.get(pk = ws_id)
    user_pk = request.POST.get('member_pk')
    group_pk = request.POST.get('group_pk')
    user = User.objects.get(pk = user_pk)
    group = WorkspacePermissionsGroup.objects.get(pk = group_pk)
    group.users.remove(user)
    admin_workspace_check_current_user_admin(request,  ws)
    return HttpResponse('ok')
        
@login_required
@permission_required('admin',  False)
def admin_workspace_remove_groups(request, ws_id):
    ws = Workspace.objects.get(pk = ws_id)   
    groups_id = request.POST.getlist('groups')
    groups = WorkspacePermissionsGroup.objects.filter(pk__in = groups_id)
    groups.delete()
    
    return HttpResponseRedirect('/admin_workspace_get_groups/%s/'%ws_id)
     
def _admin_workspace_set_permissions_users(request, ws_id,  user_id):
    ws = Workspace.objects.get(pk = ws_id)
    type = 'users'
    if user_id:
        form_action = '/admin_workspace_set_permissions/%s/%s/'%(type, user_id)
            
    else:
        form_action = '/admin_workspace_set_permissions/%s/%s/'%(  ws_id,  type)
    
    if request.method == 'POST':
        if user_id:
                members_id = [user_id]
        else:
            members_id = request.POST.getlist('members',)
            
        members = ws.members.filter(pk__in =members_id)
            
        if request.POST.has_key('onshow'):
            if user_id:
                initial = [wspa.permission.pk  for wspa in User.objects.get(pk = user_id).workspacepermissionassociation_set.filter(workspace = ws)]            
            else:
                initial = [wspa.permission.pk  for wspa in WorkSpacePermissionAssociation.objects.filter(workspace = ws,  users__in = members)]
                
                initial_to_disable  = []
                if members.count() > 1:
                
                    for wspa in WorkSpacePermissionAssociation.objects.filter(workspace = ws,  users__in = members):
                        if wspa.users.filter(pk__in = members_id).count()  < members.count():
                            initial_to_disable.append(wspa.permission.pk  )

            form = SetPermissionsForm(ws, initial = {'permissions':  initial,  'remove': 'true',  'hidden': initial_to_disable})
            
            return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'id_form_permissions': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id }))
            
        form = SetPermissionsForm(ws,  request.POST)
        if form.is_valid():
            permissions = form.cleaned_data['permissions']
            permission_one_at_least = form.cleaned_data['hidden']
            
            if request.POST.get('remove',  'false') == 'true':
                for member in members:
                    member.workspacepermissionassociation_set.remove(*member.workspacepermissionassociation_set.filter(workspace = ws).exclude(permission__in = permission_one_at_least))
                    
            for perm in permissions:     
                wspa,  created = WorkSpacePermissionAssociation.objects.get_or_create(permission = perm,  workspace = ws )
                wspa.users.add(*members)
            admin_workspace_check_current_user_admin(request,  ws)
            
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'form_id': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id  }))
    else:
       
        form = SetPermissionsForm(ws, initial = {'remove': 'true'})
            
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'id_form_permissions': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id }))
        
def _admin_workspace_set_permissions_groups(request, ws_id,  user_id):
    ws = Workspace.objects.get(pk = ws_id)
    type = 'groups'
    if user_id:
        form_action = '/admin_workspace_set_permissions/%s/%s/'%(type, user_id)
            
    else:
        form_action = '/admin_workspace_set_permissions/%s/%s/'%(type,  ws_id)
    
    if request.method == 'POST':
        form = SetPermissionsForm(ws,  request.POST)
        
        if user_id:
            members_id = [user_id]
        else:
            members_id = request.POST.getlist('groups',)
        
        groups = ws.workspacepermissionsgroup_set.all().filter(pk__in =members_id)       
        if request.POST.has_key('onshow'):
            initial = [permission.pk  for permission in  WorkSpacePermission.objects.filter(workspacepermissionsgroup__in = groups)]
            initial_to_disable  = []
            if groups.count() > 1:                
                    for permission in  WorkSpacePermission.objects.filter(workspacepermissionsgroup__in = groups):
                        if permission.workspacepermissionsgroup_set.all().count()  < groups.count():
                            initial_to_disable.append(permission.pk )
            form = SetPermissionsForm(ws, initial = {'permissions':  initial,  'remove': 'true',  'hidden': initial_to_disable})
                
            return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'id_form_permissions': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id }))
            
        form = SetPermissionsForm(ws,  request.POST)
        if form.is_valid():
            permissions = form.cleaned_data['permissions']
            permission_one_at_least = form.cleaned_data['hidden']         
            
            for group in groups:
                if request.POST.get('remove',  'false') == 'true':
                    
                    group.permissions.remove(*group.permissions.all().exclude(pk__in = [perm.pk for perm in permission_one_at_least]))
                
                group.permissions.add(*permissions)
            admin_workspace_check_current_user_admin(request,  ws)                
                
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'form_id': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id  }))
    else:       
        form = SetPermissionsForm(ws, initial = {'remove': 'true'})
        
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'id_form_permissions': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id }))
        
@login_required
@permission_required('admin',  False)
def admin_workspace_set_permissions(request,  ws_id,   type = 'users', ):
    
    if type == 'users':
        return _admin_workspace_set_permissions_users(request,  ws_id,  None)
    elif type == 'groups':
        return _admin_workspace_set_permissions_groups(request,  ws_id,  None)
    else:
        raise Exception('unknown type, must be users or groups')
        
@login_required
@permission_required('admin',  False)
def admin_workspace_set_groups(request, ws_id,  user_id = None):
    ws = Workspace.objects.get(pk = ws_id)

    if user_id:
        form_action = '/admin_workspace_set_groups/%s/'%user_id
        members_id = [user_id]
            
    else:
        form_action = '/admin_workspace_set_groups/'
        members_id = request.POST.getlist('members',)
    
    members = ws.members.filter(pk__in =members_id)
    
    if request.method == 'POST':
        if request.POST.has_key('onshow'):
            
            initial = [group.pk  for group in WorkspacePermissionsGroup.objects.filter(workspace = ws,  users__in = members)]
            
            initial_to_disable  = []
            if members.count() > 1:
            
                for group in WorkspacePermissionsGroup.objects.filter(workspace = ws,  users__in = members):
                    if group.users.filter(pk__in = members_id).count()  < members.count():
                        initial_to_disable.append(group.pk )

            form = SetGroupsForm(ws, initial = {'groups':  initial,  'remove': 'true',  'hidden': initial_to_disable})
            
            return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'id_form_permissions': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id }))
            
        form = SetGroupsForm(ws, request.POST)
        if form.is_valid():
            if user_id:
                members_id = [user_id]
            else:
                members_id = request.POST.getlist('members',)            
            
            members = ws.members.filter(pk__in =members_id)
            group_one_at_least = form.cleaned_data['hidden']
            groups = form.cleaned_data['groups']
            
            for member in members:
                if request.POST.get('remove',  'false') == 'true':               
                    member.workspacepermissionsgroup_set.remove(*member.workspacepermissionsgroup_set.all().filter(workspace = ws).exclude(pk__in = [g.pk for g in group_one_at_least]))                
                
                member.workspacepermissionsgroup_set.add(*groups)
        admin_workspace_check_current_user_admin(request,  ws)
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'form_id': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id  }))
    else:
        
        if ws.workspacepermissionsgroup_set.all().count() == 0:
            return HttpResponse('No groups avaialable.Click <a href="/admin_workspace_groups/3/add/">here</a> to create one.')
        
        if user_id:
            user = User.objects.get(pk = user_id)
            initial = [group.pk for group in user.workspacepermissionsgroup_set.all().filter(workspace = ws)]
            
        else:
            initial = []
        form = SetGroupsForm(ws,   initial = {'groups':  initial})
        
        return render_to_response('admin/workspace/add_form.html', RequestContext(request,{'form':form, 'id_form_permissions': 'id_form_permissions',  'form_action': form_action, 'user_id': user_id }))



def _add_items_to_ws(item, ws, current_ws, remove = 'false' ):
    if ws not in item.workspaces.all():             
        media_type = Type.objects.get(name = item.type.name)
        item.workspaces.add(ws)
        
#                components = item.component_set.all().filter(Q(variant__auto_generated= False, variant__is_global = True) | Q(imported = True) | Q(variant__shared = True),  workspace = current_ws)
        components = item.component_set.all().filter(variant__is_global = True, workspace = current_ws)
        logger.debug('components %s' %components)
        
        for comp in components:
            
            if not comp.variant.auto_generated:
                logger.debug('not generated, comp.variant %s' %comp.variant)
                comp.workspace.add(ws)
            
#                    elif comp.variant.shared:
#                        logger.debug('shared %s'%comp.variant)
#                        new_comp = Component.objects.create(variant = comp.variant,  item = item,  _id = comp.ID)
#                        new_comp.workspace.add(ws)
            
            elif comp.imported:
                new_comp = Component.objects.create(variant = comp.variant,  item = item,  _id = comp.ID,  imported = True)
#                    else:
#                        new_comp = Component.objects.create(variant = comp.variant,  item = item, _id = comp.ID )
#                        new_comp.workspace.add(ws)
#                        new_comp.preferences = comp.preferences
#                        new_comp.source_id = comp.source_id
#                        new_comp.save()
            
            
#                    default_source_variant = comp.variant.get_source
        ws_variants = Variant.objects.filter(Q(workspace = ws) | Q(is_global = True),  auto_generated = True,  media_type = item.type)
        logger.debug('ws_variants %s'%ws_variants)
        
#                logger.debug('item.component_set.filter(workspace = ws)[0].variant.pk %s' %item.component_set.filter(workspace = ws)[0].variant.pk)
        for variant in ws_variants:
            logger.debug('variant %s'%variant)
            if item.component_set.filter(variant = variant, workspace = ws).count() == 0: #if component for variant has not been created yet
                
                
                comps = item.component_set.filter(variant = variant, workspace = current_ws) 
                if comps.count() > 0: #if variant exists in the current ws
                    comp = comps[0]
#                    new_comp = _create_variant(variant,  item, ws)
#                    new_comp._id = comp._id
#                    new_comp.save()

#                    new_comp = Component.objects.create(variant = variant,  item = item,  _id = comp._id)
                    new_comp = Component.objects.create(variant = variant,  item = item,  _id = comp._id)
#                        new_comp.preferences = comp.preferences
#                        new_comp.source_id = comp.source_id

                else:
                    new_comp = Component.objects.create(variant = variant,  item = item,  )
#                    new_comp = _create_variant(variant,  item, ws)
                    
                    
                new_comp.workspace.add(ws)                        
#               TODO: event for upload scripts
#                generate_tasks(variant,  ws,  item,  check_for_existing = True)
        
        return True
    
    return False
        
        
    

@login_required
@permission_required('add_item', False)
def add_items_to_ws(request):   
    try:
        item_ids = request.POST.getlist('item_id')
        items_commas = item_ids[0].split(',')

        if len(items_commas) > 1:
            item_ids = items_commas

        ws_id = request.POST.get('ws_id')
        ws = Workspace.objects.get(pk = ws_id)
#        current_ws_id = request.POST.get('current_ws_id')
#        current_ws = Workspace.objects.get(pk = current_ws_id )
        current_ws = request.session['workspace']
        remove = request.POST.get('remove')
        move_public = request.POST.get('move_public', 'false')
        items = Item.objects.filter(pk__in = item_ids)
        logger.debug(items)
        
        item_imported = []
        
        for item in items:
            added = _add_items_to_ws(item, ws, current_ws,remove)
            if added:
                item_imported.append(item)
        
        if remove == 'true':
            _remove_items(request, items)
                
        if len(item_imported) > 0:
            imported = Node.objects.get(depth = 1,  label = 'Imported',  type = 'inbox',  workspace = ws)
            time_imported = time.strftime("%Y-%m-%d", time.gmtime())
            node = Node.objects.get_or_create(label = time_imported,  type = 'inbox',  parent = imported,  workspace = ws,  depth = 2)[0]
            
            node.items.add(*item_imported)
                
        resp = simplejson.dumps({'success': True, 'errors': []})

        return HttpResponse(resp)
    except Exception,  ex:
        import traceback
        raise ex

@permission_required('remove_item')
def _remove_items(request, items):
    current_ws = request.session.get('workspace')
    logger.debug('current_ws %s'%current_ws)
    for item in items:
        
        try:
            logger.debug('item.pk %s'%item.pk)
            
            inbox_nodes = Node.objects.filter(type = 'inbox', workspace = current_ws, items = item) #just to be sure, filter instead of get
            for inbox_node in inbox_nodes:
                inbox_node.items.remove(item)                
                if inbox_node.items.all().count() == 0:
                    inbox_node.delete()
                
        except Exception, ex:
            logger.exception(ex)
            raise ex
        
        
        item.workspaces.remove(current_ws)
        item.component_set.all().filter(workspace = current_ws).exclude(Q(variant__is_global= True,  variant__auto_generated = False)| Q(variant__shared = True)).delete()
        
        
         

@login_required
def remove_item(request,  item,):
    current_ws = request.session.get('workspace')
    item.workspaces.remove(current_ws)
    item.component_set.all().filter(workspace = current_ws).exclude(variant__variant_name = 'original').exclude(variant__variant_name = 'thumbnail').delete()

@login_required
@permission_required('admin')
def delete_ws(request,  ws_id):
    ws = Workspace.objects.get(pk = ws_id)
    user = User.objects.get(pk=request.session['_auth_user_id'])
    ws.delete()
#    ws_redirect = Workspace.objects.all()[0]
    return HttpResponse(simplejson.dumps({'success': True}))
    

@login_required
def get_workspaces(request):
    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        wss = Workspace.objects.filter(members = user).order_by('name').distinct()
        
#        wss = list(wss)
        resp = {'workspaces': []}
        for ws in wss:
                        
            root = Node.objects.get(workspace = ws,  depth=0,  type = 'keyword')
            collection_root = Node.objects.get(workspace  = ws,  depth=0,  type = 'collection')
            inbox_root = Node.objects.get(workspace = ws,  depth=0,  type = 'inbox')
            
            
            tmp = {
                'pk': ws.pk,
                'name': ws.name,
                'description': ws.description,
#                'media_type': media_types_selected,
                'root_id': root.pk,
                'collections_root_id': collection_root.pk,
                'inbox_root_id':inbox_root.pk
            }
            
            default_media_types_selected = ['image', 'video', 'audio', 'doc']
           
            if request.session.__contains__('media_type'):  
                              
                if not request.session['media_type'].__contains__(ws.pk):
                    request.session['media_type'][ws.pk] = default_media_types_selected  
                                                  
            else:                
                request.session['media_type'] = {ws.pk: default_media_types_selected}  
            
            request.session.modified = True
            media_types_selected = request.session['media_type'][ws.pk]                  
            
#            media_types_selected = ['image', 'video', 'audio', 'doc']
            logger.debug('media_types_selected %s'%media_types_selected)
            tmp['media_type'] = media_types_selected
            
            resp['workspaces'].append(tmp)
            
        resp = simplejson.dumps(resp)
        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

def _search_complex_query(complex_query,  items):
    
    logger.debug('items %s'%items)
    if complex_query['condition'] == 'and':
        for node_id in complex_query['nodes']:
            node = Node.objects.get(pk = node_id['id'])
            if node_id['negated']:
                items = items.exclude(node = node)
                
            else:
#                items= items.filter(node = node)
                items = items.filter(node__in = node.get_branch())
            logger.debug('items %s'%items)
            
    else:
        logger.debug('or!!')
        
        q = None
        for node_id in complex_query['nodes']:
            node = Node.objects.get(pk = node_id['id'])
            
            if node_id['negated']:
                if q == None:
                    q = ~Q(node = node)
                else:
                    q = q.__or__(~Q(node = node))
            else:
                if q == None:
                    q = Q(node = node)
                else:
                    q = q.__or__(Q(node = node))
            
        items = items.filter(q)                
    logger.debug('items %s'%items)
    logger.debug('items.__class__ %s'%items.__class__)
    return items


def _search(request,  items, workspace = None):
    
    def search_node(node, sub_branch):        
        if show_associated_items:
            return items.filter(node = node)
        else:
            return items.filter(node__in = node.get_branch())
        
    def search_smart_folder(smart_folder_node, items):
        logger.debug('smart_folder_node %s'%smart_folder_node)
                
        complex_query = smart_folder_node.get_complex_query()
        items = _search_complex_query(complex_query,  items)
        return items
        
        
    
    
    logger.debug('search, starting_items %s'%items)
    query = request.POST.get('query')
    order_by = request.POST.get('order_by',  'creation_time')
    order_mode = request.POST.get('order_mode',  'decrescent')
    
    show_associated_items = request.POST.get('show_associated_items')
    nodes_query = []
    
    nodes_query.extend(request.POST.getlist('keyword'))
    nodes_query.extend(request.POST.getlist('collection'))
    
    smart_folders_query = request.POST.getlist('smart_folder')

    queries = []
    
    complex_query = request.POST.get('complex_query')
    if not workspace:
        workspace = request.session['workspace']
    if complex_query:
        complex_query = simplejson.loads(complex_query)
        
        items = _search_complex_query(complex_query,  items)
        
    else:
        if nodes_query:            
            for node_id  in nodes_query:
                logger.debug(node_id)
                node = Node.objects.filter(pk = node_id)                
                if node.count() > 0:
                    node = node[0] 
                    queries.append(search_node(node, not show_associated_items))
                    logger.debug('queries %s'%queries)
                else:
#                    return Item.objects.none()
                    queries.append(Item.objects.none())
                    
        if smart_folders_query:
            for smart_folder_id in smart_folders_query:                
                smart_folder_node = SmartFolder.objects.get(pk = smart_folder_id)
                queries.append(search_smart_folder(smart_folder_node, items))
            
            
#            items = reduce(and_,  queries)
            
#Text query                
        if query:
            
            logger.debug('query %s'%query)
            
            metadata_query = re.findall('\s*(\w+:\w+=\w+[.\w]*)\s*', query,  re.U)
            
            inbox = re.findall('\s*Inbox:/(\w+[/\w\-]*)/\s*', query,  re.U)
            
            smart_folder = re.findall('\s*SmartFolders:"(.+)"\s*', query,  re.U)
            logger.debug('smart_folder %s'%smart_folder)
            
            
            keywords = re.findall('\s*Keywords:/(.+)/\s*', query,  re.U)
#            spaced_keywords = re.findall('\s*Keywords:"([\w\s/]*)"\s*', query,  re.U)
#            keywords.extend(spaced_keywords)
    #        
            collections= re.findall('\s*Collections:/(.+)/\s*', query,  re.U)
#            spaced_collections = re.findall('\s*Collections:"([\w\s/]*)"\s*', query,  re.U)
#            collections.extend(spaced_collections)
            
            real_objects= re.findall('\s*real_object:(\w+[\w\s]*)\s*', query,  re.U)
            spaced_real_objects = re.findall('\s*real_object:"([\w\s]*)"\s*', query,  re.U)
            real_objects.extend(spaced_real_objects)

            geo = re.findall('\s*geo:\(([\d.-]*),([\d.-]*)\),\(([\d.-]*),([\d.-]*)\)\s*', query,  re.U)
            
    #            just put out  keywords and collections....
    #        simple_query = re.sub('(\w+:\w+)', '', query,)
            simple_query = re.compile('(\w+:/.+/)',  re.U).sub('', query)
            logger.debug('simple_query %s' %simple_query,  )
            simple_query = re.sub('(\w+:".+")', '', simple_query)
            
            
            simple_query = re.sub('\s*SmartFolders:"(.+)"\s*', '', simple_query)
            simple_query = re.sub('\s*inbox:/(\w+[/\w\-]*)/\s*', '', simple_query)
            
#            removing metadata query
            simple_query = re.sub('\s*(\w+:\w+=\w+[.\w]*)\s*', '', simple_query)
            
            logger.debug('----%s'%simple_query)
            
            
    #       remove geo too...
            simple_query = re.sub('(\w+:\(([\d.-]*),([\d.-]*)\),\(([\d.-]*),([\d.-]*)\))', '', simple_query)

    #       remove real_objects too...
            simple_query = re.sub('(real_object:(\w+[\w\s]*)\s*)', '', simple_query)
            simple_query = re.sub('(real_object:"([\w\s]*)"\s*)', '', simple_query)

            multi_words = re.findall('"(.+?)"', simple_query,  re.U)
            single_word_query = re.compile('"(.+)"',  re.U).sub( '', simple_query)
            
            words = re.findall( '\s*(.+)\s*', single_word_query ,  re.U)
            
#            words = re.findall( '\s*([\w+\.*])\s*', single_word_query ,  re.U)
    #            words.extend(multi_words)
            
    #        logger.debug('keywords %s'%keywords )
    #        logger.debug('collections %s'%collections)        
            logger.debug('words %s'%words )
            logger.debug('multi_words %s'%multi_words)
            logger.debug('geo %s'%geo)
            
            
            
            logger.debug('metadata_query %s'%metadata_query)
            for metadata_q in metadata_query:
                
                key, value = metadata_q.split('=')
                
                property_namespace,   property_field_name = key.split(':')
                
                try:
                    property = MetadataProperty.objects.get(namespace__prefix = property_namespace,  field_name = property_field_name)
                    logger.debug('items %s'%items)
                    logger.debug('items.filter(metadata__value = value, metadata__schema = property) %s'%items.filter(metadata__value = value, metadata__schema = property))
                    queries.append(items.filter(metadata__value = value, metadata__schema = property))
                
                except MetadataProperty.DoesNotExist:
                    logger.debug(' MetadataProperty.DoesNotExist %s'%metadata_q)
                    queries.append(Item.objects.none())
                
                
                
            
            for inbox_el in inbox:
                logger.debug('path %s'%inbox_el)
                node = Node.objects.get_from_path(inbox_el,  'inbox')
                logger.debug('node found %s'%node)
                queries.append(items.filter(node = node))
                
            for keyword in keywords:
                if keyword: 
                    logger.debug('keyword: %s'%keyword)
                    node = Node.objects.get_from_path(keyword,  'keyword')
                    logger.debug('node found %s'%node)
                    
                    queries.append(search_node(node, not show_associated_items))
                    
                else:
                    logger.debug('without keywords')
    #                    searching for items without keyword
                    queries.append(items.exclude(node__in = Node.objects.filter(type = 'keyword')))
                    break
                
            
            for coll  in collections:
                
    #                q = Q(node__label__iexact = collection.strip(),  node__type = 'collection')
    #                queries.append(items.filter(q))
                logger.debug('path %s'%coll)
                node = Node.objects.get_from_path(coll,  'collection')
                logger.debug('node found %s'%node)
                queries.append(items.filter(node = node))
                
            logger.debug('ro: %s'%real_objects)

            
    
            if smart_folder:               
                
                logger.debug('smart_folder[0] %s'%smart_folder[0])
                smart_folder_node = SmartFolder.objects.get(workspace = workspace,  label = smart_folder[0])
                queries.append(search_smart_folder(smart_folder_node, items))
                

            for robj in real_objects:
                queries.append(items.filter(Q(real_objects__name = robj) & Q(real_objects__workspace=request.session['workspace'])))

            for coords in geo:
    #                q = Q(node__label__iexact = collection.strip(),  node__type = 'collection')
    #                queries.append(items.filter(q))
                ne_lat = coords[0]
                ne_lng = coords[1]
                sw_lat = coords[2]
                sw_lng = coords[3]
                if(float(ne_lng)>float(sw_lng)):
                    queries.append(items.filter(geoinfo__latitude__lte=ne_lat, geoinfo__latitude__gte=sw_lat, geoinfo__longitude__lt=ne_lng, geoinfo__longitude__gt=sw_lng))
                else:
                    queries.append(items.filter(Q(geoinfo__longitude__gte=sw_lng) | Q(geoinfo__longitude__lte=ne_lng), geoinfo__latitude__lte=ne_lat, geoinfo__latitude__gte=sw_lat))
            
            for word in words:
                logger.debug('word %s'%word)
                if DATABASE_ENGINE == 'sqlite3':
                    q = Q(metadata__value__iregex = u'(?:^|(?:[\w\s]*\s))(%s)(?:$|(?:\s+\w*))'%word.strip())                
                    queries.append(items.filter(q))
                elif DATABASE_ENGINE == 'mysql':
                    q = Q(metadata__value__iregex = '[[:<:]]%s[[:>:]]'%word.strip())
                    queries.append(items.filter(q))
                
                    
                    
                    
            for words in multi_words:
                logger.debug('words: %s'%words)
                tmp = re.findall('\s*(.+)\s*', words,  re.U)
                logger.debug('tmp %s'%tmp)
                if DATABASE_ENGINE == 'sqlite3':
                    words_joined = '\s+'.join(tmp)
                    words_joined = words_joined.strip() 
                    logger.debug('words_joined %s'%words_joined)            
#                    q = Q(metadata__value__iregex = '(?:^|(?:[\w\s]*\s))(%s)(?:$|(?:\s+\w*))'%words_joined)
                    q = Q(metadata__value__iregex = '%s'%words_joined)

                    queries.append(items.filter(q))
                
                elif DATABASE_ENGINE == 'mysql':
                    words_joined = '[[:blank:]]+'.join(tmp)
                    logger.debug('words_joined %s'%words_joined)            
                    q = Q(metadata__value__iregex = '[[:<:]]%s[[:>:]]'%words_joined)
                    queries.append(items.filter(q))
                
            
            logger.debug('queries %s'%queries)
            
        logger.debug('queries %s'%queries )
        if queries:
            if len(queries) == 1:
                items = queries[0]
            else:
                
    #                logger.debug(queries[1][0] == queries[2][0])
                
                items = reduce(operator.and_,  queries)
                logger.debug('items after AND %s ' %items)
        
    items.distinct()       
    logger.debug('items before ordering: %s'%items)
    property = None
    
    
    if order_by:
        
        if order_by == 'creation_time':
            pass
        
        elif order_by == 'size':            
            items = items.extra(select={order_by: 'select size from component, variants_variant where item_id = item.id and variants_variant.name == "original" '})
        
        else:
            property_namespace, property_field_name = order_by.split('_')
                
            try:
                property = MetadataProperty.objects.get(namespace__prefix__iexact = property_namespace,  field_name__iexact = property_field_name)
            except MetadataProperty.DoesNotExist:
                property = None
                logger.debug('property for ordering not found')
            
        

        
        
            if property:
                language_settings = DAMComponentSetting.objects.get(name='supported_languages')
#                language_selected = get_user_setting_by_level(language_settings,workspace)
#                TODO: change when gui multilanguage ready
                language_selected = 'en-US' 
                logger.debug('language_selected %s'%language_selected)
                items = items.extra(select=SortedDict([(order_by, 'select value from metadata_metadatavalue where object_id = item.id and schema_id = %s  and language=%s or language=null')]),  select_params = (str(property.id),  language_selected))
                
        if order_mode == 'decrescent':
            items = items.order_by('-%s'%order_by)
        else:
            items = items.order_by('%s'%order_by)

    
    logger.debug('items at the end: %s'%items)
    return items

def _search_items(request, workspace, media_type, start=0, limit=30, unlimited=False):

    user = User.objects.get(pk=request.session['_auth_user_id'])

    only_basket = simplejson.loads(request.POST.get('only_basket', 'false'))    
    
    items = workspace.items.filter(type__name__in = media_type).distinct().order_by('-creation_time')
#    if media_type != 'all':
#        items = workspace.items.filter(type=media_type).distinct().order_by('-creation_time')
#    else:
#        items = workspace.items.distinct().order_by('-creation_time')

    user_basket = Basket.get_basket(user, workspace)
    basket_items = user_basket.items.all().values_list('pk', flat=True)

    if only_basket:
        items = items.filter(pk__in=basket_items)

#    if request.POST.get('query') or request.POST.getlist('node_id') or request.POST.get('complex_query'):
    items = _search(request,  items)

    total_count = items.count()

    if not unlimited:
        items = items[start:start+limit]

    return (items, total_count)


def _get_thumb_url(item, workspace, thumb_dict = None, absolute_url = False):

    thumb_url = NOTAVAILABLE
    thumb_ready = 0
    
    if not thumb_dict:
        thumb_variants = workspace.get_variants().filter(name = 'thumbnail').values('media_type__name',  'pk')
        thumb_dict = {}
        for thumb in thumb_variants:
            thumb_dict[thumb['media_type__name']] = {'pk': thumb['pk']}
    
    try:
        url = get_component_url(workspace, item.pk, 'thumbnail', thumb=True)
        if url:
            thumb_ready = 1
            thumb_url = url
    except:
        return None, None
    return thumb_url,thumb_ready



@login_required
def load_items(request, view_type=None, unlimited=False, ):
    from datetime import datetime
    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace_id = request.POST.get('workspace_id')
        logger.debug('workspace_id %s'%workspace_id)
        if  workspace_id:
            workspace = Workspace.objects.get(pk = workspace_id)
        else:
            workspace = request.session['workspace']        

        media_type = request.POST.getlist('media_type')

        logger.debug("request.session['media_type'] %s"%request.session['media_type']) 
        
#        save media type on session

        if request.session.__contains__('media_type'):
            request.session['media_type'][workspace.pk] = list(media_type)
        else:
            request.session['media_type']= {workspace.pk: list(media_type)}
            
        request.session.modified = True

#            
        logger.debug("request.session['media_type'] %s"%request.session['media_type'])    
        
#        TODO: change movie - video, sigh 
        if 'video' in media_type:
            media_type.remove('video')
            media_type.append('movie')
        

        start = int(request.POST.get('start', 0))
        limit = int(request.POST.get('limit', 30))
		
        if limit == 0:
            unlimited = True

        items, total_count = _search_items(request, workspace, media_type, start, limit, unlimited)
                    
        item_dict = []
        now = time.time()

        items_pks = [item.pk for item in items]
        
        tasks_pending_obj = MachineState.objects.filter(action__component__workspace=workspace, action__component__item__pk__in=items_pks)     
        tasks_pending = tasks_pending_obj.values_list('action__component__item',  flat=True)
                
        thumb_caption_setting = DAMComponentSetting.objects.get(name='thumbnail_caption')
        thumb_caption = get_user_setting(user, thumb_caption_setting, workspace)

        default_language = get_metadata_default_language(user, workspace)

        user_basket = Basket.get_basket(user, workspace)

        basket_items = user_basket.items.all().values_list('pk', flat=True)
        
        for item in items:
            geotagged = 0
            inprogress = 0
            
            if item.pk in tasks_pending:
                inprogress = 1
            if GeoInfo.objects.filter(item=item).count() > 0:
                geotagged = 1
            
            item_in_basket = 0

            if item.pk in basket_items:
                item_in_basket = 1
             
            thumb_url,thumb_ready = _get_thumb_url(item, workspace)

            states = item.stateitemassociation_set.filter(workspace = workspace)

            my_caption = _get_thumb_caption(item, thumb_caption, default_language)
            if inprogress:
                preview_available = tasks_pending_obj.filter(action__component__variant__name = 'preview', action__component__item = item, action__function = 'adapt_resource').count()
            else:
                preview_available = 0
            item_info = {
                "name":my_caption,
                "pk": smart_str(item.pk),
                "geotagged": geotagged, 
                "inprogress": inprogress, 
                'thumb': thumb_ready, 
                'type': smart_str(item.type.name),
                'inbasket': item_in_basket,
                'preview_available': preview_available,
                #'inbasket':1,
                "url":smart_str(thumb_url), "url_preview":smart_str("/redirect_to_component/%s/preview/?t=%s" % (item.pk,  now))
            }
            
            if states.count():
                state_association = states[0]
                
                item_info['state'] = state_association.state.pk
                logger.debug("item_info['state'] %s"%item_info['state'])
                
            item_dict.append(item_info)
        
        res_dict = {"items": item_dict, "totalCount": str(total_count)}

        resp = simplejson.dumps(res_dict)

        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

@membership_required
def _switch_workspace(request,  workspace_id):
    logger.debug('workspace_id %s'%workspace_id)
    workspace = Workspace.objects.get(pk = workspace_id)
    request.session['workspace'] = workspace
    return workspace
    
@login_required
def workspace(request,  workspace_id = None):
    user = User.objects.get(pk=request.session['_auth_user_id'])
    logger.debug('workspace_id %s'%workspace_id)
    if not workspace_id:
        if request.session.__contains__('workspace'):
            workspace = Workspace.objects.get(pk = request.session.get('workspace', ).pk ) #ws in session could be outdated (old name)
        else:
            workspace = Workspace.objects.filter(members = user).order_by('name').distinct()[0]
            request.session['workspace'] = workspace
    else:
        workspace = _switch_workspace(request,  workspace_id)
    
    logger.debug('workspace.name %s'%workspace.name)
    logger.debug('workspace.pk %s'%workspace.pk)
    return render_to_response('workspace_gui.html', RequestContext(request,{'ws':workspace, 'GOOGLE_KEY': GOOGLE_KEY}))

def _replace_groups(group, item, default_language):
    namespace = group.group('namespace')
    field = group.group('field')
    try:
        schema = MetadataProperty.objects.get(namespace__prefix=namespace, field_name=field)
        values = item.get_metadata_values(schema)
        if isinstance(values, list):
            value = values[0]
        elif isinstance(values, dict):
            value = values.get(default_language, '')
        else:
            value = values
        if not value:
            value = ''

        return value
    except:
        raise
        return ''

def _get_thumb_caption(item, template_string, language):

    pattern = re.compile('%(?P<namespace>\w+):(?P<field>\w+)%')
    groups = re.finditer(pattern, template_string)
    values_dict = {}
    for g in groups:
        values_dict[g.group(0)] = _replace_groups(g, item, language)

    caption = template_string

    for schema in values_dict.keys():
        caption = caption.replace(schema, values_dict[schema])

    if not len(caption):
        caption = str(item.get_file_name())

    return caption
    
@login_required
def get_status(request):    
    
    items = simplejson.loads(request.POST.get('items'))

    user = User.objects.get(pk=request.session['_auth_user_id'])

    workspace = request.session.get('workspace', None) 

    ws_tasks = Machine.objects.filter(current_state__action__component__workspace=workspace)
    tasks_pending = ws_tasks.exclude(current_state__name='failed')
    tasks_failed = ws_tasks.filter(current_state__name='failed')

    items_failed = tasks_failed.values_list('current_state__action__component__item', flat=True).distinct()
    items_pending = tasks_pending.values_list('current_state__action__component__item', flat=True).distinct()

    total_pending = items_pending.count()
    total_failed = items_failed.count()
    
    update_items = {}
 
    now = time.time()

    thumb_caption_setting = DAMComponentSetting.objects.get(name='thumbnail_caption')
    thumb_caption = get_user_setting(user, thumb_caption_setting, workspace)

    default_language = get_metadata_default_language(user, workspace)

    for i in items:
        item = Item.objects.get(pk=i)

        thumb_url,thumb_ready = _get_thumb_url(item, workspace)

        my_caption = _get_thumb_caption(item, thumb_caption, default_language)

        if tasks_pending.filter(current_state__action__component__item=item).count() > 0:
            update_items[i] = {"name":my_caption,"size":item.get_file_size(), "pk": smart_str(item.pk), 'thumb': thumb_ready,
                              "url":smart_str(thumb_url), "url_preview":smart_str("/redirect_to_component/%s/preview/?t=%s" % (item.pk,  now))}
        else:
            preview_available = tasks_pending.filter(current_state__action__component__variant__name = 'preview', current_state__action__component__item=item).count()
            update_items[i] = {"name":my_caption,"size":item.get_file_size(), "pk": smart_str(item.pk), 'inprogress': 0, 'thumb': thumb_ready, 
                              'preview_available': preview_available,"url":smart_str(thumb_url), "url_preview":smart_str("/redirect_to_component/%s/preview/?t=%s" % (item.pk,  now))}

#    resp_dict = {'adapt': adapt_pending, 'feat': feat_pending, 'metadata': metadata_pending, 'items': update_items}
    resp_dict = {'pending': total_pending, 'failed': total_failed, 'items': update_items}

    resp = simplejson.dumps(resp_dict)
    return HttpResponse(resp)
    
@login_required
def get_n_items(request):
    workspace = request.session.get('workspace')
    n_items = workspace.items.all().count()
    resp = {'success': True,  'n_items': n_items}
    return HttpResponse(simplejson.dumps(resp))
    


@login_required
def get_permissions(request):
    workspace = request.session.get('workspace')
    logger.debug('-----------workspace %s'%workspace)
    user = User.objects.get(pk=request.session['_auth_user_id'])
    permissions = workspace.get_permissions(user)
    resp = {'permissions':[]}
    if user.has_perm('workspace.add_workspace'):
        resp['permissions'].append({'name': 'add_ws'})
    for perm in permissions:
        resp['permissions'].append({'name': perm.codename})
    return HttpResponse(simplejson.dumps(resp))
    
@login_required
@permission_required('admin',  False)
def get_ws_members(request):

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    admin_user = User.objects.get(pk=request.session['_auth_user_id'])

    ws = Workspace.objects.get(pk = ws_id)

    members = ws.members.all()
    
    available_permissions = WorkSpacePermission.objects.all()    
    permissions_list = [{'pk': str(p.pk), 'name': str(p.name)} for p in available_permissions]
    
    data = {'elements':[]}
    for u in members:
        permissions = ws.get_permissions(u)
        perm_list = [p.pk for p in permissions]
        user_dict = {'id':u.id, 'name':u.username}
        for p in available_permissions:
            if p.pk in perm_list:
                user_dict[p.codename] = 1
            else:
                user_dict[p.codename] = 0
        if admin_user == u:
            user_dict['editable'] = False
        else:
            user_dict['editable'] = True        
        data['elements'].append(user_dict)
    return HttpResponse(simplejson.dumps(data))

@login_required
@permission_required('admin',  False)
def get_available_users(request):

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    ws = Workspace.objects.get(pk = ws_id)
    
    users = User.objects.exclude(workspaces=ws)
    
    users_list = [{'id': u.pk, 'name': str(u.username)} for u in users]
    
    data = {'users': users_list}
    
    return HttpResponse(simplejson.dumps(data))

@login_required
@permission_required('admin',  False)
def get_available_permissions(request):

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    ws = Workspace.objects.get(pk = ws_id)
    
    available_permissions = WorkSpacePermission.objects.all()    
    permissions_list = [{'pk': str(p.pk), 'name': str(p.name)} for p in available_permissions]
    
    data = {'available_permissions': permissions_list}
    
    return HttpResponse(simplejson.dumps(data))    
    
@login_required
@permission_required('admin',  False)
def save_members(request):

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    ws = Workspace.objects.get(pk = ws_id)

    permissions = request.POST.get('permissions', None)
    
    if permissions:
        permissions_list = simplejson.loads(permissions)
    else:
        permissions_list = []
    
    current_users = []

    for p in permissions_list:
        try:
            user = User.objects.get(pk=p['id'])
            ws.members.add(user)
            current_users.append(user.pk)
        except:
            continue

    removed_users = ws.members.exclude(pk__in=current_users)
        
    for p in permissions_list:
        for k, v in p.iteritems():
            if k not in ['id', 'name', 'editable']:
                try: 
                    user = User.objects.get(pk=p['id'])
                    ws_permission = WorkSpacePermission.objects.get(codename=k)
                    wspa = WorkSpacePermissionAssociation.objects.get_or_create(workspace = ws, permission = ws_permission)[0]
                    if v == 0:
                        wspa.users.remove(user)
                    else:
                        wspa.users.add(user)
                except:
                    raise
                    pass
        
    for wsp in WorkSpacePermission.objects.all():
        try:
            wspa = WorkSpacePermissionAssociation.objects.get(workspace = ws, permission = wsp)
            wspa.users.remove(*removed_users)
        except:
            pass

    ws.members.remove(*removed_users)
    
    data = {'success': True}
    
    return HttpResponse(simplejson.dumps(data))        
    
@login_required
def switch_ws(request):
    workspace_id = request.POST['workspace_id']
    logger.debug('workspace_id %s'%workspace_id)
    _switch_workspace(request,  workspace_id)
    return HttpResponse(simplejson.dumps({'success': True}))
    
