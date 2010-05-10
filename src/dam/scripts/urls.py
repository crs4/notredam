from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^get_script_actions/', 'dam.scripts.views.get_script_actions'),
    (r'^get_scripts/', 'dam.scripts.views.get_script_actions'),
    (r'^new_script/', 'dam.scripts.views.new_script'),
    (r'^edit_script/', 'dam.scripts.views.edit_script'),
    (r'^delete_script/', 'dam.scripts.views.delete_script'),
)
