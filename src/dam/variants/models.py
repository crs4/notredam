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

from django.db import models, connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.utils import simplejson

from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Component
from dam.metadata.models import RightsValue

from dam.framework.dam_repository.models import Type

import logger
import time

class Variant(models.Model):    
    name = models.CharField(max_length=50)
    caption = models.CharField(max_length=64)
#    is_global = models.BooleanField(default=False) #common for all ws
    workspace = models.ForeignKey(Workspace, null = True, blank = True)
    editable = models.BooleanField(default=True)    
    hidden= models.BooleanField(default=False)    
#    media_type = models.ForeignKey(Type)
#    dest_media_type = models.ForeignKey(Type, null = True, blank = True, related_name = 'dest_media_type')
    auto_generated = models.BooleanField(default=True)
    shared = models.BooleanField(default= False) #the same component will be shared through ws
#    default_rank = models.IntegerField(null = True, blank = True) #not null for imported variants. variant with rank 1 will be used for generating  the others
#    resizable = models.BooleanField(default=True)
#    TODO foreign key to ws
#    def is_original(self):
#        return self.name == 'original' and self.is_global
#    
#    def get_source(self,  workspace,  item):
##        if not self.auto_generated:
##            return None
#            
#        sources = SourceVariant.objects.filter(destination = self,  workspace = workspace)
#        for source_variant in sources:
#            v = source_variant.source
#            logger.debug('source_variant.source %s'%v)
#            if Component.objects.filter(item = item, variant = v).count( ) > 0:
#                return v
#            
           
  
    def get_component(self, workspace,  item,  media_type = None):
        from variants.views import _create_variant
        try:
            return self.component_set.get(item = item,  workspace = workspace)
        except:            
#            if self.dest_media_type:
#                dest_media_type = self.dest_media_type
#            else: 
#                dest_media_type = self.media_type
                
            component = _create_variant(self,  item, workspace,  media_type)
            logger.error('component for ws %s and item %s and variant %s not found. Created.'%(workspace, item.pk, self.name))
            return component
    
    def __str__(self):
        return self.name

#    def save(self,  *args,  **kwargs):
#        if self.is_global and Variant.objects.filter(name = self.name,  is_global = True,  media_type= self.media_type).count() > 0:
#            raise Exception('A global variant with name %s already exists'%self.name)
#        super(Variant, self).save(*args,  **kwargs)

