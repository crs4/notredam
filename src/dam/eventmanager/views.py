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
from django.contrib.contenttypes.models import ContentType

from dam.eventmanager.models import Event, EventRegistration
 
@login_required
def set_script_associations(request):
    workspace = request.session.get('workspace')
    event_id = request.POST['event_id']
    script_id = request.POST.getlist('script_id')
    scripts = Script.objects.filter(pk__in = script_id)
    event = Event.objects.get(pk = event_id) 
    EventRegistration.objects.filter(event = event, workspace = workspace).delete()
    for script in scripts:
        
        EventRegistration.objects.create(event = event, listener = script, workspace = workspace)
    
    return HttpResponse(simplejson.dumps({'success': True})) 
    

@login_required
def get_event_scripts(request):
    workspace = request.session.get('workspace')
    event_id = request.POST['event_id']
    event = Event.objects.get(pk = event_id) 
    workspace = request.session.get('workspace')
    resp = {'scripts':[]}
    script_ctype = ContentType.objects.get_for_model(Script)
    event_regs = EventRegistration.objects.filter(event = event, content_type = script_ctype, workspace = request.session.get('workspace'))
    for event_reg in event_regs:
        resp['scripts'].append({'id': event_reg.listener.pk, 'name': event_reg.listener.name})
    
    return HttpResponse(simplejson.dumps(resp))

    
