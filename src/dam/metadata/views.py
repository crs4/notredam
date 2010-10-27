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

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.contrib.auth.models import User
from django.db.models import Q

from dam.repository.models import Item, Component
from dam.preferences.models import DAMComponent, DAMComponentSetting
from dam.preferences.views import get_metadata_default_language
from dam.workspace.models import DAMWorkspace as Workspace
from dam.metadata.models import MetadataLanguage, MetadataValue, MetadataProperty, MetadataDescriptorGroup, MetadataDescriptor, RightsValue
from dam.variants.models import Variant
from dam.core.dam_workspace import decorators
from dam.batch_processor.models import MachineState, Action, Machine
from dam.core.dam_metadata.models import XMPNamespace, XMPStructure

from mx.DateTime.Parser import DateTimeFromString
import logger
import re
import time

@login_required
def get_cuepoint_keywords(request):
    """
    Get cue point keywords list from system preferences
    """

    item_id = request.POST.get('item_id')

    item = Item.objects.get(pk=item_id)

    schema = MetadataProperty.objects.get(field_name='CuePoint')
    keyword_schema = MetadataProperty.objects.get(field_name='CPKeyword')

    values = item.get_metadata_values(schema)

    setting = DAMComponentSetting.objects.get(name__iexact='cue_point_list')
    value = setting.get_user_setting_by_level().split(',')

    formatted_values = []
    keywords = []

    if values:
        for el in values:
            tmp_dict = {}
            for k, v in el.iteritems():
                new_key = MetadataProperty.objects.get(pk=k).field_name
                tmp_dict[new_key] = v
            formatted_values.append(tmp_dict)

    for current_keyword in value:
        keyword_dict = {'keyword': current_keyword, 'item_values': []}
        for v in formatted_values:
            if v.get('CPKeyword') == current_keyword:
                keyword_dict['item_values'].append(v)                
        keywords.append(keyword_dict)

    resp = {'keywords':keywords}

    return HttpResponse(simplejson.dumps(resp))

@login_required
def set_cuepoint(request):
    """
    Set cue points for the given item
    """

    item_id = request.POST.get('item')
    cuepoints = simplejson.loads(request.POST.get('cuepoints'))
    
    schema = MetadataProperty.objects.get(field_name='CuePoint')
    
    item = Item.objects.get(pk=item_id)
    
    item.metadata.filter(schema=schema).delete()
    
    for x in xrange(1, len(cuepoints)+1):
    	cp = cuepoints[x-1]
    	keyword = cp['keyword']
    	value = cp['value']
    	start = cp['start']
    	duration = cp['duration']

    	item.metadata.create(schema=schema, xpath='notreDAM:CuePoint[%d]/notreDAM:CPKeyword' % x, value=keyword)
    	item.metadata.create(schema=schema, xpath='notreDAM:CuePoint[%d]/notreDAM:CPStart' % x, value=start)
    	item.metadata.create(schema=schema, xpath='notreDAM:CuePoint[%d]/notreDAM:CPDuration' % x, value=duration)
    	item.metadata.create(schema=schema, xpath='notreDAM:CuePoint[%d]/notreDAM:CPValue' % x, value=value)

    return HttpResponse('')

@login_required
def get_item_cuepoint(request):
    """
    Retrieves cue points of the given item
    """

    item_id = request.POST.get('item')
    
    
    logger.debug(values)
    
    return HttpResponse('')

def _add_sync_machine(component):

    end = MachineState.objects.create(name='finished')

    embed_action = Action.objects.create(component=component, function='embed_xmp')
    embed_state = MachineState.objects.create(name='comp_xmp', action=embed_action)

    embed_state.next_state = end
    embed_state.save()

    embed_task = Machine.objects.create(current_state=embed_state, initial_state=embed_state)

@login_required
def sync_component(request):
    """
    Export XMP metadata of the given items/variants
    """

    items = request.POST.getlist('items')
    variants = request.POST.getlist('variants')

    workspace = request.session['workspace']
    
    # update xmp:MetadataDate
    try:
        variant_name = request.POST.get('obj', 'original')
        user = User.objects.get(pk=request.session['_auth_user_id'])
        default_language= get_metadata_default_language(user, workspace)
        metadata_schema = MetadataProperty.objects.get(field_name = 'MetadataDate')
        metadataschema_id = str(metadata_schema.pk)
        metadatavalue = time.strftime("%d/%m/%yT%H:%M%S",time.gmtime()) + time.strftime('%z')
        my_metadata = {metadataschema_id.decode('utf-8'):[metadatavalue.decode('utf-8')]}
        items_objs = Item.objects.filter(pk__in=items)
        MetadataValue.objects.save_metadata_value(items_objs, my_metadata, variant_name, workspace, default_language)
    except Exception, err:
        print 'Error while changing xmp MetadataDate: ', err
    # end of xmp:MetadataDate updating

    for pk in items:
    
        item = Item.objects.get(pk=pk)
    
        components = item.get_variants(workspace)

        if 'all' in variants:
            sync_comp = components
        else:
            sync_comp = components.filter(variant__name__in=variants)

        for component in sync_comp:

            _add_sync_machine(component)
    return HttpResponse('')


