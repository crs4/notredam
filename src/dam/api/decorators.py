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

from django.http import HttpResponseRedirect, HttpResponse,  Http404,  HttpResponseServerError
from django.db import transaction
from django.contrib.auth.models import User

from django_restapi.responder import *
#from django_restapi.util import ErrorDict
from django.forms.util import ErrorDict
from django.utils import simplejson as json
import logging
logger = logging.getLogger('dam')

from dam.api.models import  Secret,  Application
import hashlib

from exceptions import *


def error_response( error_code, error_message, error_class,  error_dict = None):
    resp_dict = {}
#    response = HttpResponse()
    response = HttpResponseServerError()

    resp_dict['error code'] = error_code
    resp_dict['error message'] = error_message
    resp_dict['error class'] = error_class
#    if error_code == 500:
#        response.status_code = error_code
    

    
    if error_dict:
        error_dict = ErrorDict(error_dict)
        resp_dict['error message'] += '\n%s'%error_dict.as_text() 
    logger.debug('resp_dict%s' %resp_dict)
    response.write(json.dumps(resp_dict))
    logger.debug('response.content %s' %response.content)
    return response



def exception_handler(func):
    
    @transaction.commit_manually
    def _exception_handler(self,  request, *args, **kwargs):
       
        try:           
            resp = func(self,  request, *args, **kwargs)           
            transaction.commit()
            
        
             
        except CodeErrorException,  ex:
            if ex.__dict__.has_key('error_dict'):            
                resp =  error_response(ex.error_code,  ex.error_message, ex.error_class(), ex.error_dict )
            else:
                resp =  error_response(ex.error_code,  ex.error_message, ex.error_class())
            logger.exception(ex)
            
            transaction.rollback()
        except Exception,  ex:
            logger.exception(ex)            
            transaction.rollback()
            
            inner_ex = InnerException(ex)
            resp =  error_response(inner_ex.error_code,  inner_ex.error_message, inner_ex.error_class())
        else:
            transaction.commit()
            
            
            
        logger.debug('resp %s' %resp.content)
        return resp
    
    return _exception_handler
    
def api_key_required(func):
    """Check if api_key and user_id passed are valid"""
    
    def check(self,  request, *args, **kwargs):	
        if self.private:
            return func(self,  request, *args, **kwargs)        
        raise_error = False        
#        logger.debug('raw_post_data %s' %request.raw_post_data) 
        
        if request.method == 'GET':
            api_key = request.GET.get('api_key') 
            user_id = request.GET.get('user_id') 
            checksum = request.GET.get('checksum') 
            args_dict = request.GET.copy()            
                
        elif request.method == 'POST' or request.method == 'PUT' or 'DELETE':
            logger.debug('request.POST %s'%request.POST)
            api_key = request.POST.get('api_key') 
            user_id = request.POST.get('user_id') 
            checksum = request.POST.get('checksum')
            args_dict = request.POST.copy()           
    
        if not api_key:
                raise MissingAPIKey
        if not user_id:
                raise MissingUserId
        if not checksum:
            raise MissingSecret
            
        try:
            secret_obj = Secret.objects.get(application__api_key = api_key,  user__pk = user_id)
        except Secret.DoesNotExist:
            raise invalidAPIKeyOrUserId
        
        
        args_dict.pop('checksum')
        parameters = []
        for key,  value in args_dict.lists():
            if isinstance(value,  list):
                logger.debug('key %s is a list'%key)
                value.sort()
                for el in value:
                    parameters.append(str(key)+str(el))
            else:
                parameters.append(str(key)+str(value))
        
        parameters.sort()
        to_hash = secret_obj.value
        for el in parameters:
            to_hash += str(el)
                
        hashed_secret = hashlib.sha1(to_hash).hexdigest()
        
        if hashed_secret != checksum:
            raise AuthenticationFailed
                
        return func(self,  request, *args, **kwargs)
    return check

