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


class CodeErrorException(Exception):
    pass

class VerboseCodeErrorException(CodeErrorException):
    def __init__(self, error_dict = None,  *args,  **kwargs):
        super(VerboseCodeErrorException,  self).__init__(*args,  **kwargs)
        self.error_dict = error_dict
        

class MalformedJSON(CodeErrorException):
    error_code = 13
    error_message = 'malformed json request'

class TooManyArgsPassed(CodeErrorException):
    error_code = 23
    error_message = 'too many arguments passed'

class MissingArgs(VerboseCodeErrorException):
    error_code = 15
    error_message = 'missing required arguments'
    

class SmartFolderError(VerboseCodeErrorException):
    error_code = 45
    error_message = 'missing required arguments'
    
class ArgsValidationError(VerboseCodeErrorException):
    error_code = 14
    error_message = 'arguments validation error'
    
    
    
class MissingAPIKey(CodeErrorException):
    error_code = 25
    error_message = 'missing api key'
    
class MissingUserId(CodeErrorException):
    error_code = 27
    error_message = 'missing user id'

class MissingSecret(CodeErrorException):
    error_code = 28
    error_message = 'missing secret'

class InvalidAPIKey(CodeErrorException):
    error_code = 11
    error_message = 'invalid api key'    
    
class invalidAPIKeyOrUserId(CodeErrorException):
    error_code = 29
    error_message = 'invalid api_key or user id'    
    
class AuthenticationFailed(CodeErrorException):
    error_code = 30
    error_message = 'authentication failed, check your secret key'    


    
class InsufficientPermissions(CodeErrorException):
    error_code = 24
    error_message = 'insufficient permissions'
    
    
class InvalidKeyword(CodeErrorException):
    error_code = 19
    error_message = 'invalid keyword'

class WorkspaceDoesNotExist(CodeErrorException):
	error_code = 1138
	error_message = 'the workspace does not exist'

class SmartFolderDoesNotExist(CodeErrorException):
	error_code = 1139
	error_message = 'the workspace does not exist'


class InvalidMediaType(CodeErrorException):
    error_code = 32
    error_message = 'invalid media type'
    
#errors_code = {    
#    12: 'item with the given id does not exist', 
#    16: 'missing metadataschema', 
#    17: 'metadata not found', 
#    18: 'workspace does not exist', 
#    20: 'keyword does not exist', 
#    21: 'keyword does not belong to the given workspace', 
#    
#    }

class ImportedVariant(CodeErrorException):
    error_code = 33
    error_message = 'the variant has no preferences to set, since it is imported'

class InvalidPreferences(CodeErrorException):
    error_code = 34
    error_message = 'invalid variant preferences'


class LoginFailed(CodeErrorException):
    error_code = 31
    error_message = 'invalid username or password'
    
class InvalidArg(VerboseCodeErrorException):
    error_code = 50
    error_message = 'invalid argument'
    
    
class GlobalVariantDeletion(CodeErrorException):
    error_code = 78
    error_message = 'global variant cannot be deleted, sorry'
    
class WorkspaceAdminDeletion(CodeErrorException):
    error_code = 89
    error_message = 'Workspace admin cannot be deleted'
