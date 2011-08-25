"""
Views used in /dam_admin/
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.utils import simplejson
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User, Permission

from dam.preferences.models import UserSetting, SettingValue, DAMComponent, DAMComponentSetting, SystemSetting, WSSetting 
from dam.core.dam_repository.models import Type
from dam.core.dam_metadata.models import XMPStructure
from dam.core.dam_metadata.models import XMPNamespace
from dam.metadata.models import MetadataDescriptor, MetadataDescriptorGroup, MetadataProperty, RightsValue, RightsXMPValue
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.models import WorkspacePermissionAssociation, WorkspacePermissionsGroup, WorkspacePermission
from dam.workspace.views import _get_theme

from settings import BACKUP_PATH, INSTALLATIONPATH
import logging
logger = logging.getLogger('dam')

import os
import time

@staff_member_required
def dam_admin(request):
    """
    TODO: Dam Administration Interface is under development
    """
    theme = _get_theme()
    
    return render_to_response('dam_administration.html', RequestContext(request,{'theme_css':theme.css_file}))

@staff_member_required
def get_admin_settings(request):
    """
    Get system settings (dam admin)
    """
    settings = DAMComponentSetting.objects.all()
    data = {'prefs':[]}
    for s in settings:
        choices = [[c.name, c.description] for c in s.choices.all()]
        value = s.get_user_setting_by_level()
        data['prefs'].append({'id': 'pref__%d'%s.id, 'name':s.name,'caption': s.caption,'name_component': s.component.name,  'type': s.type,  'value': value,  'choices':choices})
    return HttpResponse(simplejson.dumps(data))    

@staff_member_required
def damadmin_get_desc_groups(request):
    """
    Retrieve descriptor groups
    """

    groups = MetadataDescriptorGroup.objects.filter(workspace__isnull=True).order_by('name')
    data = {'groups':[]}
    current_desc_id = request.POST.get('desc_id', 0)
    desc_groups = []
    if int(current_desc_id) > 0:
        desc = MetadataDescriptor.objects.get(id=current_desc_id)
        desc_groups = desc.metadatadescriptorgroup_set.all().values_list('id', flat=True)

    for g in groups:

        removable = False

        if g.basic_summary:
            target = 1
        elif g.specific_basic:
            target = 2
        elif g.specific_full: 
            target=3
        elif g.upload:
            target=4
        else:
            target = 0
            removable = True

        selected = False
        if g.id in desc_groups:
            selected = True

        data['groups'].append({'id':g.id, 'name':g.name,'removable': removable, 'selected': selected, 'target': target})
        
    return HttpResponse(simplejson.dumps(data))    

@staff_member_required
def damadmin_get_desc_list(request):
    """
    Retrieve descriptor list
    """

    descs = MetadataDescriptor.objects.filter(custom=False).order_by('name')
    current_group_id = request.POST.get('group_id', 0)
    
    group_descs = []
    
    if int(current_group_id) > 0:
#        descs = descs.exclude(metadatadescriptorgroup__in=MetadataDescriptorGroup.objects.exclude(pk=current_group_id))
        current_group = MetadataDescriptorGroup.objects.get(pk=current_group_id)
        group_descs = current_group.descriptors.all().values_list('id', flat=True)
        
    data = {'descs':[]}
    for g in descs:
        xmp_mapping = ["%s:%s" % (x.namespace.prefix, x.field_name) for x in g.properties.all()]
        groups = [x.name for x in g.metadatadescriptorgroup_set.all()]
        if g.id in group_descs:
            selected = True
        else:
            selected=False
        data['descs'].append({'id':g.id, 'name':g.name, 'selected': selected, 'mapping': ", ".join(xmp_mapping), 'groups': ", ".join(groups)})
    return HttpResponse(simplejson.dumps(data))
    
@staff_member_required
def damadmin_get_descriptor_properties(request):
    """
    Retrieve XMP properties for the given descriptor
    """

    props = MetadataProperty.objects.all().exclude(xmpstructure__in=XMPStructure.objects.all()).exclude(metadatadescriptor__in=MetadataDescriptor.objects.all())
    current_desc_id = request.POST.get('desc_id', 0)
    data = {'elements':[]}
    if int(current_desc_id) > 0:
        desc = MetadataDescriptor.objects.get(id=current_desc_id)            
        desc_props = desc.properties.all()
        for p in desc_props: 
            xmp_name = "%s:%s" % (p.namespace.prefix, p.field_name)
            data['elements'].append({'id':p.id, 'name':xmp_name, 'selected': True})
    for g in props:
        xmp_name = "%s:%s" % (g.namespace.prefix, g.field_name)
        data['elements'].append({'id':g.id, 'name':xmp_name})
    return HttpResponse(simplejson.dumps(data))
    
@staff_member_required
def damadmin_save_descriptor(request):
    """
    Save descriptor
    """
    prop_list_ids = simplejson.loads(request.POST.get('prop_list'))
    group_list_ids = simplejson.loads(request.POST.get('group_list'))

    current_desc_id = request.POST.get('desc_id', 0)

    if int(current_desc_id) > 0:
        MetadataDescriptor.objects.get(id=current_desc_id).delete()

    desc_name = request.POST.get('desc_name')
    if desc_name and prop_list_ids and group_list_ids:
        new_desc = MetadataDescriptor.objects.create(name=desc_name, description=desc_name)
        for p in prop_list_ids:
            new_desc.properties.add(MetadataProperty.objects.get(pk=p))
        for g in group_list_ids:
            group = MetadataDescriptorGroup.objects.get(pk=g)
            group.descriptors.add(new_desc)
            
        return HttpResponse(simplejson.dumps({'success': True}))

    else:            
        return HttpResponse(simplejson.dumps({'success': False, 'error': 'fill all the required fields'}))
    
@staff_member_required
def damadmin_save_descriptor_group(request):
    """
    Save descripto group
    """
    desc_list_ids = simplejson.loads(request.POST.get('desc_list'))

    current_group_id = request.POST.get('group_id', 0)

    if int(current_group_id) > 0:
        MetadataDescriptorGroup.objects.get(id=current_group_id).delete()

    group_name = request.POST.get('group_name')
    group_target = int(request.POST.get('group_target'))

    if group_name and desc_list_ids:
        new_group = MetadataDescriptorGroup.objects.create(name=group_name)
        for p in desc_list_ids:
            new_group.descriptors.add(MetadataDescriptor.objects.get(pk=p))
        if group_target == 1:
            new_group.basic_summary = True
        elif group_target == 2:
            new_group.specific_basic = True
        elif group_target == 3:
            new_group.specific_full = True
        elif group_target == 4:
            new_group.upload = True
            
        new_group.save()
            
        return HttpResponse(simplejson.dumps({'success': True}))

    else:            
        return HttpResponse(simplejson.dumps({'success': False, 'error': 'fill all the required fields'}))    
    
@staff_member_required
def damadmin_delete_descriptor(request):
    """
    Delete descriptor(s)
    """
    desc_ids = simplejson.loads(request.POST.get('obj_list'))
    MetadataDescriptor.objects.filter(pk__in=desc_ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))    

@staff_member_required
def damadmin_delete_descriptor_group(request):
    """
    Delete descriptor group(s)
    """
    desc_ids = simplejson.loads(request.POST.get('obj_list'))
    MetadataDescriptorGroup.objects.filter(pk__in=desc_ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))    

@staff_member_required
def damadmin_delete_rights(request):
    """
    Delete rights
    """
    rights_ids = simplejson.loads(request.POST.get('obj_list'))
    RightsXMPValue.objects.filter(rightsvalue__pk__in=rights_ids).delete()
    RightsValue.objects.filter(pk__in=rights_ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))       
    
@staff_member_required
def damadmin_get_rights_list(request):
    """
    Retrieve rights list
    """
    rights = RightsValue.objects.all().order_by('value')

    data = {'rights':[]}
    for r in rights:
        data['rights'].append({'id':r.id, 'name':r.value})
    return HttpResponse(simplejson.dumps(data))
    
@staff_member_required
def damadmin_get_rights_properties(request):
    """
    Retrieve rights mapping to XMP properties
    """
    current_rights = request.POST.get('rights_id', 0)
    add_mode = request.POST.get('add_mode', 0)
   
    data = {'elements':[]}
    if int(current_rights) > 0:
        rights = RightsValue.objects.get(id=current_rights)            
        rights_props = rights.xmp_values.all()
        for p in rights_props: 
            xmp_name = "%s:%s" % (p.xmp_property.namespace.prefix, p.xmp_property.field_name)
            data['elements'].append({'xmp_id':p.xmp_property.id, 'name':xmp_name, 'value': p.value})
    elif int(add_mode) == 1:
        props = MetadataProperty.objects.filter(rights_target=True)
        for p in props: 
            xmp_name = "%s:%s" % (p.namespace.prefix, p.field_name)
            data['elements'].append({'xmp_id':p.id, 'name':xmp_name})
        
    return HttpResponse(simplejson.dumps(data))    
       
@staff_member_required
def damadmin_save_rights(request):
    """
    Save rights
    """

    prop_list_ids = simplejson.loads(request.POST.get('prop_list'))

    current_rights_id = request.POST.get('rights_id', 0)

    rights_name = request.POST.get('rights_name')

    if rights_name and prop_list_ids:
    
        if int(current_rights_id) > 0:
            rights = RightsValue.objects.get(pk=current_rights_id)
            rights.value = rights_name
            rights.xmp_values.all().delete()
            rights.save()
        else:
            rights = RightsValue.objects.create(value=rights_name)

        for p in prop_list_ids:
            xmp_property = MetadataProperty.objects.get(pk=p['xmp_id'])
            new_value = RightsXMPValue.objects.create(xmp_property=xmp_property, value=p['value'])
            rights.xmp_values.add(new_value)
            
        return HttpResponse(simplejson.dumps({'success': True}))

    else:            
        return HttpResponse(simplejson.dumps({'success': False, 'error': 'fill all the required fields'}))
        
def _get_schema_type(schema):

    type = []
    
    if schema.is_array != 'not_array' and schema.is_choice != 'open_choice':
        type.append(schema.get_is_array_display())

    if schema.is_choice != 'not_choice':
        type.append(schema.get_is_choice_display())

    type.append(schema.get_type_display())

    return " ".join(type)

def _get_is_array(schema):

    if schema.is_array != 'not_array':
        return schema.is_array        
    else:
        return None

def _get_is_choice(schema):

    if schema.is_choice != 'not_choice':
        return schema.is_choice        
    else:
        return None

def _get_is_target(schema):

    if schema.uploaded_by:
        return 'uploaded_by'
    elif schema.creation_date:
        return 'creation_date'
    elif schema.latitude_target:
        return 'latitude_target'
    elif schema.longitude_target:
        return 'longitude_target'
    elif schema.rights_target:
        return 'rights_target'
    elif schema.item_owner_target:
        return 'item_owner_target'
    elif schema.file_size_target:
        return 'file_size_target'
    elif schema.file_name_target:
        return 'file_name_target'
    else:
        return None
        
@staff_member_required
def damadmin_get_xmp_list(request):
    """
    Retrieve XMP Properties
    """

    data = {'xmp':[]}
    props = MetadataProperty.objects.all()
    for p in props: 
        media_types = p.media_type.all().values_list('name', flat=True)
        schema_type = _get_schema_type(p)        
        prop_dict = {'id':p.id, 'namespace_name': p.namespace.name, 'name':p.field_name, 'keyword_target': p.keyword_target, 'xmp_type': p.type, 'variant': p.is_variant, 'editable': p.editable, 'searchable':p.is_searchable,  'caption': p.caption, 'description': p.description, 'namespace': p.namespace.id, 'type': schema_type, 'image': 'image' in media_types, 'video': 'video' in media_types, 'doc': 'doc' in media_types, 'audio': 'audio' in media_types}
        is_array = _get_is_array(p)
        is_choice = _get_is_choice(p)
        is_target = _get_is_target(p)
        if is_array:
            prop_dict.update({'array': is_array})
        else:
            prop_dict.update({'array': 'not_array'})
        if is_choice:
            prop_dict.update({'choice': is_choice})
        else:
            prop_dict.update({'choice': 'not_choice'})
        if is_target:
            prop_dict.update({'target': is_target})
        
        data['xmp'].append(prop_dict)
        
    return HttpResponse(simplejson.dumps(data))    

@staff_member_required
def damadmin_get_xmp_namespaces(request):
    """
    Retrieve XMP Namespace list
    """
    data = {'elements':[]}
    namespaces = XMPNamespace.objects.all()
    for p in namespaces: 
        data['elements'].append({'id':p.id, 'prefix': p.prefix, 'name':p.name, 'url': p.uri})
        
    return HttpResponse(simplejson.dumps(data))    

@staff_member_required
def damadmin_save_ns(request):
    """
    Save XMP Namespace
    """
    current_ns_id = request.POST.get('ns_id', 0)

    ns_name = request.POST.get('ns_name')
    ns_prefix = request.POST.get('ns_prefix')
    ns_url = request.POST.get('ns_url')

    if ns_name and ns_prefix and ns_url:
    
        if int(current_ns_id) > 0:
            ns = XMPNamespace.objects.get(pk=current_ns_id)
            ns.name = ns_name
            ns.prefix = ns_prefix
            ns.uri = ns_url
            ns.save()
        else:
            ns = XMPNamespace.objects.create(name=ns_name, prefix=ns_prefix, uri=ns_url)
            
        return HttpResponse(simplejson.dumps({'success': True}))

    else:            
        return HttpResponse(simplejson.dumps({'success': False, 'error': 'fill all the required fields'}))

def _get_xmp_params(request):

    params = {}
    types = []    

    params['field_name'] = request.POST.get('xmp_name')
    params['caption'] = request.POST.get('xmp_caption')
    params['description'] = request.POST.get('xmp_desc')
    params['editable'] = request.POST.get('xmp_editable')
    params['is_searchable'] = request.POST.get('xmp_searchable')
    params['is_variant'] = request.POST.get('xmp_variant')
    params['type'] = request.POST.get('xmp_type')
    xmp_target = request.POST.get('xmp_target')
    if xmp_target:
        params[str(xmp_target)] = True
    params['keyword_target'] = request.POST.get('xmp_keyword')
    params['namespace'] = XMPNamespace.objects.get(pk=int(request.POST.get('xmp_namespace')))
    params['is_array'] = request.POST.get('xmp_array')
    params['is_choice'] = request.POST.get('xmp_choice')
    for k in request.POST.keys():
        if k.startswith('xmp_media_type_'):
            types.append(k.split('_')[-1])
    
    for key in ['is_searchable', 'keyword_target', 'editable', 'is_variant']:
        if params[key] == 'true':
            params[key] = True
        else:
            params[key] = False
                
    return (params, types)

@staff_member_required
def damadmin_save_xmp(request):
    """
    Save XMP Property
    """
    current_xmp_id = request.POST.get('xmp_id', 0)

    new_params, new_types = _get_xmp_params(request)
    
    if int(current_xmp_id) > 0:
        xmp = MetadataProperty.objects.get(pk=current_xmp_id)
        for p in ['uploaded_by', 'creation_date', 'latitude_target', 'longitude_target', 'rights_target', 'item_owner_target', 'file_size_target', 'file_name_target']:
            xmp.__setattr__(p, False)
        for p in new_params:
            xmp.__setattr__(p, new_params[p])
        xmp.media_type.remove(*xmp.media_type.all())
        xmp.media_type.add(*Type.objects.filter(name__in=new_types))
        xmp.save()
    else:
        xmp = MetadataProperty.objects.create(**new_params)
        xmp.media_type.add(*Type.objects.filter(name__in=new_types))
        xmp.save()
        
    return HttpResponse(simplejson.dumps({'success': True}))
                
@staff_member_required
def damadmin_delete_namespace(request):
    """
    Delete XMP Namespace
    """
    ns_ids = simplejson.loads(request.POST.get('obj_list'))
    XMPNamespace.objects.filter(pk__in=ns_ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))           
        
@staff_member_required
def damadmin_delete_xmp(request):
    """
    Delete XMP Property
    """

    xmp_ids = simplejson.loads(request.POST.get('obj_list'))
    MetadataProperty.objects.filter(pk__in=xmp_ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))           

@staff_member_required
def damadmin_delete_user(request):
    """
    Delete user(s)
    """

    ids = simplejson.loads(request.POST.get('obj_list'))
    User.objects.filter(pk__in=ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))

@staff_member_required
def damadmin_delete_ws(request):
    """
    Delete workspace(s)
    """

    ids = simplejson.loads(request.POST.get('obj_list'))
    Workspace.objects.filter(pk__in=ids).delete()
    return HttpResponse(simplejson.dumps({'success': True}))
        
@staff_member_required
def damadmin_get_xmp_structures(request):
    """
    Retrieve XMP structures
    """

    data = {'elements':[]}
    structures = XMPStructure.objects.all()
    for s in structures: 
        data['elements'].append({'id':s.id, 'name':s.name})
        
    return HttpResponse(simplejson.dumps(data))    

@staff_member_required
def damadmin_get_user_list(request):
    """
    Retrieve user list
    """

    data = {'elements':[]}
    users = User.objects.all()
    for s in users: 
        data['elements'].append({'id':s.id, 'name':s.username, 'is_staff': s.is_staff, 'is_active': s.is_active, 'email': s.email, 'first_name': s.first_name, 'last_name': s.last_name, 'last_login': s.last_login.strftime("%d/%m/%y %H:%m:%S"), 'date_joined': s.date_joined.strftime("%d/%m/%y %H:%m:%S")})
        
    return HttpResponse(simplejson.dumps(data))    

@staff_member_required
def damadmin_get_user_permissions(request):
    """
    Retrieve user permissions
    """

    current_id = request.POST.get('id', 0)

    resp = {'elements':[]}

    if int(current_id) > 0:
        user = User.objects.get(pk=current_id)
        wss = WorkspacePermissionAssociation.objects.filter(users=user).values_list('workspace__id', flat=True)
        for ws_id in wss:
            ws = Workspace.objects.get(pk=ws_id)
            permissions = ws.get_permissions(user)
            groups = WorkspacePermissionsGroup.objects.filter(workspace=ws, users=user)
            group_name = [g.name for g in groups]
            group_ids = [g.id for g in groups]
            
            ws_dict = {'id': ws.id, 'ws': ws.name, 'permissions': [], 'groups': group_name, 'group_ids': group_ids}

            for perm in permissions:
                ws_dict['permissions'].append(perm.codename)

            resp['elements'].append(ws_dict)

    return HttpResponse(simplejson.dumps(resp))

@staff_member_required
def damadmin_save_user(request):
    """
    Save user
    """

    current_id = request.POST.get('id', 0)
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('pwd', None)
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')

    permissions = simplejson.loads(request.POST.get('permissions'))

    if int(current_id) > 0:

        user = User.objects.get(pk=current_id)

        wspa = WorkspacePermissionAssociation.objects.filter(users=user)
    
        for pa in wspa:
            pa.users.remove(user)

        wsg = WorkspacePermissionsGroup.objects.filter(users=user)
    
        for wsgroup in wsg:
            wsgroup.users.remove(user)

        wss = Workspace.objects.filter(members=user)
        
        for ws in wss:        
            ws.members.remove(user)    

    else:

        try:
            user = User.objects.create_user(username, email, password)
        except:
            return HttpResponse(simplejson.dumps({'success': False}))
        
        add_ws_permission = Permission.objects.get(codename='add_workspace')

        user.user_permissions.add(add_ws_permission)
        user.save()

        ws = Workspace.objects.create_workspace(user.username, '', user)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email

    user.save()
    
    for p in permissions:
        ws = Workspace.objects.get(pk=p['id'])
        perms_list = p['permissions']
        groups = p['groups']
        
        ws.members.add(user)    
        
        for k in perms_list:
        
            ws_permission = WorkspacePermission.objects.get(codename=k)
            wspa = WorkspacePermissionAssociation.objects.get_or_create(workspace = ws, permission = ws_permission)[0]

            wspa.users.add(user)            

        for g in groups:
    
            new_group = WorkspacePermissionsGroup.objects.get(pk=g)
            
            new_group.users.add(user)


    return HttpResponse(simplejson.dumps({'success': True}))
    
@staff_member_required
def damadmin_get_workspaces(request):
    """
    Retrieve workspace list
    """

    resp = {'elements':[]}

    wss = Workspace.objects.all()
    for ws in wss:

        ws_dict = {'id': ws.id, 'ws': ws.name, 'description': ws.description, 'creator_id': ws.creator.id, 'creator': ws.creator.username}

        resp['elements'].append(ws_dict)
        
    logger.info("get_workspaces %s" %resp)

    return HttpResponse(simplejson.dumps(resp))    

@staff_member_required
def damadmin_get_ws_users(request):
    """
    Retrieve workspace users
    """

    current_id = request.POST.get('id', 0)

    resp = {'elements':[]}

    if int(current_id) > 0:
        ws = Workspace.objects.get(pk=current_id)
        members = ws.members.all()
        for user in members:
            permissions = ws.get_permissions(user)
            groups = user.workspacepermissionsgroup_set.filter(workspace=ws)
            ws_dict = {'id': user.id, 'username': user.username, 'permissions': [], 'groups': []}

            for perm in permissions:
                ws_dict['permissions'].append(perm.codename)

            for group in groups:
                ws_dict['groups'].append(group.name)

            resp['elements'].append(ws_dict)
            
    return HttpResponse(simplejson.dumps(resp))    

def _get_ws_groups(ws_id):
    resp = []

    if int(ws_id) > 0:
        ws = Workspace.objects.get(pk=ws_id)
        groups = ws.workspacepermissionsgroup_set.all()
        for group in groups:
            permissions = group.permissions.all()
            users = group.users.all()
            ws_dict = {'id': group.id, 'group': group.name, 'permissions': [], 'users': []}

            for perm in permissions:
                ws_dict['permissions'].append(perm.codename)

            for u in users:
                ws_dict['users'].append(u.id)

            resp.append(ws_dict)

    return resp

@staff_member_required
def damadmin_get_ws_groups(request):
    """
    Retrieve workspace permission groups
    """

    current_id = request.POST.get('id', 0)

    resp = {'elements':_get_ws_groups(current_id)}
            
    return HttpResponse(simplejson.dumps(resp))

@staff_member_required
def damadmin_save_ws(request):
    """
    Save Workspace
    """

    current_id = request.POST.get('id', 0)
    ws_name = request.POST.get('name')
    description = request.POST.get('description')
    creator = request.POST.get('creator')

    permissions = simplejson.loads(request.POST.get('permissions'))
    groups = simplejson.loads(request.POST.get('groups'))

    if int(current_id) > 0:

        ws = Workspace.objects.get(pk=current_id)

        wspa = WorkspacePermissionAssociation.objects.filter(workspace=ws).delete()
        wsg = WorkspacePermissionsGroup.objects.filter(workspace=ws).delete()

        ws.name = ws_name
        ws.description = description
        ws.creator = User.objects.get(pk=creator)

        ws.members = []

        ws.save()
    else:


        user = User.objects.get(pk=creator)
        ws = Workspace.objects.create_workspace(user.username, '', user)
    
    for p in permissions:
        perms_list = p['permissions']
        user = User.objects.get(pk=p['id'])

        ws.members.add(user)
        
        for k in perms_list:
        
            try:
    
                ws_permission = WorkspacePermission.objects.get(codename=k)
                wspa = WorkspacePermissionAssociation.objects.get_or_create(workspace = ws, permission = ws_permission)[0]
    
                wspa.users.add(user)

            except:
                continue

    for g in groups:
        perms_list = g['permissions']
        users_list = set(g['users'])

        new_group = WorkspacePermissionsGroup.objects.create(name=g['name'], workspace=ws)
        
        for k in perms_list:

            try:
                        
                ws_permission = WorkspacePermission.objects.get(codename=k)
                new_group.permissions.add(ws_permission)

            except:
                continue

        for u in users_list:

            try:

                user = User.objects.get(pk=u)
                if user in ws.members.all():            
                    new_group.users.add(user)

            except:
                continue

    return HttpResponse(simplejson.dumps({'success': True}))     

@staff_member_required
def damadmin_get_list_file_backup(request):

    resp = {'file_backup':[]}
    if (os.path.exists(BACKUP_PATH)):
        files = []
        for f in os.listdir(BACKUP_PATH):
            if os.path.isfile(BACKUP_PATH + os.path.sep + f):
                data = time.ctime(os.path.getctime(BACKUP_PATH + os.path.sep + f))
                files.append({'file_name' : f, 'data' : data})
        for f in files:
            (shortname, extension) = os.path.splitext(f['file_name'])
            if extension == '.tar':
                resp['file_backup'].append(f)
    else:
        resp['file_backup'].append({})

    return HttpResponse(simplejson.dumps(resp))

@staff_member_required
def damadmin_download_file_backup(request, filename):
    from django.views.static import serve
    

    response = serve(request, filename, document_root = BACKUP_PATH)
    
    response['Content-Disposition'] = 'attachment; filename=%s'%filename

    logger.info("\n Filename: %s\n" %filename)
    
    return response

@staff_member_required
def damadmin_delete_file_backup(request):
    
    try:
        filename = request.POST.get('filename')
        filename_path = os.path.join(BACKUP_PATH, filename)
        os.remove(filename_path)
        return HttpResponse(simplejson.dumps({'success': True}))
    except Exception, ex:
        logger.exception(ex)
        return HttpResponse(simplejson.dumps({'success': False}))


@staff_member_required
def damadmin_create_file_backup(request):
    from api.views import Auth, WorkspaceResource, ItemResource, KeywordsResource
    import tempfile
    import tarfile
    from django.utils.simplejson.decoder import JSONDecoder
    from django.utils.simplejson.encoder import JSONEncoder    

    try:
        json_enc = JSONEncoder()
         
        name = request.POST.get('name')
        if not os.path.exists(BACKUP_PATH):
            os.mkdir(BACKUP_PATH)
        
        archive_name = name + '.tar'
        backup_file = os.path.join(BACKUP_PATH,archive_name)
        
        basedir = tempfile.mkdtemp()
        f = file(os.path.join(basedir, 'users.json'), 'w')
#User
        resp = Auth()._get_users()
        logger.info(resp)
        f.write(json_enc.encode(resp))
        f.close()

        for w in WorkspaceResource()._get_list(Workspace.objects.all()):
            #Backup workspace
            logger.info("Export workspace %s" % w['id'])
            workspacedir = os.path.join(basedir,'w_' + str(w['id']))
            os.mkdir(workspacedir)
            
            items = WorkspaceResource()._get_items(w['id'])
    
    
            logger.info("workspace.json")
            f = file(os.path.join(workspacedir, 'workspace.json'), 'w')
            f.write(json_enc.encode(WorkspaceResource()._read(w['id'])))
            f.close()
    
            #Backup collections
            logger.info("collections.json")
            f = file(os.path.join(workspacedir, 'collections.json'),'w')
            f.write(json_enc.encode(WorkspaceResource()._get_collections(w['id'])))    
            f.close()
    
            #Backup keywords
            logger.info("keywords.json")
            f = file(os.path.join(workspacedir, 'keywords.json'),'w')
#            logger.info("\n\n\n %s " %KeywordsResource()._read(User.objects.get(pk = request.session['_auth_user_id']), w['id'], None, True))
            f.write(json_enc.encode(KeywordsResource()._read(User.objects.get(pk = request.session['_auth_user_id']), w['id'], None, True)))
            f.close()
            
            #Backup renditions configuration
            logger.info( "renditions.json")
            f = file(os.path.join(workspacedir, 'renditions.json'),'w')
            f.write(json_enc.encode(WorkspaceResource()._get_variants(w['id'])))
            f.close()

            #Backup smartfolder configuration
            logger.info("smartfolders.json")
            f = file(os.path.join(workspacedir, 'smartfolders.json'),'w')
            f.write(json_enc.encode(WorkspaceResource()._get_smartfolders(w['id'])))
            f.close()
    
            #_workspace_get_members
            logger.info("members.json")
            f = file(os.path.join(workspacedir, 'members.json'),'w')
            f.write(json_enc.encode(WorkspaceResource()._get_members((w['id']))))
            f.close()
    
            
            #Backup items
            logger.info("items %s" %items)
            for i in items:
                #Backup item's metadata
                item = ItemResource()._read(User.objects.get(pk = request.session['_auth_user_id']), i, True, w['id'], [])
               
                logger.debug("===========")
                logger.debug("%s" %item['id'])
    

                itemdir = os.path.join(workspacedir, 'i_' + str(item['id']))
                os.mkdir(itemdir)    
                itemjson = json_enc.encode(item)
                f = file(os.path.join(itemdir,'item.json'),'w')
                f.write(itemjson)
                f.close()

                #read item's rendition
                f = file(os.path.join(itemdir,'rendition.json'),'w')
                f.write(json_enc.encode(WorkspaceResource()._get_variants(w['id'])))
                f.close()        
               
        logger.debug('backup_file %s'%backup_file)
        t = tarfile.open(backup_file, 'w')
        t.add(basedir,arcname='backup')
        t.close()

        return HttpResponse(simplejson.dumps({'success': True}))

    except Exception, ex:
        logger.exception(ex)
        return HttpResponse(simplejson.dumps({'success': False}))  
    

#@staff_member_required
#def damadmin_create_file_backup(request):      
#    import subprocess
#    
#    try:
#        name = request.POST.get('name')
#        #test if exist folder BACKUP_PATH
#        if not os.path.exists(BACKUP_PATH):
#            os.mkdir(BACKUP_PATH)
#    except Exception, ex:
#        logger.exception(ex)
#        return HttpResponse(simplejson.dumps({'success': False}))  
#
#    try:
##        mycmd = os.path.join(INSTALLATIONPATH,'api/fixtures/test_data.json')
##        arg = []
##        arg.append("python ")
##        arg.append("%s/manage.py loaddata"%INSTALLATIONPATH)
##        arg.append("%s"%mycmd)
##        logger.info('arg %s' %arg)
##        retcode = subprocess.call(arg)
#        mycmd = os.path.join(INSTALLATIONPATH,'migration_scripts/ndexport.py')
#        if os.path.exists(BACKUP_PATH) and os.path.exists(mycmd):
#            arg = []
#            arg.append("python")
#            arg.append("%s"%mycmd)
#            arg.append('-a')
#            arg.append("%s" %BACKUP_PATH)
#            arg.append('-f')
#            arg.append(name)
#            arg.append('-u')
#            arg.append('admin')
#            arg.append('-p')
#            arg.append('notredam')
#            arg.append('-m')
#            logger.info('arg %s' %arg)
#            retcode = subprocess.call(arg)
#            if retcode < 0:
#                logger.info("Child was terminated by signal %s" %retcode)
#            else:
#                logger.info("Child returned %s" %retcode)
#            return HttpResponse(simplejson.dumps({'success': True}))
#        else:
#            return HttpResponse(simplejson.dumps({'success': False}))               
#    except OSError, e:
#        logger.exception( "Execution failed: %s" %e)
#        return HttpResponse(simplejson.dumps({'success': False}))  
