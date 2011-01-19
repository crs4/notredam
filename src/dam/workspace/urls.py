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

    (r'^admin_workspace/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace'),
    (r'^admin_workspace/add/$','dam.workspace.views.create_workspace'),

    (r'^workspace/(\d+)/$', 'dam.workspace.views.workspace'),
    (r'^workspace/', 'dam.workspace.views.workspace'),

    (r'^switch_ws/', 'dam.workspace.views.switch_ws'),

    (r'^get_workspaces/$', 'dam.workspace.views.get_workspaces'),
    (r'^add_items_to_ws/$', 'dam.workspace.views.add_items_to_ws'),
    (r'^delete_ws/(.+)/$', 'dam.workspace.views.delete_ws'),

    (r'^load_items/(.+)/', 'dam.workspace.views.load_items'),
    (r'^load_items/', 'dam.workspace.views.load_items'),
    (r'^get_n_items/', 'dam.workspace.views.get_n_items'),

    (r'^get_status/', 'dam.workspace.views.get_status'),
    (r'^get_permissions/', 'dam.workspace.views.get_permissions'),

    (r'^get_ws_members/', 'dam.workspace.views.get_ws_members'),
    (r'^get_available_permissions/', 'dam.workspace.views.get_available_permissions'),
    (r'^get_available_users/', 'dam.workspace.views.get_available_users'),
    (r'^save_members/', 'dam.workspace.views.save_members'), 
    (r'^download_renditions/', 'dam.workspace.views.download_renditions'),
    (r'^script_monitor/', 'dam.workspace.views.script_monitor')
    
    
    
)


