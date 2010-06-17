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

from django.test.client import Client
from models import *
from django.contrib.auth.models import User
import urllib
from django.test import TestCase
from django.utils import simplejson as json
from django.db.models import Q

from exceptions import *
from treeview.models import Node,  NodeMetadataAssociation,  SmartFolder,  SmartFolderNodeAssociation

from variants.models import Variant
#from variants.models import VariantAssociation,   SourceVariant,  PresetParameterValue
from core.dam_workspace.models import WorkspacePermission, WorkspacePermissionAssociation

from workspace.models import DAMWorkspace as Workspace
from repository.models import Item,  Component
from metadata.models import MetadataProperty,  MetadataValue
from core.dam_repository.models import Type
from workflow.models import State, StateItemAssociation

import hashlib

class MyTestCase(TestCase):
#    fixtures = ['test_data.json', ]   

    def setUp(self):
        secret = Secret.objects.get(pk = 1)  
        self.secret = secret.value
        self.api_key = secret.application.api_key
        self.user_id = secret.user.pk
        self.user = secret.user
#        print '--------- api_key ',  self.api_key
        
    def get_final_parameters(self, kwargs = None):
        "add api_key user_id and secret"
        if  not kwargs:
            kwargs = {}
        kwargs['api_key'] = self.api_key
        kwargs['user_id'] = self.user_id
        to_hash = self.secret
        parameters = []
        
        for key,  value in kwargs.items():
            if isinstance(value,  list):
                value.sort()
                for el in value:
                    parameters.append(str(key)+str(el))
            else:                    
                parameters.append(str(key)+str(value))
        
        parameters.sort()
        for el in parameters:
            to_hash += el
            
        hashed_secret = hashlib.sha1(to_hash).hexdigest()
        kwargs['checksum'] = hashed_secret 
        return kwargs
        
        
class WSTestCase(MyTestCase):
#    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json', 'workspace/fixtures/test_data.json' ,  'variants/fixtures/test_data.json', ]   
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'variants/fixtures/test_data.json', 'workspace/fixtures/test_data.json' ,  'metadata/fixtures/test_data.json' ]    
    
    def test_get_list(self):
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/get/',  params)        
        
        resp_dict = json.loads(response.content)        
        print 'resp_dict ',  resp_dict        
        wss_list = []
        for ws in self.user.workspaces.all():
            tmp = {'id':ws.pk,  'name': ws.name,  'description':ws.description,}
            if  ws.creator:
                tmp['creator'] = ws.creator.username
            else:
                tmp['creator']  = None
            wss_list.append(tmp)
        self.assertTrue(resp_dict ==  wss_list)   
        
    def test_get_members(self):
        ws_pk = 1
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_members/'%ws_pk,  params)                
        resp_dict = json.loads(response.content)        
        print 'resp_dict ',  resp_dict        
        self.assertTrue(resp_dict == {'members': [{'username': 'demo', 'permissions': ['admin']}]})
        
        
    def test_add_members(self):
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkSpacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)


    def test_set_permissions(self):
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkSpacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)
        
        params = {'users': u.username, 'permissions':'add item'}
        params = self.get_final_parameters(params)
        response = self.client.post('/api/workspace/%s/set_permissions/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkSpacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = params['permissions']).count() == 1)


        
    def test_remove_members(self):
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkSpacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)
        
        params = self.get_final_parameters({'users': u.username})
        response = self.client.post('/api/workspace/%s/remove_members/'%ws_pk,  params)                
        
        self.assertTrue(response.content == '')
        self.assertTrue(u not in ws.members.all())
        self.assertTrue(WorkSpacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 0)
        
        
        
    def test_get_collections(self):
        ws_pk = 1
        params = {'workspace_id':ws_pk}        
        params = self.get_final_parameters(params)
        response = self.client.get('/api/workspace/%s/get_collections/'%ws_pk,  params)                
        resp_dict = json.loads(response.content)        
        print 'resp_dict ',  resp_dict        
        
        exp_resp = {'collections': [{'items': ['adcc76c9c76fe5905ea7fa27a6ea8099e5aa97ec4'], 'label': 'test_with_item', 'parent_id': None, 'workspace': 1, 'id': 19, 'children': []}, {'items': [], 'label': 'test_rename', 'parent_id': None, 'workspace': 1, 'id': 20, 'children': []}, {'items': [], 'label': 'test1', 'parent_id': None, 'workspace': 1, 'id': 21, 'children': [{'items': [], 'label': 'test1_child', 'parent_id': 21, 'workspace': 1, 'id': 23, 'children': []}]}, {'items': [], 'label': 'test2', 'parent_id': None, 'workspace': 1, 'id': 22, 'children': []}, {'items': [], 'label': 'test_delete', 'parent_id': None, 'workspace': 1, 'id': 24, 'children': []}]}

        self.assertTrue(resp_dict ==  exp_resp)   
        
    def test_get_items(self):
        ws_pk = 1
        params = {'workspace_id':ws_pk}        
        params = self.get_final_parameters(params)
        response = self.client.get('/api/workspace/%s/get_items/'%ws_pk,  params)        
        
        resp_dict = json.loads(response.content)        
#        print 'resp_dict ',  resp_dict        
        
        self.assertTrue(resp_dict ==  [i.pk for i in Item.objects.filter(workspaces__pk = ws_pk)] )   
        
        
    def test_get_variants(self):
        ws_pk = 1
        params = {'workspace_id':ws_pk}        
        params = self.get_final_parameters(params)
        response = self.client.get('/api/workspace/%s/get_variants/'%ws_pk,  params)     
        
        vas = VariantAssociation.objects.filter(workspace__pk = ws_pk)
        
#        resp = {}
#        for va in vas:
#            if va.preferences:
#                tmp = {'params':va.preferences.__dict__}
#                tmp['dest_media_type'] =  va.preferences.media_type.name
#                tmp['params'].pop('id')
#            else:
#                tmp = {}     
#            
#            tmp['id'] = va.pk            
#            v_name = va.variant.name
#            media_type = va.variant.media_type.name
#            if resp.has_key(v_name):
#                
#                resp[v_name][media_type] = tmp
#            else:
#                resp[v_name] = {media_type:tmp}
#          
#            
#           
#            
        resp_dict = json.loads(response.content)   
        print '--------------------'
        print 'resp_dict ',  resp_dict 
