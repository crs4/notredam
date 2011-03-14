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
from dam.api.models import *
from django.contrib.auth.models import User
import urllib
from django.test import TestCase
from django.utils import simplejson as json
from django.db.models import Q

from dam.api.exceptions import *
from dam.treeview.models import Node,  NodeMetadataAssociation,  SmartFolder,  SmartFolderNodeAssociation

from dam.variants.models import Variant
#from variants.models import VariantAssociation,   SourceVariant,  PresetParameterValue
from dam.core.dam_workspace.models import WorkspacePermission, WorkspacePermissionAssociation

from dam.workspace.models import DAMWorkspace
from dam.repository.models import Item,  Component
from dam.metadata.models import MetadataProperty,  MetadataValue
from dam.core.dam_repository.models import Type
from dam.workflow.models import State, StateItemAssociation
from dam.workflow.views import _set_state
from dam.mprocessor.models import Pipeline
import hashlib


def _get_final_parameters(api_key, secret, user_id, kwargs = None):
    if  not kwargs:
        kwargs = {}
    kwargs['api_key'] = api_key
    kwargs['user_id'] = user_id
    to_hash = secret
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
        return _get_final_parameters(self.api_key, self.secret, self.user_id, kwargs)
        
        
class WSTestCase(MyTestCase):
#    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json', 'workspace/fixtures/test_data.json' ,  'variants/fixtures/test_data.json', ]   
    fixtures = ['api/fixtures/test_data.json', 
                'treeview/fixtures/test_data.json', 
                 'repository/fixtures/test_data.json', 
#                 'variants/fixtures/test_data.json', 
                 'workspace/fixtures/test_data.json' , 
                  'metadata/fixtures/test_data.json' ]    
    
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
        self.assertTrue(resp_dict == {'members': [{'username': 'admin', 'permissions': ['admin']}]})
        
        
    def test_add_members(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkspacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)


    def test_set_permissions(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkspacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)
        
        params = {'users': u.username, 'permissions':'add item'}
        params = self.get_final_parameters(params)
        response = self.client.post('/api/workspace/%s/set_permissions/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkspacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = params['permissions']).count() == 1)


        
    def test_remove_members(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkspacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)
        
        params = self.get_final_parameters({'users': u.username})
        response = self.client.post('/api/workspace/%s/remove_members/'%ws_pk,  params)                
        
        self.assertTrue(response.content == '')
        self.assertTrue(u not in ws.members.all())
        self.assertTrue(WorkspacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 0)
        
        
        
    def test_get_collections(self):
        ws_pk = 1
        params = {}        
        params = self.get_final_parameters(params)
        response = self.client.get('/api/workspace/%s/get_collections/'%ws_pk,  params)                
        resp_dict = json.loads(response.content)        
        print 'resp_dict ',  resp_dict        
        
        exp_resp =  {'collections': [{'items': [], 'label': 'test1', 'parent_id': None, 'workspace': 1, 'id': 17, 'children': [{'items': [], 'label': 'test1_child', 'parent_id': 17, 'workspace': 1, 'id': 21, 'children': []}]}, {'items': [1], 'label': 'test_with_item', 'parent_id': None, 'workspace': 1, 'id': 18, 'children': []}, {'items': [], 'label': 'test2', 'parent_id': None, 'workspace': 1, 'id': 20, 'children': []}]}


        self.assertTrue(resp_dict ==  exp_resp)   
        
    def test_get_items(self):
        ws_pk = 1
        params = {'workspace_id':ws_pk}        
        params = self.get_final_parameters(params)
        response = self.client.get('/api/workspace/%s/get_items/'%ws_pk,  params)        
        
        resp_dict = json.loads(response.content)        
#        print 'resp_dict ',  resp_dict        
        
        self.assertTrue(resp_dict ==  [i.pk for i in Item.objects.filter(workspaces__pk = ws_pk)] )   
       
      
    def test_search(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
        print 'MetadataValue.objects.all() %s'%MetadataValue.objects.all()
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
#        self.assertTrue(resp_dict['totalCount'] == 2)
        self.assertTrue(resp_dict['items'][0].has_key('dc_description'))
        
        
    
    def test_search_keywords(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
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
        workspace = DAMWorkspace.objects.get(pk = 1)
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
        workspace = DAMWorkspace.objects.get(pk = 1)
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
        workspace = DAMWorkspace.objects.get(pk = 1)
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
        workspace = DAMWorkspace.objects.get(pk = 1)
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
        params = {}        
        params = self.get_final_parameters(params)
        
        response = self.client.get('/api/workspace/%s/get_keywords/'%ws_pk, params,  )        
        resp_dict = json.loads(response.content)        
#        ws = DAMWorkspace.objects.get(pk = ws_pk)
#        nodes = Node.objects.filter(workspace = ws,  type = 'keyword')        
#        self.assertTrue(resp_dict.has_key('keywords'))
#        self.assertTrue(isinstance(resp_dict['keywords'],  list))
#        self.assertTrue(len(resp_dict['keywords']) ==  nodes.count() )   

        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
    
        
    
    def test_edit(self):             
        ws_pk = 1        
        params = self.get_final_parameters({'name':'test_', 'description': 'test description' })
        
        response = self.client.post('/api/workspace/%s/edit/'%ws_pk, params,)        
        self.assertTrue(response.content == '')
        
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == params['name'])
        self.assertTrue(ws.description == params['description'])
        
    def test_get_states(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        params = self.get_final_parameters({})
        
        response = self.client.get('/api/workspace/%s/get_states/'%ws_pk, params)      
        
        resp_dict = json.loads(response.content)
        
        self.assertTrue(len(resp_dict) == 1)
        self.assertTrue(resp_dict['states'][0]['name'] == s.name)
        
    
        

        
    def test_get(self):
             
        ws_pk = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )      
        
        resp_dict = json.loads(response.content)    

        ws = DAMWorkspace.objects.get(pk = ws_pk)        
        self.assertTrue(resp_dict['id'] == str(ws.pk))
        self.assertTrue(resp_dict['name'] == ws.name)
        self.assertTrue(resp_dict['description'] == ws.description)        
        
    def test_get_except(self):             
        ws_pk = 1000
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params)      
        
        resp_dict = json.loads(response.content)    
        print 'resp_dict ',  resp_dict 
                
        self.assertTrue(resp_dict['error class'] == 'WorkspaceDoesNotExist')
        

        
    def test_delete(self):
             
        name = 'test_2'        
        params = self.get_final_parameters({'name':name, })
        response = self.client.post('/api/workspace/new/', params)        
        resp_dict = json.loads(response.content)           
        ws_pk = resp_dict['id']
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/delete/'%ws_pk, params)        
        self.assertTrue(response.content == '')
        self.assertRaises(DAMWorkspace.DoesNotExist,  DAMWorkspace.objects.get,  pk = ws_pk)

    def test_create(self):
             
        name = 'test_1'
        
        params = self.get_final_parameters({'name':name,  })
        response = self.client.post('/api/workspace/new/', params, )        
        resp_dict = json.loads(response.content)        
        ws_pk = resp_dict['id']
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == name)
        self.assertTrue(resp_dict.has_key('description'))
        self.assertTrue(resp_dict.get('name') == name)
        
        
    def test_set_creator(self):
        u = User.objects.create(username = 'test')
        ws_id = 1

        
        params = self.get_final_parameters({'creator_id':u.pk})
        response = self.client.post('/api/workspace/%s/set_creator/'%ws_id, params, )        

        ws = DAMWorkspace.objects.get(pk = ws_id)
        self.assertTrue(response.content == '')

        self.assertTrue(ws.creator == u)

    def test_get_smartfolders(self):
        ws_id = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_smartfolders/'%ws_id, params, )        

        ws = DAMWorkspace.objects.get(pk = ws_id)
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.has_key('smartfolders'))
        self.assertTrue(len(resp_dict['smartfolders']) == 1)
        
        
    def test_get_renditions(self):
        ws_id = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_renditions/'%ws_id, params, )        

        ws = DAMWorkspace.objects.get(pk = ws_id)
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.has_key('renditions'))
        
        
        
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
        params = {'workspace_id':workspace_id, 'media_type': 'image/jpeg' }
    
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
    
        
        
    #def test_create_media_type_exception(self):
        #workspace_id = 1
        #media_type = 'movieeee'
        #params = self.get_final_parameters({'workspace_id':workspace_id,  'media_type': media_type})
        #
        #response = self.client.post('/api/item/new/', params,)                
        #resp_dict = json.loads(response.content)        
        #self.assertTrue(resp_dict['error code'] == InvalidMediaType.error_code) 
        
    
    def test_get_keywords(self):
        item = Item.objects.all()[0]    
        keywords = list(item.keywords())            
        
        params = self.get_final_parameters({'workspace_id': 1})
        response = self.client.get('/api/item/%s/get_keywords/'%item.pk, params)                        
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict['keywords'] == keywords)
         
        
    def test_get_collections(self):
        item = Item.objects.all()[0]    
        collections = list(item.collections())            
        
        params = self.get_final_parameters({'workspace_id': 1})
        response = self.client.get('/api/item/%s/get_collections/'%item.pk, params)                        
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict['collections'] == collections)
    
        
    def test_get(self):
        item = Item.objects.all()[0]    
        keywords = list(item.keywords())            
        ws_pk = 1
        params = self.get_final_parameters({'renditions_workspace': ws_pk, 'renditions': 'original'})
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
        self.assertTrue(resp_dict['collections'] == list(item.collections()))
    
        metadata = {'dc_subject': ['test']}
