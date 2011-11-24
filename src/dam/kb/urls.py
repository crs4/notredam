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
# Django RESTful interface for NotreDAM knowledge base (see also
# views.py).
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

from django.conf.urls.defaults import *

urlpatterns = patterns('kb',
    (r'^get_hierarchy/$', 'views_GUI.get_object_attributes_hierarchy'),
    (r'^get_nodes_real_obj/$', 'views_GUI.get_nodes_real_obj'),
    (r'^get_specific_info_class/(?P<class_id>\w+)/?$', 'views_GUI.get_specific_info_class'),
    (r'^get_specific_info_obj/(?P<obj_id>\w+)/?$$', 'views_GUI.get_specific_info_obj'),
    (r'^get_class_attributes/(?P<class_id>\w+)/?$', 'views_GUI.get_class_attributes'),
    (r'^get_obj_attributes/$', 'views_GUI.get_object_attributes'),
    (r'^get_workspaces_with_edit_vocabulary/$', 'views_GUI.get_workspaces_with_edit_vocabulary'),
    
)