#        print 'resp ',  resp
#        self.assertTrue(resp_dict ==  resp)   
    
    
    def test_set_variants(self):
        ws_pk = 1
       
        variant = Variant.objects.get(name = 'preview',  media_type__name = 'image')
        workspace = Workspace.objects.get(pk = ws_pk)        
        
        params = {
            'codec': 'gif', 
            'max_dim': 400, 
#            'cropping':False,  
#            'watermarking': '',
            'variant_id': variant.pk, 
        }
        params = self.get_final_parameters(params)
        
        response = self.client.post('/api/workspace/%s/set_variant_preferences/'%ws_pk,  params)        
        self.assertTrue(response.content== '')   

        prefs = variant.variantassociation_set.get(workspace = workspace).preferences
        print '---------prefs.watermarking ',  prefs.watermarking
        self.assertTrue(prefs.codec == params['codec'])
        self.assertTrue(prefs.max_dim == 300)
        self.assertTrue(prefs.cropping == False)
        self.assertTrue(prefs.watermarking== False)
       
      
    def test_search(self):
        workspace = Workspace.objects.get(pk = 1)
        params = self.get_final_parameters({ 'query': 'test', 
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.post('/api/workspace/%s/search/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
        self.assertTrue(len(resp_dict['items']) == 1)
        self.assertTrue(resp_dict['totalCount'] == 2)
        self.assertTrue(resp_dict['items'][0].has_key('dc_description'))
        
        
    
    def test_search_keywords(self):
        workspace = Workspace.objects.get(pk = 1)
        node = Node.objects.get(label = 'test_remove_1')
        
        params = self.get_final_parameters({ 'keyword': node.pk, 
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.post('/api/workspace/%s/search/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
        self.assertTrue(len(resp_dict['items']) == params['limit'])
        self.assertTrue(resp_dict['totalCount'] == node.items.count())
        self.assertTrue(resp_dict['items'][0].has_key('dc_description'))
             
            
    def test_search_collections(self):
        workspace = Workspace.objects.get(pk = 1)
        collection = Node.objects.get(label = 'test_with_item')
        params = self.get_final_parameters({ 'collection': collection.pk, 
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.post('/api/workspace/%s/search/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
        self.assertTrue(len(resp_dict['items']) == params['limit'])
        self.assertTrue(resp_dict['totalCount'] == collection.items.count())
        self.assertTrue(resp_dict['items'][0].has_key('dc_description'))
        
    def test_search_smart_folders(self):
        workspace = Workspace.objects.get(pk = 1)
        smart_folder = SmartFolder.objects.get(pk = 1)
        
        params = self.get_final_parameters({ 
            'smart_folder': smart_folder.pk, 
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.post('/api/workspace/%s/search/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
#        self.assertTrue(len(resp_dict['items']) == params['limit'])
        self.assertTrue(resp_dict['totalCount'] == smart_folder.nodes.all()[0].items.count())
#        self.assertTrue(resp_dict['items'][0].has_key('dc_description'))
    


    def test_search_complex(self):
        workspace = Workspace.objects.get(pk = 1)
        params = self.get_final_parameters({ 
            'keyword': 18,
            'query': '"test prova"' ,
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.post('/api/workspace/%s/search/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
        self.assertTrue(len(resp_dict['items']) == 1)
        self.assertTrue(resp_dict['totalCount'] == 1)
    
        
        
    
    def test_search_collections_no_results(self):
        workspace = Workspace.objects.get(pk = 1)
        params = self.get_final_parameters({ 'collection': -1, 
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.post('/api/workspace/%s/search/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
        self.assertTrue(len(resp_dict['items']) == 0)
        self.assertTrue(resp_dict['totalCount'] == 0)
        
        
        
    
    
    def test_keywords(self):
             
        ws_pk = 1
        params = {'workspace_id':ws_pk}        
        params = self.get_final_parameters(params)
        
        response = self.client.get('/api/workspace/%s/get_keywords/'%ws_pk, params,  )        
        resp_dict = json.loads(response.content)        
#        ws = Workspace.objects.get(pk = ws_pk)
#        nodes = Node.objects.filter(workspace = ws,  type = 'keyword')        
#        self.assertTrue(resp_dict.has_key('keywords'))
#        self.assertTrue(isinstance(resp_dict['keywords'],  list))
#        self.assertTrue(len(resp_dict['keywords']) ==  nodes.count() )   

        ws = Workspace.objects.get(pk = ws_pk)
        nodes = Node.objects.filter(type = 'keyword',  depth = 1, workspace = ws)
        self.assertTrue(resp_dict.has_key('keywords'))
        self.assertTrue(isinstance(resp_dict['keywords'],  list))
      
        self.assertTrue(len(resp_dict['keywords']) ==  nodes.count() )  
        node_id = resp_dict['keywords'][0]['id']
        node = Node.objects.get(pk = node_id)
       
        self.assertTrue(resp_dict['keywords'][0]['workspace'] == node.workspace.pk)
        self.assertTrue(resp_dict['keywords'][0]['parent_id'] == None)
        self.assertTrue(resp_dict['keywords'][0]['label'] == node.label)
        
        items = node.items.all()
        self.assertTrue(resp_dict['keywords'][0]['items'] == [i.pk for i in items])
        self.assertTrue(len(resp_dict['keywords'][0]['children'] )== node.children.all().count())
       
        print resp_dict['keywords']
   
    def test_no_api_key(self):
             
        ws_pk = 1
        params = {'workspace_id':ws_pk,  'user_id': self.user_id}        
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )        
        resp_dict = json.loads(response.content)             
        
        self.assertTrue(resp_dict.get('error code') == 25)
        
    def test_wrong_secret(self):
             
        ws_pk = 1
        params = {'workspace_id':ws_pk,  'user_id': self.user_id,  'api_key': self.api_key,  'checksum': 'lalala'}        
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )        
        resp_dict = json.loads(response.content)             
        
        self.assertTrue(resp_dict.get('error code') == 30)
    
        
    def test_set_name(self):
             
        ws_pk = 1        
        params = self.get_final_parameters({'name':'test_', })
        
        response = self.client.post('/api/workspace/%s/set_name/'%ws_pk, params,)        
        self.assertTrue(response.content == '')
        
        ws = Workspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == 'test_')
        
        
    def test_set_description(self):
    
        ws_pk = 1
        params = self.get_final_parameters({'description':'test_'})
        response = self.client.post('/api/workspace/%s/set_description/'%ws_pk, params)        
        self.assertTrue(response.content == '')
        
        ws = Workspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.description == 'test_')
        
    def test_get(self):
             
        ws_pk = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )      
        
        resp_dict = json.loads(response.content)    
        print 'resp_dict ',  resp_dict 
        ws = Workspace.objects.get(pk = ws_pk)        
        self.assertTrue(resp_dict['id'] == str(ws.pk))
        self.assertTrue(resp_dict['name'] == ws.name)
        self.assertTrue(resp_dict['description'] == ws.description)

        
    def test_delete(self):
             
        name = 'test_2'        
        params = self.get_final_parameters({'name':name, })
        response = self.client.post('/api/workspace/new/', params)        
        resp_dict = json.loads(response.content)           
        ws_pk = resp_dict['id']
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/delete/'%ws_pk, params)        
        self.assertTrue(response.content == '')
        self.assertRaises(Workspace.DoesNotExist,  Workspace.objects.get,  pk = ws_pk)

    def test_create(self):
             
        name = 'test_1'
        
        params = self.get_final_parameters({'name':name,  })
        response = self.client.post('/api/workspace/new/', params, )        
        resp_dict = json.loads(response.content)        
        ws_pk = resp_dict['id']
        ws = Workspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == name)
        self.assertTrue(resp_dict.has_key('description'))
        self.assertTrue(resp_dict.get('name') == name)
        
        
    def test_set_creator(self):
        u = User.objects.create(username = 'test')
        ws_id = 1

        
        params = self.get_final_parameters({'creator_id':u.pk})
        response = self.client.post('/api/workspace/%s/set_creator/'%ws_id, params, )        

        ws = Workspace.objects.get(pk = ws_id)
        self.assertTrue(response.content == '')

        self.assertTrue(ws.creator == u)

    def test_get_smartfolders(self):
        ws_id = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_smartfolders/'%ws_id, params, )        

        ws = Workspace.objects.get(pk = ws_id)
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.has_key('smartfolders'))
        self.assertTrue(len(resp_dict['smartfolders']) == 1)
        
        
class ItemTest(MyTestCase):  
    fixtures = ['api/fixtures/test_data.json', 
                'treeview/fixtures/test_data.json', 
                 'repository/fixtures/test_data.json',  
#                 'variants/fixtures/test_data.json',
                  'workspace/fixtures/test_data.json' , 
                   'metadata/fixtures/test_data.json' 
                   ]    
    
    def test_create(self):
        workspace_id = 1
        metadata_dict = {'namespace':'dc',  'name':'title',  'value': 'test',  'lang': 'en', }
        params = {'workspace_id':workspace_id, 'media_type': 'image' }
    
        params = self.get_final_parameters(params)                
        
        response = self.client.post('/api/item/new/', params,)                
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict.has_key('id'))
        item = Item.objects.get(pk = resp_dict['id'])
        self.assertTrue(item.type.name == 'image')
        self.assertTrue(resp_dict['workspace_id'] == str(workspace_id))
            
#        m = item.metadata.all()
#        
#        print 'metadata ',  m
#        m = m[0]
#        print m.value
#        self.assertTrue(m.schema.field_name== metadata_dict['name'])
#        self.assertTrue(m.schema.namespace.prefix== metadata_dict['namespace'])
#        self.assertTrue(m.value == metadata_dict['value'])
#        self.assertTrue(m.language == metadata_dict['lang'])
#        
    
        
        
    def test_create_media_type_exception(self):
        workspace_id = 1
        media_type = 'movieeee'
        params = self.get_final_parameters({'workspace_id':workspace_id,  'media_type': media_type})
        
        response = self.client.post('/api/item/new/', params,)                
        resp_dict = json.loads(response.content)        
        self.assertTrue(resp_dict['error code'] == InvalidMediaType.error_code) 
        
        
        
    def test_get(self):
        item = Item.objects.all()[0]    
        keywords = item.keywords()            
        ws_pk = 1
        params = self.get_final_parameters({'variants_workspace': ws_pk})
        response = self.client.get('/api/item/%s/get/'%item.pk, params, )                        
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict.has_key('id'))
        self.assertTrue(resp_dict.has_key('keywords'))
        self.assertTrue(resp_dict.has_key('collections'))
        self.assertTrue(resp_dict.has_key('workspaces'))
        self.assertTrue(resp_dict['media_type'] == 'image') 
        
        self.assertTrue(resp_dict['id'] == item.pk) 
        self.assertTrue(resp_dict['keywords'] == keywords)
        self.assertTrue(resp_dict['upload_workspace'] == 1)
        print "resp_dict %s"%resp_dict
        print "item.node_set.filter(type = 'collection')%s"%item.node_set.filter(type = 'collection')
        self.assertTrue(resp_dict['collections'] == [c.pk for c in item.node_set.filter(type = 'collection')])
    
        metadata = {'dc_title': {'en-US': 'test'}}
#        metadata = {u'dc_subject': [u'test_remove_1', u'test', u'prova', u'provaaaa'], u'dc_identifier': u'test id', u'dc_description': {u'en-US': u'test prova\n'}, u'Iptc4xmpExt_LocationShown': [{u'Iptc4xmpExt_CountryCode': u'123', u'Iptc4xmpExt_ProvinceState': u'test', u'Iptc4xmpExt_CountryName': u'test', u'Iptc4xmpExt_City': u'test'}, {u'Iptc4xmpExt_CountryCode': u'1233', u'Iptc4xmpExt_ProvinceState': u'prova', u'Iptc4xmpExt_CountryName': u'prova', u'Iptc4xmpExt_City': u'prova'}]}                                                                                                                                                                                                    
        self.assertTrue(resp_dict['metadata'] == metadata)
        
        
    def test_move(self):
        workspace_id = 1
       
        item_id = Item.objects.all()[0].pk
        user = User.objects.get(pk = 1)
        ws_new = Workspace.objects.create_workspace('test', '', user)
        
        params = self.get_final_parameters({'workspace_id':ws_new.pk})
        response = self.client.post('/api/item/%s/add_to_workspace/'%item_id, params,  )             
        self.assertTrue(response.content == '')       
        
        wss = Item.objects.get(pk = item_id).workspaces.all()
        self.assertTrue(wss.count() == 2)
        self.assertTrue(wss.filter(Q(pk = workspace_id)| Q(pk = ws_new.pk)).count() == 2)
        
        
    def test_delete(self):
        workspace_id = 1
       
        item_id = item_id = Item.objects.all()[0].pk
        
        params = self.get_final_parameters({'workspace_id':workspace_id})
        response = self.client.get('/api/item/%s/delete_from_workspace/'%item_id, params,  )            
        
        self.assertTrue(response.content == '')               
        self.assertRaises(Item.DoesNotExist,  Item.objects.get,  pk = item_id)
        

    def test_metadata(self):
        
        item = Item.objects.all()[0]
        item_id = item.pk
        metadata_dict = {'dc_title': {'en-US': 'test'},  'dc_identifier': 'test',  'dc_subject': ['test', 'test2']}

        params = self.get_final_parameters({'metadata':json.dumps(metadata_dict),  'workspace_id':1})
        response = self.client.post('/api/item/%s/set_metadata/'%item_id, params, )            

        self.assertTrue(response.content == '')
            

        print 'metadata ',  item.metadata.all()

        title = item.metadata.get(schema__field_name = 'title')
        print 'title',  title.value
        self.assertTrue(title.value == 'test')
                
        identifier = item.metadata.get(schema__field_name = 'identifier')        
        self.assertTrue(identifier.value == 'test')
        
        sub = item.metadata.filter(schema__field_name = 'subject')        
        self.assertTrue(sub[0].value == 'test')
        self.assertTrue(sub[1].value == 'test2')
       
     
    def test_remove_metadata_single(self):
        workspace_id = 1
        params = self.get_final_parameters({'workspace_id':workspace_id,  'media_type': 'image'})        
        response = self.client.post('/api/item/new/', params,  )                
        
        resp_dict = json.loads(response.content)        
        item_id = resp_dict.get('id')
        item = Item.objects.get(pk = item_id)
       
        
#        metadata_dict = {'namespace':'dc',  'name':'subject',  'value': ['test',  'test2']}
        metadata_dict = {'dc_subject': ['test', 'test2']}
        params = self.get_final_parameters({ 'metadata':json.dumps(metadata_dict),  'workspace_id':1})        
        self.client.post('/api/item/%s/set_metadata/'%item_id, params, )         
     
        metadata_dict_to_remove = {'namespace':'dc',  'name':'subject',  'value': 'test2'}
        params = self.get_final_parameters({ 'metadata':json.dumps([metadata_dict_to_remove]), 'workspace_id':1})        
        response = self.client.post('/api/item/%s/remove_metadata/'%item_id, params, )        
        self.assertTrue(response.content == '')        
        m = item.metadata.all()        
        self.assertTrue(m.count() == 1)
        m_0 = m[0]      
#        self.assertTrue(m_0.schema.namespace == metadata_dict['namespace'])
#        self.assertTrue(m_0.schema.name== metadata_dict['name'])
#        self.assertTrue(m_0.value == metadata_dict['value'][0])        
        
        print 'm_0.value ',  m_0.value 
        print 'metadata_dict.items()[0] ',  metadata_dict.values()[0]
        self.assertTrue(m_0.value == metadata_dict.values()[0][0])        
        
    def test_remove_metadata_all(self):
        workspace_id = 1
        params = self.get_final_parameters({ 'workspace_id':workspace_id,  'media_type': 'image'})        
        response = self.client.post('/api/item/new/', params,  )                
        
        resp_dict = json.loads(response.content)        
        item_id = resp_dict.get('id')
        item = Item.objects.get(pk = item_id)
        
        metadata_dict = {'namespace':'dc',  'name':'subject',  'value': ['test',  'test2']}
        params = self.get_final_parameters({ 'metadata':json.dumps([metadata_dict])})        
        self.client.post('/api/item/%s/set_metadata/'%item_id, params, )         
     
        metadata_dict_to_remove = {'namespace':'dc',  'name':'subject'}
        params = self.get_final_parameters({ 'metadata':json.dumps([metadata_dict_to_remove])})        
        response = self.client.post('/api/item/%s/remove_metadata/'%item_id, params, )        
        self.assertTrue(response.content == '')        
        m = item.metadata.all()
        
        self.assertTrue(m.count() == 0)        
        
    def test_add_keywords(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        new_node = Node.objects.get(label = 'test',  type = 'keyword', workspace = ws)
        item = Item.objects.all()[0]
        
        item_id = item.pk
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 0)
        params = self.get_final_parameters({ 'keywords':new_node.pk})        
        response = self.client.post('/api/item/%s/add_keywords/'%item_id, params, )            
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 1)
        
        
    def test_remove_keywords(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        new_node = Node.objects.get(label = 'test_remove_1',  type = 'keyword', workspace = ws)
        item = Item.objects.all()[0]
        item_id = item.pk
        label = 'test'        
        params = self.get_final_parameters({ 'keywords':new_node.pk})
        
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 1)
        response = self.client.post('/api/item/%s/remove_keywords/'%item_id, params, )  
        
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 0)
        
    def test_add_to_collection(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        collection_node = Node.objects.get(label = 'test1',  type = 'collection')
        item = Item.objects.all()[0]
        params = self.get_final_parameters({ 'collection_id': collection_node.pk})        
        
        response = self.client.post('/api/item/%s/add_to_collection/'%item.pk, params, )            
        print 'response.content',  response.content
        self.assertTrue(response.content == '')         
        items = collection_node.items.all()
#        print '--------------------items ',  items 
        self.assertTrue(items.count() == 1)
        self.assertTrue(items[0] == item)
        
    def test_remove_from_collection(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        collection_node = Node.objects.get(label = 'test1',  type = 'collection')        
        item = Item.objects.all()[0]
        params = self.get_final_parameters({ 'collection_id': collection_node.pk})        
        
        response = self.client.post('/api/item/%s/remove_from_collection/'%item.pk, params, )            
        self.assertTrue(response.content == '')         
        items = collection_node.items.all()        
        self.assertTrue(items.count() == 0)
        
        
    def test_add_to_ws(self):
        workspace = Workspace.objects.create(name = 'test_ws',  creator = self.user)
        workspace_id = workspace.pk
        
        
        item = Item.objects.all()[0]
        params = self.get_final_parameters({ 'workspace_id': workspace_id})        
        response = self.client.post('/api/item/%s/add_to_workspace/'%item.pk, params, )            
        self.assertTrue(response.content == '')        
        self.assertTrue(item in workspace.items.all()) 
        

        
        
    def test_upload(self):
        from django.test import client 
        from batch_processor.models import Action
        workspace = Workspace.objects.all()[0]
        image = Type.objects.get(name = 'image')
        item = Item.objects.create(type = image)
        item.workspaces.add(workspace)
        
        file = open('files/images/logo_blue.jpg')
        params = self.get_final_parameters({ 'workspace_id': 1,  'variant_id':1})                
        params['Filedata'] = file
        
        response = self.client.post('/api/item/%s/upload/'%item.pk, params, )            
        file.close()
        
        print response.content 
        self.assertTrue(item.component_set.filter(variant__id = 1).count() == 1)
        self.assertTrue(Action.objects.filter(component__in = item.component_set.all()).count() == 7) #(adapt + extract feat)*3 + extract feat orig
                 
        
    def test_get_state(self):
        
        workspace = Workspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        state = State.objects.create(name = 'test',  workspace = workspace)
        state_association = StateItemAssociation.objects.create(state = state, item = item, )
        params = self.get_final_parameters({ 'workspace_id': workspace.pk,  }) 
        response = self.client.post('/api/item/%s/get_state/'%item.pk, params, )            
        resp_dict = json.loads(response.content)
        print '-------------------------',  resp_dict
        self.assertTrue(resp_dict == {'name': 'test'})
        
    
    def test_set_state(self): 
        workspace = Workspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        state = State.objects.create(name = 'test',  workspace = workspace)
        state_association = StateItemAssociation.objects.create(state = state, item = item)
        params = self.get_final_parameters({ 'workspace_id': workspace.pk, 'state': state.name}) 
        response = self.client.post('/api/item/%s/set_state/'%item.pk, params, )            
        
        self.assertTrue(response.content == '')
        self.assertTrue(StateItemAssociation.objects.get(item = item).state.name == 'test')
        
        

class KeywordsTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json']   
    

    def test_get_single(self):        
             
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        node = Node.objects.get(label = 'test_remove_1',  workspace = ws)
        response = self.client.get('/api/keyword/%s/get/'%node.pk, params)        
        resp_dict = json.loads(response.content)        
        print '---------------------------+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ resp_dict',  resp_dict 
        self.assertTrue(resp_dict.get('id') == node.pk)
        
        self.assertTrue(resp_dict['workspace'] == node.workspace.pk)
        self.assertTrue(resp_dict['parent_id'] == node.parent.pk)
        self.assertTrue(resp_dict['label'] == node.label)
        self.assertTrue(resp_dict['type'] == 'keyword')
        self.assertTrue(resp_dict['associate_ancestors'] == node.associate_ancestors)
        self.assertTrue(len(resp_dict['metadata_schema']) == node.metadata_schema.all().count())
        self.assertTrue(resp_dict['metadata_schema'][0]['name'] == node.metadata_schema.all()[0].field_name)
        self.assertTrue(resp_dict['metadata_schema'][0]['value'] ==  NodeMetadataAssociation.objects.get(node = node,  metadata_schema = node.metadata_schema.all()[0]).value)
        self.assertTrue(resp_dict['items'] == [Item.objects.all()[0].pk])
        self.assertTrue(len(resp_dict['children']) == node.children.all().count())
        
        
    def test_get_single_category(self):        
             
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        node = Node.objects.get(label = 'People',  workspace = ws)
        response = self.client.get('/api/keyword/%s/get/'%node.pk, params)        
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.get('id') == node.pk)
        
        self.assertTrue(resp_dict['workspace'] == node.workspace.pk)
        self.assertTrue(resp_dict['parent_id'] == None)
        self.assertTrue(resp_dict['label'] == node.label)
        self.assertTrue(resp_dict['type'] == 'category')
        self.assertTrue(len(resp_dict['children']) == node.children.all().count())
        self.assertTrue(resp_dict['children'][0]['id'] == node.children.all()[0].pk)
        
        
    
    def test_create(self):             
        parent_node = Node.objects.get(pk = 3)
        label = 'test_create'
        params = self.get_final_parameters({ 'parent_id':parent_node.pk,  'label':label, 'type': 'keyword' })     
        response = self.client.post('/api/keyword/new/', params,  )  
        resp_dict = json.loads(response.content)        
        new_node = Node.objects.get(pk = resp_dict['id'])
        
        self.assertTrue(new_node.parent == parent_node)
        self.assertTrue(new_node.workspace == parent_node.workspace)        
        self.assertTrue(new_node.label == label)        
        self.assertTrue(new_node.associate_ancestors == False)        
        self.assertTrue(new_node.metadata_schema.all().count()== 0)
        self.assertTrue(new_node.cls == 'keyword')
        


    def test_create_2(self):             
        parent_node = Node.objects.get(pk = 3)
        label = 'test_create'
        params = self.get_final_parameters({ 'parent_id':parent_node.pk,  'label':label, 'associate_ancestors': 'true',  'type': 'keyword' })     
        response = self.client.post('/api/keyword/new/', params,  )  
        resp_dict = json.loads(response.content)        
        new_node = Node.objects.get(pk = resp_dict['id'])
        
        self.assertTrue(new_node.parent == parent_node)
        self.assertTrue(new_node.workspace == parent_node.workspace)        
        self.assertTrue(new_node.label == label)        
        self.assertTrue(new_node.associate_ancestors == True)        
        self.assertTrue(new_node.metadata_schema.all().count()== 0)
        
        
    def test_create_no_parent(self):             
        parent_node = Node.objects.get(pk = 3)
        label = 'test_create'
        params = self.get_final_parameters({ 'workspace_id':1,  'label':label, 'type': 'keyword' })     
        response = self.client.post('/api/keyword/new/', params,  )  
        resp_dict = json.loads(response.content)        
        new_node = Node.objects.get(pk = resp_dict['id'])        

        self.assertTrue(new_node.workspace == parent_node.workspace)        
        self.assertTrue(new_node.label == label)        
        self.assertTrue(new_node.associate_ancestors == False)        
        self.assertTrue(new_node.metadata_schema.all().count()== 0)
        self.assertTrue(new_node.cls == 'keyword')

    def test_create_metadata(self):             
        parent_node = Node.objects.get(pk = 3)
        label = 'test_create'
        metadata_schema = MetadataProperty.objects.get(field_name = 'title')
        
        params = self.get_final_parameters({ 
            'parent_id':parent_node.pk,  
            'label':label, 
#            'associate_ancestors': 'false', 
            'type': 'keyword',  
            'metadata_schema': json.dumps([{"namespace": 'dublin core','name': metadata_schema.field_name  ,   "value": label}])
        })     
        response = self.client.post('/api/keyword/new/', params,  )  
        resp_dict = json.loads(response.content)        
        new_node = Node.objects.get(pk = resp_dict['id'])
        
        self.assertTrue(new_node.parent == parent_node)
        self.assertTrue(new_node.workspace == parent_node.workspace)        
        self.assertTrue(new_node.label == label)        
        self.assertTrue(new_node.associate_ancestors == False)        
        self.assertTrue(new_node.metadata_schema.all().count()== 1)
        self.assertTrue(new_node.metadata_schema.all()[0].pk== metadata_schema.pk)
        self.assertTrue(NodeMetadataAssociation.objects.get(node = new_node,  metadata_schema = metadata_schema).value == label)

        
    def test_create_category(self):
            
        ws = Workspace.objects.get(pk = 1)
        label = 'test_category'
        parent_node = Node.objects.get(pk = 3)
        params = self.get_final_parameters({ 'parent_id':parent_node.pk,  'label':label, 'type': 'category' })     
        response = self.client.post('/api/keyword/new/', params,  )  
        resp_dict = json.loads(response.content)        
        new_node = Node.objects.get(pk = resp_dict['id'])
        self.assertTrue(new_node.parent == parent_node)
        self.assertTrue(new_node.workspace == parent_node.workspace)        
        self.assertTrue(new_node.label == label)        
        self.assertTrue(new_node.type == 'keyword')        
        self.assertTrue(new_node.cls== 'category')        
            
        
    def test_edit(self):

        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'People',  workspace = ws)        
        params = self.get_final_parameters({'label':'test'})        
        self.assertTrue(node.associate_ancestors == False)
        
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        
        node = Node.objects.get(pk = node.pk)
        self.assertTrue(node.label == 'test')
        self.assertTrue(node.associate_ancestors == False)
    
    def test_edit_1(self):

        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'test',  workspace = ws)        
        params = self.get_final_parameters({'associate_ancestors':'true'})        
        self.assertTrue(node.associate_ancestors == False)
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        node = Node.objects.get(pk = node.pk)
        self.assertTrue(node.associate_ancestors == True)
        
    
    def test_edit_metadata(self):

        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'test',  workspace = ws)  
        
        label = '_test_'
        metadata_schema = MetadataProperty.objects.get(field_name = 'title')
        
        
        params = self.get_final_parameters({'metadata_schema': json.dumps([{"namespace": 'dublin core','name': metadata_schema.field_name  ,   "value": label}])})        
        self.assertTrue(node.associate_ancestors == False)
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        new_node = Node.objects.get(pk = node.pk)
        
        self.assertTrue(new_node.label == 'test')        
        self.assertTrue(new_node.associate_ancestors == False)        
        self.assertTrue(new_node.metadata_schema.all().count()== 1)
        self.assertTrue(new_node.metadata_schema.all()[0].pk== metadata_schema.pk)
        self.assertTrue(NodeMetadataAssociation.objects.get(node = new_node,  metadata_schema = metadata_schema).value == label)
        
    
    

    

    def test_move(self):
        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)        
        node_id = Node.objects.get(label = 'test').pk
        
        new_parent_node_pk = parent_node = Node.objects.get(workspace = ws, label = 'Places',  depth = 1).pk
        params = self.get_final_parameters({ 'parent_id':new_parent_node_pk,  })        
        self.client.post('/api/keyword/%s/move/'%node_id, params,  )      
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/get/'%node_id, params)        
        resp_dict = json.loads(response.content)
        parent_id = resp_dict['parent_id']        
        self.assertTrue(parent_id == new_parent_node_pk)        
        
    def test_delete(self):
        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)
        node_id = Node.objects.get(label = 'test').pk
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/delete/'%node_id, params,  ) 
        
        self.assertTrue(response.content == '')
        self.assertRaises(Node.DoesNotExist,  Node.objects.get, pk = node_id )
        
    def test_add_items(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.all()[0]
        item_id = item.pk
        new_node = Node.objects.get(label = 'test')
        
        params = self.get_final_parameters({ 'items':item.pk})        
        response = self.client.post('/api/keyword/%s/add_items/'%new_node.pk, params, )            
        self.assertTrue(item.node_set.filter(label = 'test').count() == 1)
      
    def test_remove_items(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.create(uploader = User.objects.get(pk = 1),  type = Type.objects.get(name = 'image'),)
        
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.all()[0]
        item_id = item.pk
        new_node = Node.objects.get(label = 'test')
        
        params = self.get_final_parameters({ 'items':item.pk})        
        response = self.client.post('/api/keyword/%s/remove_items/'%new_node.pk, params, )  
        self.assertTrue(item.node_set.filter(label = 'test').count() == 0)

class CollectionsTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json']   
    
    def test_get_single(self):        
             
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters()
        label ='test1'
        node = Node.objects.get(label = label,  workspace = ws)
        response = self.client.get('/api/collection/%s/get/'%node.pk, params)                
        
        resp_dict = json.loads(response.content)                
        self.assertTrue(resp_dict.get('id') == node.pk)
        self.assertTrue(resp_dict['workspace'] == node.workspace.pk)
        self.assertTrue(resp_dict['parent_id'] == None)
        self.assertTrue(resp_dict['label'] == label)
        
        items = node.items.all()
        self.assertTrue(resp_dict['items'] == [i.pk for i in items])
        self.assertTrue(len(resp_dict['children']) == node.children.all().count())
    
#    def test_get(self):
#             
#        ws_pk = 1
#        params = self.get_final_parameters({'workspace_id':ws_pk})
#        response = self.client.get('/api/collection/get/', params,  )        
#        resp_dict = json.loads(response.content)    
#
#        ws = Workspace.objects.get(pk = ws_pk)
#        
#        collections = Node.objects.filter( type = 'collection',  workspace = ws,  depth= 1)       
#        self.assertTrue(resp_dict.has_key('collections'))
#        self.assertTrue(isinstance(resp_dict['collections'],  list))
#        self.assertTrue(len(resp_dict['collections']) ==  collections.count())   
#        
#        node_id = resp_dict['collections'][0]['id']
#        node = Node.objects.get(pk = node_id)
#        
#        
#        self.assertTrue(resp_dict['collections'][0]['workspace'] == node.workspace.pk)
##        if node.parent.depth > 0:
##            self.assertTrue(resp_dict['collections'][node_id]['parent_id'] == node.parent.pk)
##        else:
#        self.assertTrue(resp_dict['collections'][0]['parent_id'] == None)
#        self.assertTrue(resp_dict['collections'][0]['label'] == node.label)
#        
#        items = node.items.all()
#        self.assertTrue(resp_dict['collections'][0]['items'] == [i.pk for i in items])
#        self.assertTrue(len(resp_dict['collections'][0]['children'] )== node.children.all().count())
#        
#        
#    
    def test_create(self):             
        
        ws = Workspace.objects.get(pk = 1)
        label = 'collection_test'
        params = self.get_final_parameters({ 'workspace_id':ws.pk,  'label':label})     
        response = self.client.post('/api/collection/new/', params,  )  
        resp_dict = json.loads(response.content)        
        
        self.assertTrue(resp_dict.has_key('id'))
        
        self.assertTrue(resp_dict['workspace_id'] == ws.pk)
        self.assertTrue(resp_dict['parent_id'] == None)
        self.assertTrue(resp_dict['label'] == label)        


    def test_rename(self):
        "changing label"

        node_id = Node.objects.get(label = 'test1',  depth = 1).pk
        new_label = 'new_label'
        params = self.get_final_parameters({'label':new_label})        
        response = self.client.post('/api/collection/%s/rename/'%node_id , params,  )                
        node = Node.objects.get(pk = node_id )
        self.assertTrue(node.label == new_label)
        
    def test_move(self):
        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)
        
        node_id = Node.objects.get(label = 'test1', depth = 1).pk
        dest_id= Node.objects.get(label = 'test2', depth = 1).pk
        params = self.get_final_parameters({ 'parent_id':dest_id,  })
        resp = self.client.get('/api/collection/%s/move/'%node_id, params)      
        
        self.assertTrue(resp.content == '')
        self.assertTrue(resp.status_code == 200)
        node = Node.objects.get(pk = node_id)
        self.assertTrue(node.parent.pk == dest_id)
        
    def test_move_to_the_top(self):
        ws_pk = 1 
        ws = Workspace.objects.get(pk = ws_pk)
        
        node_id = Node.objects.get(label = 'test1_child', ).pk
        root_pk = Node.objects.get(workspace = ws, type ="collection",depth = 0).id
        params = self.get_final_parameters({ })
        resp = self.client.get('/api/collection/%s/move/'%node_id, params)      
        
        self.assertTrue(resp.content == '')
        self.assertTrue(resp.status_code == 200)
        node = Node.objects.get(pk = node_id)
        self.assertTrue(node.parent.pk == root_pk)        
        
    def test_delete(self):       
        node = Node.objects.get(label = 'test1')
        params = self.get_final_parameters()
        response = self.client.get('/api/collection/%s/delete/'%node.pk, params,  ) 
        
        self.assertTrue(response.content == '')
        self.assertRaises(Node.DoesNotExist,  Node.objects.get, pk = node.pk)

    def test_add_items(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        coll= Node.objects.get(label = 'test1',  workspace = ws,  type = 'collection')
        item = Item.objects.all()[0]        
        
        params = self.get_final_parameters({ 'items':[item.pk,  item.pk]})        
        response = self.client.post('/api/collection/%s/add_items/'%coll.pk, params) 
        self.assertTrue(response.content == '')
        
        items = coll.items.all()
        
        self.assertTrue(items.count() == 1)
        
    def test_remove_items(self):
        workspace_id = 1
        ws = Workspace.objects.get(pk = workspace_id)
        coll = Node.objects.get(label = 'test_with_item',  workspace = ws)
        item = Item.objects.all()[0]
        items = coll.items.all()        
        self.assertTrue(items.count() == 1)
        params = self.get_final_parameters({ 'items':item.pk})        
        response = self.client.post('/api/collection/%s/remove_items/'%coll.pk, params, ) 
        
        self.assertTrue(response.content == '')        
        items = coll.items.all()        
        self.assertTrue(items.count() == 0)
        

class TestLogin(MyTestCase):
    fixtures = ['api/fixtures/test_data.json', ]   
    def test_login(self):
        user = User.objects.get(pk = self.user_id)
        
        password = 'demo'
        params = {'user_name':user.username,  'api_key':self.api_key,  'password': password}
        response = self.client.post('/api/login/', params)        
        json_resp = json.loads(response.content)
        self.assertTrue(json_resp['user_id'] == user.pk)
        self.assertTrue(json_resp['secret'] == self.secret)
        self.assertTrue(json_resp['workspace_id'] == 1)
        self.assertTrue(json_resp.has_key('session_id'))
        
    def test_login_wrong(self):
        user = User.objects.get(pk = self.user_id)
        
        password = 'demoooo'
        params = {'user_name':user.username,  'api_key':self.api_key,  'password': password}
        response = self.client.post('/api/login/', params)        
        json_resp = json.loads(response.content)
        print 'json_resp  %s' %json_resp 
        self.assertTrue(json_resp['error code'] == 31)
        
    def test_get_users(self):
        user = User.objects.get(pk =1)
        
        params = self.get_final_parameters({})
        print '------- params ',  params
        response = self.client.get('/api/get_users/', params)        
        
        json_resp = json.loads(response.content)
        print 'json_resp ',  json_resp 
        expected_resp = {'users': [{'id':user.pk, 'username': user.username, 'password': user.password, 'email': user.email, 'is_superuser': user.is_superuser}]}
        self.assertTrue(json_resp== expected_resp)
    

    def test_add_user(self):
        
        params = {'username': 'test',  'email': 't@t.it',  'password': 'sha1$fa34f$1b63507b88b494bb58d466d7f669a1670fe838fb'}
        params = self.get_final_parameters(params)
        
        response = self.client.post('/api/add_user/', params)        
        
        json_resp = json.loads(response.content)
        print 'json_resp ',  json_resp 
        
        self.assertTrue(json_resp.has_key('id'))
    





class VariantsTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
    
    def test_get_single(self):
        variant_pk = 1
        variant = Variant.objects.get(pk = variant_pk)
        workspace = Workspace.objects.get(pk = 1)
        params = self.get_final_parameters({'workspace_id': workspace.pk})
    
        response = self.client.get('/api/variant/%s/get/'%variant.pk, params)                
        
        resp_dict = json.loads(response.content)     
        
        self.assertTrue(resp_dict['id'] == variant_pk)
        self.assertTrue(resp_dict['name'] == variant.name)
        self.assertTrue(resp_dict['caption'] == variant.caption)
        self.assertTrue(resp_dict['media_type'] == variant.media_type.name)
        self.assertTrue(resp_dict['auto_generated'] == variant.auto_generated)
        
        
    def test_get_single_preset(self):
        
        variant = Variant.objects.get(name = 'preview',  media_type__name = 'video')
        workspace = Workspace.objects.get(pk = 1)
        prefs = VariantAssociation.objects.get(workspace = workspace,  variant = variant).preferences
        
        
        params = self.get_final_parameters({'workspace_id': workspace.pk})
    
        response = self.client.get('/api/variant/%s/get/'%variant.pk, params)                
        
        resp_dict = json.loads(response.content)                
        self.assertTrue(resp_dict['id'] == variant.pk)
        self.assertTrue(resp_dict['name'] == variant.name)
        self.assertTrue(resp_dict['caption'] == variant.caption)
        self.assertTrue(resp_dict['media_type'] == 'video')
        self.assertTrue(resp_dict['auto_generated'] == variant.auto_generated)
        self.assertTrue(resp_dict.has_key('preferences'))
        self.assertTrue(resp_dict['preferences'].has_key('preset'))
        self.assertTrue(resp_dict['preferences']['preset']['name'] == prefs.preset.name)
        self.assertTrue(len(resp_dict['preferences']['preset']['parameters'].keys()) == prefs.values.all().count())
        for value in  prefs.values.all():
            self.assertTrue(resp_dict['preferences']['preset']['parameters'][value.parameter.name] == value.value)
        
        self.assertTrue(resp_dict['sources'] == [{'id': source.source.pk,  'name': source.source.name} for source in SourceVariant.objects.filter(workspace = workspace,  destination = variant).order_by('rank')])

        
#    def test_get(self):
#        
#        workspace = Workspace.objects.get(pk = 1)        
#        
#        params = self.get_final_parameters({'workspace_id': workspace.pk})
#    
#        response = self.client.get('/api/variant/get/',  params)                
#        resp_dict = json.loads(response.content)                
#        print resp_dict
#      
#        self.assertTrue(len(resp_dict['variants']) == workspace.get_variants().exclude(auto_generated = False, default_url__isnull = False).count())
#        
        
    def test_edit(self):
    
        variant = Variant.objects.get(name = 'preview',  media_type__name = 'image')
        workspace = Workspace.objects.get(pk = 1)        
        
        params = {
            'codec': 'gif', 
            'max_dim': 400, 
#            'cropping':False,  
#            'watermarking': '',
            'workspace_id': workspace.pk,     
        }
        params = self.get_final_parameters(params)
        
        
        response = self.client.post('/api/variant/%s/edit/'%variant.pk,  params)                

        prefs = variant.variantassociation_set.get(workspace = workspace).preferences
        print '---------prefs.watermarking ',  prefs.watermarking
        self.assertTrue(prefs.codec == params['codec'])
        self.assertTrue(prefs.max_dim == 300)
        self.assertTrue(prefs.cropping == False)
        self.assertTrue(prefs.watermarking== False)


    def test_edit_wm(self):
    
        variant = Variant.objects.get(name = 'preview',  media_type__name = 'image')
        workspace = Workspace.objects.get(pk = 1)        
        
        params = {
            'codec': 'gif', 
            'max_dim': 400, 
#            'cropping':False,  
#            'watermarking': '',
            'workspace_id': workspace.pk, 
            'watermarking': True,
            'watermark_uri': 'a123b',
            'watermarking_position': 2    
        }
        params = self.get_final_parameters(params)
        
        
        response = self.client.post('/api/variant/%s/edit/'%variant.pk,  params)                

        prefs = variant.variantassociation_set.get(workspace = workspace).preferences
        print '---------prefs.watermarking ',  prefs.watermarking
        print '---------prefs.watermark_uri ',  prefs.watermark_uri
        print '---------prefs.watermarking_position ',  prefs.watermarking_position


        self.assertTrue(prefs.codec == params['codec'])
        self.assertTrue(prefs.max_dim == 300)
        self.assertTrue(prefs.cropping == False)
        self.assertTrue(prefs.watermarking== True)

        self.assertTrue(prefs.watermark_uri == params['watermark_uri'])
        self.assertTrue(int(prefs.watermarking_position) == int(params['watermarking_position']))



    def test_edit_preset(self):
    
        variant = Variant.objects.get(name = 'preview',  media_type__name = 'video')
        workspace = Workspace.objects.get(pk = 1)        
        
        params = {
            'audio_bitrate_kb':256, 
            'audio_rate':44100, 
            'preset': 'flv', 
            'sources': [11,  10], 
            'video_bitrate_b': 640000, 
            'video_framerate':	25/1,       
            'workspace_id': workspace.pk, 
            'max_size':300
        
        }
        params = self.get_final_parameters(params)
        
        
        response = self.client.post('/api/variant/%s/edit/'%variant.pk,  params)                
        print response.content
        prefs = variant.variantassociation_set.get(workspace = workspace).preferences
        
        for param_value in prefs.values.all():
            print 'params[param_value.parameter.name]',  params[param_value.parameter.name]
            print 'param_value.value',  param_value.value
            self.assertTrue(str(params[param_value.parameter.name]) == str(param_value.value))
        
      
#        self.assertTrue(len(resp_dict['variants']) == workspace.get_variants().count())
    
    def test_create_auto_generated_no_preset(self):
        
        workspace = Workspace.objects.get(pk = 1)        
        name = 'test'
        auto_generated = True
        media_type = 'image'
        caption = 'test'
        params = {
            'workspace_id': workspace.pk, 
            'name': name, 
            'auto_generated': auto_generated, 
            'media_type': media_type, 
            'caption': caption, 
            'codec': 'gif', 
            'max_dim': 400, 
            
        }
        params = self.get_final_parameters(params)
        
        response = self.client.post('/api/variant/new/',  params)                
        resp_dict = json.loads(response.content)
        print 'resp_dict',  resp_dict
        self.assertTrue(Variant.objects.filter(pk = resp_dict['id']).count() == 1)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).name == name)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).auto_generated == auto_generated)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).media_type.name == media_type)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).caption == caption)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).get_preferences(workspace).codec == params['codec'])
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).get_preferences(workspace).max_dim == params['max_dim'])
        
    def test_create_source(self):
        
        workspace = Workspace.objects.get(pk = 1)        
        name = 'test'
        auto_generated = False
        media_type = 'image'
        caption = 'test'
        params = {
            'workspace_id': workspace.pk, 
            'name': name, 
#            'auto_generated': auto_generated, 
            'media_type': media_type, 
            'caption': caption, 
            
        }
        params = self.get_final_parameters(params)
        
        response = self.client.post('/api/variant/new/',  params)                
        resp_dict = json.loads(response.content)
        print 'resp_dict',  resp_dict
        self.assertTrue(Variant.objects.filter(pk = resp_dict['id']).count() == 1)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).name == name)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).auto_generated == auto_generated)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).media_type.name == media_type)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).caption == caption)
        
        
    def test_create_auto_generated_preset(self):
        
        workspace = Workspace.objects.get(pk = 1)        
        name = 'test'
        auto_generated = True
        media_type = 'video'
        caption = 'test'
        preset_name = 'flv'
        params = {
            'workspace_id': workspace.pk, 
            'name': name, 
            'auto_generated': auto_generated, 
            'media_type': media_type, 
            'caption': caption, 
           'preset': preset_name, 
           
           'audio_bitrate_kb':256, 
            'audio_rate':44100, 
            'sources': [11,  10], 
            'video_bitrate_b': 640000, 
            'video_framerate':	25/1,       
            'max_size':300
           
            
        }
        params = self.get_final_parameters(params)
        
        response = self.client.post('/api/variant/new/',  params)                
        resp_dict = json.loads(response.content)
        print 'resp_dict',  resp_dict
        variant = Variant.objects.get(pk = resp_dict['id'])
        self.assertTrue(Variant.objects.filter(pk = resp_dict['id']).count() == 1)
        self.assertTrue(variant.name == name)
        self.assertTrue(variant.auto_generated == auto_generated)