@login_required
def get_basic_descriptors(request): 
    """
    Returns basic descriptors for the given item
    """
    item_ids = request.POST.get('items', '')
    item_list = item_ids.split(',')

    workspace = request.session['workspace']

    user = User.objects.get(pk=request.session['_auth_user_id'])

    item = Item.objects.get(pk=item_list[0])
    values = item.get_formatted_descriptors(user, workspace)
    
    resp_dict = {'descriptors': values}
    resp = simplejson.dumps(resp_dict)
    return HttpResponse(resp)

@login_required
@decorators.permission_required('edit_metadata')
def save_metadata(request):

    """
    Save XMP Values for the items in item_list
    """

    metadata = simplejson.loads(request.POST.get('metadata'))

    item_list = request.POST.getlist('items')
    variant_name = request.POST.get('obj', 'original')

    workspace = request.session.get('workspace', None) 

    user = User.objects.get(pk=request.session['_auth_user_id'])
    default_language = get_metadata_default_language(user, workspace)

    items = Item.objects.filter(pk__in=item_list)
    MetadataValue.objects.save_metadata_value(items, metadata, variant_name, workspace, default_language)

    return HttpResponse('OK')   

@login_required
@decorators.permission_required('edit_metadata')
def save_descriptors(request):

    """
    Save descriptors values (method called by DAM GUI)
    """

    metadata = simplejson.loads(request.POST.get('metadata'))

    item_list = request.POST.getlist('items')
    variant_name = request.POST.get('obj', 'original')

    ctype_item = ContentType.objects.get_for_model(Item)
    ctype_obj = ContentType.objects.get_for_model(Component)

    workspace = request.session.get('workspace', None) 
    user = User.objects.get(pk=request.session['_auth_user_id'])

    default_language = get_metadata_default_language(user, workspace)

    items = Item.objects.filter(pk__in=item_list)            
            
    for m in metadata:
        ids = m.split('_')
        desc_id = ids[1]
        if desc_id == 'license':
            license_id = metadata[m]
            license = RightsValue.objects.get(pk=int(license_id))
            comp = Component.objects.get(item=item, variant__name=variant_name, workspace=workspace)
            comp.save_rights_value(license, workspace)
        else:
            descriptor = MetadataDescriptor.objects.get(pk=int(desc_id))
            if len(ids) == 2:
                MetadataValue.objects.save_descriptor_values(descriptor, items, metadata[m], workspace, variant_name, default_language)
            else:
                MetadataValue.objects.save_descriptor_structure_values(descriptor, ids[2], items, metadata[m], workspace, variant_name)
                        
    return HttpResponse('OK')

def get_items_types(item_list):

    """
    Returns the media types of the items in item_list
    """

    types = Item.objects.filter(pk__in=item_list).values_list('type__name', flat=True)
    item_media_types = set(types)
  
    return item_media_types

def get_components_types(item_list, variant, workspace):

    """
    Returns the media types of the components of the items in item_list
    """

    components_types = set()

    for i in item_list:
                
        if len(i.strip()) == 0:
            break

        comp=Component.objects.get(item__pk=i, variant__name=variant, workspace=workspace)

        components_types.add(comp.media_type.name)

    return components_types

def get_components_list(item_list, variant, workspace):

    """
    Returns the component ids of the items in item_list
    """

    ids = Component.objects.filter(item__pk__in=item_list, variant__name=variant, workspace=workspace).values_list('pk', flat=True)

    return ids    

def _advanced_metadata_view(item_list, workspace, default_language, metadata_object, media_types):
    """
    Returns list of metadata in XMP Editing Mode
    """

    form_list = []
    items_types = get_items_types(item_list)
    components_types = get_components_types(item_list, metadata_object, workspace)
    components_list = get_components_list(item_list, metadata_object, workspace)

    for namespace in XMPNamespace.objects.all():
        metadataschema_list = MetadataProperty.objects.filter(namespace=namespace).exclude(namespace__prefix='notreDAM').exclude(xmpstructure__in=XMPStructure.objects.all()).order_by('field_name')
        for metadataschema in metadataschema_list:
  
