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
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.contrib.auth.models import User

from dam.repository.models import Item,Component
from dam.preferences.models import DAMComponent, DAMComponentSetting
from dam.preferences.views import get_user_setting
from dam.workspace.models import Workspace
from dam.metadata.models import MetadataLanguage, Namespace, MetadataValue, MetadataProperty, MetadataDescriptorGroup, MetadataStructure, MetadataDescriptor, RightsValue
from dam.variants.models import Variant, VariantAssociation
from dam.workspace import decorators
from dam.batch_processor.models import MachineState, Action, Machine

from mx.DateTime.Parser import DateTimeFromString
from mimetypes import guess_type
from os import path
import logger
import re

@login_required
def sync_component(request):

    items = request.POST.getlist('items')
    workspace = request.session['workspace']
    
    for pk in items:
    
        item = Item.objects.get(pk=pk)
    
        components = item.get_variants(workspace)
    
        original = components.filter(variant__name='original')[0]
    
        end = MachineState.objects.create(name='finished')
    
        embed_action = Action.objects.create(component=original, function='embed_xmp')
        embed_state = MachineState.objects.create(name='comp_xmp', action=embed_action)
    
        embed_state.next_state = end
        embed_state.save()
    
        embed_task = Machine.objects.create(current_state=embed_state, initial_state=embed_state)

    return HttpResponse('')
    

def get_metadata_default_language(user, workspace=None):
    """
    Returns default metadata language for the given user (or the application default)
    """
    component=DAMComponent.objects.get(name__iexact='metadata')
    setting=DAMComponentSetting.objects.get(component=component, name__iexact='default_metadata_language')
    comma_separated_languages = get_user_setting(user, setting, workspace)
    list_of_languages = comma_separated_languages.split(',')
    return list_of_languages[0]

@login_required
def get_variants_menu_list(request):
    """
    Returns the list of variants of the current workspace
    """
    workspace = request.session['workspace']
    
    vas = VariantAssociation.objects.filter(workspace = workspace, variant__default_url__isnull = True, variant__editable = True).exclude(variant__name='original').exclude(variant__name='thumbnail').order_by('variant__name').values_list('variant__name', flat=True)  
    
    vas = set(vas)
    
    resp = {'variants':[]}
    for va in vas:
        resp['variants'].append({'variant_name': va})
    return HttpResponse(simplejson.dumps(resp))

def get_lang_pref(request):
    """
    Returns the list of available metadata languages chosen by the given user
    """
    workspace = request.session['workspace']
    
    user = User.objects.get(pk=request.session['_auth_user_id'])
    component=DAMComponent.objects.get(name__iexact='metadata')
    setting=DAMComponentSetting.objects.get(component=component, name__iexact='supported_languages')
    comma_separated_languages = get_user_setting(user, setting, workspace)
    list_of_languages = comma_separated_languages.split(',')
    resp = {'languages':[]}
    default_language = get_metadata_default_language(user,workspace)
    languages = MetadataLanguage.objects.filter(code__in=list_of_languages).values('code', 'language', 'country')
    for l in languages:
        if l['code'] == default_language:
            l['default_value'] = True
        resp['languages'].append(l)
    return HttpResponse(simplejson.dumps(resp))

def _get_formatted_descriptors(descriptors, user, workspace):
    """
    
    """
    default_language = get_metadata_default_language(user, workspace)
    values = []
    for d, v in descriptors.iteritems():
        desc = MetadataDescriptor.objects.get(pk=d)
        desc_dict = {'caption': '%s' % desc.name}
        desc_value = v

        if isinstance(v, dict):
            if v.has_key(default_language):
                desc_value = v.get(default_language)
            else:
                continue
        elif isinstance(v, list):
            for value in v:
                if isinstance(value, dict):
                    if not isinstance(desc_value, dict):
                        desc_value = {'properties': []}
                    for key, v_value  in value.iteritems():
                        p = MetadataProperty.objects.get(pk=key)
                        desc_value['properties'].append({'caption': p.caption, 'value': v_value})

        desc_dict['value'] = desc_value

        values.append(desc_dict)
    
    return values


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
    descriptors = item.get_descriptors(workspace)
    
    values = _get_formatted_descriptors(descriptors,  user, workspace)

    resp_dict = {'descriptors': values}
    resp = simplejson.dumps(resp_dict)
    return HttpResponse(resp)