#        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).media_type.name == media_type)
        self.assertTrue(variant.caption == caption)
        
        
        
        prefs = variant.variantassociation_set.get(workspace = workspace).preferences
        
        for param_value in prefs.values.all():
            print 'params[param_value.parameter.name]',  params[param_value.parameter.name]
            print 'param_value.value',  param_value.value
            self.assertTrue(str(params[param_value.parameter.name]) == str(param_value.value))
        

    
    def test_delete(self):
        workspace = Workspace.objects.get(pk = 1)        
        name = 'test'
        auto_generated = True
        media_type = Type.objects.get(name = 'image')
        caption = 'test'
        
        variant = Variant.objects.create(name = name, caption = caption,  auto_generated = auto_generated,  media_type = media_type)
        va = VariantAssociation.objects.create(variant = variant,  workspace = workspace)       
    
        params = self.get_final_parameters({})        
        response = self.client.post('/api/variant/%s/delete/'%variant.pk,  params) 
        
        self.assertTrue(response.content == '')
        self.assertTrue(Variant.objects.filter(pk = variant.pk).count() == 0)
        


    def test_upload_wm(self):
        
        params = self.get_final_parameters({'file_name':'test.jpg',  'fsize': 128})        
        response = self.client.post('/api/variant/get_watermarking_uri/',  params) 
        print 'response.content',  response.content
        resp = json.loads(response.content)
        
        self.assertTrue(resp.has_key('job_id'))
        self.assertTrue(resp.has_key('unique_key'))
        self.assertTrue(resp.has_key('ip'))
        self.assertTrue(resp.has_key('port'))
        self.assertTrue(resp.has_key('chunk_size'))
        self.assertTrue(resp.has_key('chunks'))
        self.assertTrue(resp.has_key('res_id'))

    def test_delete_exception(self):
        workspace = Workspace.objects.get(pk = 1)        
        name = 'test'
        auto_generated = True
        media_type = Type.objects.get(name = 'image')
        caption = 'test'
        
