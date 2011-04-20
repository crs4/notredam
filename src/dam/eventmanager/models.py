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

from exceptions import *
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from dam.logger import logger


class Event(models.Model):
    name = models.CharField(max_length=128, unique = True)
    description = models.CharField(max_length=512)
    workspace = models.ForeignKey('workspace.DAMWorkspace', null = True, blank = True) #for state change event
    
    def unicode(self):
        return unicode(self.name)
    
    def __str__(self):
        return unicode(self.name)
        
class EventManager(models.Manager):
    def notify(self,  event_name, workspace, **parameters):
        logger.debug('notifying event %s on workspace %s with parameters %s'%(event_name, workspace, parameters))
        try:
            event_registrations = self.filter(event = Event.objects.get(name = event_name), workspace = workspace)
        except Exception, ex:
            logger.debug(ex)
            return
        logger.debug('event_registrations %s'% event_registrations)
        for event_reg in event_registrations:
            listener = event_reg.listener
            logger.debug('listener=%s(%s)' % (listener, parameters))
            try:
                listener.execute(**parameters)
            except Exception, ex:
                logger.debug('listener launched an exception')
                logger.exception(ex)
                
        
class EventRegistration(models.Model):
    event = models.ForeignKey('Event')
    content_type = models.ForeignKey(ContentType)
    listener = generic.GenericForeignKey()
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    object_id = models.PositiveIntegerField()
    
    objects = EventManager()
