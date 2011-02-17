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
    (r'^dam_admin/$','dam.admin.views.dam_admin'),

    (r'^dam_admin/get_admin_settings/$', 'dam.admin.views.get_admin_settings'),
    (r'^dam_admin/get_desc_groups/$', 'dam.admin.views.damadmin_get_desc_groups'),
    (r'^dam_admin/get_desc_list/$', 'dam.admin.views.damadmin_get_desc_list'),
    (r'^dam_admin/get_descriptor_properties/$', 'dam.admin.views.damadmin_get_descriptor_properties'),
    (r'^dam_admin/save_descriptor/$', 'dam.admin.views.damadmin_save_descriptor'),
    (r'^dam_admin/delete_descriptor/$', 'dam.admin.views.damadmin_delete_descriptor'),
    (r'^dam_admin/delete_descriptor_group/$', 'dam.admin.views.damadmin_delete_descriptor_group'),
    (r'^dam_admin/save_descriptor_group/$', 'dam.admin.views.damadmin_save_descriptor_group'),
    (r'^dam_admin/get_rights_list/$', 'dam.admin.views.damadmin_get_rights_list'),
    (r'^dam_admin/get_rights_properties/$', 'dam.admin.views.damadmin_get_rights_properties'),
    (r'^dam_admin/save_rights/$', 'dam.admin.views.damadmin_save_rights'),
    (r'^dam_admin/delete_rights/$', 'dam.admin.views.damadmin_delete_rights'),
    (r'^dam_admin/get_xmp_list/$', 'dam.admin.views.damadmin_get_xmp_list'),
    (r'^dam_admin/get_xmp_namespaces/$', 'dam.admin.views.damadmin_get_xmp_namespaces'),
    (r'^dam_admin/save_ns/$', 'dam.admin.views.damadmin_save_ns'),
    (r'^dam_admin/delete_namespace/$', 'dam.admin.views.damadmin_delete_namespace'),
    (r'^dam_admin/delete_xmp/$', 'dam.admin.views.damadmin_delete_xmp'),
    (r'^dam_admin/save_xmp/$', 'dam.admin.views.damadmin_save_xmp'),
    (r'^dam_admin/get_xmp_structures/$', 'dam.admin.views.damadmin_get_xmp_structures'),
    (r'^dam_admin/get_user_list/$', 'dam.admin.views.damadmin_get_user_list'),
    (r'^dam_admin/save_user/$', 'dam.admin.views.damadmin_save_user'),
    (r'^dam_admin/delete_user/$', 'dam.admin.views.damadmin_delete_user'),
    (r'^dam_admin/get_user_permissions/$', 'dam.admin.views.damadmin_get_user_permissions'),
    (r'^dam_admin/get_workspaces/$', 'dam.admin.views.damadmin_get_workspaces'),
    (r'^dam_admin/get_ws_users/$', 'dam.admin.views.damadmin_get_ws_users'),
    (r'^dam_admin/get_ws_groups/$', 'dam.admin.views.damadmin_get_ws_groups'),
    (r'^dam_admin/save_ws/$', 'dam.admin.views.damadmin_save_ws'),
    (r'^dam_admin/delete_ws/$', 'dam.admin.views.damadmin_delete_ws'),
    (r'^dam_admin/get_list_file_backup/$', 'dam.admin.views.damadmin_get_list_file_backup'),
    (r'^dam_admin/download_file_backup/(.+)/$', 'dam.admin.views.damadmin_download_file_backup'),
    (r'^dam_admin/delete_file_backup/$', 'dam.admin.views.damadmin_delete_file_backup'),
    (r'^dam_admin/create_file_backup/$', 'dam.admin.views.damadmin_create_file_backup'),
    

)
