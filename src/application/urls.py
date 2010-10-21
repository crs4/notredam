from django.conf.urls.defaults import *
from settings import ROOT_PATH
import os
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^application/', include('application.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

#     Uncomment the next line to enable the admin:
     (r'^admin/', include(admin.site.urls)),
     (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
     (r'^logout/$', 'application.base.views.do_logout'),
     (r'^files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(ROOT_PATH, 'files')}), 
     
     (r'^$', 'application.base.views.home'),
     (r'^load_items/(.+)/$', 'application.base.views.load_items'),
     (r'^get_metadata/$', 'application.base.views.get_metadata'),
     (r'^set_metadata/$', 'application.base.views.set_metadata'),
     (r'^save_rating/$', 'application.base.views.save_rating'),
     (r'^on_view/$', 'application.base.views.on_view'),
     (r'^download_item/$', 'application.base.views.download_item'),
     (r'^get_upload_url/$', 'application.base.views.get_upload_url'),
     (r'^upload_finished/$', 'application.base.views.upload_finished'),
     (r'^get_tags/$', 'application.base.views.get_tags'),
     (r'^get_item_tags/$', 'application.base.views.get_item_tags'),
     (r'^add_tag/$', 'application.base.views.add_tag'),
     (r'^delete_tag/$', 'application.base.views.delete_tag'),
     (r'^edit_tag/$', 'application.base.views.edit_tag'),
     (r'^delete_tag/$', 'application.base.views.delete_tag'),
     (r'^delete_item/$', 'application.base.views.delete_item'),
     
)
