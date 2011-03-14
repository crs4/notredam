# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext 
from django.http import HttpResponse
from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login, logout
from django.views.generic.simple import redirect_to


from django.contrib.auth.decorators import login_required
from settings import NOTREDAM_ADDRESS, SECRET,  API_KEY, USER_ID, MAIN_WORKSPACE_ID,  ORIGINAL_VARIANTS, TAGS_NODE_ID
import hashlib
import urllib
from django.utils import simplejson
from base.models import *
from httplib import HTTP
import os

import mimetypes


def get_final_parameters(kwargs = None):
    "add api_key user_id and secret"
    if  not kwargs:
        kwargs = {}
    
    if isinstance(kwargs, dict):
         kwargs['api_key'] = API_KEY
         kwargs['user_id'] = USER_ID
         kwargs = kwargs.items()
    else:
        kwargs.append(('api_key', API_KEY))
        kwargs.append(('user_id', USER_ID))
        
    to_hash = SECRET
    parameters = []
    
    print('kwargs %s'%kwargs)
    for key,  value in kwargs:
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
    kwargs.append(('checksum', hashed_secret)) 
    return kwargs
        
@login_required
def home(request):
    return render_to_response('home.html', RequestContext(request,{}))
    
    
@login_required
def download_item(request):
    item_id = request.POST['item_id']
    params = [('variants', 'original'), ('variants_workspace', MAIN_WORKSPACE_ID)]
    
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/get/?%s"%(NOTREDAM_ADDRESS, item_id, params))
    resp = f.read()
    json_resp = simplejson.loads(resp)
    url = json_resp['variants']['original']['url']
    url =  os.path.join(url, 'download/')
    final_resp = simplejson.dumps({'url':url})
    return HttpResponse(final_resp)

@login_required
def on_view(request):
    item_id = request.POST['item_id']
    media_type = request.POST['media_type']
    
    if media_type == 'image':
        variant = 'fullscreen'
    else:
        variant = 'preview'
    
    params = [('variants', variant), ('variants_workspace', MAIN_WORKSPACE_ID)]
    
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/get/?%s"%(NOTREDAM_ADDRESS, item_id, params))
    resp = f.read()
    print resp
    json_resp = simplejson.loads(resp)
    media_type = json_resp['media_type']
    url = json_resp['variants'][variant]['url']
    title = json_resp['metadata']['dc_title']['en-US']
    final_resp = {'url':url, 'title':title, 'media_type':media_type}
    if json_resp['metadata'].has_key('dc_description'):
        description = json_resp['metadata']['dc_description']['en-US']
        final_resp['description'] = description
    final_resp = simplejson.dumps(final_resp)
    return HttpResponse(final_resp)
    
    
    
@login_required
def load_items(request,  media_type):
    
    
    query  = request.POST.get('query', '')
    rating = request.POST.get('rating')
    start =  request.POST.get('start')
    limit = request.POST.get('limit')
    params = [
              ('media_type', media_type), 
              ('variants', 'thumbnail'),              
               ('order_by', 'dc_title'), 
               ('metadata', 'xmp_rating'), 
               ('metadata', 'dc_title'),  
               ('metadata',  'notreDAM_UploadedBy'),
#               ('state',  'published'),               
               ]
    
    if start and limit:
        params.append(('start', start))
        params.append(('limit', limit))
      
    tmp_query = ''
    if rating and float(rating) > 0:

            tmp_query = ' xmp:rating=%s'%(float(rating))
              
    
    query += tmp_query
    if query:        
        params.append(('query', query))
        
    
    
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/workspace/%s/search/"%(NOTREDAM_ADDRESS, MAIN_WORKSPACE_ID), params)
    resp = f.read()
    print 'resp %s'%resp
#    json_resp = simplejson.loads(resp)
    return HttpResponse(resp)


@login_required
def set_metadata(request):
    item_id = request.POST['id']
    metadata = request.POST['metadata']
    metadata = simplejson.loads(metadata)
    
    
    metadata_to_send = {}
    print metadata
    for m in metadata:
        metadata_to_send[m['metadata_schema']] = {'en-US': m['value']}
    
    metadata_to_send = simplejson.dumps(metadata_to_send)
    params = {'metadata': metadata_to_send, 'workspace_id': MAIN_WORKSPACE_ID}
    
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/set_metadata/"%(NOTREDAM_ADDRESS, item_id), params)
    resp = f.read()
    print resp
    
    
        
    
    return HttpResponse(simplejson.dumps({'success': True}))
    
    
