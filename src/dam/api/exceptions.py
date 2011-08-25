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
from dam.treeview.models import InvalidNode,  WrongWorkspace,  NotMovableNode,    NotEditableNode, SiblingsWithSameLabel
from dam.treeview.models import Node, SmartFolder
from dam.workspace.models import Workspace
from dam.repository.models import Item
from dam.metadata.models import MetadataProperty,  MetadataValue
from dam.variants.models import Variant
from dam.workflow.models import State, WrongItemWorkspace
from dam.mprocessor.models import Pipeline
from django.db import IntegrityError



class CodeErrorException(Exception): #abstract
    error_code = None
    error_message = None
    
    def error_class(self):
        return self.__class__.__name__
    

class VerboseCodeErrorException(CodeErrorException):
    def __init__(self, error_dict = None,  *args,  **kwargs):
        super(VerboseCodeErrorException,  self).__init__(*args,  **kwargs)
        self.error_dict = error_dict
        

class BadRequest(CodeErrorException):
    error_code = 400

class Forbidden(CodeErrorException):
    error_code = 403

class NotFound(CodeErrorException):
    error_code = 404



class MalformedJSON(BadRequest):
    
    error_message = 'malformed json request'

class TooManyArgsPassed(BadRequest):
    error_code = 23
    error_message = 'too many arguments passed'
    

class MissingArgs(BadRequest):    
    error_message = 'missing required arguments'
    

class SmartFolderError(BadRequest):    
    error_message = 'missing required arguments'
    
class ArgsValidationError(BadRequest):   
    error_message = 'arguments validation error'
    
class MissingAPIKey(BadRequest):
    
    error_message = 'missing api key'
    
class MissingUserId(BadRequest):    
    error_message = 'missing user id'

class MissingSecret(BadRequest):    
    error_message = 'missing secret'

class InvalidAPIKey(BadRequest):    
    error_message = 'invalid api key'    
    
class InvalidAPIKeyOrUserId(BadRequest):
    
    error_message = 'invalid api_key or user id'    
    
class AuthenticationFailed(Forbidden):    
    error_message = 'authentication failed, check your secret key'    

class InsufficientPermissions(Forbidden):    
    error_message = 'insufficient permissions'
    
    
class InvalidKeyword(BadRequest):
    error_message = 'invalid keyword'


class SmartFolderDoesNotExist(NotFound):	
	error_message = 'the smarfolder does not exist'

class InvalidMediaType(BadRequest):
    error_message = 'invalid media type'

class ImportedVariant(BadRequest):
    error_message = 'the variant has no preferences to set, since it is imported'

class InvalidPreferences(BadRequest):
    error_message = 'invalid variant preferences'

class LoginFailed(Forbidden):
    error_message = 'invalid username or password'
    
class InvalidArg(BadRequest):
    error_message = 'invalid argument'
    
    
class GlobalVariantDeletion(Forbidden):    
    error_message = 'global variant cannot be deleted, sorry'
    
class WorkspaceAdminDeletion(Forbidden):    
    error_message = 'Workspace admin cannot be deleted'

class GlobalScriptDeletion(Forbidden):    
    error_message = 'global script cannot be deleted'
    
class InnerException(VerboseCodeErrorException):
    
    def error_class(self):
        if self.__error_class:
            return self.__error_class
        else:
            return self.ex.__class__.__name__
    
    def __init__(self, ex):
        self.ex = ex
        self.error_dict = {}
        self.__error_class = '' 
        if  isinstance(ex, SiblingsWithSameLabel):  
            self.error_code = 90
            self.error_message =  'a keyword or collection with the same name with the same parent already exists'
            
        
        elif isinstance(ex, Node.DoesNotExist):     
            self.error_code = NotFound.error_code
            self.error_message =  'keyword or collection does not exist'
            self.__error_class = 'CatalogueElement' + ex.__class__.__name__
        
        elif isinstance(ex, State.DoesNotExist):   
            
            self.error_code = NotFound.error_code
            self.error_message = 'state does not exist'
            self.__error_class = 'State' + ex.__class__.__name__
        
        
        elif isinstance(ex, Variant.DoesNotExist):
            self.error_code = NotFound.error_code
            self.error_message = 'rendition does not exist'
            self.__error_class = 'Rendition' + ex.__class__.__name__
            
        elif isinstance(ex, SmartFolder.DoesNotExist):
            self.error_code = NotFound.error_code
            self.error_message = 'smartfolder does not exist'
            self.__error_class = 'SmartFolder' + ex.__class__.__name__

        elif isinstance(ex, InvalidNode):
            
            self.error_code = BadRequest.error_code
            self.error_message = 'invalid keywords'
                    
        elif  isinstance(ex, WrongWorkspace):
            self.error_code = BadRequest.error_code
            self.error_message = 'keywords does not belong to the same workspace'
                
#        except NotEditableNode,  ex:
#            logger.exception(ex)
#            transaction.rollback()
#            resp =  error_response(22)
            
        elif isinstance(ex, Workspace.DoesNotExist):
            
            self.error_code = NotFound.error_code
            self.error_message = 'workspace does not exist'
            self.__error_class = 'Workspace' + ex.__class__.__name__
               
           
        elif isinstance(ex, Item.DoesNotExist):
            self.error_code = NotFound.error_code
            self.error_message = 'item does not exist'
            self.__error_class = 'Item' + ex.__class__.__name__
            
        elif isinstance(ex, Pipeline.DoesNotExist):
            self.error_code = NotFound.error_code
            self.error_message = 'script does not exist'
            self.__error_class = 'Script' + ex.__class__.__name__
            
        elif isinstance(ex, MetadataProperty.DoesNotExist):             
            self.error_message = 'metadata schema does not exist'
            if ex.__dict__.has_key('error_dict'):
                self.error_code = NotFound.error_code
                self.error_dict =   ex.error_dict
            self.__error_class = 'MetadataSchema' + ex.__class__.__name__
            
                
        elif isinstance(ex,MetadataValue.DoesNotExist):             
            self.error_message = 'metadata does not exist'
            self.__error_class = 'Metadata' + ex.__class__.__name__
            if ex.__dict__.has_key('error_dict'):
                self.error_code = NotFound.error_code
                self.error_dict = ex.error_dict 
        
        elif isinstance(ex, IntegrityError) or isinstance(ex, WrongItemWorkspace): 
            self.error_message = str(ex)
            
        
            
        else:
            self.error_code = 500
            self.error_message = 'internal server error'
            self.__error_class =  'InternalServerError'
                    
        
        

    
    
    
