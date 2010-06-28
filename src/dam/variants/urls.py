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
    (r'^edit_variant/$', 'dam.variants.views.edit_variant'),
    (r'^delete_variant/$', 'dam.variants.views.delete_variant'),
    (r'^force_variant_generation/(.+)/(.+)/$', 'dam.variants.views.force_variant_generation'),
    (r'^get_variants/$', 'dam.variants.views.get_variants'),
    (r'^get_variant_metadata/$', 'dam.variants.views.get_variant_metadata'),
    (r'^get_variants_list/$', 'dam.variants.views.get_variants_list'),
    (r'^get_variant_info/$', 'dam.variants.views.get_variant_info'),
    (r'^get_variant_sources/$', 'dam.variants.views.get_variant_sources'),
    (r'^save_sources/$', 'dam.variants.views.save_sources'),
    (r'^get_variants_menu_list/$', 'dam.variants.views.get_variants_menu_list'),

)
