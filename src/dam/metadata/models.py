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

from django.db import models

import logger
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from dam.core.dam_metadata.models import AbstractMetadataLanguage, XMPProperty, XMPStructure, XMPPropertyChoice

import re

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

def _round_size(v1, v2):
    value = float(v1) + float(v2)/1024.0
    return str(round(value, 1))

def format_filesize(size):
    """
    Format file size in MB/KB
    """

    mb, r = divmod(size, 1048576)
    kb, b = divmod(r, 1024)
    if mb:
        return _round_size(mb, kb) + ' MB'
    elif kb:
        return _round_size(kb, b) + ' KB'
    else:
        return str(b) + ' bytes'

def set_modified_flag(mtdata, comp):

   """
   Set flag modified in metadata and in Component
   """
   
   from dam.repository.models import Component
   
   if mtdata.modified == False:
       mtdata.modified = True
       mtdata.save()
   if isinstance(comp, Component):
       if comp.modified_metadata == False:
           comp.modified_metadata = True
           comp.save()

class MetadataLanguage(AbstractMetadataLanguage): pass
    
class MetadataProperty(XMPProperty):
    """
    XMP Property (as defined in XMP Specification docs)
    """

    keyword_target = models.BooleanField(default=False)
    is_searchable = models.BooleanField(default=False)
    is_variant = models.BooleanField(default=False)
    creation_date = models.BooleanField(default=False)
    uploaded_by = models.BooleanField(default=False)
    resource_format = models.BooleanField(default=False)
    latitude_target = models.BooleanField(default=False)
    longitude_target = models.BooleanField(default=False)
    rights_target = models.BooleanField(default=False)
    item_owner_target = models.BooleanField(default=False)
    file_size_target = models.BooleanField(default=False)
    file_name_target = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Metadata properties"
    
    def metadata_definition(self):
        
        """
        Returns a dictionary containing definition info of a given metadataschema 
        (es. {type: string, array: true, editable: False, ...}
        """
        
        metadataschema = self
        
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
    
class MetadataDescriptor(models.Model):
    """
    Descriptors are application-defined metadata used to 
    simplify metadata editing
    One descriptor is mapped to 1-N XMP Properties
    """
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255)
    properties = models.ManyToManyField(MetadataProperty)
    custom = models.BooleanField(default=False)    
    
    def __str__(self):
        return "%s" % (self.name)

class MetadataManager(models.Manager):

    def get_metadata_values(self, item_list, metadataschema, items_types, components_types, components_list, component_obj=None):
    
        """
        Get metadataschema values for the given items/components
        """
    
        from django.db import connection
        from dam.repository.models import Item, Component
        
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

