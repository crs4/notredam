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

from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from dam.repository.models import Item, Component, Watermark
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.decorators import permission_required
from dam.treeview.models import Node

import logging
logger = logging.getLogger('dam')

import settings
from operator import and_, or_

@login_required
@permission_required('remove_item')
def check_item_wss(request):
    """
    Check if items are owned by more than one workspace
    """
    
    items_id = request.POST.getlist('item_ids')

    multiple_ws = False

    for item in items_id:
        try:
            i = Item.objects.get(pk=item)
        except:
            continue
        if i.get_workspaces_count() > 1:
            multiple_ws = True
            break

    return HttpResponse(simplejson.dumps({'success': True, 'multiple_ws': multiple_ws}))

@login_required
@permission_required('remove_item')
def delete_item(request):
    """
    Delete an item from the current workspace or from all workspaces 
    where the user is a member: these options are sent via request.POST
    """

    cw = request.session['workspace']
    user = User.objects.get(pk=request.session['_auth_user_id'])
    
    items_id = request.POST.getlist('item_ids')
        
    choose = request.POST.get('choose')

    inbox_deleted = None

    if choose == 'current_w':
        workspaces = [cw]

        try:        
            inbox = Node.objects.get(type = 'inbox',  workspace = cw) #just to be sure, filter instead of get

            if inbox.items.count() == 0:
                if inbox.parent:
                    inbox_deleted = inbox.parent.label
                inbox.delete()

        except:
            pass

    else:
        workspaces = None

    for item in items_id:
        i = Item.objects.get(pk=item)
        i.delete_from_ws(user, workspaces)
                
    return HttpResponse(simplejson.dumps({'inbox_to_reload': inbox_deleted,  'success': True}))

@login_required
def get_watermarks(request):
    workspace = request.session.get('workspace')
    watermarks = Watermark.objects.filter(workspace = workspace)
    logger.debug('watermarks %s' %watermarks)
    resp = {'watermarks':[]}
    for watermark in watermarks:
        resp['watermarks'].append({'id': watermark._id, 'file_name': watermark.file_name, 'url' : watermark.get_url()})
        logger.debug(watermark)
    
    return HttpResponse(simplejson.dumps(resp))

@login_required
def delete_watermark(request):
    watermark_id = request.POST['watermark']
    try:
        Watermark.objects.get(_id = watermark_id).delete()
    except Watermark.DoesNotExist:
        pass
        
    return HttpResponse(simplejson.dumps({'success': True}))  

def get_variant_url(request, item_ID, variant_name):
    from mprocessor.storage import Storage
    from django.views.generic.simple import redirect_to
    
    try:
        workspace = request.session['workspace']
        storage = Storage()
        
        try:
            component = Component.objects.get(item___id = item_ID, workspace = workspace, variant__name = variant_name)
            url =  component.get_url()
                        
        except Component.DoesNotExist, ex:
            return HttpResponseNotFound()
            
#        if not url:
#            url = settings.INPROGRESS
        logger.debug('url %s'%url)
        return redirect_to(request, url)
    except Exception, ex:
        logger.exception(ex)
        raise ex 
    
    
#@login_required
def get_resource(request, resource_name):
    from django.views.static import serve
    from settings import MPROCESSOR_STORAGE
    download = request.GET.get('download')
    response = serve(request, resource_name, document_root = MPROCESSOR_STORAGE)
    if download: # downloading of single resources from subpanel on the right   
        # the following is to provide a resource name other than the one in repository
        comp = Component.objects.filter(uri = resource_name)
        original_file_name = comp[0].item.get_file_name()
        variant_name = comp[0].variant.name
        download_file_name = original_file_name.replace('.', ('_' + variant_name + '.'))
        #logger.info('download file name inside get_resource: %s' % resource_name)
        response['Content-Disposition'] = 'attachment; filename=%s'%download_file_name
        
    
    return response

@login_required
def get_resource_uri(request, item_id, variant_name):	
    workspace = request.session.get('workspace')
    item = Item.objects.get(_id = item_id, workspaceitem__workspace = workspace)
    component = Component.objects.get(item = item, variant__name = variant_name)
    return HttpResponse(component.uri)
