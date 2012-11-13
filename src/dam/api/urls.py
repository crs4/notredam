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
from dam.api.views import WorkspaceResource,  ItemResource,  KeywordsResource,  CollectionResource, VariantsResource,   Auth,  SmartFolderResource,  ScriptResource, StateResource



urlpatterns = patterns('',
   
    url(r'^api/item/(.+)/get/$', ItemResource(permitted_methods=('GET'),).read),
    url(r'^api/item/(.+)/add_to_workspace/$', ItemResource(permitted_methods=('GET', ), ).add_to_ws),
    url(r'^api/item/(.+)/delete_from_workspace/$', ItemResource(permitted_methods=('GET',),).delete),
#    url(r'^api/item/(.+)/set_public/$', ItemResource(permitted_methods=('POST',  ),).set_public),
    url(r'^api/item/(.+)/set_metadata/$', ItemResource(permitted_methods=('POST')).set_metadata),
    url(r'^api/item/(.+)/remove_metadata/$', ItemResource(permitted_methods=('POST')).remove_metadata),
   url(r'^api/item/new/$', ItemResource(permitted_methods=('POST',), ).create),
   
   url(r'^api/item/(.+)/add_keywords/$', ItemResource(permitted_methods=('POST',), ).add_keywords),
   url(r'^api/item/(.+)/remove_keywords/$', ItemResource(permitted_methods=('POST',), ).remove_keywords),
   
   url(r'^api/item/(.+)/add_to_collection/$', ItemResource(permitted_methods=('POST',), ).add_to_collection),
   url(r'^api/item/(.+)/remove_from_collection/$', ItemResource(permitted_methods=('POST',), ).remove_from_collection),
   
   url(r'^api/item/(.+)/generate_renditions/$', ItemResource(permitted_methods=('POST',), ).generate_variants),
   url(r'^api/private/item/(.+)/generate_renditions/$', ItemResource(permitted_methods=('POST',), private= True).generate_variants),
   
   url(r'^api/item/(.+)/upload/$', ItemResource(permitted_methods=('POST',), ).upload_variant),
   url(r'^api/item/(.+)/add_component/$', ItemResource(permitted_methods=('POST'),).add_component),
   
#   url(r'^api/item/(.+)/(.+)/get/$', ItemResource(permitted_methods=('POST',), ).get_variant),
   url(r'^api/item/(.+)/get_state/$', ItemResource(permitted_methods=('POST'),).get_state),
   url(r'^api/item/(.+)/get_all_states/$', ItemResource(permitted_methods=('POST'),).get_all_states),
   url(r'^api/item/(.+)/set_state/$', ItemResource(permitted_methods=('POST'),).set_state),
   

#   url(r'^api/item/search/$', ItemResource(permitted_methods=('POST'),).search),
   url(r'^api/item/(.+)/get_keywords/$', ItemResource(permitted_methods=('GET'),).get_keywords),
   url(r'^api/item/(.+)/get_collections/$', ItemResource(permitted_methods=('GET'),).get_collections),
   
   url(r'^api/item/get_type/$', ItemResource(permitted_methods=('POST'),).get_type),


   
   url(r'^api/workspace/new/$', WorkspaceResource(permitted_methods=('POST',), ).create),   
   
   url(r'^api/workspace/(\d+)/delete/$', WorkspaceResource(permitted_methods=('GET',), ).delete),  
   url(r'^api/workspace/(\d+)/edit/$', WorkspaceResource(permitted_methods=('POST')).edit), 
   url(r'^api/workspace/(\d+)/set_name/$', WorkspaceResource(permitted_methods=('POST')).set_name),  
   url(r'^api/workspace/(\d+)/set_description/$', WorkspaceResource(permitted_methods=('POST')).set_description),  
   
   url(r'^api/workspace/(\d+)/get/$', WorkspaceResource(permitted_methods=('GET',), ).read),  
   url(r'^api/workspace/get/$', WorkspaceResource(permitted_methods=('GET',), ).get_list),  
   url(r'^api/workspace/(\d+)/get_keywords/$', WorkspaceResource(permitted_methods=('GET',), ).get_keywords),  
   url(r'^api/workspace/(\d+)/get_items/$', WorkspaceResource(permitted_methods=('GET',), ).get_items),  
   url(r'^api/workspace/(\d+)/get_metadata_languages/$', WorkspaceResource(permitted_methods=('GET',), ).get_metadata_languages),  
     
   url(r'^api/workspace/(\d+)/get_renditions/$', WorkspaceResource(permitted_methods=('GET',), ).get_variants),  
   url(r'^api/workspace/(\d+)/get_collections/$', WorkspaceResource(permitted_methods=('GET',), ).get_collections),  
   url(r'^api/workspace/(\d+)/get_members/$', WorkspaceResource(permitted_methods=('GET',), ).get_members),  
   url(r'^api/workspace/(\d+)/add_members/$', WorkspaceResource(permitted_methods=('POST',), ).add_members),  
   url(r'^api/workspace/(\d+)/remove_members/$', WorkspaceResource(permitted_methods=('POST',), ).remove_members),  
   url(r'^api/workspace/(\d+)/set_permissions/$', WorkspaceResource(permitted_methods=('POST',), ).set_permissions),  
    
   url(r'^api/workspace/(\d+)/get_smartfolders/$', WorkspaceResource(permitted_methods=('GET'), ).get_smartfolders),
   url(r'^api/workspace/(\d+)/get_scripts/$', WorkspaceResource(permitted_methods=('GET'), ).get_scripts),
   url(r'^api/workspace/(\d+)/set_creator/$', WorkspaceResource(permitted_methods=('POST',), ).set_creator),  
   url(r'^api/workspace/(\d+)/get_items_complete/$', WorkspaceResource(permitted_methods=('GET',), ).get_items_complete),  
   #url(r'^api/workspace/(\d+)/search/$', WorkspaceResource(permitted_methods=('POST',), ).search),
   
   url(r'^api/workspace/(\d+)/get_states/$', WorkspaceResource(permitted_methods=('GET',),).get_states),
   
   
   url(r'^api/keyword/new/$', KeywordsResource(permitted_methods=('POST',  ), ).create),   
   url(r'^api/keyword/(\d+)/delete/$', KeywordsResource(permitted_methods=('GET',  ), ).delete),   
   url(r'^api/keyword/(\d+)/move/$', KeywordsResource(permitted_methods=('GET',  ), ).move),   
   url(r'^api/keyword/(\d+)/edit/$', KeywordsResource(permitted_methods=('POST',  ), ).edit),   
   url(r'^api/keyword/(\d+)/get/$', KeywordsResource(permitted_methods=('GET',), ).read),  
   url(r'^api/keyword/(\d+)/add_items/$', KeywordsResource(permitted_methods=('POST')).add_items),   
   url(r'^api/keyword/(\d+)/remove_items/$', KeywordsResource(permitted_methods=('POST'), ).remove_items),      
#   url(r'^api/keyword/get/$', KeywordsResource(permitted_methods=('GET',  ), )),   
   
   
   url(r'^api/collection/new/$', CollectionResource(permitted_methods=('POST'),  ).create),   
   url(r'^api/collection/new/$', CollectionResource(permitted_methods=('POST')).create),   
   url(r'^api/collection/(\d+)/delete/$', CollectionResource(permitted_methods=('GET',  ), ).delete),   
   url(r'^api/collection/(\d+)/move/$', CollectionResource(permitted_methods=('POST',  ), ).move),   
   url(r'^api/collection/(\d+)/edit/$', CollectionResource(permitted_methods=('POST')).edit),   
   url(r'^api/collection/(\d+)/get/$', CollectionResource(permitted_methods=('GET',), ).read),      
#   url(r'^api/collection/get/$', CollectionResource(permitted_methods=('GET',), ).read),      
   url(r'^api/collection/(\d+)/add_items/$', CollectionResource(permitted_methods=('POST')).add_items),   
   url(r'^api/collection/(\d+)/remove_items/$', CollectionResource(permitted_methods=('POST'), ).remove_items),   
   
   url(r'^api/rendition/new/$', VariantsResource(permitted_methods=('POST'), ).create),   
   url(r'^api/rendition/(\d+)/get/$', VariantsResource(permitted_methods=('GET'), ).read),   
#   url(r'^api/rendition/get/$', VariantsResource(permitted_methods=('GET'), ).read),   
   url(r'^api/rendition/(\d+)/edit/$', VariantsResource(permitted_methods=('POST'), ).edit),   
   url(r'^api/rendition/(\d+)/delete/$', VariantsResource(permitted_methods=('GET'), ).delete),   
  
   url(r'^api/smartfolder/new/$', SmartFolderResource(permitted_methods=('POST'), ).create),   
   url(r'^api/smartfolder/(\d+)/get/$', SmartFolderResource(permitted_methods=('GET')).read),   
#   url(r'^api/smartfolder/get/$', SmartFolderResource(permitted_methods=('GET'), ).read),   
   url(r'^api/smartfolder/(\d+)/edit/$', SmartFolderResource(permitted_methods=('POST'), ).edit),   
   url(r'^api/smartfolder/(\d+)/delete/$', SmartFolderResource(permitted_methods=('GET'), ).delete),   
   url(r'^api/smartfolder/(\d+)/get_items/$', SmartFolderResource(permitted_methods=('POST'), ).get_items),   
#   
   url(r'^api/script/new/$', ScriptResource(permitted_methods=('POST'), ).create),   
   url(r'^api/script/(\d+)/run/$', ScriptResource(permitted_methods=('POST'), ).run),
   url(r'^api/script/(\d+)/run_again/$', ScriptResource(permitted_methods=('POST'), ).run_again),   
   url(r'^api/script/(\d+)/edit/$', ScriptResource(permitted_methods=('POST'), ).edit),   
   url(r'^api/script/(\d+)/delete/$', ScriptResource(permitted_methods=('POST'), ).delete),   
   url(r'^api/script/(\d+)/get/$', ScriptResource(permitted_methods=('GET'), ).read),   
   
   url(r'^api/state/(\d+)/delete/$', StateResource(permitted_methods=('POST',),).delete),  
   url(r'^api/state/new/$', StateResource(permitted_methods=('POST',),).create),
   url(r'^api/state/(\d+)/edit/$', StateResource(permitted_methods=('POST',),).edit),
   url(r'^api/state/(\d+)/get/$', StateResource(permitted_methods=('GET',),).read),
   url(r'^api/state/(\d+)/add_items/$', StateResource(permitted_methods=('POST',),).add_items),
   url(r'^api/state/(\d+)/remove_items/$', StateResource(permitted_methods=('POST',),).remove_items),
   
   url(r'^api/login/$', Auth(permitted_methods=('POST'), )._login),   
   url(r'^api/get_users/$', Auth(permitted_methods=('GET'), ).get_users),   
   url(r'^api/add_user/$', Auth(permitted_methods=('GET'), ).add_user),   
 
   # Knowledge base public API
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/class/?$', 'kb.views.class_index'),
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/class/(?P<class_id>\w+)/?$',
       'kb.views.class_'),
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/class/(?P<class_id>\w+)/objects/?$',
       'kb.views.class_objects'),
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/class/(?P<class_id>\w+)/catalog_nodes/?$',
       'kb.views.class_catalog_nodes'),
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/object/?$', 'kb.views.object_index'),
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/object/(?P<object_id>\w+)/?$',
       'kb.views.object_'),
   url(r'^api/workspace/(?P<ws_id>\d+)/kb/object/(?P<object_id>\w+)/catalog_nodes/?$',
       'kb.views.object_catalog_nodes'),
)
