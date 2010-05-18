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

from django.contrib import admin
from dam.application.admin import mod_admin
from dam.workspace.views import Workspace, WorkspacePermissionsGroup, WorkSpacePermissionAssociation, WorkSpacePermission

class WorkspaceAdmin(admin.ModelAdmin):
    filter_horizontal = ('members','items',)
    label = 'main'
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'creator', )
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('members','items', 'states')
        }),
    )

    
admin.site.register(Workspace,  WorkspaceAdmin)

admin.site.register(WorkspacePermissionsGroup)
admin.site.register(WorkSpacePermission)
admin.site.register(WorkSpacePermissionAssociation)

mod_admin.register(Workspace, WorkspaceAdmin)