def set_modified_flag(mtdata, comp):

   """
   Set flag modified in metadata and in Component
   """
   if mtdata.modified == False:
       mtdata.modified = True
       mtdata.save()
   if isinstance(comp, Component):
       if comp.modified_metadata == False:
           comp.modified_metadata = True
           comp.save()

def save_metadata_value(item_list, metadata, metadata_object, workspace, default_language='en-US'):
    
    """
    Save XMP Values for the items in item_list
    """
    
    ctype_item = ContentType.objects.get_for_model(Item)
    ctype_obj = ContentType.objects.get_for_model(Component)

    for i in item_list:
        item = Item.objects.get(pk=i)
        for m in metadata:
            metadataschema = MetadataProperty.objects.get(pk=int(m))

            if metadataschema.is_variant:
                obj = Component.objects.get(item=item, variant__name=metadata_object, workspace=workspace)
                ctype = ctype_obj
            else:
                obj = item
                ctype = ctype_item

            obj.metadata.filter(schema__id=int(m)).delete()

            if isinstance(metadata[m], list):
                if metadataschema.type == 'lang':
                    for value in metadata[m]:
                        new_metadata = MetadataValue.objects.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=value[0], language=value[1])
                        set_modified_flag(new_metadata[0],obj)
                else:
                    for index in range(len(metadata[m])):
                        value = metadata[m][index]
                        if isinstance(value, dict):
                            for k, v in value.iteritems():
                                subproperty = MetadataProperty.objects.get(pk=int(k))
                                xpath = '%s:%s[%d]/%s:%s' % (metadataschema.namespace.prefix, metadataschema.field_name, index+1, subproperty.namespace.prefix, subproperty.field_name)
                                if subproperty.type == 'lang':
                                    new_metadata = MetadataValue.objects.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath, language=default_language)                                        
                                    set_modified_flag(new_metadata[0],obj)
                                else:
                                    new_metadata = MetadataValue.objects.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath)
                                    set_modified_flag(new_metadata[0],obj)
                        else:
                            new_metadata = MetadataValue.objects.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=value)
                            set_modified_flag(new_metadata[0],obj)
            else:
                value = metadata[m]
                new_metadata = MetadataValue.objects.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=value)
                set_modified_flag(new_metadata[0],obj)

@login_required
#@decorators.permission_required('edit_metadata')
def save_metadata(request):

    """
    Save XMP Values for the items in item_list
    """

    metadata = simplejson.loads(request.POST.get('metadata'))

    item_list = request.POST.getlist('items')
    metadata_object = request.POST.get('obj', 'original')

    workspace = request.session.get('workspace', None) 

    user = User.objects.get(pk=request.session['_auth_user_id'])
    default_language = get_metadata_default_language(user, workspace)

    save_metadata_value(item_list, metadata, metadata_object, workspace, default_language)

    return HttpResponse('OK')   

