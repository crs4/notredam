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
from dam.repository.models import Component

class MDTask(models.Model):

    """
    MediaDART task specifications
    """

    component = models.ForeignKey(Component)
    
    filepath = models.CharField(max_length=64, null=True, blank=True)
    job_id = models.CharField(max_length=64, null=True, blank=True)
    task_type = models.CharField(max_length=64)
    wait_for = models.ForeignKey('self', null=True, blank=True)
    last_try_timestamp = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return "%s"  % (self.component.get_variant().name )
