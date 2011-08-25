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
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from dam.workflow.models import State, StateItemAssociation
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item
from dam.core.dam_workspace.decorators import permission_required

def _set_state(items,state):
    
    for item in items:
        try:
            sa = StateItemAssociation.objects.get(item=item)
            sa.state = state
            sa.save()
        except StateItemAssociation.DoesNotExist:
            sa = StateItemAssociation.objects.create(state=state, item=item)

@login_required
@permission_required('set_state')
def set_state(request):
    workspace = request.session['workspace']
    item_ids = request.POST.getlist('item_id')
    items = Item.objects.filter(pk__in = item_ids)
    state = State.objects.get(pk = request.POST['state_id'])
    
    _set_state(items, state)
    return HttpResponse(simplejson.dumps({'success': True}))

@login_required
def get_states(request):
    workspace = request.session['workspace']
    states = State.objects.filter(workspace = workspace)
    states_resp = []
    for state in states:
        states_resp.append({'pk': state.pk,  'name':  state.name})
    resp = {'success': True,  'states': states_resp}
    return HttpResponse(simplejson.dumps(resp))

@login_required
@permission_required('admin')
def save_states(request):
    workspace = request.session['workspace']
    states = simplejson.loads(request.POST['states'])
    existing_states = []
    for s in states:
        if s['pk']:
            state = State.objects.get(pk = s['pk'])
            if state.name != s['name']:
                state.name = s['name']
                state.save()                
        else:
            state = State.objects.create(name = s['name'], workspace = workspace)          
                    
        existing_states.append(state.pk)    
    
    return HttpResponse(simplejson.dumps({'success': True}))
