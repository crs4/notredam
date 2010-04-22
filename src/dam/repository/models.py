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
from django.contrib.auth.models import User, Permission, Group

from dam.metadata.models import MetadataValue,MetadataProperty
from dam.workflow.models import State, StateItemAssociation

import sha
import random
import logger

class Type(models.Model):
    """
    It contains the supported media type.
    """
    name =  models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Item(models.Model):

    """ Base model describing items. They can contain components (see method 'add_child') and can be contained by containers """

    _id = models.CharField(max_length=41)
    owner =  models.CharField(max_length=50, null = True)
    uploader = models.ForeignKey(User)
    type =  models.CharField(max_length=20, null = True)
    privacy =  models.CharField(max_length=20, null = True)
    state = models.DecimalField(decimal_places=0, max_digits=10, null = True)
    creation_time = models.DateTimeField(auto_now_add = True)
    update_time = models.DateTimeField(auto_now = True)
    is_public = models.BooleanField(default=False)
    metadata = generic.GenericRelation(MetadataValue)
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'item'

    def get_metadata_values(self, metadataschema=None):
        from dam.metadata.views import get_metadata_values
        values = []
        original_component = Component.objects.get(item=self, variant__name='original', workspace=self.workspaces.all()[0])
        if metadataschema:
            schema_value, delete, b = get_metadata_values([self.pk], metadataschema, set([self.type]), set([original_component.media_type.name]), [original_component.pk])
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
                schema_value, delete, b = get_metadata_values([self.pk], prop, set([self.type]), set([original_component.media_type.name]), [original_component.pk])
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.pk]})

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
        orig = self.component_set.get(variant = Variant.objects.get(name = 'original', media_type__name = self.type))
        return float(orig.size)

    def get_states(self, workspace=None):
        if workspace is None:
            return StateItemAssociation.objects.filter(item = self)
        else:
            return StateItemAssociation.get(item=self, workspace=workspace)
                        
    def get_variants(self,  workspace):
        from dam.variants.models import Variant
        return self.component_set.filter(variant__in = Variant.objects.filter(Q(is_global = True,) | Q(variantassociation__workspace__pk = workspace.pk), media_type__name = self.type),  workspace = workspace)
                
    def description(self):
        mydescription = self.metadata.get(schema__is_description = True, language ="it-IT")
        return mydescription.value

    def keywords(self):
        self.node_set.filter(type = 'keyword' ).values('id','label')
#        k = {}
#        mykeywords = self.metadata.filter(schema__keyword_target = True)
#        for i in mykeywords:
#            k.append(i.value)
#        return mykeywords    

    def uploaded_by(self):
        try:
            return self.uploader.username
        except:
            return 'unknown'
                
    def _get_id(self):
        return  self._id
    
    ID = property(fget=_get_id)
        
    def save(self, force_insert=False):
        if self._id == '':
            self._id = 'a' + sha.new(str(random.random())).hexdigest()
        try:
            models.Model.save(self, force_insert=force_insert)   
        except:
            self._id = ''
            raise
            
    
    def __str__(self):
        return self.ID
        
def _new_md_id():
        return sha.new(str(random.random())).hexdigest()
        
class Component(models.Model):
    """ Base model describing components. They can be contained by items."""
    _id = models.CharField(max_length=40,  db_column = 'md_id')
    owner =  models.CharField(max_length=50, null = True)
    type =  models.CharField(max_length=20, null = True)
    state = models.DecimalField(decimal_places=0, max_digits=10, null = True)
    creation_time = models.DateTimeField(auto_now = True)
    update_time = models.DateTimeField(auto_now = True)

    format = models.CharField(max_length=50, null = True)
    width = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    height = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    bitrate = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    duration = models.DecimalField(decimal_places=0, max_digits=10,default = 0, null = True)
    size = models.DecimalField(decimal_places=0, max_digits=10, default = 0)
    embedded_license = models.BooleanField(default = False)
    condition_class = models.TextField( null = True)
    metadata = generic.GenericRelation(MetadataValue)
    
    variant = models.ForeignKey('variants.Variant')
    workspace = models.ManyToManyField('workspace.Workspace')    
    item = models.ForeignKey('Item')
    source_id = models.CharField(max_length=40,  null = True,  blank = True)
    preferences = generic.GenericForeignKey()
    content_type = models.ForeignKey(ContentType,  null = True, blank = True)
    object_id = models.PositiveIntegerField(null = True, blank = True)
    
    uri = models.URLField(max_length=512,  verify_exists = False,  blank = True,  null = True)
    imported = models.BooleanField(default = False) # if true related variant must not be regenarated from the original
    #properties

    file_name = models.CharField(max_length=128, null=True, blank=True)
    modified_metadata = models.BooleanField(default = False)    
    
    class Meta:
        db_table = 'component'
    
    def _get_id(self):
        return self._id
    ID = property(fget=_get_id)
    
    def _get_media_type(self):
        if self.variant.auto_generated:
            pref = self.variant.get_preferences(workspace = self.workspace.all()[0])
            return pref.media_type
            
        else:
            return self.variant.media_type
            
    media_type = property(fget=_get_media_type)
    
    def __str__(self):
        return self.ID

    def get_formatted_filesize(self):
        from dam.metadata.views import format_filesize
        return format_filesize(self.size)
    
    def get_metadata_values(self, metadataschema=None):
        from dam.metadata.views import get_metadata_values
        values = []
        if metadataschema:
            schema_value, delete, b = get_metadata_values([self.item.pk], metadataschema, set([self.item.type]), set([self.media_type.name]), [self.pk], self)
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
                schema_value, delete, b = get_metadata_values([self.item.pk], prop, set([self.item.type]), set([self.media_type.name]), [self.pk], self)
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.item.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.item.pk]})

        return values

    def get_descriptors(self, desc_group):

        item_list = [self.item.pk]
        descriptors = {}
        desc_group    
        for d in desc_group.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors

    
    def get_variant(self):
        return self.variant
    
    def new_md_id(self):
        self._id = _new_md_id()
        self.save()
            
    def save(self, *args,  **kwargs):
        if self._id == '':
            self._id = sha.new(str(random.random())).hexdigest()
        try:
            models.Model.save(self,*args,  **kwargs)
        except:
            self._id = ''
            raise
            