def save_descriptor_values(descriptor, item, values, workspace, metadata_object='original', default_language='en-US'):
	
    """
    Save descriptor values for the given item
    """	
	
    properties = descriptor.properties.filter(media_type__name=item.type)
    ctype_item = ContentType.objects.get_for_model(Item)
    ctype_obj = ContentType.objects.get_for_model(Component)
    for p in properties:

        if not p.editable:
            continue

        if p.is_variant:
            obj = Component.objects.get(item=item, variant__name=metadata_object, workspace=workspace)
            ctype = ctype_obj
        else:
            obj = item
            ctype = ctype_item

        obj.metadata.filter(schema__id=int(p.id)).delete()

        if isinstance(values, list):
            if p.type == 'lang':
                if p.is_array != 'not_array':
                    for value in values:
                        new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value[0], language=value[1])
                        set_modified_flag(new_metadata[0],obj)
                else:
                    value = values[0]
                    new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value[0], language=value[1])                      
                    set_modified_flag(new_metadata[0],obj)
            else:
                if p.is_array != 'not_array':                   
                    for index in range(len(values)):
                        value = values[index]
                        if isinstance(value, dict):
                            for k, v in value.iteritems():
                                subproperty = MetadataProperty.objects.get(pk=int(k))                               
                                xpath = '%s:%s[%d]/%s:%s' % (p.namespace.prefix, p.field_name, index+1, subproperty.namespace.prefix, subproperty.field_name)
                                new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath)                               
                                set_modified_flag(new_metadata[0],obj)
                        else:
                            new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value)
                            set_modified_flag(new_metadata[0],obj)
                else:
                    value = values[0]
                    index = 0
                    if isinstance(value, dict):
                        for k, v in value.iteritems():
                            subproperty = MetadataProperty.objects.get(pk=int(k))                               
                            xpath = '%s:%s[%d]/%s:%s' % (p.namespace.prefix, p.field_name, index+1, subproperty.namespace.prefix, subproperty.field_name)
                            new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath)                               
                            set_modified_flag(new_metadata[0],obj)
                    else:
                        new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value)
                        set_modified_flag(new_metadata[0],obj)
        else:
            if p.type == 'lang':
                new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=values, language=default_language)
                set_modified_flag(new_metadata[0],obj)
            else:
                if p.is_array != 'not_array':
                    value = values.split(',')
                    for v in value:
                        new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=v.strip())
                        set_modified_flag(new_metadata[0],obj)
                else:
                    value = values
                    new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value)
                    set_modified_flag(new_metadata[0],obj)

def save_descriptor_structure_values(descriptor, schema_id, item, values, workspace, metadata_object='original'):
	
    """
    Save descriptor values for the given item 
    (if the descriptor is mapped to an array of XMP Structure, 
    it saves the values as the first item of the array)
    """
	
    properties = descriptor.properties.filter(media_type__name=item.type)
    ctype_item = ContentType.objects.get_for_model(Item)
    ctype_obj = ContentType.objects.get_for_model(Component)
    for p in properties:

        if not p.editable:
            continue

        if p.is_variant:
            obj = Component.objects.get(item=item, variant__name=metadata_object, workspace=workspace)
            ctype = ctype_obj
        else:
            obj = item
            ctype = ctype_item

        subproperty = MetadataProperty.objects.get(pk=int(schema_id))                               
        xpath = '%s:%s[1]/%s:%s' % (p.namespace.prefix, p.field_name, subproperty.namespace.prefix, subproperty.field_name)
        new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, xpath=xpath)
        new_metadata[0].value = values
        new_metadata[0].save()
        set_modified_flag(new_metadata[0],obj)

def save_rights_value(comp, license, workspace):

    """
    Save license to the given component and set xmp 
    values according to right rules (as defined in XMPRightsValue)
    """

    logger.debug("SAVING RIGHTS")

    comp.comp_rights = []    
    comp.metadata.filter(schema__rights_target=True).delete()
    license.components.add(comp)
    item_list = [comp.item.pk]

    xmp_values = {}
    for m in license.xmp_values.all():
        xmp_values[m.xmp_property.id] = m.value
    save_metadata_value(item_list, xmp_values, comp.variant.name, workspace)    

