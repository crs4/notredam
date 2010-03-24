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
from dam.metadata.models import MetadataProperty, Namespace, MetadataStructure, MetadataDescriptor, MetadataDescriptorGroup, MetadataPropertyChoice, MetadataValue, RightsValue, RightsXMPValue

admin.site.register(Namespace)
admin.site.register(MetadataProperty)
admin.site.register(MetadataStructure)
admin.site.register(MetadataDescriptor)
admin.site.register(MetadataDescriptorGroup)
admin.site.register(MetadataPropertyChoice)
admin.site.register(MetadataValue)
admin.site.register(RightsValue)
admin.site.register(RightsXMPValue)
