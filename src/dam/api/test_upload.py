from django.core.management import setup_environ
from django.utils import simplejson
import dam.settings as settings
setup_environ(settings)

from api.tests import _get_final_parameters
from django.test.client import Client
from dam.api.models import *
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item,  Component
from dam.variants.models import Variant
import os
from dam.core.dam_repository.models import Type
import sys
import unittest
import hashlib

def md5(fileName, excludeLine="", includeLine=""):
    """Compute md5 hash of the specified file"""
    m = hashlib.md5()
    try:
        fd = open(fileName,"rb")
    except IOError:
        print "Unable to open the file in readmode:", filename
        return
    content = fd.readlines()
    fd.close()
    for eachLine in content:
        if excludeLine and eachLine.startswith(excludeLine):
            continue
        m.update(eachLine)
    m.update(includeLine)
    return m.hexdigest()


file_path = os.path.join(settings.ROOT_PATH, 'files/images/logo_blue.jpg')
print file_path

class TestUpload(unittest.TestCase):
    def test_upload(self):
        client = Client()
        secret_obj = Secret.objects.get(pk = 1)  
        secret = secret_obj.value
        api_key = secret_obj.application.api_key
        user_id = secret_obj.user.pk
        
        workspace_id = 1
        workspace = Workspace.objects.get(pk = workspace_id)
        metadata_dict = {'namespace':'dc',  'name':'title',  'value': 'test',  'lang': 'en'}
        params = {'workspace_id':workspace_id, 'media_type': 'image/jpeg' }

        params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = params)                
        
        response = client.post('/api/item/new/', params,)                
        resp_dict = simplejson.loads(response.content)
        item = Item.objects.get(pk = resp_dict['id'])

        file = open(file_path)
        rendition_id = 1
        params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'workspace_id': workspace_id,  'rendition_id':rendition_id})                
        params['files_to_upload'] = file
        
        
        response = client.post('/api/item/%s/upload/'%item.pk, params, )            
        
       
        
        file.close()
        hash_source = md5(file_path)
       
        self.assertTrue(response.content == '')        
        
        component = Variant.objects.get(pk = rendition_id).get_component(workspace,  item)
        
        hash_uploaded = md5(component.get_file_path())
        print 'component.get_file_path() ', component.get_file_path()
        
        self.assertTrue(hash_uploaded == hash_source)
        
        
if __name__ == "__main__":    
    unittest.main()
    
