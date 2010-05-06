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

from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from dam.scripts.models import *
from dam.framework.dam_repository.models import Type

@login_required
def get_actions(request):    
    actions = {'actions':[]}    
    
    for action in BaseAction.__subclasses__():
      
            
            actions['actions'].append({                                
                    'name':action.__name__.lower(),
                    'media_type': action.media_type_supported,
                    'parameters': action.required_parameters                    
            })
                
    return HttpResponse(simplejson.dumps(actions))
                 