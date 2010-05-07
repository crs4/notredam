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

from dam.repository.models import Item
from dam.workflow.models import State
from django.db.models import Q

from dam.framework.dam_workspace.models import Workspace

class DAMWorkspace(Workspace):
    items = models.ManyToManyField(Item, related_name="workspaces",  blank=True)
    states = models.ManyToManyField(State)
        
    def get_variants(self):
        from dam.variants.models import Variant
        return Variant.objects.filter(Q(workspace = self) | Q(is_global = True,  )).distinct()    
    
    def  get_permissions(self,  user):
        return WorkSpacePermission.objects.filter(Q(workspacepermissionassociation__in = WorkSpacePermissionAssociation.objects.filter(Q(users=user, workspace = self)) ) | Q(workspacepermissionsgroup__in= WorkspacePermissionsGroup.objects.filter(users = user, workspace = self) )).distinct()
