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

class Action(models.Model):
    """
    Method to call on a component (i.e. adapt_resource, extract_features, etc.)
    """
    component = models.ForeignKey(Component)
    function = models.CharField(max_length=64)

    def __str__(self):
        return "%s %s"  % (self.component.get_variant().name, self.function )

class MachineState(models.Model):
    """
    Basic implementation of the state of a finite state machine
    """
    name = models.CharField(max_length=64)
    action = models.ForeignKey(Action, null=True, blank=True)
    next_state =  models.ForeignKey('self', null=True, blank=True)

    def copy(self):
        initial = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields if not isinstance(f, models.AutoField) and not f in self._meta.parents.values()])
        return self.__class__(**initial)
        
class Machine(models.Model):
    """
    Finite state machine implementation. Contains a reference to the current
    machine state, to the initial state and to another state machine to wait for
    """
    initial_state = models.ForeignKey(MachineState, related_name='initial')
    current_state = models.ForeignKey(MachineState)
    wait_for = models.ForeignKey('self', null=True, blank=True)
