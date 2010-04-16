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

from scripts.models import *


class ActionScriptInline(admin.TabularInline):
    model = ActionScriptAssociation
    extra = 1
    
class ScriptAdmin(admin.ModelAdmin):
    inlines = [ActionScriptInline]

admin.site.register(Script,  ScriptAdmin)
admin.site.register(Action)
#admin.site.register(ActionScriptAssociation)
admin.site.register(Parameter)
#admin.site.register(ParameterToAction)
