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

from dam.eventmanager.models import Event

@login_required
def get_events(request):
    workspace = request.session.get('workspace')
    
    resp = {'events':[]}
    for event in Event.objects.filter(Q(workspace = workspace)| Q(workspace__isnull = True)):
        resp['events'].append({'name': event.name})
    
    return HttpResponse(simplejson.dumps(resp)) 