#            schema_media_types = set(metadataschema.media_type.all().values_list('name', flat=True))

#            if schema_media_types & media_types != media_types:
#                continue

            form_list.append(metadataschema.metadata_definition())

            schema_value, multiple_values, to_be_deleted = MetadataValue.objects.get_metadata_values(item_list, metadataschema, items_types, components_types, components_list)

            if to_be_deleted:
                form_list.pop()
                continue

            form_list[-1]['value'] = schema_value[item_list[0]]
            form_list[-1]['multiplevalues'] = multiple_values

            if metadataschema.type == 'lang':
                form_list[-1]['choices'] = schema_value[item_list[0]]
                form_list[-1]['value'] = schema_value[item_list[0]].get(default_language, '')
    return form_list

def _generate_metadata_structure_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language):

    metadata_list = []

    metadata_info = _generate_metadata_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language)

    if metadata_info:

        structure = XMPStructure.objects.get(name=metadata_info['type'])
        for schema in structure.properties.all():
            schema_info = schema.metadataproperty.metadata_definition()
            schema_info['id'] = '%d_%d_%d' % (group.id, metadatadescriptor.id, schema.id)
            schema_info['groupname'] = group.name
            schema_info['value'] = ''
            schema_info['array'] = False
            schema_info['is_choice'] = False
            if schema.type == 'lang':
                schema_info['type'] = 'text'               
            schema_info['tooltip'] = "%s/%s:%s" % (metadata_info['tooltip'].strip(), schema.namespace.prefix, schema.field_name)

            if metadata_info['value']:
                first_item = metadata_info['value'][0]                
                schema_info['value'] = first_item.get(schema.id, '')

            metadata_list.append(schema_info)
                
    return metadata_list

def _generate_metadata_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language):

    metadata_info = None

    for m in metadatadescriptor.properties.all():

        metadata_info = m.metadata_definition()

        schema_value, multiple_values, to_be_deleted = MetadataValue.objects.get_metadata_values(item_list, m, items_types, components_types, components_list)

        if not to_be_deleted:
            metadata_info['to_be_deleted'] = False
        else:
            continue

        if schema_value[item_list[0]]:
            metadata_info['value'] = schema_value[item_list[0]]
            metadata_info['multiplevalues'] = multiple_values

            if m.type == 'lang':
                metadata_info['choices'] = schema_value[item_list[0]]
                metadata_info['value'] = schema_value[item_list[0]].get(default_language, '')

            if metadata_info['value']:
                break

    if metadata_info:

        metadata_info['id'] = '%d_%d' % (group.id, metadatadescriptor.id)
        metadata_info['name'] = metadatadescriptor.name
        metadata_info['groupname'] = group.name
        metadata_info['editable'] = False

        if not metadata_info.has_key('to_be_deleted'):
            metadata_info['to_be_deleted'] = True

        if metadata_info['to_be_deleted']:
            return None
        else:
            del(metadata_info['to_be_deleted'])    

        tooltip = ""
    
        for m in metadatadescriptor.properties.all():
            tooltip += "%s:%s - " % (m.namespace.prefix, m.field_name)
    
        metadata_info['tooltip'] = tooltip[:-2]
    
        for m in metadatadescriptor.properties.all():
            if m.editable:
                metadata_info['editable'] = True
                break

    return metadata_info