#        metadata = {u'dc_subject': [u'test_remove_1', u'test', u'prova', u'provaaaa'], u'dc_identifier': u'test id', u'dc_description': {u'en-US': u'test prova\n'}, u'Iptc4xmpExt_LocationShown': [{u'Iptc4xmpExt_CountryCode': u'123', u'Iptc4xmpExt_ProvinceState': u'test', u'Iptc4xmpExt_CountryName': u'test', u'Iptc4xmpExt_City': u'test'}, {u'Iptc4xmpExt_CountryCode': u'1233', u'Iptc4xmpExt_ProvinceState': u'prova', u'Iptc4xmpExt_CountryName': u'prova', u'Iptc4xmpExt_City': u'prova'}]}                                                                                                                                                                                                    
        print("resp_dict['metadata'] %s"%resp_dict['metadata'])
        self.assertTrue(resp_dict['metadata'] == metadata)
        
        
    def test_get_except(self):
        item_pk = 1000    
                    
        ws_pk = 1
        params = self.get_final_parameters({'renditions_workspace': ws_pk, 'renditions': 'original'})
        response = self.client.get('/api/item/%s/get/'%item_pk, params) 
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict['error class'] == 'ItemDoesNotExist')
        
    def test_move(self):
        workspace_id = 1
       
        item_id = Item.objects.all()[0].pk
        user = User.objects.get(pk = 1)
        ws_new = DAMWorkspace.objects.create_workspace('test', '', user)
        
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

        params = self.get_final_parameters({'metadata':json.dumps(metadata_dict)})
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
        params = self.get_final_parameters({'workspace_id':workspace_id,  'media_type': 'image/jpeg'})        
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
        params = self.get_final_parameters({ 'workspace_id':workspace_id,  'media_type': 'image/jpeg'})        
        response = self.client.post('/api/item/new/', params,  )                
        
        resp_dict = json.loads(response.content) 
        print('resp_dict %s'%resp_dict)       
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
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        new_node = Node.objects.get(label = 'test',  type = 'keyword', workspace = ws)
        item = Item.objects.all()[0]
        
        item_id = item.pk
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 0)
        params = self.get_final_parameters({ 'keywords':new_node.pk})        
        response = self.client.post('/api/item/%s/add_keywords/'%item_id, params, )            
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 1)
        
        
    def test_remove_keywords(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
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
        ws = DAMWorkspace.objects.get(pk = workspace_id)
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
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        collection_node = Node.objects.get(label = 'test1',  type = 'collection')        
        item = Item.objects.all()[0]
        params = self.get_final_parameters({ 'collection_id': collection_node.pk})        
        
        response = self.client.post('/api/item/%s/remove_from_collection/'%item.pk, params, )            
        self.assertTrue(response.content == '')         
        items = collection_node.items.all()        
        self.assertTrue(items.count() == 0)
        
        
    def test_add_to_ws(self):
        
        workspace = DAMWorkspace.objects.create(name = 'test', creator = self.user)
        workspace_id = workspace.pk
        
        
        item = Item.objects.all()[0]
        params = self.get_final_parameters({ 'workspace_id': workspace_id})        
        response = self.client.post('/api/item/%s/add_to_workspace/'%item.pk, params, )            
        self.assertTrue(response.content == '')        
        self.assertTrue(item in workspace.items.all()) 
        

        
        
    #def test_upload(self):
        #from django.test import client 
        #from mprocessor.models import Task
        #workspace = DAMWorkspace.objects.all()[0]
        #image = Type.objects.get(name = 'image')
        #item = Item.objects.create(type = image)
        #item.workspaces.add(workspace)
        #
        #file = open('files/images/logo_blue.jpg')
        #params = self.get_final_parameters({ 'workspace_id': 1,  'rendition_id':1})                
        #params['Filedata'] = file
        #
        #response = self.client.post('/api/item/%s/upload/'%item.pk, params, )            
        #file.close()
        #
        #print response.content 
        #self.assertTrue(response.content == '')
        #self.assertTrue(item.component_set.filter(variant__id = 1).count() == 1)
        #self.assertTrue(Task.objects.filter(component__in = item.component_set.all()).count()) #(adapt + extract feat)*3 + extract feat orig
                 
        
    def test_get_state(self):
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        state = State.objects.create(name = 'test',  workspace = workspace)
        state_association = StateItemAssociation.objects.create(state = state, item = item, )
        params = self.get_final_parameters({ 'workspace_id': workspace.pk,  }) 
        response = self.client.post('/api/item/%s/get_state/'%item.pk, params, )            
        resp_dict = json.loads(response.content)
        print '-------------------------',  resp_dict
        self.assertTrue(resp_dict == {'name': 'test', 'id': state.pk})
        
    def test_get_keywords(self):
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        
        params = self.get_final_parameters({ 'workspace_id': workspace.pk,  }) 
        response = self.client.get('/api/item/%s/get_keywords/'%item.pk, params, )            
        resp_dict = json.loads(response.content)
        print '-------------------------',  resp_dict
        
    
        
    
    def test_set_state(self): 
        workspace = DAMWorkspace.objects.get(pk = 1)
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
        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
        
        
    def test_get_except(self):        
             
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        node_pk = 1000
        response = self.client.get('/api/keyword/%s/get/'%node_pk, params)        
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'CatalogueElementDoesNotExist')
        
    def test_get_single_category(self):        
             
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
            
        ws = DAMWorkspace.objects.get(pk = 1)
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
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'People',  workspace = ws)        
        params = self.get_final_parameters({'label':'test'})        
        self.assertTrue(node.associate_ancestors == False)
        
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        
        node = Node.objects.get(pk = node.pk)
        self.assertTrue(node.label == 'test')
        self.assertTrue(node.associate_ancestors == False)
    
    def test_edit_1(self):

        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'test',  workspace = ws)        
        params = self.get_final_parameters({'associate_ancestors':'true'})        
        self.assertTrue(node.associate_ancestors == False)
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        node = Node.objects.get(pk = node.pk)
        self.assertTrue(node.associate_ancestors == True)
        
    
    def test_edit_metadata(self):

        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
        ws = DAMWorkspace.objects.get(pk = ws_pk)        
        node_id = Node.objects.get(label = 'test').pk
        
        new_parent_node_pk = parent_node = Node.objects.get(workspace = ws, label = 'Places',  depth = 1).pk
        params = self.get_final_parameters({ 'parent_id':new_parent_node_pk,  })        
        self.client.post('/api/keyword/%s/move/'%node_id, params,  )      
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/get/'%node_id, params)        
        resp_dict = json.loads(response.content)
        print resp_dict
        parent_id = resp_dict['parent_id']        
        self.assertTrue(parent_id == new_parent_node_pk)        
        
        
    def test_move_on_top(self):
        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)        
        node_id = Node.objects.get(label = 'test').pk
        
        
        params = self.get_final_parameters({ })        
        self.client.post('/api/keyword/%s/move/'%node_id, params,  )      
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/get/'%node_id, params)        
        resp_dict = json.loads(response.content)
        print resp_dict
        parent_id = resp_dict['parent_id']        
        self.assertTrue(parent_id == None)        
        
    def test_delete(self):
        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        node_id = Node.objects.get(label = 'test').pk
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/delete/'%node_id, params,  ) 
        
        self.assertTrue(response.content == '')
        self.assertRaises(Node.DoesNotExist,  Node.objects.get, pk = node_id )
        
    def test_add_items(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.all()[0]
        item_id = item.pk
        new_node = Node.objects.get(label = 'test')
        
        params = self.get_final_parameters({ 'items':item.pk})        
        response = self.client.post('/api/keyword/%s/add_items/'%new_node.pk, params, )            
        self.assertTrue(item.node_set.filter(label = 'test').count() == 1)
      
    def test_remove_items(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
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
        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
        
    def test_get_except(self):                
        params = self.get_final_parameters()
        node_pk = 1000
        response = self.client.get('/api/collection/%s/get/'%node_pk, params)
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'CatalogueElementDoesNotExist')         
            
#    def test_get(self):
#             
#        ws_pk = 1
#        params = self.get_final_parameters({'workspace_id':ws_pk})
#        response = self.client.get('/api/collection/get/', params,  )        
#        resp_dict = json.loads(response.content)    
#
#        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
        
        ws = DAMWorkspace.objects.get(pk = 1)
        label = 'collection_test'
        params = self.get_final_parameters({ 'workspace_id':ws.pk,  'label':label})     
        response = self.client.post('/api/collection/new/', params,  )  
        resp_dict = json.loads(response.content)        
        
        self.assertTrue(resp_dict.has_key('id'))
        
        self.assertTrue(resp_dict['workspace_id'] == ws.pk)
        self.assertTrue(resp_dict['parent_id'] == None)
        self.assertTrue(resp_dict['label'] == label)        


    def test_create_except(self):             
        
        ws = DAMWorkspace.objects.get(pk = 1)
        label = 'collection_test'
        params = self.get_final_parameters({ 'workspace_id':ws.pk,  'label':label})     
        response = self.client.post('/api/collection/new/', params,  )  
        resp_dict = json.loads(response.content)        
        
        self.assertTrue(resp_dict.has_key('id'))
        
        self.assertTrue(resp_dict['workspace_id'] == ws.pk)
        self.assertTrue(resp_dict['parent_id'] == None)
        self.assertTrue(resp_dict['label'] == label)        
        
        params = self.get_final_parameters({ 'workspace_id':ws.pk,  'label':label})     
        response = self.client.post('/api/collection/new/', params)  
        print response
        





    def test_rename(self):
        "changing label"

        node_id = Node.objects.get(label = 'test1',  depth = 1).pk
        new_label = 'new_label'
        params = self.get_final_parameters({'label':new_label})        
        response = self.client.post('/api/collection/%s/edit/'%node_id , params,  )                
        node = Node.objects.get(pk = node_id )
        self.assertTrue(node.label == new_label)
        
    def test_move(self):
        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        
        node_id = Node.objects.get(label = 'test1', depth = 1).pk
        dest_id= Node.objects.get(label = 'test2', depth = 1).pk
        params = self.get_final_parameters({ 'parent_id':dest_id,  })
        resp = self.client.post('/api/collection/%s/move/'%node_id, params)      
        
        self.assertTrue(resp.content == '')
        self.assertTrue(resp.status_code == 200)
        node = Node.objects.get(pk = node_id)
        self.assertTrue(node.parent.pk == dest_id)
        
    def test_move_to_the_top(self):
        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        
        node_id = Node.objects.get(label = 'test1_child', ).pk
        root_pk = Node.objects.get(workspace = ws, type ="collection",depth = 0).id
        params = self.get_final_parameters({ })
        resp = self.client.post('/api/collection/%s/move/'%node_id, params)      
        
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
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        coll= Node.objects.get(label = 'test1',  workspace = ws,  type = 'collection')
        item = Item.objects.all()[0]        
        
        params = self.get_final_parameters({ 'items':[item.pk,  item.pk]})        
        response = self.client.post('/api/collection/%s/add_items/'%coll.pk, params) 
        self.assertTrue(response.content == '')
        
        items = coll.items.all()
        
        self.assertTrue(items.count() == 1)
        
    def test_remove_items(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
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
        
        password = 'notredam'
        params = {'user_name':user.username,  'api_key':self.api_key,  'password': password}
        response = self.client.post('/api/login/', params)        
        json_resp = json.loads(response.content)
        self.assertTrue(json_resp['user_id'] == user.pk)
        self.assertTrue(json_resp['secret'] == self.secret)
        self.assertTrue(json_resp['workspaces'] == [1])
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
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({'workspace_id': workspace.pk})
    
        response = self.client.get('/api/rendition/%s/get/'%variant.pk, params)                
        
        resp_dict = json.loads(response.content)     
        
        self.assertTrue(resp_dict['id'] == variant_pk)
        self.assertTrue(resp_dict['name'] == variant.name)
        self.assertTrue(resp_dict['caption'] == variant.caption)
        self.assertTrue(resp_dict['media_type'] == [media_type.name for media_type in variant.media_type.all()])
        self.assertTrue(resp_dict['auto_generated'] == variant.auto_generated)
        
        
    def test_get_except(self):
        variant_pk = 1000
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({'workspace_id': workspace.pk})    
        response = self.client.get('/api/rendition/%s/get/'%variant_pk, params)
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'RenditionDoesNotExist')
          
    def test_edit(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
        variant = Variant.objects.create(name = 'test', caption= 'test', auto_generated = True, workspace = workspace)
        variant.media_type.add(*Type.objects.all())
        
                
        
        params = {'name': 'test_rename','caption':'test_rename', 'media_type': ['image']}
        params = self.get_final_parameters(params)
        
        
        response = self.client.post('/api/rendition/%s/edit/'%variant.pk,  params)                
        
        variant = Variant.objects.get(pk = variant.pk)
        print ' variant.caption ', variant.caption 
        self.assertTrue(variant.name == params['name'])
        self.assertTrue(variant.caption == params['caption'])
        
        
        print 'variant.media_type.all() %s'%variant.media_type.all()
        self.assertTrue(len(variant.media_type.all()) == len(params['media_type']))
        self.assertTrue(variant.media_type.all()[0].name == params['media_type'][0])
        
        
        
    def test_create(self):
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = {'name': 'test', 'media_type': ['image'], 'workspace_id': 1, 'caption':'test'}
        params = self.get_final_parameters(params)
        
        
        response = self.client.post('/api/rendition/new/',  params)                
        resp_dict = json.loads(response.content)     
                
        self.assertTrue(Variant.objects.filter(pk = resp_dict['id']).count() == 1)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).workspace.pk == params['workspace_id'])
        
        
    def test_delete(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({})
        variant = Variant.objects.create(name = 'test', auto_generated = True, workspace = workspace)
        response = self.client.get('/api/rendition/%s/delete/'%variant.pk, params)
        self.assertTrue(response.content == '')
        self.assertTrue(Variant.objects.filter(pk = variant.pk).count() == 0)
    

class SmartFolderTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
    
    def test_get_single(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
        
    def test_get_except(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        sm_pk = 1000
        response = self.client.get('/api/smartfolder/%s/get/'%sm_pk, params)        
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'SmartFolderDoesNotExist')
        
    
    
#    def test_get(self):
#        ws_pk = 1
#        ws = DAMWorkspace.objects.get(pk = ws_pk)
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
        
        response = self.client.get('/api/smartfolder/%s/get/'%sm_id, params,)
        print 'response.content', response.content
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict == {"and_condition": True, "workspace_id": 1, "queries": [{"negated": False, "type": "keyword", "id": 19}, {"negated": False, "type": "keyword", "id": 22}], "id": 1, "label": "test_sm"})    
    
    
    
    def test_get_items(self):
       
        sm_id = 1
        params = self.get_final_parameters({})                
        
        response = self.client.post('/api/smartfolder/%s/get_items/'%sm_id, params,)                
        
        print 'response.content', response.content
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['items'] == [2])
        

class ScriptsTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json',  'repository/fixtures/test_data.json', 'core/dam_repository/fixtures/test_data.json',  
#                'scripts/fixtures/test_data.json'
                ]   
   
    def test_create(self):
        ws = DAMWorkspace.objects.get(pk = 1)
        name = 'test'
        description = 'test'
        pipeline =  {
        'image':{
            'source_variant': 'original',
            'actions': [
                {
                 'type': 'resize',
                'parameters':{
                   'max_height': 300,
                   'max_width': 300,
                }
                        
                },
                {
                     'type': 'setrights',
                     'parameters':{
                        'rights': 'creative commons by'
                     }
                 },
                {
                'type': 'save',
                'parameters':{
                    'output_format': 'jpeg',
                    'output': 'preview'
                    
#                    'output': 'preview'
                }
                        
            }    
        ]
                 
        }}
        params = self.get_final_parameters({ 'workspace_id':ws.pk,  'name':name,  'description': description,  'params': json.dumps(pipeline)})     
                
        response = self.client.post('/api/script/new/', params,  )  
        
        resp_dict = json.loads(response.content)     
        print resp_dict   
        self.assertTrue(resp_dict.has_key('id'))
        self.assertTrue(resp_dict['name'] == name)
        self.assertTrue(resp_dict['description'] == description)
        
        
    def test_edit(self):
        ws = DAMWorkspace.objects.get(pk = 1)
        name = 'test_edit'
        description = 'test_edit'
        pipeline =  {
             
                 
        }
        script = Pipeline.objects.get(name = 'pipe_image')
        params = self.get_final_parameters({ 'name':name,  'description': description,  'params': json.dumps(pipeline)})     
                
        response = self.client.post('/api/script/%s/edit/'%script.pk, params,  )  
        script = Pipeline.objects.get(pk = script.pk)
        self.assertTrue(response.content == '')
        print script.name
        self.assertTrue(script.name == params['name'])
               
       
    def test_run(self):
        script = Pipeline.objects.get(name = 'pipe_image')
        params = self.get_final_parameters({ 'items': [i.pk for i in Item.objects.all()]})     
        response = self.client.post('/api/script/%s/run/'%script.pk, params)  
        self.assertTrue(response.content == '')
        
        
