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
from django.template import RequestContext
from django.views.generic.simple import redirect_to
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseForbidden

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import simplejson
from django.contrib.admin.views.decorators import staff_member_required

from dam.repository.models import Item, _get_resource_url, Component
from dam.workspace.models import DAMWorkspace as Workspace
from dam.settings import EMAIL_SENDER, SERVER_PUBLIC_ADDRESS
from dam.application.forms import Registration
from dam.application.models import VerificationUrl

from dam.core.dam_workspace.decorators import permission_required

from mediadart.storage import Storage

import logger

NOTAVAILABLE = None
  
def home(request, msg=None):
    """
    Always redirect user from http://host/ to http://host/workspace
    """
    return redirect_to(request, '/workspace/')

def do_login(request):
    """
    Manage user login
    """
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return home(request)
        else:
            return home(request, "User disabled.")
    else:
        return HttpResponseForbidden("User or/and password wrong. Please check and try again.")

@login_required
def do_logout(request):
    """
    User logout
    """
    logout(request)
    if request.session.__contains__('workspace'):
        request.session.__delitem__('workspace')
    return home(request)

@login_required
def redirect_to_resource(request, id):
    """
    Redirects to the resource url given by MediaDART
    """

    try:
        url = _get_resource_url(id)
    except:
        url = NOTAVAILABLE

    return redirect_to(request,  url)


@login_required
def resources(request, component_id, workspace_id):
    
    try:
        component = Component.objects.get(pk = component_id)
        workspace = component.workspace.get(pk = workspace_id)
    except:
        return HttpResponseNotFound()    
    
    
    if request.user not in workspace.members.all():
        return HttpResponseForbidden()
         
    url = component.get_component_url()    
    return redirect_to(request, url)

@login_required
def get_component(request, item_id, variant_name, redirect=False):
    """
    Looks for the component named variant_name of the item item_id in the given workspace
    """
    workspace = request.session.get('workspace', None) 
    
    try:
        item = Item.objects.get(pk=item_id)
        variant = workspace.get_variants().distinct().get(name = variant_name)
        url = item.get_variant(workspace, variant).get_component_url()
    except Exception,  ex:
        logger.exception(ex)
        return HttpResponse(simplejson.dumps({'failure': True}))

    if redirect:
        return redirect_to(request, url)
    else:
        return HttpResponse(url)

@login_required
def redirect_to_component(request, item_id, variant_name,  ws_id = None):
    """
    Redirects to the component url
    """
    url = get_component(request, item_id, variant_name, True)    
    return url

def registration(request):
    """
    Creates registration form or saves registration info
    """

    def save_user_and_login(form):
        form.save(commit = True)
        user = authenticate(username = form.cleaned_data['username'], password =  form.cleaned_data['password1'])
        login(request,  user)
        ws = Workspace.objects.create_workspace(user.username, '', user)
        return user

    if request.method == 'POST': 
        form = Registration(request.POST) 

        if form.is_valid():
            user = save_user_and_login(form)
#            user = form.save()
#            user.is_active = True
#            user.save()
#            url = VerificationUrl.objects.create(user = user).url
#            final_url = 'http://%s/confirm_user/%s/'%(SERVER_PUBLIC_ADDRESS , url)

#            send_mail('Registration confirmation', 'Hi %s,\nclick at this url %s \n to confirm your registration at DAM.'%(user.username, final_url), EMAIL_SENDER, [user.email], fail_silently=False)

            resp = simplejson.dumps({'success': True, 'errors': []})
            return HttpResponse(resp)

        else:
            from django.template.defaultfilters import striptags
            errors = []
            for field in form:
                if field.errors:
                    errors.append(striptags(field.errors))

            resp = simplejson.dumps({'success': False, 'errors': errors})
            return HttpResponse(resp)
    else:

        form = Registration()

    return render_to_response('registration.html', RequestContext(request,{'form': form }))

def confirm_user(request, url):
    """
    Confirms user registration and creates a new workspace for the new user
    """


    user = VerificationUrl.objects.get(url= url).user
    user.is_active = True
    user.save()
    logout(request)

    ws = Workspace.objects.create_workspace(user.username, '', user)

    return render_to_response('registration_completed.html', RequestContext(request,{'usr':user}))
    
@login_required
def download_component(request, item_id, variant_name):
    from django.views.static import serve
    from settings import MEDIADART_STORAGE
    
    workspace = request.session.get('workspace', None)
    try:
        item = Item.objects.get(pk=item_id)
        variant = workspace.get_variants().distinct().get(name = variant_name)
        comp = item.get_variant(workspace, variant)

        path = comp._id

    except Exception,  ex:
        logger.exception(ex)
        return HttpResponseNotFound()
    
    
    
    response = serve(request, path, document_root = MEDIADART_STORAGE)
    
    if variant_name == 'original':
        file_name = comp.file_name
    else:
        
        orig = comp.source
        try:
            tmp = orig.file_name.split('.')
            file_name = tmp[0] + '_' +  variant_name + '.' + comp.format
        except:
            file_name = 'resource_' + variant_name   
        
    response['Content-Disposition'] = 'attachment; filename=%s'%file_name
    return response
    
    