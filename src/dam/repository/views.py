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
from operator import and_, or_
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from dam.settings import MEDIADART_CONF

from dam.repository.models import Item, Component
from dam.workspace.models import Workspace
from dam.workspace.decorators import permission_required

import logger
from django.utils import simplejson

@login_required
@permission_required('remove_item')
def check_item_wss(request):
    """
    Check if items are owned by more than one workspace
    """
    
    items_id = request.POST.getlist('item_id')
    items_commas = items_id[0].split(',')

    if len(items_commas) > 1:
        items_id = items_commas

    multiple_ws = False

    for item in items_id:
        try:
            i = Item.objects.get(pk=item)
        except:
            continue
        if i.workspaces.all().count() > 1:
            multiple_ws = True
            break

    return HttpResponse(simplejson.dumps({'success': True, 'multiple_ws': multiple_ws}))


@login_required
@permission_required('remove_item')
def delete_item(request):
    """
    Deletes an item from the current workspace or from all workspaces where the user is a member: these options are sent via request.POST
    """
    cw = request.session['workspace']
    user = User.objects.get(pk=request.session['_auth_user_id'])
    
    items_id = request.POST.getlist('item_id')
    items_commas = items_id[0].split(',')

    if len(items_commas) > 1:
        items_id = items_commas

    logger.debug('items_id %s' %items_id)
        
    choose = request.POST.get('choose')
    inbox_deleted = None
    
    if choose == 'current_w':
        for item in items_id:
            i = Item.objects.get(pk=item)
            i.workspaces.remove(cw)
            components = Component.objects.filter(item__pk=i.pk,workspace__pk=cw.pk)
            for c in components:
                c.workspace.remove(cw)
                
                if c.workspace.all().count() == 0:
                    c.delete()

            inboxes = i.node_set.filter(type = 'inbox',  workspace = cw) #just to be sure, filter instead of get
            for inbox in inboxes:
            
                inbox.items.remove(i)
                
                if inbox.items.count() == 0:
                    inbox_deleted = inbox.parent.label            
                    inbox.delete()
                
            if i.workspaces.all().count() == 0:
                components = Component.objects.filter(item=i)
                for c in components:
                    c.delete()
                i.delete() 
                
    elif choose == 'all_w':
        q1 = Workspace.objects.filter( Q(workspacepermissionassociation__permission__codename = 'admin') | Q(workspacepermissionassociation__permission__codename = 'remove_item'), members = user,workspacepermissionassociation__users = user)
        q2 =  Workspace.objects.filter(Q(workspacepermissionsgroup__permissions__codename = 'admin') | Q(workspacepermissionsgroup__permissions__codename = 'remove_item'), members = user, workspacepermissionsgroup__users = user)
        wss = reduce(or_, [q1,q2])
        logger.debug('wss %s'%wss)

        for item in items_id:
            i = Item.objects.filter(pk=item)[0]
            for w in wss:
                if i in w.items.all():
                    try:
                        w.items.remove(i)
                    except Exception,e:
                        logger.debug( "errore eliminazione %s" % e )
                        pass

    
            if i.workspaces.all().count() == 0:
                components = Component.objects.filter(item=i)
                for c in components:
                    c.delete()
                i.delete() 
            
    if inbox_deleted:
        return HttpResponse(simplejson.dumps({'inbox_to_reload': inbox_deleted,  'success': True}))
    else:
        return HttpResponse(simplejson.dumps({'success': True}))
