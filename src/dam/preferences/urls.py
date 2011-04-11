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
    (r'^get_user_settings/$', 'dam.preferences.views.get_user_settings'),
    (r'^save_pref/$', 'dam.preferences.views.save_pref'),
    (r'^save_system_pref/$', 'dam.preferences.views.save_system_pref'),
    (r'^get_ws_settings/$', 'dam.preferences.views.get_ws_settings'),
    (r'^save_ws_pref/$', 'dam.preferences.views.save_ws_pref'),
    (r'^get_lang_pref/$', 'dam.preferences.views.get_lang_pref'),
    (r'^account_prefs/$', 'dam.preferences.views.account_prefs'),
    (r'^get_account_info/$', 'dam.preferences.views.get_account_info'),
    
)
