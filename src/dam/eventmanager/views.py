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


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import simplejson
from django.db.models import Q

from dam.eventmanager.models import Event, EventRegistration
from dam.scripts.models import Script

@login_required
def get_events(request):
    workspace = request.session.get('workspace')
    
    resp = {'events':[]}
    for event in Event.objects.filter(Q(workspace = workspace)| Q(workspace__isnull = True)):
        resp['events'].append({'id': event.pk, 'name': event.name})
    
    return HttpResponse(simplejson.dumps(resp))
 
@login_required
def set_script_associations(request):
    workspace = request.session.get('workspace')
    event_id = request.POST['event_id']
    script_id = request.getlist('script_id')
    scripts = Script.objects.filter(pk__in = script_id)
    event = Event.objects.get(pk = event_id) 
    for script in scripts:
        EventRegistration.objects.filter(event = event, workspace = workspace).delete()
        EventRegistration.objects.create(event = event, listener = script, workspace = workspace)
    
    return HttpResponse(simplejson.dumps({'success': True})) 
    
    
    
    