def save_variants_rights(item, workspace, variant):

    """
    Save license to the given component and set xmp 
    values according to right rules (as defined in XMPRightsValue)
    """
    
    comp = Component.objects.get(item=item, variant=variant, workspace=workspace)

    variant_association = VariantAssociation.objects.get(workspace = workspace,  variant = variant) 
    vp = variant_association.preferences

    if vp:
        license = vp.rights_type

        logger.debug(license)
    
        if license:
            save_rights_value(comp, license, workspace)
        else:
            comp.metadata.filter(schema__rights_target=True).delete()
            source_variant = variant.get_source(workspace,  item)
            original_comp = source_variant.get_component(workspace = workspace,  item = item) 
            comp.comp_rights = []
            comp.comp_rights.add(*original_comp.comp_rights.all())
            for m in original_comp.metadata.filter(schema__rights_target=True):
                MetadataValue.objects.create(schema = m.schema, xpath=m.xpath, content_object = comp,  value = m.value, language=m.language)

@login_required
#@decorators.permission_required('edit_metadata')
def save_descriptors(request):

    """
    Save descriptors values (method called by DAM GUI)
    """

    metadata = simplejson.loads(request.POST.get('metadata'))

    item_list = request.POST.getlist('items')
    metadata_object = request.POST.get('obj', 'original')

    ctype_item = ContentType.objects.get_for_model(Item)
    ctype_obj = ContentType.objects.get_for_model(Component)

    workspace = request.session.get('workspace', None) 
    user = User.objects.get(pk=request.session['_auth_user_id'])

    default_language = get_metadata_default_language(user, workspace)

    for i in item_list:
        if len(i.strip()) > 0:
            item = Item.objects.get(pk=i)
            for m in metadata:
                ids = m.split('_')
                desc_id = ids[1]
                if desc_id == 'license':
                    license_id = metadata[m]
                    license = RightsValue.objects.get(pk=int(license_id))
                    comp = Component.objects.get(item=item, variant__name=metadata_object, workspace=workspace)
                    save_rights_value(comp, license, workspace)
                else:
                    descriptor = MetadataDescriptor.objects.get(pk=int(desc_id))
                    if len(ids) == 2:
                        save_descriptor_values(descriptor, item, metadata[m], workspace, metadata_object, default_language)
                    else:
                        save_descriptor_structure_values(descriptor, ids[2], item, metadata[m], workspace, metadata_object)
                        
    return HttpResponse('OK')

def convert_rational(s):
    """
    Converts a rational XMP Value (es. ApertureSize 16/10) to
    float type
    """
    try:
        return float(s)
    except:
        num, denom = s.split('/')
        return round(float(num) / float(denom), 3)

def convert_datetime(s):
    """
    Convert a datetime string to a standard format
    """
    try:
        dt = DateTimeFromString(s)
        date_string = dt.Format("%m/%d/%Y %H:%M:%S")
        return date_string
    except:
        return s

def round_size(v1, v2):
    value = float(v1) + float(v2)/1024.0
    return str(round(value, 1))

def format_filesize(size):
    mb, r = divmod(size, 1048576)
    kb, b = divmod(r, 1024)
    if mb:
        return round_size(mb, kb) + ' MB'
    elif kb:
        return round_size(kb, b) + ' KB'
    else:
        return str(b) + ' bytes'

def get_items_types(item_list):

    """
    Returns the media types of the items in item_list
    """

    types = Item.objects.filter(pk__in=item_list).values_list('type', flat=True)
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
    
