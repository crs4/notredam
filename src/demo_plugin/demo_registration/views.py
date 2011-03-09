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

from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader,  Template
from django.views.generic.simple import redirect_to
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.models import User, Permission
from django.utils import simplejson
from django.core.mail import EmailMessage

from dam.settings import EMAIL_SENDER, EMAIL_ADMIN
from dam.application.forms import Registration
from dam.workspace.models import Workspace

import os, datetime
import logger

def registration(request):
    """
    Creates registration form or saves registration info
    """
    #from dam.workspace.views import _create_workspace
    from dam.workspace.models import DAMWorkspace as Workspace

    def save_user(form):
        form.save(commit = True)
        user = User.objects.get(username=form.cleaned_data['username'])
        user.is_active = False

        add_ws_permission = Permission.objects.get(codename='add_workspace')
        user.user_permissions.add(add_ws_permission)

        user.save()
        #ws = Workspace(name=user.username)
        #_create_workspace(ws,  user)
        Workspace.objects.create_workspace(user.username, '', user)        
        return user

    if request.method == 'POST': 
        logger.debug('POST %s'%request.POST)
        form = Registration(request.POST) 

        if form.is_valid():
            user = save_user(form)

            resp = simplejson.dumps({'success': True, 'errors': []})
            
            email = EmailMessage('Registration required', 'Hi Administrator,\n\nactive this account  %s.'%(user.username), 'NotreDAM <%s>' % EMAIL_SENDER,
            [EMAIL_ADMIN], [],
            headers = {'Reply-To': 'NotreDAM <%s>' % EMAIL_SENDER})
            email.send()
            return HttpResponse(resp)

        else:
            from django.template.defaultfilters import striptags
            errors = []
            for field in form:
                if field.errors:
                    errors.append(striptags(field.errors))

            resp = simplejson.dumps({'success': False, 'errors': errors})
            return HttpResponse(resp)

    return render_to_response('demo_registration.html', RequestContext(request))


@staff_member_required
def confirm_user(request):
    """
    Confirms user registration
    """

    ids = simplejson.loads(request.POST.get('obj_list'))
    for id in ids:
    
        user = User.objects.get(pk=id)
    
        user.is_active = True
        user.date_joined = datetime.datetime.today()
        user.save()
        email = EmailMessage('Registration confirmation', 'Hi %s,\n\nYour account has been created.\n\nVisit http://demo.notre-dam.org to login.\n\nRemember that your account will be automatically disabled after 10 days.'%(user.username), 'NotreDAM <%s>' % EMAIL_SENDER,
            [user.email], [],
            headers = {'Reply-To': 'NotreDAM <%s>' % EMAIL_SENDER})
        email.send()

    resp = simplejson.dumps({'success': True, 'errors': []})
    return HttpResponse(resp)

@staff_member_required
def disable_user(request):
    """
    Disable user
    """

    ids = simplejson.loads(request.POST.get('obj_list'))

    for id in ids:
    
        user = User.objects.get(pk=id)
    
        user.is_active = False
        user.save()
    
    resp = simplejson.dumps({'success': True, 'errors': []})
    return HttpResponse(resp)

@staff_member_required
def demo_admin(request):
    return render_to_response('demo_admin.html', RequestContext(request))

@staff_member_required
def get_user_list(request):
    data = {'elements':[]}
    users = User.objects.all()
    for s in users: 
        data['elements'].append({'id':s.id, 'name':s.username, 'is_staff': s.is_staff, 'is_active': s.is_active, 'email': s.email, 'first_name': s.first_name, 'last_name': s.last_name })
        
    return HttpResponse(simplejson.dumps(data))    

