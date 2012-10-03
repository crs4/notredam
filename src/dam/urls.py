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
from dam.settings import ROOT_PATH, INSTALLATIONPATH, THUMBS_DIR
import os.path

#for admin
from django.contrib import admin
admin.autodiscover()

from dam.settings import MEDIADART_STORAGE

urlpatterns = patterns('', 
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    #(r'^admin/(.*)', admin.site.root), 
     (r'^admin/', include(admin.site.urls)),
    (r'^files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(ROOT_PATH, 'files')}), 
#    (r'^storage/(?P<path>.*)$', 'django.views.static.serve', {'document_root': MEDIADART_STORAGE}), 
#    (r'^storage/(?P<path>.*)/download$', 'django.views.static.serve', {'document_root': MEDIADART_STORAGE}), 
    
    (r'^', include('dam.application.urls')),
    (r'^', include('dam.geo_features.urls')),
    (r'^', include('dam.basket.urls')),
    (r'^', include('dam.variants.urls')),
    (r'^', include('dam.treeview.urls')),
    (r'^', include('dam.metadata.urls')),
    (r'^', include('dam.preferences.urls')),
    (r'^', include('dam.upload.urls')),
    (r'^', include('dam.workspace.urls')),
    (r'^', include('dam.repository.urls')),
    (r'^', include('dam.api.urls')),
    (r'^', include('dam.workflow.urls')),
    (r'^', include('dam.eventmanager.urls')),
    (r'^', include('dam.admin.urls')),
    (r'^', include('dam.scripts.urls')),
    (r'^', include('dam.eventmanager.urls')),
    (r'^kb/', include('dam.kb.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