def get_metadata_values(item_list, metadataschema, items_types, components_types, components_list, component_obj=None):

    """
    Get metadataschema values for the given items/components
    """

    from django.db import connection

    to_be_deleted = False
    multiple_values = False

    values = {}

    object_list = []

    if not component_obj:
        if metadataschema.is_variant:
            ctype = ContentType.objects.get_for_model(Component)
        else:
            ctype = ContentType.objects.get_for_model(Item)
    else:
        if not metadataschema.is_variant:
            return (None, None, None)
        ctype = ContentType.objects.get_for_model(Component)

    required_media_types = set()

    if metadataschema.is_variant:
        object_list = ["'%s'" % c for c in components_list]
        required_media_types = components_types
    else:
        object_list = ["'%s'" % c for c in item_list]
        required_media_types = items_types

    schema_media_types = set(metadataschema.media_type.all().values_list('name', flat=True))

    if required_media_types - schema_media_types:
        return None, False, True
    
    if metadataschema.is_array != 'not_array' or metadataschema.is_choice == 'open_choice':
        if metadataschema.type == 'lang':
            values[item_list[0]] = {}
        else:
            values[item_list[0]] = []
    else:
        values[item_list[0]] = ''

    c = connection.cursor()
    c.execute("select schema_id, value, count(*), language, xpath from metadata_metadatavalue where schema_id=%d AND content_type_id=%d AND object_id IN (%s) GROUP BY schema_id, value, xpath, language;" % (metadataschema.id, ctype.id, str(",".join(object_list))))

    results = [r for r in c.fetchall()]
    

    xpath_re = re.compile(r'(?P<prefix>\w+):(?P<property>\w+)(?P<array_index>\[\d+\]){,1}')
    xpath_values = []

    for r in results:
        value = r[1]
        count = r[2]
        language = r[3]
        xpath = r[4]
        if r[2] < len(item_list): 
            multiple_values = True
        if metadataschema.type == 'filesize':
            value = format_filesize(float(value))
        elif metadataschema.type == 'rational':
            value = convert_rational(value)
        elif metadataschema.type == 'date_and_time':
            value = convert_datetime(value)
        if metadataschema.is_choice != 'not_choice':
            p_choice = metadataschema.property_choices.filter(value=str(value))
            if p_choice.count() > 0:
                if p_choice[0].description:
                    value = p_choice[0].description

        xpath_splitted = xpath_re.findall(xpath)

        if len(xpath_splitted) > 1:
            metadata_ns = xpath_splitted[1][0].strip()
            metadata_property = xpath_splitted[1][1].strip()
            metadata_index = xpath_splitted[0][2].strip()

            if len(metadata_index) == 0:
                metadata_index = 1
            else:
                metadata_index = int(re.sub('\D', '', metadata_index))

            while len(xpath_values) < metadata_index:
                xpath_values.append({})

            try:
                found_property = MetadataProperty.objects.get(namespace__prefix=metadata_ns, field_name__iexact=metadata_property)
            except Exception, ex:
                to_be_deleted = True
                logger.debug('metadata: %s %s %s, %s' % (xpath_splitted, metadataschema, metadata_property, str(ex)))
                break
            xpath_values[metadata_index-1][found_property.id] = value

        elif isinstance(values[item_list[0]], list):
            schema_value = value
            values[item_list[0]].append(schema_value)
        elif isinstance(values[item_list[0]], dict):
            values[item_list[0]][language] = value
        else:
            values[item_list[0]] = value

    if xpath_values:
        values[item_list[0]] = xpath_values

    if (len(results) == 0 or multiple_values) and not metadataschema.editable:
        to_be_deleted = True

    return values, multiple_values, to_be_deleted

def _metadata_definition(metadataschema):
    
    """
    Returns a dictionary containing definition info of a given metadataschema 
    (es. {type: string, array: true, editable: False, ...}
    """
    
    string_type_list = ['txt', 'proper_name','mimetype','agent_name','xpath' ,'date_only_year', 'rational']

    tooltip=metadataschema.namespace.prefix+':'+metadataschema.field_name + ": " + metadataschema.description

    definition = {'id': metadataschema.id, 'name': metadataschema.caption, 'groupname': metadataschema.namespace.name, 'tooltip': tooltip, 'value': '', 'type': metadataschema.type, 'editable': metadataschema.editable, 'is_variant': metadataschema.is_variant, 'is_choice': metadataschema.is_choice}

    if metadataschema.is_choice == 'close_choice' or metadataschema.is_choice == 'open_choice':
        choices = []

        for x in metadataschema.property_choices.all():
            if metadataschema.is_array != 'not_array':
                choices.append(x.value)
            else:
                if x.description:
                    choices.append([x.value, x.description])
                else:
                    choices.append([x.value, x.value])
                
        definition['choices'] = choices

    elif metadataschema.type in string_type_list:
        definition['type'] = 'text'

    if metadataschema.is_array == 'not_array':
        definition['array'] = 'false'
    else:
        definition['array'] = 'true'

    return definition

