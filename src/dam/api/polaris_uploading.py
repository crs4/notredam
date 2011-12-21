import os
import sys
from django.core.management import setup_environ
from django.utils import simplejson
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_apps
get_apps() 

from django.utils import simplejson as json

from time import sleep
import traceback

from dam.api.utils import _get_final_parameters
from django.test.client import Client
from dam.api.models import *
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item,  Component
from dam.variants.models import Variant
from dam.supported_types import supported_extensions, guess_file_type, mime_types_by_type, supported_types
from dam.treeview.models import Node,  NodeMetadataAssociation,  SmartFolder,  SmartFolderNodeAssociation



from dam.core.dam_repository.models import Type
from dam.upload.views import guess_media_type
import mimetypes
WORKSPACE_NAME = 'Archivio'
MEDIA_TYPE = 'image/jpeg'
ROOT_DIR = os.path.join(settings.ROOT_PATH, 'api')

if __name__ == "__main__":

    fixtures = ['api/fixtures/test_data.json']
    for fixture in fixtures:
        fixture_file = os.path.join(settings.ROOT_PATH, fixture)
        load_data_cmd = 'python ../manage.py loaddata ' + fixture_file
        try:
            os.system(load_data_cmd)
            print 'loaded fixture with secret api key'
        except Exception, err:
            print 'Error while loading fixture with secret api key: ', err

    if len(sys.argv) == 1:
        print 'I need a root directory as input'
        sys.exit(0)
    else:
        my_root_dir = sys.argv[1]
        print 'starting from directory ', my_root_dir
    client = Client()
    secret_obj = Secret.objects.get(pk = 1)  
    secret = secret_obj.value
    api_key = secret_obj.application.api_key
    user_id = secret_obj.user.pk
    
    #metadata_dict = {'namespace':'dc',  'name':'title',  'value': 'test',  'lang': 'en', }
    workspace = Workspace.objects.get(name = WORKSPACE_NAME) 
    params_a = {'workspace_id':workspace.pk, 'media_type': MEDIA_TYPE}
    params_a = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = params_a)                
    allimages = []
    subfiles = []
    badfiles = []
    current_keyword = ''
    keywords_list_history = {}
    keywords_list = []
    for (path,dirs,files) in os.walk(my_root_dir):
        print 'path: ', path
        print 'dirs: ', dirs
        print 'files: ', files
        print 'basename of path: ', os.path.basename(path)
        if os.path.basename(path) != current_keyword:
            current_keyword = os.path.basename(path)
            all_ks = path.split('/')
            print 'list of keywords for each file in files is: ', all_ks
            if len(all_ks) >= 2:
                print '\ncreate new keyord ',current_keyword, ' inside ', all_ks[-2], '\n'
            
        for f in files:
            try:
                mtype = guess_media_type(f)
                mime_type = mimetypes.guess_type(f)[0]

                print 'f is: ', f, ' type of f is: ', type, 'mime type is: ', mime_type
                if mtype == 'image':
                    #allimages.append(os.path.join(path,f))
                    print 'call uploading for this file'

                    
                    params = {'workspace_id': workspace.pk, 'media_type': mime_type}
                    params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = params)        
                    #print '\n api item new - params: ', params
                    try:
                        response = client.post('/api/item/new/', params,)
                    except Exception, err:
                        print 'Could not create new item: ', err
                        continue
                    i_resp_dict = json.loads(response.content)
                    print '\napi item new -  i_resp_dict: ', i_resp_dict
                    new_item = Item.objects.get(pk = i_resp_dict['id'])
                    new_item_id = i_resp_dict.get('id')

                    print '\n***\n- Uploading content file for new item just created'
                    try:
                        input_file = open(os.path.join(path,f))
                    except IOError, err:
                        print 'error while opening input file: ', err
                    if input_file == None:
                        print 'file  is None!'
                        continue
                    upload_params = {}
                    upload_params['rendition_id'] = 1
                    upload_params['files_to_upload'] = input_file
                    upload_params['workspace_id'] = workspace.pk
                    upload_params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = upload_params)        
                    print '\n api item upload - params: ', upload_params
                    print '\n api item upload - no response is expected.'
                    try: 
                        upload_response = client.post('/api/item/%s/upload/'% new_item_id, upload_params )            
                    except Exception, err:
                        print 'error while uploading input file: ', err
                        continue

                    # now wait until uploading processes have completed
                    #processes = ws.get_active_processes()
                    #for i,p in enumerate(processes):
                    #    while p.is_completed() == 0:
                    #        p = Process.objects.get(pk = p.pk)
                    #        print 'i= ',i,'*** process ', p, ' is completed?', p.is_completed(), ' pk ', p.pk
                    #       sleep(2)
                    #    if p.is_completed():
                    #        print 'uploading was completed'



                    file_keywords = path.split('/')
                    print 'keywords for this file are: ', file_keywords
                    metadata_dict = {'dc_description':{'it-IT':path}, 'dc_subject': file_keywords}
                    m_params = _get_final_parameters(api_key = api_key, secret = secret, user_id = user_id, kwargs = {'metadata':json.dumps(metadata_dict)})        
                    m_response = ''
            
                    try:
                        m_response = client.post('/api/item/%s/set_metadata/'% new_item_id,m_params,)
                    except Exception, err:
                        print 'error in api set_metadata: ', err
                        continue





                    #if (path != my_root_dir): # I am in a subdirectory
                    #    subfiles.append(os.path.join(path, f))
            except Exception, err:
                badfiles.append(os.path.join(path, f))
                print 'Error:' , err
                continue
                   
        
