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
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

class Type(models.Model):
    """
    It contains the supported media type.
    """
    name =  models.CharField(max_length=30)

    def __str__(self):
        return self.name

class AbstractItem(models.Model):

    """ Base abstract model describing items."""

    owner =  models.ForeignKey(User, related_name='owned_items', null=True, blank=True)
    uploader = models.ForeignKey(User, related_name='uploaded_items', null=True, blank=True)
    type =  models.ForeignKey(Type, null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add = True)
    update_time = models.DateTimeField(auto_now = True)

    class Meta:
        abstract = True
                                
class AbstractComponent(models.Model):

    """ Base abstract model describing components."""

    owner =  models.ForeignKey(User, null=True, blank=True)
    type =  models.ForeignKey(Type, null=True)
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
