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

from dam.core.dam_repository.models import AbstractItem, AbstractComponent
from dam.settings import SERVER_PUBLIC_ADDRESS

import urlparse
import logger
from django.utils import simplejson
import time

from mediadart.storage import Storage


def _get_resource_url(id):
    """
    Returns resource path
    """

    storage = Storage()

    if not id:
        return None

    try:
        
        if storage.exists(id):
            url = '/storage/' + id
        else:
            url = None
    except:
        url = None
    return url

class Item(AbstractItem):

    """
    Concrete class that inherits from the abstract class AbstractItem found in core/dam_repository/models.py     
    Base model describing items. They can contain components only.
    """
    
    metadata = generic.GenericRelation('metadata.MetadataValue')

    class Meta:
        db_table = 'item'

    def __unicode__(self):
        return self.get_file_name()

    def get_workspaces_count(self):
        """
        Number of workspaces where the current item has been added
        """
        return self.workspaces.all().count()
        
    def create_variant(self, variant, ws,  media_type = None):
        """
        Create a new component for this item, using the given variant/media_type 
        and add it to the given workspace
        @param variant an instance of variants.Variant
        @param ws an instance of workspace.DAMWorkspace
        @param media_type an instance of dam_repository.Type
        """
        logger.debug('variant %s'%variant)
        logger.debug('item.type %s'%self.type.name)
        if not media_type:
            media_type = self.type
        logger.debug('ws %s'%ws)
    #    if variant_name =='original':
    #        variant,  created = Variant.objects.get_or_create(variant_name = 'original')        
    #    else:        
    
    #    variant = Variant.objects.get(name = variant_name)
        
        try:
            if variant.shared:
                comp = Component.objects.get(item = self, variant= variant)
                comp.workspace.add(ws)
                comp.workspace.add(*self.workspaces.all())
            else:
                comp = Component.objects.get(item = self, variant= variant,  workspace = ws,  type = media_type)
#                comp.metadata.all().delete()
            
            
        except Component.DoesNotExist:
            logger.debug('variant does not exist yet')
          
                    
            comp = Component.objects.create(variant = variant, item = self, type = media_type)
            comp.workspace.add(ws)
            
            if variant.shared:
                comp.workspace.add(*self.workspaces.all())
        
        logger.debug('============== COMPONENT_VARIANT =========== %s' % comp.variant)
        
        return comp

    def add_to_uploaded_inbox(self, workspace):
        """
        Add the item to the uploaded inbox of the given workspace
        @param ws an instance of workspace.DAMWorkspace
        """
        
        uploaded = workspace.tree_nodes.get(depth = 1, label = 'Uploaded', type = 'inbox')
        time_uploaded = time.strftime("%Y-%m-%d", time.gmtime())
        node = workspace.tree_nodes.get_or_create(label = time_uploaded,  type = 'inbox',  parent = uploaded,  depth = 2)[0]
        node.items.add(self)

    def delete_from_ws(self, user, workspaces=None):
        """
        Delete the item from the given workspaces 
        If workspaces is not specified, remove the item from the user's workspaces
        @param user an instance of auth.User
        @param workspaces a querySet of workspace.DAMWorkspace (optional)
        """
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
        """
        Returns item's metadata for the given XMP Property 
        If the XMP Property is not specified, all the metadata will be returned
        @param metadataschema an instance of metadata.MetadataProperty
        """
        from dam.metadata.models import MetadataValue, MetadataProperty
    
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
        """
        Retrieves all the values for the descriptors for the current item
        and returns them in the format required by the Metadata GUI
        @param user an instance of auth.User
        @param workspace an instance of workspace.DAMWorkspace
        """
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
        """
        Retrieve descriptor values of the current item for the 
        given workspace
        @param workspace an instance of workspace.DAMWorkspace
        """
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
        """
        Returns the file name found in the original variant
        """
        from dam.variants.models import Variant
        try:
            orig = self.component_set.get(variant__name = 'original')
            name = orig.file_name 
        except Component.DoesNotExist:
            name = ''
        return name

    def get_file_size(self):
        """
        Returns the file size found in the original variant
        """
        from dam.variants.models import Variant
        orig = self.component_set.get(variant = Variant.objects.get(name = 'original'))
        return float(orig.size)

    def get_states(self, workspace=None):
        from dam.workflow.models import StateItemAssociation

        if workspace is None:
            return StateItemAssociation.objects.filter(item = self)
        else:
            return StateItemAssociation.get(item=self, workspace=workspace)

    def get_variant(self, workspace, variant):
        """
        Retrieve the component for the given variant and workspace
        @param workspace an instance of workspace.DAMWorkspace
        @param variant an instance of variants.Variant
        """
        from dam.variants.models import Variant
        return self.component_set.get(variant = variant, workspace = workspace)

    def get_variants(self, workspace):
        """
        Retrieve all the item's components
        """
        from dam.variants.models import Variant
        return self.component_set.filter(variant__in = Variant.objects.filter(Q(workspace__isnull = True) | Q(workspace__pk = workspace.pk), hidden = False,  media_type = self.type),  workspace = workspace)

    def keywords(self):    
        """
        Retrieve all the keywords (taxonomy nodes)
        """
        
        return self.node_set.filter(type = 'keyword').values('id','label')

    def collections(self):    
        """
        Retrieve all the keywords (taxonomy nodes)
        """
        
        return self.node_set.filter(type = 'collection').values('id','label')


    def uploaded_by(self):
        """
        Return the uploader username (or unknown)
        """
        try:
            return self.uploader.username
        except:
            return 'unknown'
                                
