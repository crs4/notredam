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


from dam.workspace.models import Workspace
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth.models import User

def membership_required(func):
    def check(request, *args, **kwargs):			
        user =  User.objects.get(pk = request.session['_auth_user_id'])
        ws_id = args[0]
        if not user.workspaces.filter(pk = ws_id).count():
            return HttpResponseForbidden('403 Forbidden: membership required!')
        
        return func(request, *args, **kwargs)
    return check

def permission_required(permission,  ws_in_session = True):	
    def check_call(func):
        		
        def check(request, *args, **kwargs):	
            if ws_in_session:
                workspace = request.session.get('workspace', None)
                if workspace == None:
                    return Exception('no workspace passed')

            else:
                if kwargs.has_key('ws_id'):
                    ws_id = kwargs['ws_id']
                    
                elif request.POST.__contains__('ws_id'):
                    
                    ws_id = request.POST['ws_id']
                    
                else:
                    
                    raise Exception('no workspace passed')
                workspace = Workspace.objects.get(pk = ws_id)
            
            user =  User.objects.get(pk = request.session['_auth_user_id'])			
            if user.workspacepermissionassociation_set.filter(Q(workspace = workspace),  Q(permission__codename = 'admin') | Q(permission__codename = permission)).count() > 0 or user.workspacepermissionsgroup_set.filter(Q(workspace = workspace),  Q(permissions__codename = 'admin') | Q(permissions__codename = permission)).count() > 0:
            	return func(request, *args, **kwargs)
            else:
            	return HttpResponseForbidden('403 Forbidden: you have no permission to access this page!')

        return check
    
    return check_call

	
	
		