#        variant = Variant.objects.create(name = name, caption = caption,  auto_generated = auto_generated,  media_type = media_type)
#        va = VariantAssociation.objects.create(variant = variant,  workspace = workspace)       
#    
        variant_id = 1
        params = self.get_final_parameters({})        
        response = self.client.post('/api/variant/%s/delete/'%variant_id,  params) 
        resp_dict = json.loads(response.content)
        
        self.assertTrue(resp_dict['error code'] == GlobalVariantDeletion.error_code)
        self.assertTrue(Variant.objects.filter(pk = variant_id).count() == 1)
        

class SmartFolderTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
    
    def test_get_single(self):
        ws_pk = 1
        ws = Workspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        sm = SmartFolder.objects.get(label = 'test',  workspace = ws)
        response = self.client.get('/api/smartfolder/%s/get/'%sm.pk, params)        
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.get('id') == sm.pk)        
        self.assertTrue(resp_dict['workspace_id'] == sm.workspace.pk)
        self.assertTrue(resp_dict['label'] == sm.label)
        self.assertTrue(resp_dict['and_condition'] == sm.and_condition)
        queries = []
        for node in sm.nodes.all():
            queries.append({
                'id': node.pk, 
                'type': node.type, 
                'negated': SmartFolderNodeAssociation.objects.get(node = node, smart_folder = sm).negated
            })
        self.assertTrue(resp_dict['queries'] == queries)
        
        
