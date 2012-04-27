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

class AbstractMetadataLanguage(models.Model):
    """
    List of Languages compliant to RFC 3066
    """
    code = models.CharField(max_length=12)
    language = models.CharField(max_length=64)
    country = models.CharField(max_length=64)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s:%s/%s" % (self.code, self.language, self.country)

class XMPNamespace(models.Model):
    """
    XMP Namespaces (es. Dublin Core, Xmp Basic, and so on)
    """
    name = models.CharField(max_length=64)
    uri = models.URLField(verify_exists=False)
    prefix = models.CharField(max_length=16, null=True)
    
    def __str__(self):
        return "%s (%s)" % (self.name, self.uri)

class XMPPropertyManager(models.Manager):
    """
    XMP Property Manager
    """
    
    def filter_by_namespace(ns):
        if isinstance(ns, XMPNamespace):
            return self.filter(namespace=ns)
        else:
            try:
                ns_obj = XMPNamespace.objects.get(prefix=ns)
                return self.filter(namespace = ns_obj)
            except:
                return self.none()

class XMPProperty(models.Model):
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
        ('cuepoint','cuepoint')
        )

    namespace = models.ForeignKey(XMPNamespace)
    field_name = models.CharField(max_length=64)
    caption = models.CharField(max_length=128)
    description = models.CharField(max_length=256)
    type = models.CharField(max_length=128, choices=VALUE_TYPES, default='text')
    is_array = models.CharField(max_length=15, choices=ARRAY_CHOICES, default='not_array')
    is_choice = models.CharField(max_length=15, choices=CHOICE_TYPES, default='not_choice')
    internal = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    objects = XMPPropertyManager()
    
    if models.get_app('dam_repository'):
        media_type = models.ManyToManyField('dam_repository.Type', default='image' )
    else:
        media_type = models.CharField(max_length=64, default='image')
    
    class Meta:
        verbose_name_plural = "Metadata properties"

    def __str__(self):
        return "%s:%s" % (self.namespace.prefix, self.field_name)

    def get_choices(self):
        return self.property_choices.all()

class XMPStructure(models.Model):
    """
    XMP Structure Definition (es. Dimensions is a structure
    containing 2 XMP Properties)
    """
    name = models.CharField(max_length=128)
    properties = models.ManyToManyField(XMPProperty)	
    
    def __str__(self):
        return "%s" % (self.name)

class XMPPropertyChoice(models.Model):
    """
    Choice values of an XMP Property 
    """
    value = models.CharField(max_length=128)
    description = models.CharField(max_length=255, null=True, blank=True)
    choice_property = models.ForeignKey(XMPProperty, related_name='property_choices')
    
    def __str__(self):
        return "%s (%s)" % (self.value, self.choice_property)