#        logger.debug ("select schema_id, value, count(*), language, xpath from metadata_metadatavalue where schema_id=%d AND content_type_id=%d AND object_id IN (%s) GROUP BY schema_id, value, xpath, language;" % (metadataschema.id, ctype.id, str(",".join(object_list))))

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

    def save_descriptor_structure_values(self, descriptor, schema_id, items, values, workspace, variant_name='original'):
        
        """
        Save descriptor values for the given item 
        (if the descriptor is mapped to an array of XMP Structure, 
        it saves the values as the first item of the array)
        """
        
        from dam.repository.models import Item, Component
        
        ctype_item = ContentType.objects.get_for_model(Item)
        ctype_obj = ContentType.objects.get_for_model(Component)
        logger.debug('descriptor %s'%descriptor)
        logger.debug('descriptor.properties %s'%descriptor.properties)
        for item in items:
        
            properties = descriptor.properties.filter(media_type__name=item.type.name)
            logger.debug('properties %s'%properties)
            logger.debug('item.type %s'%item.type)
            for p in properties:
                logger.debug('p.editable %s'%p.editable)
                if not p.editable:
                    continue
        
                if p.is_variant:
                    obj = Component.objects.get(item=item, variant__name=variant_name, workspace=workspace)
                    ctype = ctype_obj
                else:
                    obj = item
                    ctype = ctype_item
        
                subproperty = MetadataProperty.objects.get(pk=int(schema_id))                               
                xpath = '%s:%s[1]/%s:%s' % (p.namespace.prefix, p.field_name, subproperty.namespace.prefix, subproperty.field_name)
                new_metadata = MetadataValue.objects.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, xpath=xpath)
                new_metadata[0].value = values
                new_metadata[0].save()
                logger.debug('new_metadata[0] %s'%new_metadata[0])
                set_modified_flag(new_metadata[0],obj)

    def save_descriptor_values(self, descriptor, items, values, workspace, variant_name='original', default_language='en-US'):
        
        """
        Save descriptor values for the given item
        """	

        from dam.repository.models import Item, Component

        ctype_item = ContentType.objects.get_for_model(Item)
        ctype_obj = ContentType.objects.get_for_model(Component)
        
        for item in items:        

            properties = descriptor.properties.filter(media_type=item.type)
    
            for p in properties:
        
                if not p.editable:
                    continue
        
                if p.is_variant:
                    obj = Component.objects.get(item=item, variant__name=variant_name, workspace=workspace)
                    ctype = ctype_obj
                else:
                    obj = item
                    ctype = ctype_item
        
                obj.metadata.filter(schema__id=int(p.id)).delete()
        
                if isinstance(values, list):
                    if p.type == 'lang':
                        if p.is_array != 'not_array':
                            for value in values:
                                new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value[0], language=value[1])
                                set_modified_flag(new_metadata[0],obj)
                        else:
                            value = values[0]
                            new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value[0], language=value[1])                      
                            set_modified_flag(new_metadata[0],obj)
                    else:
                        if p.is_array != 'not_array':                   
                            for index in range(len(values)):
                                value = values[index]
                                if isinstance(value, dict):
                                    for k, v in value.iteritems():
                                        subproperty = MetadataProperty.objects.get(pk=int(k))                               
                                        xpath = '%s:%s[%d]/%s:%s' % (p.namespace.prefix, p.field_name, index+1, subproperty.namespace.prefix, subproperty.field_name)
                                        new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath)                               
                                        set_modified_flag(new_metadata[0],obj)
                                else:
                                    new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value)
                                    set_modified_flag(new_metadata[0],obj)
                        else:
                            value = values[0]
                            index = 0
                            if isinstance(value, dict):
                                for k, v in value.iteritems():
                                    subproperty = MetadataProperty.objects.get(pk=int(k))                               
                                    xpath = '%s:%s[%d]/%s:%s' % (p.namespace.prefix, p.field_name, index+1, subproperty.namespace.prefix, subproperty.field_name)
                                    new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath)                               
                                    set_modified_flag(new_metadata[0],obj)
                            else:
                                new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value)
                                set_modified_flag(new_metadata[0],obj)
                else:
                    if p.type == 'lang':
                        new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=values, language=default_language)
                        set_modified_flag(new_metadata[0],obj)
                    else:
                        if p.is_array != 'not_array':
                            value = values.split(',')
                            for v in value:
                                new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=v.strip())
                                set_modified_flag(new_metadata[0],obj)
                        else:
                            value = values
                            new_metadata = self.get_or_create(schema=p, object_id=obj.pk, content_type=ctype, value=value)
                            set_modified_flag(new_metadata[0],obj)

    def save_metadata_value(self, items, metadata, variant_name, workspace, default_language='en-US'):
        
        """
        Save XMP Values for the items in item_list
        """
        
        from dam.repository.models import Item, Component
        
        ctype_item = ContentType.objects.get_for_model(Item)
        ctype_obj = ContentType.objects.get_for_model(Component)
    
        for item in items:
            for m in metadata:
                metadataschema = MetadataProperty.objects.get(pk=int(m))
    
                if metadataschema.is_variant:
                    obj = Component.objects.get(item=item, variant__name=variant_name, workspace=workspace)
                    ctype = ctype_obj
                else:
                    obj = item
                    ctype = ctype_item
    
                obj.metadata.filter(schema__id=int(m)).delete()
    
                if isinstance(metadata[m], list):
                    if metadataschema.type == 'lang':
                        for value in metadata[m]:
                            new_metadata = self.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=value[0], language=value[1])
                            set_modified_flag(new_metadata[0],obj)
                    else:
                        for index in range(len(metadata[m])):
                            value = metadata[m][index]
                            if isinstance(value, dict):
                                for k, v in value.iteritems():
                                    subproperty = MetadataProperty.objects.get(pk=int(k))
                                    xpath = '%s:%s[%d]/%s:%s' % (metadataschema.namespace.prefix, metadataschema.field_name, index+1, subproperty.namespace.prefix, subproperty.field_name)
                                    if subproperty.type == 'lang':
                                        new_metadata = self.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath, language=default_language)                                        
                                        set_modified_flag(new_metadata[0],obj)
                                    else:
                                        new_metadata = self.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=v, xpath=xpath)
                                        set_modified_flag(new_metadata[0],obj)
                            else:
                                new_metadata = self.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=value)
                                set_modified_flag(new_metadata[0],obj)
                else:
                    value = metadata[m]
                    new_metadata = self.get_or_create(schema=metadataschema, object_id=obj.pk, content_type=ctype, value=value)
                    set_modified_flag(new_metadata[0],obj)

class MetadataValue(models.Model):
    """
    Xmp property values are saved here
    """
    schema = models.ForeignKey(MetadataProperty, null=True, blank=True)
    xpath = models.TextField()
    value = models.TextField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey()
    object_id = models.PositiveIntegerField()
    language = models.CharField(max_length=12, null=True, blank=True)
    modified = models.BooleanField(default=False)
    objects = MetadataManager()
    
    def __str__(self):
        return "%s (%s)" % (self.schema.namespace, self.schema.field_name)

class MetadataDescriptorGroup(models.Model):
    """
    Group of Metadata Descriptor
    Special groups are basic_summary, specific basic, specific full and upload,
    used in specific parts of DAM GUI
    """
    name = models.CharField(max_length=128)
    descriptors = models.ManyToManyField(MetadataDescriptor)
    basic_summary = models.BooleanField(default=False)
    specific_basic = models.BooleanField(default=False)
    specific_full = models.BooleanField(default=False)
    upload = models.BooleanField(default=False)
    workspace = models.ForeignKey('workspace.DAMWorkspace', null=True, blank=True) 
    
    def __str__(self):
        return "%s" % (self.name)

class RightsXMPValue(models.Model):
    """
    XMP value to be set for a specific license choice
    """
    value = models.CharField(max_length=128)
    xmp_property = models.ForeignKey(MetadataProperty)
    
    def __str__(self):
        return "%s (%s)" % (self.value, self.xmp_property)

class RightsValue(models.Model):
    """
    Rights values (es. all rights reserved, Creative Commons Attribution, ...)
    It automatically sets values for the XMP Properties as defined in 
    xmp_values list
    """
    value = models.CharField(max_length=255)
    xmp_values = models.ManyToManyField(RightsXMPValue)
    components = models.ManyToManyField('repository.Component', related_name='comp_rights', null=True, blank=True)
    
    def __str__(self):
        return "%s" % (self.value)
