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
from django.db.models import Q
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from dam.workflow.models import StateItemAssociation
from dam.framework.dam_repository.models import AbstractItem, AbstractComponent

import urlparse
import logger
import simplejson

from mediadart.storage import Storage

def _get_resource_url(id):
    """
    Returns resource path
    """

    storage = Storage()

    try:
        if storage.exists(id):
            url = '/storage/' + id
        else:
            url = None
    except:
        url = None
    return url

class Item(AbstractItem):

    """ Base model describing items. They can contain components """

    metadata = generic.GenericRelation('metadata.MetadataValue')

    class Meta:
        db_table = 'item'

    def __unicode__(self):
        return self.get_file_name()

    def get_workspaces_count(self):
        return self.workspaces.all().count()    

    def delete_from_ws(self, user, workspaces=None):
    
        if not workspaces:
            q1 = Workspace.objects.filter( Q(workspacepermissionassociation__permission__codename = 'admin') | Q(workspacepermissionassociation__permission__codename = 'remove_item'), members = user,workspacepermissionassociation__users = user)
            q2 =  Workspace.objects.filter(Q(workspacepermissionsgroup__permissions__codename = 'admin') | Q(workspacepermissionsgroup__permissions__codename = 'remove_item'), members = user, workspacepermissionsgroup__users = user)
            workspaces = reduce(or_, [q1,q2])

        self.workspaces.remove(*workspaces)
            
        if self.get_workspaces_count() == 0:
            components = self.component_set.all().delete()
            self.delete()
        else:
            inboxes = self.node_set.filter(type = 'inbox',  workspace__in= workspaces)
            for inbox in inboxes:
                inbox.items.remove(self)
            
    def get_metadata_values(self, metadataschema=None):
        from dam.metadata.models import MetadataValue
    
        values = []
        original_component = Component.objects.get(item=self, variant__name='original', workspace=self.workspaces.all()[0])
        if metadataschema:
            schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.pk], metadataschema, set([self.type.name]), set([original_component.media_type.name]), [original_component.pk])
            if delete:
                return None
            if schema_value:
                if schema_value[self.pk]:
                    values = schema_value[self.pk]
                else:
                    values = None
            else:
                values = None
        else:
            for m in self.metadata.all().distinct('schema').values('schema'):
                prop = MetadataProperty.objects.get(pk=m['schema'])
                schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.pk], prop, set([self.type.name]), set([original_component.media_type.name]), [original_component.pk])
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.pk]})

        return values

    def get_formatted_descriptors(self, user, workspace):
        from dam.metadata.models import MetadataDescriptor, MetadataProperty
        from dam.preferences.views import get_metadata_default_language

        descriptors = self.get_descriptors(workspace)
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

    def get_descriptors(self, workspace=None):
        from dam.metadata.models import MetadataDescriptorGroup

        if workspace:
            basic = MetadataDescriptorGroup.objects.filter(basic_summary=True, workspace=workspace)
            if basic.count() == 0:
                basic = MetadataDescriptorGroup.objects.filter(basic_summary=True)[0]
            else:
                basic = basic[0]
        else:
            basic = MetadataDescriptorGroup.objects.filter(basic_summary=True)[0]
        
        descriptors = {}
        for d in basic.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors

    def get_file_name(self):
        from dam.variants.models import Variant
        try:
            orig = self.component_set.get(variant__name = 'original')
            name = orig.file_name 
        except Component.DoesNotExist:
            name = ''
        return name

    def get_file_size(self):
        from dam.variants.models import Variant
        orig = self.component_set.get(variant = Variant.objects.get(name = 'original', media_type = self.type))
        return float(orig.size)

    def get_states(self, workspace=None):
        if workspace is None:
            return StateItemAssociation.objects.filter(item = self)
        else:
            return StateItemAssociation.get(item=self, workspace=workspace)

    def get_variant(self, workspace, variant):
        from dam.variants.models import Variant
        return self.component_set.get(variant = variant, workspace = workspace)

    def get_variants(self, workspace):
        from dam.variants.models import Variant
        return self.component_set.filter(variant__in = Variant.objects.filter(Q(is_global = True,) | Q(workspace__pk = workspace.pk), media_type = self.type),  workspace = workspace)

    def keywords(self):    
        self.node_set.filter(type = 'keyword').values('id','label')

    def uploaded_by(self):
        try:
            return self.uploader.username
        except:
            return 'unknown'
                                
class Component(AbstractComponent):

    """ Base model describing components. They can be contained by items."""

    _id = models.CharField(max_length=40,  db_column = 'md_id')
    metadata = generic.GenericRelation('metadata.MetadataValue')
    
    variant = models.ForeignKey('variants.Variant')
    workspace = models.ManyToManyField('workspace.DAMWorkspace')    
