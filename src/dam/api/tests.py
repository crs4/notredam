"""
NotreDAM API tests use the django standard library django.test and are collected in a file in the same api code directory: dam/api/tests.py.
All the tests in this module run without MediaDART. So here is not an uploading test. Uploading test are in another module test_upload.py, which requires both MediaDART and NotreDAM up and running.
While System tests are in a further module, system_tests.py, which also requires MediaDART and NotreDAM up and running.

It is possible to choose between different levels of verbosity for the tests execution: the stdout is the same of the dam code, so it is possible to change the verbosity level of the logging changing it in file dam/logger.py. Possible text logging level for the messages are: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. For further information about this topic, consult the logging python library documentation at:
http://docs.python.org/library/logging.html#module-level-functions

In the dam/settings.py file, sqlite3 should be chosen as application database because when the tests are running, a test db is created which is kept in the memory, so this way the tests will run faster (sqlite3 is a light db).
The django.test library uses a virtual server which is faster then the http server.

About the structure of the tests.py file:
there is an abstract class MyTestCase from which inherit all the other classes in the same module. This class define the setup and the structure of the test final parameters.
The tests related to a single application of NotreDAM are collected in a class; for example, the tests related to workspaces are collected in WSTestCase, and the unit tests related to workspaces are all the methods of this class.

It is possible to run all the tests with the following command:
python manage.py test api

It is also possible to run a single class test with the following command (where the class WSTestCase, related to the workspace, is used as example):
python manage.py test api.WSTestCase
Moreover, It is possible to specify a single method test (the example is related to the method  test_get_list of the class WSTestCase):
python manage.py test api.WSTestCase.test_get_list

Instructions about how to add new tests.
Please group in a single class all the tests related to the same part of NotreDAM and keep on using the following name convention:
The class name must end with the string Test.
The name of each method in the class must starts with the string test_ 

It is important to remember that if more than one api method call is necessary to complete the same test, all the api methods must be called inside the same test method.  The reason of this is that after each single method test all the information are deleted. It seems to be a good idea to group each test of this kind in the only method of a class.

NB. test_add_user uses an api method, /api/add_user/ which has been implemented for particular purposes: it is needed during demo updating. For this reason it requires the criptated user password instead of the clear version of it. Moreover, this operation does not add any default workspace for the new user (actually this should not be correct).

"""
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
from dam.api.utils import _get_final_parameters
from datetime import datetime

class MyTestCase(TestCase):
    """
    Abstract class from which all the other TestCase must inherit
    """
#    fixtures = ['test_data.json', ]   

    def setUp(self):
        secret = Secret.objects.get(pk = 1)  
        self.secret = secret.value
        self.api_key = secret.application.api_key
        self.user_id = secret.user.pk
        self.user = secret.user
#        print '--------- api_key ',  self.api_key
        
    def get_final_parameters(self, kwargs = None):
        "add api_key user_id and secret (required by check sum)"
        return _get_final_parameters(self.api_key, self.secret, self.user_id, kwargs)
        
        
class WSTestCase(MyTestCase):
    """
    Tests related to workspaces
    """

