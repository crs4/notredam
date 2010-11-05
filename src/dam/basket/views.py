
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
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from dam.basket.models import Basket
from dam.repository.models import Item

from dam import logger

@login_required
def reload_item(request):
    """
    Add items to the current user basket
    """

    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace = request.session['workspace']
        items_post = request.POST.getlist('items')
        logger.debug('items_post %s'%items_post)

        basket = Basket.get_basket(user, workspace)
        items = Item.objects.filter(pk__in=items_post)     
        logger.debug('items %s'%items)
        logger.debug('basket.items %s'%Basket.objects.all())  
        basket.add_items(items)
	
    except Exception,  ex:
        logger.exception(ex)
        raise ex

    return HttpResponse(basket.items.all().count())

@login_required
def remove_from_basket(request):
    """
    Remove items from the current user basket
    """

    try:
        items_post = request.POST.getlist('items')

        items = Item.objects.filter(pk__in=items_post)       
 	
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace = request.session['workspace']

        basket = Basket.get_basket(user, workspace)
        basket.remove_items(items)

        count = basket.get_size()

    except Exception,  ex:
        count = 0
        logger.exception(ex)
        raise ex

    return HttpResponse(count)
 
@login_required
def clear_basket(request):
    """
    Empty the basket for the current user  
    """
    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        workspace = request.session['workspace'] 	
        
        Basket.empty_basket(user, workspace)
        
    except Exception,  ex:
        logger.exception(ex)
        raise ex

    return HttpResponse(0)

@login_required
def basket_size(request):
    """
    Return size of the current user basket
    """
    user = User.objects.get(pk=request.session['_auth_user_id'])
    workspace = request.session['workspace']

    basket = Basket.get_basket(user, workspace)
    
    count = basket.get_size()

    return HttpResponse(count)