#    def test_run_again(self):
#        script = Pipeline.objects.get(name = 'pipe_image')
#        params = self.get_final_parameters({})    
#        
#        response = self.client.post('/api/script/%s/run_again/'%script.pk, params,  )  
#        self.assertTrue(response.content == '')
#        

#TODO: generate new fixtures for testing delete script
#    def test_delete(self):
#        script = Pipeline.objects.get(name = 'thumb_generation')
#        params = self.get_final_parameters({ })     
#        response = self.client.post('/api/script/%s/delete/'%script.pk, params,  )  
#        self.assertTrue(response.content == '')
#        self.assertTrue(Pipeline.objects.filter(pk = script.pk).count() == 0)
       
    def test_get(self):
        script = Pipeline.objects.get(name = 'pipe_image')
        params = self.get_final_parameters({ })     
        response = self.client.post('/api/script/%s/get/'%script.pk, params,  )  
        resp_dict = json.loads(response.content)        
   
        self.assertTrue(resp_dict['id'] == script.pk)
        self.assertTrue(resp_dict['name'] == script.name)
        self.assertTrue(resp_dict['description'] == script.description)
        self.assertTrue(resp_dict['workspace_id'] == script.workspace.pk)
        
    def test_get_except(self):
        script_pk = 1000
        params = self.get_final_parameters({ })     
        response = self.client.post('/api/script/%s/get/'%script_pk, params)  
        resp_dict = json.loads(response.content)       
   
        self.assertTrue(resp_dict['error class'] == 'ScriptDoesNotExist')
        
    def test_get_scripts(self):

        ws = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({ })     
        response = self.client.post('/api/workspace/%s/get_scripts/'%ws.pk , params,  )  
        resp_dict = json.loads(response.content)        
   
        self.assertTrue(len(resp_dict['scripts']) == ws.pipeline_set.all().count())
        
        
        
        
        
