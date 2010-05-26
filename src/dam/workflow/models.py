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

class State(models.Model):
	name = models.CharField(max_length=256)
	workspace = models.ForeignKey('workspace.DAMWorkspace')
	
	class Meta:
		unique_together = (('name', 'workspace'),)
	
	def save(self, *args, **kwargs):
		from eventmanager.models import Event
		super(State, self).save(*args, **kwargs)
		Event.objects.create(name = 'state change to '+ self.name, workspace = self.workspace)
	
	def __unicode__(self):
		return self.name	

class StateItemAssociation(models.Model):
	state = models.ForeignKey(State)
#	workspace = models.ForeignKey('workspace.DAMWorkspace')
	item = models.ForeignKey('repository.Item')
	
	def save(self, *args, **kwargs):
		from scripts.models import Script
		super(StateItemAssociation, self).save(*args, **kwargs)
		for script in Script.objects.filter(workspace = workspace, state = state):
		  script.execute(self.item)
		
	
	def __unicode__(self):
		return "%s in %s: %s" % (self.item, self.workspace, self.state)