def _simple_metadata_view(item_list, workspace, default_language, metadata_object, media_types):
    """
    Returns list of metadata in Metadata Editing Mode (use descriptors instead of XMP Properties)
    """
    form_list = []
    items_types = get_items_types(item_list)
    components_types = get_components_types(item_list, metadata_object, workspace)
    components_list = get_components_list(item_list, metadata_object, workspace)

    my_groups = MetadataDescriptorGroup.objects.filter(workspace=workspace)
    my_groups = my_groups.exclude(basic_summary=True).exclude(specific_basic=True).exclude(specific_full=True).exclude(upload=True)

    if my_groups.count() == 0:
        my_groups = MetadataDescriptorGroup.objects.filter(workspace__isnull=True)
        my_groups = my_groups.exclude(basic_summary=True).exclude(specific_basic=True).exclude(specific_full=True).exclude(upload=True)
    
    for group in my_groups:
    
        metadatadescriptor_list = group.descriptors.all().order_by('name')

        if group.name == 'Rights':
            rights = None
            rights_mv = False
            for i in item_list:
                item = Item.objects.get(pk=i)
                comp = Component.objects.get(item=item, variant__name=metadata_object, workspace=workspace)
                if rights:
                    my_rights = comp.comp_rights.all()
                    if my_rights.count():
                        if my_rights[0] != rights:
                            rights_mv = True
                else:
                    if comp.comp_rights.all().count() > 0:
                        rights = comp.comp_rights.all()[0]
            if rights:
                rights = rights.value
            else:
                rights = ''
            choices = [[c.id, c.value] for c in RightsValue.objects.all()]
            form_list.append({'id': '%d_license' % (group.id), 'name': 'License', 'choices': choices, 'groupname': group.name, 'tooltip': 'License', 'value': rights, 'type': 'text', 'editable': True, 'is_variant': True, 'is_choice': 'close_choice', 'array': False, 'multiplevalues': rights_mv})

        for metadatadescriptor in metadatadescriptor_list:
  
            metadataschemas = metadatadescriptor.properties.all()
            if metadataschemas.count():
                metadataschema = metadataschemas[0]

                if metadataschema.type in XMPStructure.objects.all().values_list('name', flat=True):
                    
                    metadata_info = _generate_metadata_structure_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language)
                    
                    if metadata_info:
                        form_list.extend(metadata_info)                    
                    
                else:
                
                    metadata_info = _generate_metadata_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language)
                    
                    if metadata_info:
                        form_list.append(metadata_info)                    
                    
    return form_list

@login_required
def get_metadata_structures(request):
    """
    Returns the list of XMP Structures and their definitions
    """
    structure_list = {}
    for s in XMPStructure.objects.all():
        structure_list[s.name] = [p.metadataproperty.metadata_definition() for p in s.properties.all()]

    resp = simplejson.dumps(structure_list)
    return HttpResponse(resp)

@login_required
def get_metadata(request):
    """
    Get metadata for the given items
    """
    item_list = request.POST.getlist('items')
    metadata_object = request.POST.get('obj', 'original')
    metadata_view = request.POST.get('advanced', False)
    workspace = request.session.get('workspace', None) 
    user = User.objects.get(pk=request.session['_auth_user_id'])
    default_language = get_metadata_default_language(user, workspace)
    if metadata_view == 'true':
        metadata_view = True
    else:
        metadata_view = False

    try:
    
        item_media_types = set(Item.objects.filter(pk__in=item_list).values_list('type__name', flat=True))
    
        if metadata_view:
            form_list = _advanced_metadata_view(item_list, workspace, default_language, metadata_object, item_media_types)
        else:
            form_list = _simple_metadata_view(item_list, workspace, default_language, metadata_object, item_media_types)
        form_dict = {'rows': form_list}
    except Exception, ex:
        logger.exception(ex)
        form_dict = {'rows': []}

    resp = simplejson.dumps(form_dict)
    
    return HttpResponse(resp)

def _get_ws_groups(workspace, type=None):

    query = {'workspace': workspace}
    
    if type in ['basic_summary', 'specific_full', 'specific_basic']:
        query[str(type)] = True
    else:
        query['basic_summary'] = False
        query['specific_full'] = False
        query['specific_basic'] = False
        query['upload'] = False
        
    try: 
        groups = MetadataDescriptorGroup.objects.filter(**query)
        if groups.count() == 0:
            del(query['workspace'])
            groups = MetadataDescriptorGroup.objects.filter(**query)
    except:
        del(query['workspace'])
        groups = MetadataDescriptorGroup.objects.filter(**query)

    return groups

@login_required
def wsadmin_config_descriptors(request, type='basic_summary'):
    """
    Workspace Metadata Configuration: retrieve descriptors
    """
    workspace = request.session.get('workspace')
    
    groups = _get_ws_groups(workspace, type)

    data = {'elements':[]}
    
    for g in groups:
        descriptors = g.descriptors.all();
        for d in descriptors:
            my_prop = []
            my_prop_ids = []
            for p in d.properties.all():
                xmp_name = "%s:%s" % (p.namespace.prefix, p.field_name)
                my_prop.append(xmp_name)
                my_prop_ids.append(p.id)
            data['elements'].append({'id':d.id, 'name':d.name, 'properties': my_prop, 'properties_ids': my_prop_ids})
            
    return HttpResponse(simplejson.dumps(data))
    
