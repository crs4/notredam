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

from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from dam.repository.models import Item, Component
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.decorators import permission_required
from dam.treeview.models import Node

import logger
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
