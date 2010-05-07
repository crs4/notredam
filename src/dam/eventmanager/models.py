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
import logger

class Event(models.Model):
    name = models.CharField(max_length=128, unique = True)
    
class EventManager(models.Manager):
    def notify(self,  event_name, workspace, **parameters):
        try:
            event_registrations = self.filter(event = Event.objects.get(name = event_name), workspace = workspace)
        except Exception, ex:
            logger.debug(ex)
            return
        for event_reg in event_registrations:
            listener = event_reg.listener
            try:
                listener.execute(**parameters)
            except Exception, ex:
                logger.exception(ex)
                
        
class EventRegistration(models.Model):
    event = models.ForeignKey('Event')
    content_type = models.ForeignKey(ContentType)
    listener = generic.GenericForeignKey()
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    object_id = models.PositiveIntegerField()
    
    objects = EventManager()


#class EventRegistration(models.Model):
#	event_description = models.CharField(blank=True, max_length=256)
#	event_type = models.CharField(max_length=256)
#	callback = models.CharField(max_length=256)
#	
#	def __unicode__(self):
#		return "%s: when %s notify to %s" % (str(self.id), self.event_type, self.callback)

#class EventManager(models.Model):
#	description = models.CharField(blank=True, max_length=256)
#	
#	def register(self, event_description, event_type, callback):
#		try:
#			EventRegistration.objects.get(event_type=event_type, callback=callback)
#		except:
#			registration = EventRegistration.objects.create(event_type=event_type, event_description=event_description, callback=callback)
#			return registration.id
#		else:
#			raise EventRegistrationAlreadyExists
#						
#	def unregister(self, event_id):
#		try:
#			registration = EventRegistration.objects.get(id=event_id)
#			registration.delete()
#			return True
#		except DoesNotExist:
#			raise
#		
#	def notify(self, event_type, **event_parameters):
#		listeners = EventRegistration.objects.filter(event_type=event_type)
#		
#		if listeners:
#			for l in listeners:
#				try:
#					module = __import__(l.callback, fromlist=[True])
#				except ImportError: #couldn't import the module
#					raise
#				try:
#					module.notify(**event_parameters)
#				except AttributeError, TypeError: #couldn't call method or it didn't accept parameters
#					raise
#			return len(listeners)
#		else:
#			return False
#	
#	def __unicode__(self):
#		return self.description
