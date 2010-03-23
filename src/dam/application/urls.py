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

    (r'^$', 'dam.application.views.home'),
    (r'^login/$', 'dam.application.views.do_login'),
    (r'^logout/$', 'dam.application.views.do_logout'),
    (r'^get_component_url/(.+)/(.+)/$', 'dam.application.views.get_component'),
    (r'^get_component_url/(.+)/$', 'dam.application.views.get_component'),
    (r'^redirect_to_component/(.+)/(.+)/$', 'dam.application.views.redirect_to_component'),    
    (r'^redirect_to_resource/(.+)/$','dam.application.views.redirect_to_resource'),
    (r'^registration/$','dam.application.views.registration'),
    (r'^confirm_user/(.+)/$','dam.application.views.confirm_user'),
    (r'^dam_admin/$','dam.application.views.dam_admin'),

)
