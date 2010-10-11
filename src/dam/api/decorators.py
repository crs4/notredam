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
import logger
from models import  Secret,  Application
import hashlib

import traceback

from dam.treeview.models import InvalidNode,  WrongWorkspace,  NotMovableNode,    NotEditableNode, SiblingsWithSameLabel
from dam.treeview.models import Node
from dam.workspace.models import Workspace
from dam.repository.models import Item
from dam.metadata.models import MetadataProperty,  MetadataValue
from variants.models import Variant
from workflow.models import State
from exceptions import *


def error_response( error_code, error_message,  error_dict = None):
    resp_dict = {}
#    response = HttpResponse()
    response = HttpResponseServerError()

    resp_dict['error code'] = error_code
    resp_dict['error message'] = error_message
#    if error_code == 500:
#        response.status_code = error_code
    

    
    if error_dict:
        error_dict = ErrorDict(error_dict)
        resp_dict['error message'] += '\n%s'%error_dict.as_text() 
    logger.debug('resp_dict%s' %resp_dict)
    response.write(json.dumps(resp_dict))
    logger.debug('response.content %s' %response.content)
    return response


@transaction.commit_manually
def exception_handler(func):
    logger.debug('---------------------')
    
    def _exception_handler(self,  request, *args, **kwargs):
       
        try:           
            resp = func(self,  request, *args, **kwargs)           
            transaction.commit()
            
        
        except SiblingsWithSameLabel,  ex:            
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            
            transaction.rollback()
            resp =  error_response(90,  'a keyword or collection with the same name with the same parent already exists')
        
        
        except Node.DoesNotExist,  ex:            
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            
            transaction.rollback()
            resp =  error_response(20,  'keyword does not exist')
            
        
        except State.DoesNotExist,ex:            
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            
            transaction.rollback()
            resp =  error_response(65,  'state does not exist')
            
        except Variant.DoesNotExist,  ex:            
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            
            transaction.rollback()
            resp =  error_response(26,  'variant does not exist')

        except InvalidNode,  ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback()
            resp = error_response(19,  'invalid keywords')
                    
        except WrongWorkspace, ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback()
            resp =  error_response(21,'keywords does not belong to the same workspace')
                
#        except NotEditableNode,  ex:
#            logger.exception(ex)
#            transaction.rollback()
#            resp =  error_response(22)
            
        except Workspace.DoesNotExist,  ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback()
            resp =  error_response(18,  'workspace does not exist')   
           
        except Item.DoesNotExist,  ex:
            logger.exception(ex)
            transaction.rollback() 
            resp =  error_response(12,  'item does not exist')
            
        except MetadataProperty.DoesNotExist,  ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback() 
            message = 'metadata schema does not exist'
            if ex.__dict__.has_key('error_dict'):
                resp =  error_response(16, message,  ex.error_dict )
            else:
                resp =  error_response(16, message)
                
        except MetadataValue.DoesNotExist,  ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback() 
            message = 'metadata does not exist'
            if ex.__dict__.has_key('error_dict'):
                resp =  error_response(17, message,  ex.error_dict )
            else:
                resp =  error_response(17, message)        
        
        
        
#        except MissingArgs,  ex:
#            logger.exception(ex)
#            transaction.rollback() 
#            resp =  error_response(15)
#            
#        except ArgsValidationError,  ex:
#            transaction.rollback()            
#            resp =  error_response(14, ex.error_dict)
#            
#        except MalformedJSON,  ex:
#            if ex.__dict__.has_key('error_dict'):
#                resp =  error_response(13,  ex.error_dict )
#            else:
#                resp =  error_response(13,)
#            
#        except TooManyArgsPassed,  ex:
#            logger.exception(ex)
#            transaction.rollback() 
#            resp =  error_response(23)
#            
#        except InsufficientPermissions,  ex:
#            logger.exception(ex)
#            transaction.rollback() 
#            resp =  error_response(24)
#            
#        except MissingAPIKey,  ex:
#            logger.exception(ex)
#            transaction.rollback() 
#            resp =  error_response(ex.error_code,  ex.error_message)
#            
#        except InvalidAPIKey,  ex:
#            logger.exception(ex)
#            transaction.rollback() 
#            resp =  error_response(11)
#        
        except CodeErrorException,  ex:
            if ex.__dict__.has_key('error_dict'):            
                resp =  error_response(ex.error_code,  ex.error_message, ex.error_dict )
            else:
                resp =  error_response(ex.error_code,  ex.error_message)
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback()
        except Exception,  ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())
            transaction.rollback()
            resp =  error_response(500,'internal server error')
            
            
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
        except:
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

