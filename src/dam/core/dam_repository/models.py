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

import os
import mimetypes
from django.db import models
from django.contrib.auth.models import User
from dam.supported_types import supported_extensions, guess_file_type

class MimeError(Exception):
    pass

class TypeManager(models.Manager):
    def get_by_mime(self, mime_type):
        name, subname = mime_type.split('/')
        return self.filter(name=name, subname=subname)

    def get_or_create_by_mime(self, mime_type, extension=None):
        "Returns just the type, not the tuple (type, created) and get_or_create"
        standard_exts = supported_extensions(mime_type)        
        if not standard_exts:
            raise MimeError("Type %s is not supported" % mime_type)
        if extension: 
            extension = extension.lower()
            if extension[0] != '.':
                extension = '.' + extension
            if extension not in standard_exts: 
                raise MimeError('extension %s is not standard for mime type %s' % (extension, mime_type))
            register_ext = extension
        else:
            register_ext = standard_exts[0]
        name, subname = mime_type.split('/')
        t, created = self.get_or_create(name=name, subname=subname)
        if created:
            t.ext = register_ext
            t.save()
        return t

    def get_or_create_by_filename(self, filename):
        filename = filename.lower()
        "Return a type registered in notre dam for use. Create a type if does not exists"
        mime_type = guess_file_type(filename)
        basename, ext = os.path.splitext(filename)
        if mime_type is None:
            raise MimeError('Unrecognized file type: %s' % filename)
        return self.get_or_create_by_mime(mime_type, ext)

class Type(models.Model):
    """
    It contains the supported media type.
    """
    name =  models.CharField(max_length=30)      # the mime type
    subname = models.CharField(max_length=30)    # the mime subtype
    ext = models.CharField(max_length=5)         # the extension used in Notredam (with the leading dot)
    objects = TypeManager()

    def __str__(self):
        return "%s/%s" % (self.name, self.subname)


class ItemManager(models.Manager):

    """ Item Manager """

    def get_items_owned_by(self, user):
        return self.filter(owner = user)

    def get_items_uploaded_by(self, user):
        return self.filter(uploader = user)
        
    def get_items_by_type(self, type):
        return self.filter(type = type)

class AbstractItem(models.Model):

    """ Base abstract model describing items."""

    owner =  models.ForeignKey(User, related_name='owned_items', null=True, blank=True)
    uploader = models.ForeignKey(User, related_name='uploaded_items', null=True, blank=True)
    type =  models.ForeignKey(Type)  # used to create new components when the type is not specified
    creation_time = models.DateTimeField(auto_now_add = True)
    update_time = models.DateTimeField(auto_now = True)
    objects = ItemManager()

    class Meta:
        abstract = True
        
class AbstractComponent(models.Model):

    """ Base abstract model describing components."""

    owner =  models.ForeignKey(User, null=True, blank=True)
    type =  models.ForeignKey(Type)
    creation_time = models.DateTimeField(auto_now = True)
    update_time = models.DateTimeField(auto_now = True)

    format = models.CharField(max_length=50, null = True)
    width = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    height = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    bitrate = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    duration = models.DecimalField(decimal_places=0, max_digits=10,default = 0, null = True)
    size = models.DecimalField(decimal_places=0, max_digits=10, default = 0)
        
    file_name = models.CharField(max_length=128, null=True, blank=True)
    
    class Meta:
        abstract = True
