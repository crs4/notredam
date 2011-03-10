from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^get_scripts/', 'dam.scripts.views.get_scripts'),
    (r'^edit_script/', 'dam.scripts.views.edit_script'),
    (r'^delete_script/', 'dam.scripts.views.delete_script'),
    (r'^get_actions/', 'dam.scripts.views.get_actions'),
    (r'^run_script/', 'dam.scripts.views.run_script'),
    (r'^script_monitor/', 'dam.scripts.views.script_monitor'),
    (r'^script_editor/(.+)/$', 'dam.scripts.views.editor'),
    (r'^script_editor/$', 'dam.scripts.views.editor'),
	(r'^get_events/$', 'dam.scripts.views.get_events'),
	(r'^get_types/$', 'dam.scripts.views.get_media_types'),
    
)