#    media_type = models.ForeignKey('application.Type')
    item = models.ForeignKey('repository.Item')
#    source_id = models.CharField(max_length=40,  null = True,  blank = True)
    
    preferences = generic.GenericForeignKey()
    content_type = models.ForeignKey(ContentType,  null = True, blank = True)
    object_id = models.PositiveIntegerField(null = True, blank = True)
    
    uri = models.URLField(max_length=512,  verify_exists = False,  blank = True,  null = True)
    imported = models.BooleanField(default = False) # if true related variant must not be regenarated from the original

    #new
    parameters = models.TextField(null = True,  blank = True)
    source = models.ForeignKey('self', null = True, blank = True)
    modified_metadata = models.BooleanField(default = False)    

    
    class Meta:
        db_table = 'component'
    
    def _get_id(self):
        return self._id
        
    ID = property(fget=_get_id)
    
    def get_component_url(self):
    
        from dam.application.views import NOTAVAILABLE

        url = NOTAVAILABLE    
       
        try:
            component = self
        
            if component.uri:
                return component.uri
    
            url = _get_resource_url(component.ID)
    
        except Exception,ex:
            url = NOTAVAILABLE    
            
        return url

    def save_rights_value(self, license_value, workspace):
    
        """
        Save license to the given component and set xmp 
        values according to right rules (as defined in XMPRightsValue)
        """
    
        logger.debug("SAVING RIGHTS")

        try:    
            if isinstance(license_value, RightsValue):
                license = license_value
            else:
                license = RightsValue.objects.get(value__iexact = license_value)

            self.comp_rights = []
            self.metadata.filter(schema__rights_target=True).delete()
            license.components.add(self)
            item_list = [self.item]
        
            xmp_values = {}
            for m in license.xmp_values.all():
                xmp_values[m.xmp_property.id] = m.value
            MetadataValue.objects.save_metadata_value(item_list, xmp_values, self.variant.name, workspace)

        except:

            self.metadata.filter(schema__rights_target=True).delete()

            original_comp = self.source
            
            self.comp_rights = []
            self.comp_rights.add(*original_comp.comp_rights.all())
            for m in original_comp.metadata.filter(schema__rights_target=True):
                MetadataValue.objects.create(schema = m.schema, xpath=m.xpath, content_object = self,  value = m.value, language=m.language)
    
    def set_parameters(self, params):
        params_str = ''
        logger.debug('params %s'%params)
        logger.debug('params.keys()%s'%params.keys())
        keys = params.keys()
        keys.sort()
        for key in keys:
            params_str += '%s=%s&'%(key,simplejson.dumps(params[key]))
        
        self.parameters = params_str
        self.save()
        
    def get_parameters(self):
        logger.debug('self.parameters %s'%self.parameters)
        if self.parameters:
            tmp = dict(urlparse.parse_qsl(self.parameters))
            for key in tmp.keys():
                logger.debug('key %s value %s'%(key, tmp[key]))
                try:
                    tmp[key] = simplejson.loads(tmp[key])
                except:
                    pass
            return tmp
        else:
            return {}
        
    
    def _get_media_type(self):        
            return self.type            
     
    media_type = property(fget=_get_media_type)
    
    def __str__(self):
        return self.ID

    def get_formatted_filesize(self):
        from dam.metadata.views import format_filesize
        return format_filesize(self.size)
    
    def get_metadata_values(self, metadataschema=None):
        from dam.metadata.models import MetadataValue
        values = []
        if metadataschema:
            schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.item.pk], metadataschema, set([self.item.type.name]), set([self.media_type.name]), [self.pk], self)
            if delete:
                return None
            if schema_value:
                if schema_value[self.item.pk]:
                    values = schema_value[self.item.pk]
                else:
	                values = None
            else:
                values = None
        else:
            for m in self.metadata.all().distinct('schema').values('schema'):
                prop = MetadataProperty.objects.get(pk=m['schema'])
                schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.item.pk], prop, set([self.item.type.name]), set([self.media_type.name]), [self.pk], self)
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.item.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.item.pk]})

        return values

    def get_formatted_descriptors(self, group, user, workspace):
        from dam.metadata.models import MetadataDescriptor, MetadataProperty
        from dam.preferences.views import get_metadata_default_language
    
        descriptors = self.get_descriptors(group)
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

    def get_descriptors(self, desc_group):

        item_list = [self.item.pk]
        descriptors = {}
        for d in desc_group.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors
    
    def get_variant(self):
        return self.variant
                
