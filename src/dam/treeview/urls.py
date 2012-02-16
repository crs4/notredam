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
   
    (r'^delete_node/$', 'dam.treeview.views.delete'),
    (r'^add_node/$', 'dam.treeview.views.add'),
    (r'^move_node/$', 'dam.treeview.views.move_node'),
    (r'^save_keyword/$', 'dam.treeview.views.save_association'),
    (r'^get_nodes/$', 'dam.treeview.views.get_nodes'),
    (r'^edit_node/$', 'dam.treeview.views.edit_node'),
    (r'^get_representative_url/$', 'dam.treeview.views.get_representative_url'),
    (r'^remove_association/$', 'dam.treeview.views.remove_association'),
    (r'^get_metadataschema_keyword_target/$', 'dam.treeview.views.get_metadataschema_keyword_target'),
    (r'^get_item_nodes/$', 'dam.treeview.views.get_item_nodes'),
    (r'^save_smart_folder/$', 'dam.treeview.views.save_smart_folder'),
    (r'^get_smart_folders/$', 'dam.treeview.views.get_smart_folders'),
    (r'^get_query_smart_folder/$', 'dam.treeview.views.get_query_smart_folder'),
    (r'^delete_smart_folder/$', 'dam.treeview.views.delete_smart_folder'),
)
