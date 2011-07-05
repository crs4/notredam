from django.core.management import setup_environ
from django.utils import simplejson
import dam.settings as settings
setup_environ(settings)

from api.tests import _get_final_parameters
from django.test.client import Client
from dam.api.models import *
from dam.workspace.models import DAMWorkspace
from dam.repository.models import Item,  Component
import os
from dam.core.dam_repository.models import Type
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print """No file passed. 
        Typical use:
        
            python manage.py loaddata api/fixtures/test_data.json
            python test_upload.py /path/file/to/upload
        
        """
        sys.exit(2)
        
    file_path = sys.argv[1]
    client = Client()
    secret_obj = Secret.objects.get(pk = 1)  
    secret = secret_obj.value
    api_key = secret_obj.application.api_key
    user_id = secret_obj.user.pk
    
    workspace_id = 1
    metadata_dict = {'namespace':'dc',  'name':'title',  'value': 'test',  'lang': 'en'}
    params = {'workspace_id':workspace_id, 'media_type': 'image/jpeg' }

    params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = params)                
    
    response = client.post('/api/item/new/', params,)                
    resp_dict = simplejson.loads(response.content)

    file = open(file_path)
    params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'workspace_id': 1,  'rendition_id':1})                
    params['files_to_upload'] = file
    
    
    response = client.post('/api/item/%s/upload/'%resp_dict['id'], params, )            
    file.close()

    print response.content 