class Component(AbstractComponent):

    """ 
    Concrete class that inherits from the abstract class AbstractComponent found in core/dam_repository/models.py
    Base model describing components. They can be contained by items.
    """

    _id = models.CharField(max_length=40,  db_column = 'md_id')
    metadata = generic.GenericRelation('metadata.MetadataValue')
    
    variant = models.ForeignKey('variants.Variant')
    workspace = models.ManyToManyField('workspace.DAMWorkspace')    
#    media_type = models.ForeignKey('application.Type')
    item = models.ForeignKey('repository.Item')
    _previous_source_id = models.CharField(max_length=40,  null = True,  blank = True)
        
    uri = models.URLField(max_length=512, verify_exists = False,  blank = True,  null = True)
    imported = models.BooleanField(default = False) # if true related variant must not be regenarated from the original

    #new
    parameters = models.TextField(null = True,  blank = True)
    source = models.ForeignKey('self', null = True, blank = True)
    modified_metadata = models.BooleanField(default = False) 
    script = models.ForeignKey('scripts.Script', null = True, blank  = True, default = None)   
    
    class Meta:
        db_table = 'component'

    def __unicode__(self):
        return self.ID
            
    def set_source(self, source):
        self.source = source
        self._previous_source_id = source._id
    
    def copy_metadata(self, component):
        from dam.metadata.models import MetadataValue, MetadataProperty
        values = component.metadata.all().values('xpath', 'language', 'schema_id', 'value', 'content_type_id')
        for value in values:
            schema_id = value.pop('schema_id')
            value['schema'] = MetadataProperty.objects.get(pk = schema_id)
            value['object_id'] = self.pk
            MetadataValue.objects.create(**value)
            
    def _get_id(self):
        return self._id

    def _get_media_type(self):
        return self.type            

    ID = property(fget=_get_id)     
    media_type = property(fget=_get_media_type)
    
    def get_component_url(self, full_address = False):
        """
        Returns the component url (something like /storage/res_id.ext)
        """
        from dam.application.views import NOTAVAILABLE

        url = NOTAVAILABLE    
        
        try:
            component = self
        
            if component.uri:
                url =  component.uri
            else:
                url = _get_resource_url(component.ID)
            logger.debug('full_address %s'% full_address)
            logger.debug('SERVER_PUBLIC_ADDRESS %s'% SERVER_PUBLIC_ADDRESS)
            if full_address:
                url = SERVER_PUBLIC_ADDRESS + url
        
        except Exception,ex:
            url = NOTAVAILABLE    
        
        logger.debug('url %s'%url)
        return url

    def save_rights_value(self, license_value, workspace):
    
        """
        Save license to the given component and set xmp 
        values according to right rules (as defined in XMPRightsValue)
        @param license_value an instance of metadata.RightsValue
        @param workspace an instance of workspace.DAMWorkspace
        """
        from metadata.models import RightsValue,  MetadataValue
    
        logger.debug("SAVING RIGHTS")

        try:    
            logger.debug('try')
            if isinstance(license_value, RightsValue):
                license = license_value
            else:
                license = RightsValue.objects.get(value__iexact = license_value)

            self.comp_rights = []
            logger.debug('license %s'%license)
            self.metadata.filter(schema__rights_target=True).delete()
            license.components.add(self)
            item_list = [self.item]
        
            xmp_values = {}
            for m in license.xmp_values.all():
                xmp_values[m.xmp_property.id] = m.value
            logger.debug('xmp_values %s'%xmp_values)
            MetadataValue.objects.save_metadata_value(item_list, xmp_values, self.variant.name, workspace)

        except Exception,  ex:
            logger.error(ex)
            logger.debug('ex')
            logger.debug(self.variant.name)
            self.metadata.filter(schema__rights_target=True).delete()

            original_comp = self.source
            
            self.comp_rights = []
            self.comp_rights.add(*original_comp.comp_rights.all())
            for m in original_comp.metadata.filter(schema__rights_target=True):
                mv = MetadataValue.objects.create(schema = m.schema, xpath=m.xpath, content_object = self,  value = m.value, language=m.language)
                logger.debug('mv %s'%mv)
    
    def set_parameters(self, params):
        """
        Set adaptation parameters (ex. max_size, transcoding format, and so on)
        @param params a dictionary containing the adaptation parameters
        """
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
        """
        Get adaptation parameters (ex. max_size, transcoding format, and so on)
        """
    
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
                
    def get_formatted_filesize(self):
        """
        Returns the file size (something like 1.4 KB, 2.7 MB, ...)
        """
        from dam.metadata.views import format_filesize
        return format_filesize(self.size)
    
    def get_metadata_values(self, metadataschema=None):
        """
        Returns the metadata values for the current component and the given
        XMP Property
        If the XMP Property is not specified, it retrieves the metadata values
        for all the XMP Properties
        @param metadataschema an instance of metadata.MetadataProperty (optional)
        """
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
        """
        Retrieves all the values for the descriptors for the current component
        and returns them in the format required by the Metadata GUI
        @param group an instance of MetadataDescriptorGroup
        @param user an instance of auth.User
        @param workspace an instance of workspace.DAMWorkspace
        """
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
        """
        Returns the descriptors value for the given descriptor group
        @param desc_group an instance of metadata.MetadataDescriptorGroup
        """
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
        """
        Returns the component's variant
        """
        return self.variant
                
class Watermark(AbstractComponent):

    """ 
    Concrete class that inherits from the abstract class AbstractComponent found in core/dam_repository/models.py
    Base model describing watermark images. They can be contained by workspaces only.
    """

    _id = models.CharField(max_length=40,  db_column = 'md_id')
    workspace = models.ForeignKey('workspace.DAMWorkspace')    
    
    class Meta:
        db_table = 'watermark'

    def __unicode__(self):
        return self.ID
    
    def _get_id(self):
        return self._id

    def get_url(self):
        """
        Returns the component url (something like /storage/res_id.ext)
        """
        from dam.application.views import NOTAVAILABLE

        url = NOTAVAILABLE    
       
        try:
            url = _get_resource_url(self.ID)
            logger.debug('url : %s' %url)
        except Exception,ex:
            logger.error(ex)
            url = NOTAVAILABLE    
            
        return url

    ID = property(fget=_get_id)     

    
