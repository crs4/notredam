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

class MetadataLanguage(models.Model):
    """
    List of Languages compliant to RFC 3066
    """
    code = models.CharField(max_length=12)
    language = models.CharField(max_length=64)
    country = models.CharField(max_length=64)
    def __str__(self):
        return "%s:%s/%s" % (self.code, self.language, self.country)

class Namespace(models.Model):
    """
    XMP Namespaces (es. Dublin Core, Xmp Basic, and so on)
    """
    name = models.CharField(max_length=64)
    uri = models.URLField(verify_exists=False)
    prefix = models.CharField(max_length=16, null=True)
    
    def __str__(self):
        return "%s (%s)" % (self.name, self.uri)

class MetadataProperty(models.Model):
    """
    XMP Property (as defined in XMP Specification docs)
    """
    ARRAY_CHOICES = (
        ('not_array','Not array'),
        ('alt','Alt'),
        ('bag','Bag'),
        ('seq','Seq'),
        )
    CHOICE_TYPES = (
        ('not_choice','Not choice'),
        ('close_choice','Close choice'),
        ('open_choice','Open choice'),
        )
    VALUE_TYPES = (
        ('agent_name','AgentName'),
        ('bool','Bool'),
        ('beat_splice_stretch', 'BeatSliceStretch'), 
        ('cfapattern', 'CFAPattern'), 
        ('colorant', 'Colorant'), 
        ('date','Date'),
        ('date_only_year','Date (only year)'),
        ('date_and_time','Date and time'),
        ('device_settings', 'DeviceSettings'), 
        ('Dimensions', 'Dimensions'), 
        ('Flash', 'Flash'), 
        ('font', 'Font'), 
        ('gpscoordinate','GPSCoordinate'),
        ('int','Integer'),
        ('job', 'Job'), 
        ('lang','Lang'),
        ('locale', 'Locale'), 
        ('marker', 'Marker'), 
        ('media', 'Media'), 
        ('mimetype','MIMEType'),
        ('oecf_sfr', 'OECF/SFR'), 
        ('ProjectLink', 'ProjectLink'), 
        ('proper_name','ProperName'),
        ('rational', 'Rational'), 
        ('real', 'Real'), 
        ('rendition_class', 'RenditionClass'), 
        ('resample_params', 'ReasmpleParams'), 
        ('resource_event','ResourceEvent'),
        ('resource_ref','ResourceRef'),
        ('txt','Text'),
        ('time', 'Time'),
        ('time_scale_stretch', 'timeScaleStretch'), 
        ('timecode', 'Timecode'), 
        ('thumbnail','Thumbnail'),
        ('uri','URI'),
        ('url','URL'),
        ('version','Version'),
        ('xpath','XPath'),
        ('ContactInfo','ContactInfo'),
        ('LocationDetails','LocationDetails'),
        ('LicensorDetail','LicensorDetail'),
        ('CopyrightOwnerDetail','CopyrightOwnerDetail'),
        ('ImageCreatorDetail','ImageCreatorDetail'),
        ('ArtworkOrObjectDetails','ArtworkOrObjectDetails'),
        ('filesize','filesize'),
        
        )

    namespace = models.ForeignKey(Namespace)
    field_name = models.CharField(max_length=64)
    caption = models.CharField(max_length=128)
    description = models.CharField(max_length=256)
    type = models.CharField(max_length=128, choices=VALUE_TYPES, default='text')
    is_array = models.CharField(max_length=15, choices=ARRAY_CHOICES, default='not_array')
    is_choice = models.CharField(max_length=15, choices=CHOICE_TYPES, default='not_choice')
    internal = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    media_type = models.ManyToManyField('repository.Type', default='image' )
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
    
    def __str__(self):
        return "%s:%s" % (self.namespace.prefix, self.field_name)

    class Meta:
        verbose_name_plural = "Metadata properties"

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

class MetadataStructure(models.Model):
    """
    XMP Structure Definition (es. Dimensions is a structure
    containing 2 XMP Properties)
    """
    name = models.CharField(max_length=128)
    properties = models.ManyToManyField(MetadataProperty)	
    
    def __str__(self):
        return "%s" % (self.name)


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
    workspace = models.ForeignKey('workspace.Workspace', null=True, blank=True) 
    
    def __str__(self):
        return "%s" % (self.name)

class MetadataPropertyChoice(models.Model):
    """
    Choice values of an XMP Property 
    """
    value = models.CharField(max_length=128)
    description = models.CharField(max_length=255, null=True, blank=True)
    choice_property = models.ForeignKey(MetadataProperty, related_name='property_choices')
    
    def __str__(self):
        return "%s (%s)" % (self.value, self.choice_property)

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
