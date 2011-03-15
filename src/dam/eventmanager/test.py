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

from dam.workflow.models import State
from dam.eventmanager.models import EventManager

from django.http import HttpResponse

import time


def register(request,event_type ):
	em = EventManager.objects.all()[0]
	ticket = em.register('evento@%s' % time.time(), event_type, 'dam.eventmanager.test')
	return HttpResponse(str(ticket))

def makeithappen(request,event_type):
	em = EventManager.objects.all()[0]
	l = em.notify(event_type, a='a',aNumber=1238923,name='ciccio',tupla=(1,2,3))
	
	return HttpResponse(str(l))
	
def notify(**kwargs):
	State.objects.create(name="SUCCESS")
	#raise Exception, kwargs