@login_required
def wsadmin_get_descriptor_properties(request):
    """
    Workspace Metadata Configuration: retrieve XMP properties
    """

    prop_list = simplejson.loads(request.POST.get('prop_list'))
    variant_only = request.POST.get('variant', 'all')
    if variant_only == 'variant':
        props = MetadataProperty.objects.filter(is_variant=True).exclude(xmpstructure__in=XMPStructure.objects.all()).exclude(pk__in=prop_list)
    elif variant_only == 'item':
        props = MetadataProperty.objects.filter(is_variant=False).exclude(xmpstructure=XMPStructure.objects.all()).exclude(pk__in=prop_list)
    else:
        props = MetadataProperty.objects.exclude(xmpstructure__in=XMPStructure.objects.all()).exclude(pk__in=prop_list)
    data = {'elements':[]}
    desc_props = MetadataProperty.objects.filter(pk__in=prop_list)
    for p in desc_props: 
        xmp_name = "%s:%s" % (p.namespace.prefix, p.field_name)
        data['elements'].append({'id':p.id, 'name':xmp_name, 'selected': True})
    for g in props:
        xmp_name = "%s:%s" % (g.namespace.prefix, g.field_name)
        data['elements'].append({'id':g.id, 'name':xmp_name})
    return HttpResponse(simplejson.dumps(data))    

def _get_new_desc(d):

    properties = MetadataProperty.objects.filter(pk__in=d['properties_ids'])

    if d['id'] > 0:
        desc = MetadataDescriptor.objects.get(pk=d['id'])
        old_properties = desc.properties.all()
        desc.properties.remove(*old_properties)
    else:
        desc = MetadataDescriptor.objects.create(name=d['name'], custom=True)

    desc.name = d['name']

    for p in properties:
        desc.properties.add(p)

    desc.save()

    return desc

@login_required
def wsadmin_save_ws_descriptors(request):
    """
    Workspace Metadata Configuration: Save descriptors for the current workspace
    """

    workspace = request.session.get('workspace')

    basic_list = simplejson.loads(request.POST.get('basic'))
    vbasic_list = simplejson.loads(request.POST.get('vbasic'))
    vfull_list = simplejson.loads(request.POST.get('vfull'))
    groups_list = simplejson.loads(request.POST.get('custom_groups'))

    MetadataDescriptorGroup.objects.filter(workspace=workspace).delete()
    
    basic_group = MetadataDescriptorGroup.objects.create(name='Basic', workspace=workspace, basic_summary=True)
    vbasic_group = MetadataDescriptorGroup.objects.create(name='Variant Basic', workspace=workspace, specific_basic=True)
    vfull_group = MetadataDescriptorGroup.objects.create(name='Variant Full', workspace=workspace, specific_full=True)

    for g in groups_list:
        new_group = MetadataDescriptorGroup.objects.create(name=g['name'], workspace=workspace)        

        for d in g['descriptors']:
        
            desc = _get_new_desc(d)
                    
            new_group.descriptors.add(desc)
            
    basic_descs = []
    vbasic_descs = []
    vfull_descs = []

    for d in basic_list:
    
        desc = _get_new_desc(d)
                
        basic_group.descriptors.add(desc)

    for d in vbasic_list:

        desc = _get_new_desc(d)

        vbasic_group.descriptors.add(desc)

    for d in vfull_list:

        desc = _get_new_desc(d)

        vfull_group.descriptors.add(desc)

    return HttpResponse(simplejson.dumps({'success': True}))



@login_required
def wsadmin_config_descriptor_groups(request):
    """
    Workspace Metadata Configuration: retrieve descriptor groups
    """

    workspace = request.session.get('workspace')
    
    groups = _get_ws_groups(workspace)

    data = {'elements':[]}
    
    groups = groups.exclude(basic_summary=True).exclude(specific_basic=True).exclude(specific_full=True).exclude(upload=True)

    for g in groups:
        descriptors = g.descriptors.all();
        g_desc_list = []
        for d in descriptors:
            my_prop = []
            my_prop_ids = []
            for p in d.properties.all():
                xmp_name = "%s:%s" % (p.namespace.prefix, p.field_name)
                my_prop.append(xmp_name)
                my_prop_ids.append(p.id)
            g_desc_list.append({'id':d.id, 'name':d.name, 'properties': my_prop, 'properties_ids': my_prop_ids})
        data['elements'].append({'id':g.id, 'name':g.name, 'descriptors': g_desc_list})
            
    return HttpResponse(simplejson.dumps(data))

@login_required
def wsadmin_set_default_descriptors(request):
    """
    Workspace Metadata Configuration: Reset configuration to defaults
    """

    workspace = request.session.get('workspace')

    my_groups = MetadataDescriptorGroup.objects.filter(workspace=workspace)
    for g in my_groups:
        my_descs = g.descriptors.filter(custom=True)
        my_descs.delete()

    my_groups.delete()
    
    return HttpResponse(simplejson.dumps({'success': True}))


