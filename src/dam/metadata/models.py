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

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import connection
from datetime import datetime

from dam.framework.dam_metadata.models import AbstractMetadataLanguage, XMPProperty, XMPStructure, XMPValue, XMPPropertyChoice

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

class MetadataValue(XMPValue):
    pass

class MetadataStructure(XMPStructure):
    pass

class MetadataPropertyChoice(XMPPropertyChoice):
    pass

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
    workspace = models.ForeignKey('workspace.Workspace', null=True, blank=True) 
    
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
