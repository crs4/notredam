#########################################################################
#
# NotreDAM, Copyright (C) 2011, Sardegna Ricerche.
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
#
# Django models for NotreDAM knowledge base.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

from django.db import models

import tinykb.schema as kb_schema

# This is a partial, read-only copy of the 'object' table defined in
# tinykb/schema.py, used for guaranteeing referential integrity from
# the DAM catalog.
class Object(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=128, blank=False, null=False)

    # Override save and delete method, thus making the model read-only
    def save(self):
        raise RuntimeError(('BUG: trying to save a KB object through its '
                            + 'read-only Django model! (id="%s", name="%s")')
                           % self.id, self.name)
    def delete(self):
        raise RuntimeError(('BUG: trying to delete a KB object through its '
                            + 'read-only Django model! (id="%s", name="%s")')
                           % self.id, self.name)

    class Meta:
        db_table = kb_schema.Schema().object_t.name # FIXME: consider prefix
        managed = False # Since it's handled in/by the KB