#    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json', 'workspace/fixtures/test_data.json' ,  'variants/fixtures/test_data.json', ]   
    fixtures = ['api/fixtures/test_data.json', 
                'treeview/fixtures/test_data.json', 
                 'repository/fixtures/test_data.json', 
#                 'variants/fixtures/test_data.json', 
                 'workspace/fixtures/test_data.json' , 
                  'metadata/fixtures/test_data.json' ]    
    
    def test_0000_get_list(self):
        """
        checks the list of workspaces returned by api method /api/workspace/get against the list of them in django db 
        """
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
        
    def test_0001_get_members(self):
        """
        checks the list of members of the first returned by api method /api/workspace/ws_name/get_members against the list of them in django db 
        """
        ws_pk = 1
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_members/'%ws_pk,  params)                
        resp_dict = json.loads(response.content)        
        print 'resp_dict ',  resp_dict        
        self.assertTrue(resp_dict == {'members': [{'username': 'admin', 'permissions': ['admin']}]})
        
        
    def test_0002_add_members(self):
        """
        1 - creates a new user test in db, tries to add test user as a new member using the api method /api/workspace/ws_name/add_members/ of the first ws
        2 - checks if the new user is in the member list of the workspace in the django db 
        """
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        u = User.objects.create(username = 'test')
        
        params = self.get_final_parameters({'users': u.username, 'permissions':'admin'})
        response = self.client.post('/api/workspace/%s/add_members/'%ws_pk,  params)                
                
        self.assertTrue(response.content == '')
        self.assertTrue(u in ws.members.all())
        self.assertTrue(WorkspacePermissionAssociation.objects.filter(users = u,  workspace__pk = ws_pk,  permission__name = 'admin').count() == 1)


    def test_0003_set_permissions(self):
        """
        1 - adds a new admin member to the first workspace using the api method /api/workspace/ws_name/add_members/
        2 - checks if the new admin user is in workspace member list (in the django db)
        """
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


        
    def test_0004_remove_members(self):
        """
        1 - adds a new admin member to the first workspace using the api method /api/workspace/ws_name/add_members/, 
        2 - removes him using the api method /api/workspace/ws_name/remove_memmbers/
        3 - checks if it was really removed from the django db
        """
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
        
    def test_0005_get_items(self):
        """
        Retrieve one of the images on ws 1, with some renditions info.
        """
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        print 'MetadataValue.objects.all() %s'%MetadataValue.objects.all()
        params = self.get_final_parameters({             
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'renditions': ['original', 'thumbnail']
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        self.assertTrue(len(resp_dict['items']) == params['limit'])
        self.assertTrue(int(resp_dict['totalCount']) == Item.objects.filter(workspaceitem__workspace = workspace, workspaceitem__deleted = False).distinct().count())
        self.assertTrue(resp_dict['items'][0].has_key('pk'))
        self.assertTrue(resp_dict['items'][0].has_key('media_type'))
        self.assertTrue(resp_dict['items'][0].has_key('last_update'))
        self.assertTrue(resp_dict['items'][0].has_key('creation_time'))
        self.assertTrue(datetime.strptime(resp_dict['items'][0]['last_update'], '%c') == Item.objects.get(pk = resp_dict['items'][0]['pk']).get_last_update(workspace))
        self.assertTrue(resp_dict['items'][0].has_key('renditions'))
        self.assertTrue(resp_dict['items'][0]['renditions'].has_key('original'))
        self.assertTrue(resp_dict['items'][0]['renditions'].has_key('thumbnail'))
        self.assertTrue(resp_dict['items'][0]['renditions']['original'].has_key('url'))
        self.assertTrue(resp_dict['items'][0]['renditions']['thumbnail'].has_key('url'))
    
    def test_0006_get_items_filtering_by_last_update(self):
        """
        Search items filtering by last update.        
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        item1 = Item.objects.get(pk = 2)        
        
        print 'item.last_update', item.get_last_update(workspace).strftime('%c')
        print 'item1.last_update', item1.get_last_update(workspace).strftime('%c')
        
        params = self.get_final_parameters({ 
            'last_update>=': item1.get_last_update(workspace).strftime('%d/%m/%Y %H:%M:%S')
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['totalCount'] == 2)           
    
    def test_0007_search_keywords(self):
        """
        Search an image with a given keyword  using the api method /api/workspace/ws_name/search/ and checks if the image is actually found in django db (it must be because it is in a fixture file loaded at testing start up)
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        node = Node.objects.get(label = 'test_remove_1')
        
        params = self.get_final_parameters({ 
            'keyword': node.pk, 
            'media_type': 'image'
          
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
      
        self.assertTrue(resp_dict['totalCount'] == node.items.count())
     
     
    def test_search_keywords_failure(self):
        """
        Search an image with a given keyword  using the api method /api/workspace/ws_name/search/ and checks if the image is actually found in django db (it must be because it is in a fixture file loaded at testing start up)
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
      
        
        params = self.get_final_parameters({ 
            'keyword': 1000, 
            'media_type': 'image'
          
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
      
        self.assertTrue(resp_dict['totalCount'] == 0)
    
    def test_search_in_metadata(self):
        """
        Search items by a string.
        """
        
        workspace = DAMWorkspace.objects.get(pk = 1)
      
        
        params = self.get_final_parameters({ 
            'query': 'test1', 
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)      
        self.assertTrue(resp_dict['totalCount'] == 1)
             
    def test_0008_search_smart_folders(self):
        """
        Search an image with a given smart folder  using the api method /api/workspace/ws_name/search/ and checks if the image is actually found in django db (it must be because it is in a fixture file loaded at testing start up)
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        smart_folder = SmartFolder.objects.get(pk = 1)
        
        params = self.get_final_parameters({ 
            'smart_folder': smart_folder.pk, 
            'media_type': 'image', 
            'start':0,
            'limit':1,
            'metadata': 'dc_description'
          
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        print resp_dict
#        self.assertTrue(len(resp_dict['items']) == params['limit'])
        self.assertTrue(resp_dict['totalCount'] == smart_folder.nodes.all()[0].items.count())
#        self.assertTrue(resp_dict['items'][0].has_key('dc_description'))
        
    def test_0010_keywords(self):
        """
        Search images with some given keywords using the api method /api/workspace/ws_name/get_keywords/. An image with the given keywords is found and it is checked that also the node children have the same keywords.
        """
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
   
    def test_0011_no_api_key(self):
        """
        Checks that an error 400 arises when an image with no api_key is looked for using api command /api/workspace/ws_name/get.
        """
        ws_pk = 1
        params = {'workspace_id':ws_pk,  'user_id': self.user_id}        
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )        
        resp_dict = json.loads(response.content)             
        
        self.assertTrue(resp_dict.get('error code') == 400)
        
    def test_0012_wrong_secret(self):
        """
        Checks that an error 403 arises when an image with wrong secret is looked for using api command /api/workspace/ws_name/get.
        """
        ws_pk = 1
        params = {'workspace_id':ws_pk,  'user_id': self.user_id,  'api_key': self.api_key,  'checksum': 'lalala'}        
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )        
        resp_dict = json.loads(response.content)             
        
        self.assertTrue(resp_dict.get('error code') == 403)
    
        
    
    def test_0013_edit(self):             
        """
        edit the first workspace (just name and description) using api command /api/workspace/ws_name/edit/ and checks a workspace like this actually is present in django db
        """
        ws_pk = 1        
        params = self.get_final_parameters({'name':'test_', 'description': 'test description' })
        
        response = self.client.post('/api/workspace/%s/edit/'%ws_pk, params,)        
        self.assertTrue(response.content == '')
        
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == params['name'])
        self.assertTrue(ws.description == params['description'])
        
    def test_0014_get_states(self):
        """
        Creates an object with a given state in the first ws using the api method /api/workspace/ws_name/get_states/ and checks a ws with that state actually is present in django db
        """
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        params = self.get_final_parameters({})
        
        response = self.client.get('/api/workspace/%s/get_states/'%ws_pk, params)      
        
        resp_dict = json.loads(response.content)
        
        self.assertTrue(len(resp_dict) == 1)
        self.assertTrue(resp_dict['states'][0]['name'] == s.name)
        
    
        

        
    def test_0015_get(self):
        """ 
        Call api method /api/workspace/ws_pk/get to get the first workspace with no parameters and checks that the return workspace actually is the first onewith same id, name and description.
        """ 
        ws_pk = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params,  )      
         
        resp_dict = json.loads(response.content)    

        ws = DAMWorkspace.objects.get(pk = ws_pk)        
        self.assertTrue(resp_dict['id'] == str(ws.pk))
        self.assertTrue(resp_dict['name'] == ws.name)
        self.assertTrue(resp_dict['description'] == ws.description)        
        
    def test_0016_get_except(self):            
        """ 
        Tries to get a non existent workspace using api method /api/workspace/ws_name/get/ and checks if a WorkspaceDoesNotExist Exception arises.
        """ 
        ws_pk = 1000
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get/'%ws_pk, params)      
        
        resp_dict = json.loads(response.content)    
        print 'resp_dict ',  resp_dict 
                
        self.assertTrue(resp_dict['error class'] == 'WorkspaceDoesNotExist')
        

        
    def test_0017_delete(self):
        """ 
        1 - Creates a new workspace with api method /api/workspace/new/
        2 - Deletes the new workspace with api method /api/workspace/ws_pk/delete
        3 - Checks that in django db the deleted workspace does not exist any more and that a DAMWorkspace exception arises
        """ 
        name = 'test_2'        
        params = self.get_final_parameters({'name':name, })
        response = self.client.post('/api/workspace/new/', params)        
        resp_dict = json.loads(response.content)           
        ws_pk = resp_dict['id']
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/delete/'%ws_pk, params)        
        self.assertTrue(response.content == '')
        self.assertRaises(DAMWorkspace.DoesNotExist,  DAMWorkspace.objects.get,  pk = ws_pk)

    def test_0018_create(self):
        """ 
        Creates a new workspace using api method /api/workspace/new/ and checks it is really in django db
        """ 
        name = 'test_1'
        
        params = self.get_final_parameters({'name':name,  })
        response = self.client.post('/api/workspace/new/', params, )        
        resp_dict = json.loads(response.content)        
        ws_pk = resp_dict['id']
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == name)
        self.assertTrue(resp_dict.has_key('description'))
        self.assertTrue(resp_dict.get('name') == name)
        
        
    def test_0019_set_creator(self):
        """
        Set workspace creator name using api method /api/workspace/ws_id/set_creator/ and checks if it was actually set in django db
        """
        u = User.objects.create(username = 'test')
        ws_id = 1

        
        params = self.get_final_parameters({'creator_id':u.pk})
        response = self.client.post('/api/workspace/%s/set_creator/'%ws_id, params, )        

        ws = DAMWorkspace.objects.get(pk = ws_id)
        self.assertTrue(response.content == '')

        self.assertTrue(ws.creator == u)

    def test_0020_get_smartfolders(self):
        """
        Gets all the smart folders of the first workspace calling api method /api/workspace/ws_id/get_smartfolders/ and checks if in django db that workspace actually has that smartfolder.
        """
        ws_id = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_smartfolders/'%ws_id, params, )        

        ws = DAMWorkspace.objects.get(pk = ws_id)
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.has_key('smartfolders'))
        self.assertTrue(len(resp_dict['smartfolders']) == 1)
        
        
    def test_0021_get_renditions(self):
        """
        Gets all the renditions of the first workspace calling api method /api/workspace/ws_id/get_renditions/ and checks if in django db that workspace actually has that rendition.
        """
        ws_id = 1
        params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/get_renditions/'%ws_id, params, )        

        ws = DAMWorkspace.objects.get(pk = ws_id)
        resp_dict = json.loads(response.content)        
        print resp_dict 
        self.assertTrue(resp_dict.has_key('renditions'))
        
    def test_0022_get_items_filtering_by_creation_time(self):
        """
        Search iterms filtering by last update.        
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        item1 = Item.objects.get(pk = 2)
        print 'item.creation_time', item.creation_time.strftime('%c')
        print 'item1.creation_time', item1.creation_time.strftime('%c')
        params = self.get_final_parameters({ 
            'creation_time>': item.creation_time.strftime('%d/%m/%Y %H:%M:%S')
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['totalCount'] == 1)
        self.assertTrue(resp_dict['items'][0]['pk'] == 2)
        
        
    def test_get_items_with_metadata(self):
        """
        Search items retrieving a given metadata.        
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        item1 = Item.objects.get(pk = 2)
        params = self.get_final_parameters({ 
            'metadata': 'dc:title'
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        self.assertTrue(resp_dict['totalCount'] == 2)
        self.assertTrue(resp_dict['items'][0]['metadata'].has_key('dc:title'))
        self.assertTrue(len(resp_dict['items'][0]['metadata'].keys()) == 1)
        
        self.assertTrue(resp_dict['items'][1]['metadata'].has_key('dc:title'))
        self.assertTrue(len(resp_dict['items'][1]['metadata'].keys()) == 1)        
        
    def test_get_items_with_all_metadata(self):
        """
        Search items retrieving all metadata.        
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        item1 = Item.objects.get(pk = 2)
        params = self.get_final_parameters({ 
            'metadata': '*'
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        self.assertTrue(resp_dict['totalCount'] == 2)
        self.assertTrue(len(resp_dict['items'][0]['metadata'].keys()) > 1)
        self.assertTrue(len(resp_dict['items'][1]['metadata'].keys()) > 1)
        
    
    def test_get_items_with_keywords(self):
        """
        Search items retrieving all metadata.        
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
       
        params = self.get_final_parameters({ 
            'get_keywords': True
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        self.assertTrue(resp_dict['totalCount'] == 2)
        self.assertTrue(resp_dict['items'][0].has_key('keywords') == True) 
        self.assertTrue(resp_dict['items'][1].has_key('keywords') == True) 
        self.assertTrue(len(resp_dict['items'][0]['keywords']) == 1)
        self.assertTrue(len(resp_dict['items'][1]['keywords']) == 1)
        
    
    def test_get_items_with_deleted_ones(self):
        """
        Search items retrieving all items. included deleted.        
        """
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        item1 = Item.objects.get(pk = 2)
        params = self.get_final_parameters({ 
            'show_deleted': True
        }) 
        response = self.client.get('/api/workspace/%s/get_items/'%workspace.pk, params)   
        resp_dict = json.loads(response.content)
        
        self.assertTrue(resp_dict['totalCount'] == 3)
        self.assertTrue(resp_dict['items'][0]['deleted'] == True)
        self.assertTrue(resp_dict['items'][1]['deleted'] == False)
        self.assertTrue(resp_dict['items'][2]['deleted'] == False)
    
        
        
class ItemTest(MyTestCase):  
    """
    Tests on items
    """
    fixtures = ['api/fixtures/test_data.json', 
                'treeview/fixtures/test_data.json', 
                 'repository/fixtures/test_data.json',  
#                 'variants/fixtures/test_data.json',
                  'workspace/fixtures/test_data.json' , 
                   'metadata/fixtures/test_data.json' 
                   ]    
    
    def test_0022_create(self):
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
    
        
        
    
    def test_0023_get_keywords(self):
        item = Item.objects.all()[0]    
        keywords = list(item.keywords())            
        
        params = self.get_final_parameters({'workspace_id': 1})
        response = self.client.get('/api/item/%s/get_keywords/'%item.pk, params)                        
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict['keywords'] == keywords)
         
    
    def test_0024_get(self):
        
        item = Item.objects.all()[0]    
        keywords = list(item.keywords())            
        ws_pk = 1
        params = self.get_final_parameters({'workspace': ws_pk, 'renditions': 'original'})
        response = self.client.get('/api/item/%s/get/'%item.pk, params, )                        
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict.has_key('pk'))
        self.assertTrue(resp_dict.has_key('keywords'))
        
        self.assertTrue(resp_dict.has_key('workspaces'))
        self.assertTrue(resp_dict['media_type'] == 'image') 
        
        self.assertTrue(resp_dict['pk'] == item.pk) 
        self.assertTrue(resp_dict['keywords'] == keywords)
        self.assertTrue(resp_dict['upload_workspace'] == 1)
      
        metadata = {}
        for metadata_value in MetadataValue.objects.filter(item = item):
            metadata[str(metadata_value.schema)] = metadata_value.value
        
        self.assertTrue(resp_dict['metadata'] == metadata)
        
        
    def test_0025_get_except(self):
        item_pk = 1000    
                    
        ws_pk = 1
        params = self.get_final_parameters({'workspace': ws_pk, 'renditions': 'original'})
        response = self.client.get('/api/item/%s/get/'%item_pk, params) 
        resp_dict = json.loads(response.content)
        print resp_dict 
        self.assertTrue(resp_dict['error class'] == 'ItemDoesNotExist')
        
    def test_0026_move(self):
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
        
        
    def test_0027_delete(self):
        workspace_id = 1
       
        item_id = item_id = Item.objects.all()[0].pk
        
        params = self.get_final_parameters({'workspace_id':workspace_id})
        response = self.client.get('/api/item/%s/delete_from_workspace/'%item_id, params,  )            
        
        self.assertTrue(response.content == '')               
        self.assertRaises(Item.DoesNotExist,  Item.objects.get,  pk = item_id)
        

    def test_0028_metadata(self):
        
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
        
    
       
     
    def test_0029_remove_metadata_single(self):
        workspace_id = 1
        params = self.get_final_parameters({'workspace_id':workspace_id,  'media_type': 'image/jpeg'})        
        response = self.client.post('/api/item/new/', params,  )                
        
        resp_dict = json.loads(response.content)        
        item_id = resp_dict.get('id')
        print 'item_id',  item_id
        item = Item.objects.get(pk = item_id)
       
        
#        metadata_dict = {'namespace':'dc',  'name':'subject',  'value': ['test',  'test2']}
        item.metadata.clear()
        metadata_dict = {'dc_subject': ['test', 'test2']}
        params = self.get_final_parameters({ 'metadata':json.dumps(metadata_dict),  'workspace_id':1})        
        self.client.post('/api/item/%s/set_metadata/'%item_id, params, )         
     
        metadata_dict_to_remove = {'namespace':'dc',  'name':'subject',  'value': 'test2'}
        params = self.get_final_parameters({ 'metadata':json.dumps([metadata_dict_to_remove]), 'workspace_id':1})        
        response = self.client.post('/api/item/%s/remove_metadata/'%item_id, params, )        
        self.assertTrue(response.content == '')        
        m = item.metadata.all() 
        print '----m',m       
        self.assertTrue(m.count() == 1)
        m_0 = m[0]      
#        self.assertTrue(m_0.schema.namespace == metadata_dict['namespace'])
#        self.assertTrue(m_0.schema.name== metadata_dict['name'])
#        self.assertTrue(m_0.value == metadata_dict['value'][0])        
        
        print 'm_0.value ',  m_0.value 
        print 'metadata_dict.items()[0] ',  metadata_dict.values()[0]
        self.assertTrue(m_0.value == metadata_dict.values()[0][0])        
        
    def test_0030_remove_metadata_all(self):
        workspace_id = 1
        params = self.get_final_parameters({ 'workspace_id':workspace_id,  'media_type': 'image/jpeg'})        
        response = self.client.post('/api/item/new/', params,  )                
        
        resp_dict = json.loads(response.content) 
        print('resp_dict %s'%resp_dict)       
        item_id = resp_dict.get('id')
        item = Item.objects.get(pk = item_id)
        
        item.metadata.clear()
        metadata_dict = {'namespace':'dc',  'name':'subject',  'value': ['test',  'test2']}
        params = self.get_final_parameters({ 'metadata':json.dumps([metadata_dict])})        
        self.client.post('/api/item/%s/set_metadata/'%item_id, params, )         
     
        metadata_dict_to_remove = {'namespace':'dc',  'name':'subject'}
        params = self.get_final_parameters({ 'metadata':json.dumps([metadata_dict_to_remove])})        
        response = self.client.post('/api/item/%s/remove_metadata/'%item_id, params, )        
        self.assertTrue(response.content == '')        
        m = item.metadata.all()
        
        self.assertTrue(m.count() == 0)        
        
    def test_0031_add_keywords(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        new_node = Node.objects.get(label = 'test',  type = 'keyword', workspace = ws)
        item = Item.objects.all()[0]
        
        item_id = item.pk
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 0)
        params = self.get_final_parameters({ 'keywords':new_node.pk})        
        response = self.client.post('/api/item/%s/add_keywords/'%item_id, params, )            
        self.assertTrue(item.node_set.filter(pk = new_node.pk).count() == 1)
        
        
    def test_0032_remove_keywords(self):
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
               
    def test_0033_add_to_ws(self):
        
        workspace = DAMWorkspace.objects.create(name = 'test', creator = self.user)
        workspace_id = workspace.pk
        
        
        item = Item.objects.all()[0]
        params = self.get_final_parameters({ 'workspace_id': workspace_id})        
        response = self.client.post('/api/item/%s/add_to_workspace/'%item.pk, params, )            
        self.assertTrue(response.content == '')        
        self.assertTrue(item in workspace.items.all()) 
        

        
        
        
    def test_0034_get_state(self):
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        state = State.objects.create(name = 'test',  workspace = workspace)
        state_association = StateItemAssociation.objects.create(state = state, item = item, )
        params = self.get_final_parameters({ 'workspace_id': workspace.pk,  }) 
        response = self.client.post('/api/item/%s/get_state/'%item.pk, params, )            
        resp_dict = json.loads(response.content)
        print '-------------------------',  resp_dict
        self.assertTrue(resp_dict == {'name': 'test', 'id': state.pk})
        
    def test_0035_get_keywords(self):
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        
        params = self.get_final_parameters({ 'workspace_id': workspace.pk,  }) 
        response = self.client.get('/api/item/%s/get_keywords/'%item.pk, params, )            
        resp_dict = json.loads(response.content)
        print '-------------------------',  resp_dict
        
    
    def test_0036_set_state(self): 
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.all()[0]
        state = State.objects.create(name = 'test',  workspace = workspace)
        state_association = StateItemAssociation.objects.create(state = state, item = item)
        params = self.get_final_parameters({ 'workspace_id': workspace.pk, 'state': state.name}) 
        response = self.client.post('/api/item/%s/set_state/'%item.pk, params, )            
        
        self.assertTrue(response.content == '')
        self.assertTrue(StateItemAssociation.objects.get(item = item).state.name == 'test')
        
    def test_last_update_on_change_metadata(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        get_params = self.get_final_parameters({'workspace': 1})        
        resp =  self.client.get('/api/item/%s/get/'%item.pk, get_params)       
        last_update = datetime.strptime(json.loads(resp.content)['last_update'], '%c')
        item.set_metadata('dc','subject', ['test_last_update'])
                
        resp =  self.client.get('/api/item/%s/get/'%item.pk, get_params)
        last_update2 = datetime.strptime(json.loads(resp.content)['last_update'], '%c')
        self.assertTrue(last_update2 > last_update)
    
    def test_last_update_on_add_keyword(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
        item = Item.objects.get(pk = 1)
        get_params = self.get_final_parameters({'workspace': 1})        
        resp =  self.client.get('/api/item/%s/get/'%item.pk, get_params)       
        last_update = datetime.strptime(json.loads(resp.content)['last_update'], '%c')
      
        node = Node.objects.get(label = 'test')
        node.save_keyword_association([item.pk])
        
        resp =  self.client.get('/api/item/%s/get/'%item.pk, get_params)
        last_update2 = datetime.strptime(json.loads(resp.content)['last_update'], '%c')        
        self.assertTrue(last_update2 > last_update)
        
    def test_last_update_on_add_to_ws(self):
        workspace = DAMWorkspace.objects.get(pk = 1)        
        workspace_receiver = DAMWorkspace.objects.create_workspace('test_item_add_to_ws', '', workspace.creator)
        item = Item.objects.get(pk = 1)
        get_params = self.get_final_parameters({'workspace': 1})        
        resp =  self.client.get('/api/item/%s/get/'%item.pk, get_params)       
        last_update = datetime.strptime(json.loads(resp.content)['last_update'], '%c')
      
        item.add_to_ws(workspace_receiver)
        get_params = self.get_final_parameters({'workspace': workspace_receiver.pk})      
        resp =  self.client.get('/api/item/%s/get/'%item.pk, get_params)
        last_update2 = datetime.strptime(json.loads(resp.content)['last_update'], '%c')        
        self.assertTrue(last_update2 > last_update)
        

class KeywordsTest(MyTestCase):
    """
    Tests about keywords
    """
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json']   
    

    def test_0037_get_single(self):        
             
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
        
        
    def test_0038_get_except(self):        
             
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        node_pk = 1000
        response = self.client.get('/api/keyword/%s/get/'%node_pk, params)        
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'CatalogueElementDoesNotExist')
        
    def test_0039_get_single_category(self):        
             
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
        
        
    
    def test_0040_create(self):             
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
        


    def test_0041_create_2(self):             
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
        
        
    def test_0042_create_no_parent(self):             
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

    def test_0043_create_metadata(self):             
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

        
    def test_0044_create_category(self):
            
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
            
        
    def test_0045_edit(self):

        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'People',  workspace = ws)        
        params = self.get_final_parameters({'label':'test'})        
        self.assertTrue(node.associate_ancestors == False)
        
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        
        node = Node.objects.get(pk = node.pk)
        self.assertTrue(node.label == 'test')
        self.assertTrue(node.associate_ancestors == False)
    
    def test_0046_edit_1(self):

        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        node = Node.objects.get(label = 'test',  workspace = ws)        
        params = self.get_final_parameters({'associate_ancestors':'true'})        
        self.assertTrue(node.associate_ancestors == False)
        response = self.client.post('/api/keyword/%s/edit/'%node.pk, params,  )                
        node = Node.objects.get(pk = node.pk)
        self.assertTrue(node.associate_ancestors == True)
        
    
    def test_0047_edit_metadata(self):

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
        
    
    

    

    def test_0048_move(self):
        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)        
        node_id = Node.objects.get(label = 'test').pk
        
        new_parent_node_pk = parent_node = Node.objects.get(workspace = ws, label = 'Places',  depth = 1).pk
        params = self.get_final_parameters({ 'parent_id':new_parent_node_pk,  })        
        self.client.post('/api/keyword/%s/move/'%node_id, params,  )      
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/get/'%node_id, params)        
        resp_dict = json.loads(response.content)
        print '-----', resp_dict
        parent_id = resp_dict['parent_id']        
        self.assertTrue(parent_id == new_parent_node_pk)        
        
        
    def test_0049_move_on_top(self):
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
        
    def test_0050_delete(self):
        ws_pk = 1 
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        node_id = Node.objects.get(label = 'test').pk
        
        params = self.get_final_parameters({})
        response = self.client.get('/api/keyword/%s/delete/'%node_id, params,  ) 
        
        self.assertTrue(response.content == '')
        self.assertRaises(Node.DoesNotExist,  Node.objects.get, pk = node_id )
        
    def test_0051_add_items(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.all()[0]
        item_id = item.pk
        new_node = Node.objects.get(label = 'test')
        
        params = self.get_final_parameters({ 'items':item.pk})        
        response = self.client.post('/api/keyword/%s/add_items/'%new_node.pk, params, )            
        self.assertTrue(item.node_set.filter(label = 'test').count() == 1)
      
    def test_0052_remove_items(self):
        workspace_id = 1
        ws = DAMWorkspace.objects.get(pk = workspace_id)
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.create(ws, uploader = User.objects.get(pk = 1),  type = Type.objects.get_by_mime('image/jpeg')[0],)
        
        node_parent = Node.objects.get(label = 'People',  workspace = ws)
        item = Item.objects.all()[0]
        item_id = item.pk
        new_node = Node.objects.get(label = 'test')
        
        params = self.get_final_parameters({ 'items':item.pk})        
        response = self.client.post('/api/keyword/%s/remove_items/'%new_node.pk, params, )  
        self.assertTrue(item.node_set.filter(label = 'test').count() == 0)


class TestLogin(MyTestCase):
    """
    Tests about login operation
    """
    fixtures = ['api/fixtures/test_data.json', ]   
    def test_0053_login(self):
        user = User.objects.get(pk = self.user_id)
        
        password = 'notredam'
        params = {'user_name':user.username,  'api_key':self.api_key,  'password': password}
        response = self.client.post('/api/login/', params)        
        json_resp = json.loads(response.content)
        self.assertTrue(json_resp['user_id'] == user.pk)
        self.assertTrue(json_resp['secret'] == self.secret)
        self.assertTrue(json_resp['workspaces'] == [1])
        self.assertTrue(json_resp.has_key('session_id'))
        
    def test_0054_login_wrong(self):
        user = User.objects.get(pk = self.user_id)
        
        password = 'demoooo'
        params = {'user_name':user.username,  'api_key':self.api_key,  'password': password}
        response = self.client.post('/api/login/', params)        
        json_resp = json.loads(response.content)
        print 'json_resp  %s' %json_resp 
        self.assertTrue(json_resp['error code'] == 403)
        
    def test_0055_get_users(self):
        user = User.objects.get(pk =1)
        
        params = self.get_final_parameters({})
        print '------- params ',  params
        response = self.client.get('/api/get_users/', params)        
        
        json_resp = json.loads(response.content)
        print 'json_resp ',  json_resp 
        expected_resp = {'users': [{'id':user.pk, 'username': user.username, 'password': user.password, 'email': user.email, 'is_superuser': user.is_superuser}]}
        self.assertTrue(json_resp== expected_resp)
    

    def test_0056_add_user(self):
        
        params = {'username': 'test',  'email': 't@t.it',  'password': 'sha1$fa34f$1b63507b88b494bb58d466d7f669a1670fe838fb'}
        params = self.get_final_parameters(params)
        
        response = self.client.post('/api/add_user/', params)        
        
        json_resp = json.loads(response.content)
        print 'json_resp ',  json_resp 
        
        self.assertTrue(json_resp.has_key('id'))
    





class VariantsTest(MyTestCase):
    """
    Tests related to Variants
    """
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
    
    def test_0057_get_single(self):
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
        
        
    def test_0058_get_except(self):
        variant_pk = 1000
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({'workspace_id': workspace.pk})    
        response = self.client.get('/api/rendition/%s/get/'%variant_pk, params)
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'RenditionDoesNotExist')
          
    def test_0059_edit(self):
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
        #self.assertTrue(len(variant.media_type.all()) == len(params['media_type']))
        self.assertTrue(variant.media_type.all()[0].name == params['media_type'][0])
        
        
        
    def test_0060_create(self):
        
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = {'name': 'test', 'media_type': ['image'], 'workspace_id': 1, 'caption':'test'}
        params = self.get_final_parameters(params)
        
        
        response = self.client.post('/api/rendition/new/',  params)                
        resp_dict = json.loads(response.content)     
                
        self.assertTrue(Variant.objects.filter(pk = resp_dict['id']).count() == 1)
        self.assertTrue(Variant.objects.get(pk = resp_dict['id']).workspace.pk == params['workspace_id'])
        
        
    def test_0061_delete(self):
        workspace = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({})
        variant = Variant.objects.create(name = 'test', auto_generated = True, workspace = workspace)
        response = self.client.get('/api/rendition/%s/delete/'%variant.pk, params)
        self.assertTrue(response.content == '')
        self.assertTrue(Variant.objects.filter(pk = variant.pk).count() == 0)
    

class SmartFolderTest(MyTestCase):
    """
    Tests related to SmartFolders
    """
    fixtures = ['api/fixtures/test_data.json', 'treeview/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
    
    def test_0062_get_single(self):
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
        
    def test_0063_get_except(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({})        
        sm_pk = 1000
        response = self.client.get('/api/smartfolder/%s/get/'%sm_pk, params)        
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['error class'] == 'SmartFolderDoesNotExist')
        
    
    
    
    def test_0064_create(self):
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
        
        
        
    def test_0065_delete(self):
        
        params = self.get_final_parameters()        
        sm = SmartFolder.objects.get(pk = 1)
        response = self.client.get('/api/smartfolder/%s/delete/'%sm.pk, params)        
       
        self.assertTrue(SmartFolder.objects.filter(pk = 1).count() == 0)
        self.assertTrue(response.content == '')       

    
    def test_0066_edit(self):
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
    
    
    
    def test_0067_get_items(self):
       
        sm_id = 1
        params = self.get_final_parameters({})                
        
        response = self.client.post('/api/smartfolder/%s/get_items/'%sm_id, params,)                
        
        print 'response.content', response.content
        resp_dict = json.loads(response.content)
        self.assertTrue(resp_dict['items'] == [2])
        

class ScriptsTest(MyTestCase):
    """
    Tests related to Scripts
    """
    fixtures = ['api/fixtures/test_data.json',  'repository/fixtures/test_data.json', 'core/dam_repository/fixtures/test_data.json',  
#                'scripts/fixtures/test_data.json'
                ]   
   
    def test_0068_create(self):
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
        
        
    def test_0069_edit(self):
        ws = DAMWorkspace.objects.get(pk = 1)
        name = 'test_edit'
        description = 'test_edit'
        pipeline =  {
             
                 
        }
        script = Pipeline.objects.get(pk = 1)
        params = self.get_final_parameters({ 'name':name,  'description': description,  'params': json.dumps(pipeline)})     
                
        response = self.client.post('/api/script/%s/edit/'%script.pk, params,  )  
        script = Pipeline.objects.get(pk = script.pk)
        self.assertTrue(response.content == '')
        print script.name
        self.assertTrue(script.name == params['name'])
               
       
    def test_0070_run(self):
        script = Pipeline.objects.get(pk = 1)
        #self.assertTrue(response.content == '')

    def test_0071_get(self):
        script = Pipeline.objects.get(pk = 1)
        params = self.get_final_parameters({ })     
        response = self.client.post('/api/script/%s/get/'%script.pk, params,  )  
        resp_dict = json.loads(response.content)        
   
        self.assertTrue(resp_dict['id'] == script.pk)
        self.assertTrue(resp_dict['name'] == script.name)
        self.assertTrue(resp_dict['description'] == script.description)
        self.assertTrue(resp_dict['workspace_id'] == script.workspace.pk)
        
    def test_0072_get_except(self):
        script_pk = 1000
        params = self.get_final_parameters({ })     
        response = self.client.post('/api/script/%s/get/'%script_pk, params)  
        resp_dict = json.loads(response.content)       
   
        self.assertTrue(resp_dict['error class'] == 'ScriptDoesNotExist')
        
    def test_0073_get_scripts(self):

        ws = DAMWorkspace.objects.get(pk = 1)
        params = self.get_final_parameters({ })     
        response = self.client.post('/api/workspace/%s/get_scripts/'%ws.pk , params,  )  
        resp_dict = json.loads(response.content)        
   
        self.assertTrue(len(resp_dict['scripts']) == ws.pipeline_set.all().count())
        
        
        
        
        
class StatesTest(MyTestCase):
    """
    Tests related to States
    """
    fixtures = ['api/fixtures/test_data.json',  'repository/fixtures/test_data.json',  'workspace/fixtures/test_data.json']   
        
    def test_0074_delete(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        params = self.get_final_parameters({})
        
        response = self.client.post('/api/state/%s/delete/'%s.pk, params)      
        
        
        self.assertTrue(response.content == '')
        self.assertTrue(State.objects.filter(workspace__pk = ws_pk).count() == 0)
        
        
    def test_0075_create(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        params = self.get_final_parameters({'name': 'test', 'workspace_id': ws_pk})
        response = self.client.post('/api/state/new/', params)      
        resp_dict = json.loads(response.content)    
        self.assertTrue(resp_dict['name'] == 'test')
        self.assertTrue(State.objects.filter(workspace__pk = ws_pk).count() == 1)
        
        
    def test_0076_edit(self):
        
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        params = self.get_final_parameters({'name': 'test_edit'})
        response = self.client.post('/api/state/%s/edit/'%s.pk, params)      
            
        self.assertTrue(response.content == '')        
        self.assertTrue(State.objects.filter(workspace__pk = ws_pk, name = 'test_edit').count() == 1)
        
    def test_0077_get(self):
        
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
        
    def test_0078_add_items(self):
        ws_pk = 1
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        s = State.objects.create(name = 'test', workspace = ws)
        i = ws.items.all()[0]
        
        params = self.get_final_parameters({'items': [i.pk]})
        response = self.client.post('/api/state/%s/add_items/'%s.pk, params)      
        
        self.assertTrue(response.content == '')
        self.assertTrue(StateItemAssociation.objects.get(state = s).item == i)
        
        
    def test_0079_remove_items(self):
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