#    def test_get(self):
#        ws_pk = 1
#        ws = Workspace.objects.get(pk = ws_pk)
#        params = self.get_final_parameters({'workspace_id': ws.pk})        
#        sm = SmartFolder.objects.get(label = 'test',  workspace = ws)
#        response = self.client.get('/api/smartfolder/get/', params)        
#        resp_dict = json.loads(response.content)        
#        print resp_dict 
#        self.assertTrue(len(resp_dict) == ws.smartfolder_set.all().count())       
#       
#       
#        sm_id = '1'
#        sm = SmartFolder.objects.get(pk = sm_id)
#        
#        self.assertTrue(resp_dict['smart_folders'][0]['workspace_id'] == sm.workspace.pk)
#        self.assertTrue(resp_dict['smart_folders'][0]['label'] == sm.label)
#        self.assertTrue(resp_dict['smart_folders'][0]['and_condition'] == sm.and_condition)
#        queries = []
#        for node in sm.nodes.all():
#            queries.append({
#                'id': node.pk, 
#                'type': node.type, 
#                'negated': SmartFolderNodeAssociation.objects.get(node = node, smart_folder = sm).negated
#            })
#            
#        self.assertTrue(resp_dict['smart_folders'][0]['queries'] == queries)
        
    
    def test_create(self):
        workspace_id = 1
        
        node = Node.objects.get(label = 'test')
        query = {'negated': False,  'id': node.pk, }
        params = {'workspace_id':workspace_id, 'label':'test_sm',  'queries': json.dumps([query]) }
    
        params = self.get_final_parameters(params)                
        
        response = self.client.post('/api/smartfolder/new/', params,)                
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict.has_key('id'))
        sm = SmartFolder.objects.filter(pk = resp_dict['id'])
        self.assertTrue(sm.count() == 1)
        self.assertTrue(sm[0].nodes.all().count() == 1)
        self.assertTrue(SmartFolderNodeAssociation.objects.get(node = node,  smart_folder = sm).negated ==  query['negated'])
        
        
        
    def test_delete(self):
        
        params = self.get_final_parameters()        
        sm = SmartFolder.objects.get(pk = 1)
        response = self.client.get('/api/smartfolder/%s/delete/'%sm.pk, params)        
       
        self.assertTrue(SmartFolder.objects.filter(pk = 1).count() == 0)
        self.assertTrue(response.content == '')       

    
    def test_edit(self):
        workspace_id = 1
        
        node = Node.objects.get(label = 'test_remove_1')
        sm_id = 1
        query = {'negated': False,  'id': node.pk, }
        params = {'workspace_id':workspace_id, 'label':'test_sm',  'queries': json.dumps([query]) }
    
        params = self.get_final_parameters(params)                
        
        response = self.client.post('/api/smartfolder/%s/edit/'%sm_id, params,)                
        self.assertTrue(response.content == '')       
        sm = SmartFolder.objects.get(pk = sm_id)
        self.assertTrue(sm.nodes.all().count() == 2)
        self.assertTrue(SmartFolderNodeAssociation.objects.get(node = node,  smart_folder = sm).negated ==  query['negated'])
        
    
