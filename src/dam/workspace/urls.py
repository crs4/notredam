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

    (r'^get_workspaces/$', 'dam.workspace.views.get_workspaces'),

    (r'^get_permissions/(.+)/(.+)/', 'dam.workspace.views.get_ws_permissions'),
    (r'^get_user_ws_permissions/(.+)/(.+)/', 'dam.workspace.views.get_user_ws_permissions'),
    (r'^get_user_ws_groups/(.+)/(.+)/', 'dam.workspace.views.get_user_ws_groups'),
    (r'^get_group_permissions/$', 'dam.workspace.views.get_group_permissions'),
    (r'^get_available_permissions/(.+)/(.+)/', 'dam.workspace.views.get_available_permissions'),
    (r'^get_groups/(.+)/(.+)/', 'dam.workspace.views.get_groups'),
    (r'^get_members/$', 'dam.workspace.views.get_members'),

    (r'^is_workspace_member/(.+)/(.+)/', 'dam.workspace.views.is_workspace_member'),
    (r'^update_available_workspaces/(.+)/(.+)/$', 'dam.workspace.views.update_available_workspaces'),
    (r'^add_items_to_ws/$', 'dam.workspace.views.add_items_to_ws'),
    (r'^delete_ws/(.+)/$', 'dam.workspace.views.delete_ws'),

    (r'^admin_workspace/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace'),
    (r'^admin_workspace/add/$','dam.workspace.views.create_workspace'),
    (r'^admin_workspace_add_members/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_add_members'),
    (r'^admin_workspace_add_members_to_group/(?P<ws_id>\d+)/(?P<group_id>\d+)/$','dam.workspace.views.admin_workspace_add_members_to_group'),
    (r'^admin_workspace_add_members_to_group/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_add_members_to_group'),
    (r'^admin_workspace_remove_members/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_remove_members'),
    (r'^admin_workspace_remove_groups/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_remove_groups'),
    (r'^admin_workspace_get_groups_count/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_get_groups_count'),

    (r'^admin_workspace_set_permissions/(?P<ws_id>\d+)/(?P<type>.+)/$','dam.workspace.views.admin_workspace_set_permissions'),

    (r'^admin_workspace_set_groups/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_set_groups'),
    (r'^admin_workspace_remove_user_from_groups/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_remove_user_from_groups'),
    (r'^admin_workspace_get_groups/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_groups'),

#    (r'^admin_workspace_members/(?P<ws_id>\d+)/(?P<user_id>\d+)/$','dam.workspace.views.admin_workspace_members'),

    (r'^admin_workspace_groups/(?P<ws_id>\d+)/(?P<group_id>\d+)/$','dam.workspace.views.admin_workspace_add_groups'),
    (r'^admin_workspace_groups/(?P<ws_id>\d+)/add/$','dam.workspace.views.admin_workspace_add_groups'),
    (r'^admin_workspace_groups/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_add_groups'),

    (r'^admin_workspace_permissions/(?P<type>.+)/(?P<ws_id>\d+)/$','dam.workspace.views.admin_workspace_permissions'),

#    (r'^load_items/(.+)/(.+)/', 'dam.workspace.views.load_items'),
    (r'^load_items/(.+)/', 'dam.workspace.views.load_items'),
    (r'^load_items/', 'dam.workspace.views.load_items'),

    (r'^workspace/(\d+)/$', 'dam.workspace.views.workspace'),
    (r'^workspace/', 'dam.workspace.views.workspace'),
    (r'^get_n_items/', 'dam.workspace.views.get_n_items'),

    (r'^get_status/', 'dam.workspace.views.get_status'),
    (r'^get_permissions/', 'dam.workspace.views.get_permissions'),

    (r'^get_ws_members/', 'dam.workspace.views.get_ws_members'),
    (r'^get_available_permissions/', 'dam.workspace.views.get_available_permissions'),
    (r'^get_available_users/', 'dam.workspace.views.get_available_users'),
    (r'^save_members/', 'dam.workspace.views.save_members'),
    (r'^switch_ws/', 'dam.workspace.views.switch_ws'),
)
