
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

"""
Views used for basket functionalities
"""

from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Q

from dam.basket.models import Basket
from dam.repository.models import Item

import logger

@login_required
def reload_item(request):
    """
    Add items to the current user basket
    """

    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace = request.session['workspace']
        items_post = request.POST.getlist('items')
        for i in items_post:
            item = Item.objects.get(pk=i)
            Basket.objects.get_or_create(user=user, item=item, workspace=workspace)
	
    except Exception,  ex:
        logger.exception(ex)
        raise ex

    return HttpResponse(Basket.objects.all().count())

@login_required
def remove_from_basket(request):
    """
    Remove items from the current user basket
    """

    try:
        items_post = request.POST.getlist('items')
 	
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace = request.session['workspace']

        for item in items_post :
            Basket.objects.get(user=user, item__pk=item, workspace=workspace).delete()
	
    except Exception,  ex:
        logger.exception(ex)
        raise ex

    return HttpResponse(Basket.objects.filter(user=user, workspace=workspace).count())
 
@login_required
def clear_basket(request):
    """
    Empty the basket for the current user  
    """
    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace = request.session['workspace'] 	
        all_b = Basket.objects.filter(user=user, workspace=workspace)
        all_b.delete()
        
    except Exception,  ex:
        logger.exception(ex)
        raise ex

    return HttpResponse(Basket.objects.all().count())

@login_required
def basket_size(request):
    """
    Return size of the current user basket
    """
    user = User.objects.get(pk=request.session['_auth_user_id'])
    workspace = request.session['workspace']

    return HttpResponse(Basket.objects.filter(user=user, workspace=workspace).count())

def __inbasket(user,item,workspace):
    """
    Check if the given item is in basket
    """

    try:

        if Basket.objects.filter(user=user, item=item, workspace=workspace).count()== 0 :
            return 0
	
    except Exception,  ex:
        logger.exception(ex)
        return 0	

    return 1


