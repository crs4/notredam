
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
 try:
 	user = User.objects.get(pk=request.session['_auth_user_id'])
	#user = User.objects.filter(username=str(username))[0]
	logger.debug('user %s'%user)
	workspace = request.session['workspace']
 	logger.debug('workspace %s'%workspace)	
	items_post = request.POST.getlist('items')
 	logger.debug('items post %s'%items_post)
	for i in range(len(items_post)) :
		items = Item.objects.filter(pk=items_post[i])[0]
		logger.debug('items %s'%items)
		logger.debug(Basket.objects.filter(user=user,item=items,workspace=workspace))
		if len( Basket.objects.filter(user=user,item=items,workspace=workspace))== 0 :
			bas = Basket(user=user,item=items,workspace=workspace)	
			logger.debug('bas %s'%bas)
			bas.save()
			logger.debug('salvato')	
		#else : 
		#	Basket.objects.filter(user=user,item=items,workspace=workspace)[0].delete()
		#	logger.debug('delitato')
	
 except Exception,  ex:
        logger.exception(ex)
        raise ex
 return HttpResponse(len(Basket.objects.all()))

@login_required
def remove_from_basket(request):
 try:
 	logger.debug('remove from basket') 
 	
 	user = User.objects.get(pk=request.session['_auth_user_id'])
	#user = User.objects.filter(username=str(username))[0]
	logger.debug('user %s'%user)
	workspace = request.session['workspace']
 	logger.debug('workspace %s'%workspace)	
	items_post = request.POST.getlist('items')
 	logger.debug('items post %s'%items_post)
	for i in range(len(items_post)) :
			items = Item.objects.filter(pk=items_post[i])[0]
			Basket.objects.filter(user=user,item=items,workspace=workspace)[0].delete()
			logger.debug('delitato')
	
 except Exception,  ex:
        logger.exception(ex)
        raise ex
 return HttpResponse(len(Basket.objects.filter(user=user,workspace=workspace)))
 
 
@login_required
def clear_basket(request):
 try:
 	logger.debug('clear basket')
 	user = User.objects.get(pk=request.session['_auth_user_id'])
	#user = User.objects.filter(username=str(username))[0]
	logger.debug('user %s'%user)
	workspace = request.session['workspace'] 	
 	all_b = Basket.objects.filter(user=user,workspace=workspace)
	for i in range(len(all_b)) :
			all_b[i].delete()
			logger.debug('delitato')
	
 except Exception,  ex:
        logger.exception(ex)
        raise ex
 return HttpResponse(len(Basket.objects.all()  ))

def basket_size(request):
 	user = User.objects.get(pk=request.session['_auth_user_id'])
	#user = User.objects.filter(username=str(username))[0]
	logger.debug('user %s'%user)
	workspace = request.session['workspace']
	return HttpResponse(len(Basket.objects.filter(user=user,workspace=workspace)))

def __inbasket(user,item,workspace):
  try:
    logger.debug('workspace %s'%workspace)
    logger.debug('item %s'%item)
    logger.debug('user %s'%user)

    if len( Basket.objects.filter(user=user,item=item,workspace=workspace))== 0 :
		return 0
	
  except Exception,  ex:
        logger.exception(ex)
        return 0	
  return 1


