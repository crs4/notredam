from django.test import TestCase
from django.core.management import setup_environ
from django.utils import simplejson as json
import dam.settings
setup_environ(dam.settings)
from time import sleep

from api.tests import _get_final_parameters
from django.test.client import Client
from dam.api.models import *
from dam.workspace.models import DAMWorkspace
from dam.repository.models import Item,  Component
from dam.variants.models import Variant
from dam.mprocessor.models import Process
from dam.core.dam_repository.models import Type

# This separate module of tests was necessary in order to have
# some uploading tests, because uploading tests are not possible
# using the module tests.py where a test db is created.
# The reason of this is that uploading operations need MediaDART
# which uses the real application db defined in 
# settings.py. Since they use the real application db, all the tests 
# collected in this module end with clean up operations. So the
# application db is restored after each test.

# TO DO: Remember to implement uploading test of ALL the types declared as
# supported in NotreDAM documentation

# the tests in this file are called from dam directory with the following:
# python api/uploading_testcases.py

INPUT_FILE = 'api/muffin_small.jpeg'

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



class MultiPurposeTestCase(TestCase):

    def __init__(self):
        self.client = Client()
        secret_obj = Secret.objects.get(pk = 1)
        self.secret = secret_obj.value
        self.api_key = secret_obj.application.api_key
        self.user_id = secret_obj.user.pk
        fixtures = ['api/fixtures/test_data.json',]

    def get_final_parameters(self, kwargs = None):
        "add api_key user_id and secret (required by check sum)"
        return _get_final_parameters(self.api_key, self.secret, self.user_id, kwargs)
        
    def test_1000_ws_create_delete(self):

        # 1 - test new ws creation
        user = User.objects.get( pk = 1 )
        name = 'ws_user_test_1'
        try:
            check_ws = DAMWorkspace.objects.get(name = name, creator = user)
            if check_ws.name == name : # it already exist, first delete it!
                ws_params = self.get_final_parameters({})
                response = self.client.get('/api/workspace/%s/delete/' % check_ws.pk, ws_params)
            try:
                check_ws = DAMWorkspace.objects.get(name = name, creator = user)
            except DAMWorkspace.DoesNotExist:
                print 'OK workspace %s does not exist' % name
        except DAMWorkspace.DoesNotExist:
            print 'OK workspace %s does not exist' % name
        print 'workspace %s does not exist, now create it' % name
        
        params = self.get_final_parameters({'username':user.username,'name':name,  })
        try:
            response = self.client.post('/api/workspace/new/', params, )        
        except Exception, err:
            print 'api workspace new err: ', err
        resp_dict = json.loads(response.content)        
        print '\n api - ws - new, response dict: ', resp_dict 
        ws_pk = resp_dict['id']
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == name)
        self.assertTrue(resp_dict.has_key('description'))
        self.assertTrue(resp_dict.get('name') == name)

        # 2 - remove ws_user_test_1
        ws_params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/delete/' % ws_pk, params)
        self.assertTrue(response.content == '')
        self.assertRaises(DAMWorkspace.DoesNotExist, DAMWorkspace.objects.get, pk = ws_pk)
        
        print '\n\n**** end of test: create and delete a workspace'


    def test_0100(self):
        """
        add new user user_test_1 (not allowed through api)
        1 - login as self.user
        2 - self.user adds a new workspace ws_user_test_1
        3 - self.user adds new_item in ws_user_test_1
        4 - self.user upload the content of new_item in ws_user_test_1
        5 - self.user adds new_metadata to new_item
        The following are restoring steps:
        6 - delete new_metadata from new_item
        7 - remove new_item from all workspaces (this should be a complete removal)
        8 - remove ws_user_test_1
        """
        import os.path
        #params = {'username': 'user_test_1',  'email': 'u_test1@crs4.it',  'password': 'sha1$d345c$3861b4f1caa14a266b1b8e53143121529a86a272'}
        #params = self.get_final_parameters(params)
        #response = self.client.post('/api/add_user/', params)        
        #json_resp = json.loads(response.content)
        #self.assertTrue(json_resp.has_key('id'))

        # 1 - login self.user using /api/login/
        user = User.objects.get( pk = 1 )
        print 'username: ', user.username, ' psswd = ', user.password
        params = {'user_name':user.username, 'api_key':self.api_key,  'password': 'notredam' }
        try:
            response = self.client.post('/api/login/', params)        
        except Exception, err:
            print 'api user login err: ', err
        json_resp = json.loads(response.content)
        print '\n\napi login - json_resp ',  json_resp 
        print 'api login - user.pk = ', user.pk
        print 'api login - self.secret = ', self.secret
        self.assertTrue(json_resp['user_id'] == user.pk)
        self.assertTrue(json_resp['secret'] == self.secret)
        self.assertTrue(json_resp.has_key('session_id'))
        self.assertTrue(json_resp.has_key('workspaces'))

        # 2 - test new ws creation
        name = 'ws_user_test_1'
        print '\n\n&&&&&&&&&&&&&&&\napi ws new - username: ', user.username, ' \n\n&&&&&&&&&&&&&&&&&&&&&&'
        try:
            check_ws = DAMWorkspace.objects.get(name = name, creator = user)
            if check_ws.name == name : # it already exist, first delete it!
                ws_params = self.get_final_parameters({})
                response = self.client.get('/api/workspace/%s/delete/' % check_ws.pk, ws_params)
            try:
                check_ws = DAMWorkspace.objects.get(name = name, creator = user)
            except DAMWorkspace.DoesNotExist:
                print 'OK workspace %s does not exist' % name
        except DAMWorkspace.DoesNotExist:
            print 'OK workspace %s does not exist' % name
        print 'workspace %s does not exist, now create it' % name
        

        params = self.get_final_parameters({'username':user.username,'name':name,  })
        try:
            response = self.client.post('/api/workspace/new/', params, )        
        except Exception, err:
            print 'api workspace new err: ', err
        resp_dict = json.loads(response.content)        
        print '\n api - ws - new, response dict: ', resp_dict 
        ws_pk = resp_dict['id']
        ws = DAMWorkspace.objects.get(pk = ws_pk)
        self.assertTrue(ws.name == name)
        self.assertTrue(resp_dict.has_key('description'))
        self.assertTrue(resp_dict.get('name') == name)

        # 3 - self.user adds new_item in ws_user_test_1

        params = {'workspace_id': ws_pk, 'media_type':'image/jpeg'}
        params = self.get_final_parameters(kwargs = params)        
        print '\n api item new - params: ', params
        try:
            response = self.client.post('/api/item/new/', params,)
        except Exception, err:
            print 'error in api item new: ', err
        i_resp_dict = json.loads(response.content)
        print '\napi item new -  i_resp_dict: ', i_resp_dict
        print 'checks if new item was created'
        new_item = Item.objects.get(pk = i_resp_dict['id'])
        new_item_id = i_resp_dict.get('id')

        self.assertTrue(new_item.type.name == 'image')
        self.assertTrue(i_resp_dict['workspace_id'] == str(ws_pk))

        # 4 - upload content file for new item just created 
        file = None
        try:
            file = open(INPUT_FILE)
        except IOError, err:
            print 'error while opening input file: ', err
        if file == None:
            print 'file variable is None!'
            return
        upload_params = self.get_final_parameters()        
        upload_params['rendition_id'] = 1
        upload_params['Filedata.jpeg'] = file
        upload_params['workspace_id'] = ws_pk
        print '\n api item upload - params: ', upload_params
        print '\n api item upload - returns no response.'
        try: 
            upload_response = self.client.post('/api/item/%s/upload/'% new_item_id, upload_params )            
        except Exception, err:
            print 'error in api item upload : ', err

        # now wait until uploading processes have completed
        processes = ws.get_active_processes()
        for i,p in enumerate(processes):
            while p.is_completed() == 0:
                p = Process.objects.get(pk = p.pk)
                print '\n\n********* i= ',i,'***********\np: ', p, ' is completed?', p.is_completed(), ' pk ', p.pk
                sleep(2)
        
        # 5 - add metadata to newly uploaded item 
        
        metadata_dict = {'dc_title':{'en-US':'A muffin'}, 'dc_subject': ['muffin','topping', 'cake', 'good']}
        m_params = self.get_final_parameters(kwargs = {'metadata':json.dumps(metadata_dict)})
            
        try:
            m_response = self.client.post('/api/item/%s/set_metadata/'% new_item_id,m_params,)
        except Exception, err:
            print 'error in api set_metadata: ', err
        self.assertTrue(m_response.content == '')
        title = new_item.metadata.get(schema__field_name = 'title')
        self.assertTrue(title.value == 'A muffin')
        subject = new_item.metadata.filter(schema__field_name = 'subject')
        
        self.assertTrue(subject[0].value == 'muffin')
        self.assertTrue(subject[1].value == 'topping')
        self.assertTrue(subject[2].value == 'cake')
        self.assertTrue(subject[3].value == 'good')


        print '<====== END. Now come back ======>\n'
        """
        # list files created in cache dir in order to check if they have been removed
        # when the item is deleted

        list_of_files = []
        print 'workspace = ', ws, ' workspace_id = ', ws_pk, ' workspace.name = ', ws.name
        original = Variant.objects.filter(name = 'original', workspace = ws)[0]
        original_file = new_item.get_variant(ws, original)
        original_file_path = original_file.get_file_path()
        list_of_files.append(original_file_path)
        #  for the other variants, it is necessary to ask if their creation has finished

        """
                
        
        #  The following steps are intended to have an application db restoring:
        # 6 - delete new_metadata from new_item
        title_to_remove = {'namespace':'dc',  'name':'title'}
        params = self.get_final_parameters({ 'metadata':json.dumps([title_to_remove])})        
        ir_response = self.client.post('/api/item/%s/remove_metadata/' % new_item_id, params, )        
        subject_to_remove = {'namespace':'dc',  'name':'subject'}
        params = self.get_final_parameters({ 'metadata':json.dumps([subject_to_remove])})        
        ir_response = self.client.post('/api/item/%s/remove_metadata/' % new_item_id, params, )        
        self.assertTrue(ir_response.content == '')        
        m = new_item.metadata.all()
        self.assertTrue(m.count() == 0)        
        

        
        # 7 - remove new_item from workspace (item and content)
        params = self.get_final_parameters({'workspace_id':ws_pk})
        id_response = self.client.get('/api/item/%s/delete_from_workspace/'%new_item_id, params,  ) 
        self.assertTrue(id_response.content == '')               
        self.assertRaises(Item.DoesNotExist,  Item.objects.get,  pk = new_item_id)
        # now check if files have been removed from repository
        

        # 8 - remove ws_user_test_1
        ws_params = self.get_final_parameters({})
        response = self.client.get('/api/workspace/%s/delete/' % ws_pk, params)
        self.assertTrue(response.content == '')
        self.assertRaises(DAMWorkspace.DoesNotExist, DAMWorkspace.objects.get, pk = ws_pk)
        # 9 - user logout (the api method does not exist!)





if __name__ == "__main__":
    import sys
    import os
    import traceback
    os.system('python manage.py loaddata api/fixtures/test_data.json')
    if len(sys.argv) < 2:
        # the following code has to be repeated for each class in this file!
        try:
            test_setup = MultiPurposeTestCase()
        except Exception, err:
            print 'error in MultiPurposeTestCase setup, err: ', err
        try:
            test_setup.test_0100()
        except Exception, err:
            print 'error in test_0100, err: ', err, ' \n'
    elif len(sys.argv) == 2:
        print 'in uploading_testcases.py sys.argv[1]: ', sys.argv[1] 
        class_name, test_name = sys.argv[1].split('.')
        try:
            my_test = eval(class_name + '().' + test_name + '()')
            print 'TEST PASSED!'
        except Exception, err:
            print traceback.print_exc(err), '\nTEST FAILED!'