@login_required
def get_metadata(request):
    item_id = request.POST['id']
    params = get_final_parameters({})
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/get/?%s" % (NOTREDAM_ADDRESS, item_id,  params))
    resp = f.read()
    print resp
    json_resp = simplejson.loads(resp)
    metadata = json_resp['metadata']
    try:
        title = metadata['dc_title']['en-US']
    except:
        title =  ''
    try:
        description= metadata['dc_description']['en-US']
    except:
        description = ''
    
    
    rating = metadata.get('xmp_rating',  '')
    upload_date = metadata.get('notreDAM_UploadedOn',  '')
    uploader = metadata.get('notreDAM_UploadedBy',  '')
    user = User.objects.get(pk=request.session['_auth_user_id'])
    username = user.username
    final_resp = simplejson.dumps({'metadata':[{'metadata':'title', 'value': title, 'metadata_schema': 'dc_title', 'editable': username == uploader}, 
                                               {'metadata': 'description', 'value': description, 'metadata_schema': 'dc_description', 'editable': username == uploader},
                                               {'metadata': 'upload date', 'value': upload_date, 'metadata_schema': 'notreDAM_UploadedOn', 'editable': False},
                                               {'metadata': 'uploaded by', 'value': uploader, 'metadata_schema': 'notreDAM_UploadedBy', 'editable': False},
                                               {'metadata': 'rating', 'value': rating, 'metadata_schema': 'xmp_Rating', 'editable': False},
                                               ]
    
    })
    
    return HttpResponse(final_resp)

@login_required
def save_rating(request):
    value = int(request.POST['rating'])
    item_id = request.POST['item_id']
    rating = Rating.objects.filter(dam_id = item_id)
    user = User.objects.get(pk=request.session['_auth_user_id'])
    
    
    if rating.count() == 0:
        rating = Rating(dam_id = item_id, value = 0, number_of_votes = 0)
    else:
        rating = rating[0]
        if user in rating.users.all():
            return HttpResponse(simplejson.dumps({'success': True, 'already_voted': True}))
    
    
    new_numbers_of_votes = rating.number_of_votes + 1
    new_value = float(rating.value*rating.number_of_votes + value)/(new_numbers_of_votes)
    new_value = new_value
    rating.value = new_value
    rating.number_of_votes = new_numbers_of_votes
    rating.save()
    rating.users.add(user)
    
    
    metadata_value = simplejson.dumps({'xmp_rating':str(float(round(rating.value)))})
    
    
    
    params = {'metadata': metadata_value, 'workspace_id':MAIN_WORKSPACE_ID}
    
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/set_metadata/"%(NOTREDAM_ADDRESS, item_id), params)
    resp = f.read()
    print 'resp ', resp
    return HttpResponse(simplejson.dumps({'success': True}))

@login_required
def do_logout(request):
    """
    User logout
    """
    logout(request)
    if request.session.__contains__('workspace'):
        request.session.__delitem__('workspace')
    return redirect_to(request, '/')
@login_required
def get_upload_url(request):
    file_name = request.POST['file_name']
    file_size = request.POST['file_size']
    media_type = guess_media_type(file_name)
    
    params = {'workspace_id':MAIN_WORKSPACE_ID,  'media_type':media_type}
    
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    
    f = urllib.urlopen("http://%s/api/item/new/"%(NOTREDAM_ADDRESS), params)
    resp = f.read()
    json_resp = simplejson.loads(resp)
    item_id = json_resp['id']
    variant_id = ORIGINAL_VARIANTS[media_type]
    
    
    params = {'file_name': file_name,  'fsize': file_size,  'variant_id':variant_id, 'workspace_id':MAIN_WORKSPACE_ID, }
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/upload/"%(NOTREDAM_ADDRESS,  item_id), params)
    resp = f.read()
    json_resp = simplejson.loads(resp)
    json_resp ['item_id'] = item_id
    final_resp = simplejson.dumps(json_resp)
     
    return HttpResponse(final_resp )
    