class StatesTest(MyTestCase):
    fixtures = ['api/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
        
    def test_delete(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        params = self.get_final_parameters({})
        
        response = self.client.post('/api/state/%s/delete/'%s.pk, params)      
        
        
        self.assertTrue(response.content == '')
        self.assertTrue(State.objects.filter(workspace__pk = ws_pk).count() == 0)
        
        
    def test_create(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({'name': 'test', 'workspace_id': ws_pk})
        response = self.client.post('/api/state/new/', params)      
        resp_dict = json.loads(response.content)    
        self.assertTrue(resp_dict['name'] == 'test')
        self.assertTrue(State.objects.filter(workspace__pk = ws_pk).count() == 1)
        
        
    def test_edit(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        params = self.get_final_parameters({'name': 'test_edit'})
        response = self.client.post('/api/state/%s/edit/'%s.pk, params)      
            
        self.assertTrue(response.content == '')        
        self.assertTrue(State.objects.filter(workspace__pk = ws_pk, name = 'test_edit').count() == 1)
        
    def test_get(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        i = ws.items.all()[0]
        StateItemAssociation.objects.create(item = i, state = s)
        params = self.get_final_parameters({})
        response = self.client.get('/api/state/%s/get/'%s.pk, params)      
        
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['name'] == s.name)
                
        self.assertTrue(resp_dict['items'] == [i.pk])
        
    def test_add_items(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        i = ws.items.all()[0]
        
        params = self.get_final_parameters({'items': [i.pk]})
        response = self.client.post('/api/state/%s/add_items/'%s.pk, params)      
        
        self.assertTrue(response.content == '')
        self.assertTrue(StateItemAssociation.objects.get(state = s).item == i)
        
        
    def test_remove_items(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        items = ws.items.all()
        _set_state(items, s)
        self.assertTrue(StateItemAssociation.objects.filter(state = s).count() == items.count())
        params = self.get_final_parameters({'items': [i.pk for i in items]})
        response = self.client.post('/api/state/%s/remove_items/'%s.pk, params)      
        
        self.assertTrue(response.content == '')
        self.assertTrue(StateItemAssociation.objects.filter(state = s).count() == 0)
                