def _advanced_metadata_view(item_list, workspace, default_language, metadata_object, media_types):
    """
    Returns list of metadata in XMP Editing Mode
    """

    form_list = []
    items_types = get_items_types(item_list)
    components_types = get_components_types(item_list, metadata_object, workspace)
    components_list = get_components_list(item_list, metadata_object, workspace)

    for namespace in Namespace.objects.all():
        metadataschema_list = MetadataProperty.objects.filter(namespace=namespace).exclude(namespace__prefix='notreDAM').exclude(metadatastructure__in=MetadataStructure.objects.all()).order_by('field_name')
        for metadataschema in metadataschema_list:
  
#            schema_media_types = set(metadataschema.media_type.all().values_list('name', flat=True))

#            if schema_media_types & media_types != media_types:
#                continue

            form_list.append(_metadata_definition(metadataschema))

            schema_value, multiple_values, to_be_deleted = get_metadata_values(item_list, metadataschema, items_types, components_types, components_list)

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
        logger.debug(metadata_info)

        structure = MetadataStructure.objects.get(name=metadata_info['type'])
        for schema in structure.properties.all():
            schema_info = _metadata_definition(schema)
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

        metadata_info = _metadata_definition(m)

        schema_value, multiple_values, to_be_deleted = get_metadata_values(item_list, m, items_types, components_types, components_list)

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

            metadataschema = metadataschemas[0]

            if metadataschema.type in MetadataStructure.objects.all().values_list('name', flat=True):
                
                metadata_info = _generate_metadata_structure_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language)
                
                if metadata_info:
                    form_list.extend(metadata_info)                    
                
            else:
            
                metadata_info = _generate_metadata_item(group, metadatadescriptor, item_list, items_types, components_types, components_list, default_language)
                
                if metadata_info:
                    form_list.append(metadata_info)                    
                    
    return form_list

def get_metadata_structures(request):
    """
    Returns the list of XMP Structures and their definitions
    """
    structure_list = {}
    for s in MetadataStructure.objects.all():
        structure_list[s.name] = [_metadata_definition(p) for p in s.properties.all()]

    resp = simplejson.dumps(structure_list)
    return HttpResponse(resp)

@login_required
def get_metadata(request):
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
    
        item_media_types = set(Item.objects.filter(pk__in=item_list).values_list('type', flat=True))
    
        if metadata_view:
            form_list = _advanced_metadata_view(item_list, workspace, default_language, metadata_object, item_media_types)
        else:
            form_list = _simple_metadata_view(item_list, workspace, default_language, metadata_object, item_media_types)
        form_dict = {'rows': form_list}
    except:
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
    prop_list = simplejson.loads(request.POST.get('prop_list'))
    variant_only = request.POST.get('variant', 'all')
    if variant_only == 'variant':
        props = MetadataProperty.objects.filter(is_variant=True).exclude(metadatastructure__in=MetadataStructure.objects.all()).exclude(pk__in=prop_list)
    elif variant_only == 'item':
        props = MetadataProperty.objects.filter(is_variant=False).exclude(metadatastructure__in=MetadataStructure.objects.all()).exclude(pk__in=prop_list)
    else:
        props = MetadataProperty.objects.exclude(metadatastructure__in=MetadataStructure.objects.all()).exclude(pk__in=prop_list)
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
    workspace = request.session.get('workspace')

    my_groups = MetadataDescriptorGroup.objects.filter(workspace=workspace)
    for g in my_groups:
        my_descs = g.descriptors.filter(custom=True)
        my_descs.delete()

    my_groups.delete()
    
    return HttpResponse(simplejson.dumps({'success': True}))


