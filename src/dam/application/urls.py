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
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',

    (r'^$', 'dam.application.views.home'),
    (r'^login/$', 'dam.application.views.do_login'),
    (r'^logout/$', 'dam.application.views.do_logout'),
    (r'^get_component_url/(.+)/(.+)/$', 'dam.application.views.get_component'),
    (r'^redirect_to_component/(.+)/(.+)/$', 'dam.application.views.redirect_to_component'),
    (r'^resources/(.+)/(.+)/$', 'dam.application.views.resources'),
#    (r'^items/(.+)/(.+)/$', 'dam.application.views.redirect_to_component'),    
    (r'^redirect_to_resource/(.+)/$','dam.application.views.redirect_to_resource'),
    (r'^registration/$','dam.application.views.registration'),
    (r'^confirm_user/(.+)/$','dam.application.views.confirm_user'),
    (r'^captcha_check/$','dam.application.views.captcha_check'),
    (r'^new_password/$',direct_to_template, {'template': 'new_password.html'}),
    (r'^get_new_password/$','dam.application.views.get_new_password'),
   
)
