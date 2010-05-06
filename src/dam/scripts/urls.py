from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^get_actions/', 'dam.scripts.views.get_actions'),
)
