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
    (r'^get_metadata_upload/$', 'dam.upload.views.get_metadata_upload'),
    (r'^get_upload_url/$', 'dam.upload.views.get_upload_url'),
    (r'^upload_resource/$', 'dam.upload.views.upload_resource'),
    (r'^upload_variant/$', 'dam.upload.views.upload_variant'),
    (r'^upload_watermark/$', 'dam.upload.views.upload_watermark'),
    (r'^upload_session_finished/$', 'dam.upload.views.upload_session_finished')
)
