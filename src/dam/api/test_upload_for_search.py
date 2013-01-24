import os
from django.core.management import setup_environ
from django.utils import simplejson
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_apps
get_apps() 


from time import sleep

from dam.api.utils import _get_final_parameters
from django.test.client import Client
from dam.api.models import *
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item,  Component
from dam.variants.models import Variant


from dam.core.dam_repository.models import Type
INPUT_FILE = os.path.join(settings.ROOT_PATH, 'api/muffin_small.jpeg')
#INPUT_FILE = os.path.join(settings.ROOT_PATH, 'files/images/logo_blue.jpg')
print INPUT_FILE
TOTAL = 1


if __name__ == "__main__":
    client = Client()
    secret_obj = Secret.objects.get(pk = 1)  
    secret = secret_obj.value
    api_key = secret_obj.application.api_key
    user_id = secret_obj.user.pk
    
    #metadata_dict = {'namespace':'dc',  'name':'title',  'value': 'test',  'lang': 'en', }
    workspace_id = 1
    workspace = Workspace.objects.get(pk = workspace_id) 
    print 'workspace is: ', workspace
    params_a = {'workspace_id':workspace_id, 'media_type': 'image/jpeg' }
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
        item = Item.objects.get(pk=resp_dict['id'])
        print 'item id is: ', item.pk
        print '<======\n'
        params_b = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'workspace_id': 1,  'rendition_id':1})                
        params_b['files_to_upload'] = file
        try: 
            response = client.post('/api/item/%s/upload/'%item.pk, params_b, )            
            print '**** **** **** resopnse to uploading is ', response
        except Exception, err:
            print '\nerror in client post upload item: ', err

        #component = Variant.objects.get(pk = 1).get_component(workspace,  item)
        
        #print 'component.get_file_path() ', component.get_file_path()
        print 'no file path is required! '


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
        try:
            params_c = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'metadata':simplejson.dumps(metadata_dict)})
        except Exception, err:
            print 'error in _get_final_parameters: ', err
        try:
            response_c = client.post('/api/item/%s/set_metadata/'%resp_dict['id'], params_c, )            
        except Exception, err:
            print 'error in client post set_metadata: ', err

        print "\n************* END ***************\n"

        #print '\n\n**** i = **** response.content:\n', response.content 
        #sleep(10)
        #file.seek(0)
    #file.close()

