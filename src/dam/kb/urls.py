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
    (r'class/?$', 'views.class_index'),
    (r'class/(?P<class_id>\w+)/?$', 'views.class_'),
    (r'class/(?P<class_id>\w+)/objects/?$', 'views.class_objects'),
    (r'object/?$', 'views.object_index'),
    (r'object/(?P<object_id>\w+)/?$', 'views.object_'),
)
