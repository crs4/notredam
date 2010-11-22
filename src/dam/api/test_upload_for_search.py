from django.core.management import setup_environ
from django.utils import simplejson
import dam.settings
setup_environ(dam.settings)
from time import sleep

from api.tests import _get_final_parameters
from django.test.client import Client
from dam.api.models import *
from dam.workspace.models import DAMWorkspace
from dam.repository.models import Item,  Component

from dam.core.dam_repository.models import Type
INPUT_FILE = 'muffin_small.jpeg'
TOTAL = 10000

if __name__ == "__main__":
    client = Client()
    secret_obj = Secret.objects.get(pk = 1)  
    secret = secret_obj.value
    api_key = secret_obj.application.api_key
    user_id = secret_obj.user.pk
    
    #metadata_dict = {'namespace':'dc',  'name':'title',  'value': 'test',  'lang': 'en', }
    
    workspace_id = 1
    params_a = {'workspace_id':workspace_id, 'media_type': 'image' }
    params_a = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = params_a)                
    file = open(INPUT_FILE)
    for i in range(TOTAL):
        
        print "\n************* START ***************\n"
        print ('\n\n**** i = %d **** \n' % i)
        item_id = 'ITEM_' + str(i).zfill(10)
        print 'item_id = ', item_id
        try:
            response = client.post('/api/item/new/', params_a,)                
        except Exception, err:
            print 'error in client post item new: ', err
        resp_dict = simplejson.loads(response.content)
        print '\n====> resp_dict: ', resp_dict
        print '<======\n'
        params_b = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'workspace_id': 1,  'rendition_id':1})                
        params_b['Filedata'] = file
        try: 
            response = client.post('/api/item/%s/upload/'%resp_dict['id'], params_b, )            
        except Exception, err:
            print 'error in client post upload item: ', err
        print "\n************* set item metadata ***************\n"
        if i <= TOTAL/10:
            metadata_list = ['muffin', 'topping', 'cake', 'good']
        elif i > TOTAL/10 and i <= TOTAL/4:
            metadata_list = ['muffin', 'topping', 'cake']
        elif i > TOTAL/4  and i <= TOTAL/2:
            metadata_list = ['muffin', 'topping']
        elif i > TOTAL/2 :
            metadata_list = ['muffin']

    
        metadata_dict = {'dc_title': {'en-US': str(item_id)},  'dc_identifier': 'test',  'dc_subject': metadata_list }

        params_c = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'metadata':simplejson.dumps(metadata_dict)})
        try:
            response_c = client.post('/api/item/%s/set_metadata/'%resp_dict['id'], params_c, )            
        except Exception, err:
            print 'error in client post set_metadata: ', err
        print "\n************* END ***************\n"

        #print '\n\n**** i = **** response.content:\n', response.content 
        #sleep(10)
        file.seek(0)
    file.close()

