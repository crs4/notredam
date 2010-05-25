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

from django.conf.urls.defaults import *

urlpatterns = patterns('',

    (r'^get_metadata/$', 'dam.metadata.views.get_metadata'),
    (r'^save_metadata/$', 'dam.metadata.views.save_metadata'),
    (r'^metadata_structures/$', 'dam.metadata.views.get_metadata_structures'),
    (r'^save_descriptors/$', 'dam.metadata.views.save_descriptors'),
    (r'^get_basic_descriptors/$', 'dam.metadata.views.get_basic_descriptors'),
    (r'^sync_component/$', 'dam.metadata.views.sync_component'),
    
    (r'^ws_admin/config_descriptors/(.+)/$', 'dam.metadata.views.wsadmin_config_descriptors'),
    (r'^ws_admin/get_descriptor_properties/$', 'dam.metadata.views.wsadmin_get_descriptor_properties'),
    (r'^ws_admin/save_ws_descriptors/$', 'dam.metadata.views.wsadmin_save_ws_descriptors'),
    (r'^ws_admin/config_descriptor_groups/$', 'dam.metadata.views.wsadmin_config_descriptor_groups'),
    (r'^ws_admin/set_default_descriptors/$', 'dam.metadata.views.wsadmin_set_default_descriptors'),
    (r'^get_cuepoint_keywords/$', 'dam.metadata.views.get_cuepoint_keywords'),
    (r'^set_cuepoint/$', 'dam.metadata.views.set_cuepoint'),
    (r'^get_item_cuepoint/$', 'dam.metadata.views.get_item_cuepoint')

)
