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

    (r'^delete_item/', 'dam.repository.views.delete_item'),
    (r'^check_item_wss/', 'dam.repository.views.check_item_wss'),
    (r'^get_watermarks/', 'dam.repository.views.get_watermarks'),
    (r'^delete_watermark/', 'dam.repository.views.delete_watermark'),
    (r'^item/(.+)/(.+)/', 'dam.repository.views.get_variant_url'),
    (r'^storage/(?P<resource_name>.*)$', 'dam.repository.views.get_resource'),
     
)