@login_required
def upload_finished(request):
    item_id = request.POST['item_id']
    title = request.POST['metadata_1']
    description = request.POST.get('metadata_2',  '')
    user = User.objects.get(pk=request.session['_auth_user_id'])    
    metadata = {'dc_description': {'en-US':description},  'dc_title': {'en-US': title},  'notreDAM_UploadedBy':user.username}
    params = {'workspace_id':MAIN_WORKSPACE_ID,  'metadata': simplejson.dumps(metadata)}
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/set_metadata/"%(NOTREDAM_ADDRESS,  item_id), params)
    
    params = {'workspace_id':MAIN_WORKSPACE_ID,  'state': 'uploaded'}
    params = get_final_parameters(params)
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/set_state/"%(NOTREDAM_ADDRESS,  item_id), params)
    resp = f.read()
    
    return HttpResponse('')
    

def guess_media_type (file):

    mimetypes.add_type('video/flv','.flv')
    mimetypes.add_type('video/ts','.ts')
    mimetypes.add_type('video/mpeg4','.m4v')
    mimetypes.add_type('doc/pdf','.pdf')
    mimetypes.add_type('image/nikon', '.nef')
    mimetypes.add_type('image/canon', '.cr2')
    mimetypes.add_type('image/digitalnegative', '.dng')
    media_type = mimetypes.guess_type(file)
    try:
        media_type = media_type[0][:media_type[0].find("/")]
    
        if media_type not in ['image',  'audio', 'video',  'doc']:
            raise Exception
            
    except Exception, ex:
        media_type = 'media_type sconociuto'
        
        raise Exception('unsupported media type')

    print('media type %s'%media_type)
    return media_type


@login_required
def get_tags(request):
    params = get_final_parameters({})
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/keyword/%s/get/?%s"%(NOTREDAM_ADDRESS,  TAGS_NODE_ID, params))
    resp = f.read()
    print resp
    json_resp = simplejson.loads(resp)
    final_resp = {'tags': json_resp['children']}
    final_resp  = simplejson.dumps(final_resp)
    return HttpResponse(final_resp)
    
@login_required
def get_item_tags(request):
    item_id = request.POST['id']
    params = get_final_parameters({'workspace_id':MAIN_WORKSPACE_ID, 'parent': TAGS_NODE_ID})
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/get_keywords/?%s"%(NOTREDAM_ADDRESS, item_id, params))
    resp = f.read()
    print resp
    
    return HttpResponse(resp)
    

@login_required
def add_tag(request):
    item_id = request.POST['id']
    label = request.POST['label']
    metadata_schema = simplejson.dumps([{"namespace": 'dublin core','name': 'subject', "value": label}])
    
    params = get_final_parameters({ 'label': label, 'parent_id': TAGS_NODE_ID, 'type': 'keyword', 'metadata_schema':metadata_schema, 'items': item_id })
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/keyword/new/"%(NOTREDAM_ADDRESS),params)
    resp = f.read()
    print resp
    
    return HttpResponse(resp)

@login_required
def edit_tag(request):
    item_id = request.POST['id']
    label = request.POST['label']
    metadata_schema = simplejson.dumps([{"namespace": 'dublin core','name': 'subject', "value": label}])
    
    params = get_final_parameters({ 'label': label, 'parent_id': TAGS_NODE_ID, 'type': 'keyword', 'metadata_schema':metadata_schema, 'items': item_id })
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/keyword/new/"%(NOTREDAM_ADDRESS),params)
    resp = f.read()
    print resp
    
    return HttpResponse(resp)
        
@login_required
def delete_tag(request):
    item_id = request.POST['id']
    node_id = request.POST['tag']
   
    
    params = get_final_parameters({ 'keywords': node_id})
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/remove_keywords/"%(NOTREDAM_ADDRESS, item_id),params)
    resp = f.read()
    print resp
    
    return HttpResponse(simplejson.dumps({'success': True}))
   
@login_required
def delete_item(request):
    item_id = request.POST['id']
     
    params = get_final_parameters({'workspace_id':MAIN_WORKSPACE_ID})
    params = urllib.urlencode(params)
    
    f = urllib.urlopen("http://%s/api/item/%s/delete_from_workspace/?%s"%(NOTREDAM_ADDRESS, item_id,params))
    resp = f.read()
    print resp
    
    return HttpResponse(simplejson.dumps({'success': True}))
        



