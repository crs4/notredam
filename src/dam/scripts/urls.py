from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^get_script_actions/', 'dam.scripts.views.get_script_actions'),
    (r'^get_scripts/', 'dam.scripts.views.get_scripts'),
    (r'^new_script/', 'dam.scripts.views.new_script'),
    (r'^edit_script/', 'dam.scripts.views.edit_script'),
    (r'^delete_script/', 'dam.scripts.views.delete_script'),
    (r'^get_actions/', 'dam.scripts.views.get_actions'),
    (r'^run_script/', 'dam.scripts.views.run_script'),
    (r'^rename_script/', 'dam.scripts.views.rename_script'),
    (r'^get_available_actions/', 'dam.scripts.views.get_available_actions'),
    (r'^script_monitor/', 'dam.scripts.views.script_monitor'),
    (r'^script_editor/$', 'django.views.generic.simple.direct_to_template', {'template': 'test_wireit.html'}),
    
)
