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

import httplib
import urllib
from hashlib import sha1 
from django.utils.simplejson.decoder import JSONDecoder
from django.utils.simplejson.encoder import JSONEncoder
from dam import logger

class ImportExport(object):
    """
    """
    def __init__(self, host, port, api_key, username , password):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.username = username
        self.password = password
        self.method = 'POST'
        self.secret = None
        self.sessionid = None
        self.loggedin = False
        self.userid = None
        self.conn = httplib.HTTPConnection(self.host, self.port)
        
    def __del__(self):
        self.conn.close()
        
    def _call_server(self, method, url, *args, **kwargs):
        """
        -parameter:
                 url: url string for the server
               *args: list of arguments
            **kwargs: dict of argument
        -return:
            data return the application
        """
        p =  {    'api_key': self.api_key,
                'user_id': self.userid }

        logger.debug("%s" %url)
            
        if kwargs:
            p.update(kwargs)
        elif args:
            p = p.items()
            p.extend(args)
            p.extend(kwargs.items())
            
        logger.debug("params: %s " %p) 
        logger.debug("%s" %url)

        p = self._add_checksum_new(p)
        params = urllib.urlencode(p)
        logger.debug("---------------params: %s" %params) 
        if method == 'POST':
            self.conn.request(method, url, params)
        elif method == 'GET':
            self.conn.request(method, "%s?%s" % (url, params))
        else:
            raise Exception, "method %s unknown" % method
        
        response = self.conn.getresponse()
        json_data = response.read()
        logger.debug('response xxxx: %s' %json_data)
        if json_data != '':
            data = JSONDecoder().decode(json_data)
            return data
        else:
            return ''

    def _add_checksum_new(self, params):
        """
        Takes a parameter dictionary as input.
        Returns THE SAME dictionary adding checksum as one of its values.
        """
        if isinstance(params, dict):
            params = params.items()
        p_list = [str(k) + str(v) for k,v in params]
        
        p_list.sort()
        s = self.secret + ''.join(p_list)
        params.append(('checksum', sha1(s).hexdigest()))

        return params
    
    def _add_checksum(self, params):
        """
        Takes a parameter dictionary as input.
        Returns THE SAME dictionary adding checksum as one of its values.
        """
        try:
            params['checksum']
        except KeyError:
            p_list = [str(k) + str(v) for k,v in params.items()]
            p_list.sort()
            s = self.secret + ''.join(p_list)
            params['checksum'] = sha1(s).hexdigest()

            return params
        else:
            raise Exception, "given dictionary already has a checksum"
            
    def login(self):
        """
        Login application
        - parameters: 
            - self.
        -returns: True if login is established, false else.

        """
        
        params = urllib.urlencode({'api_key':self.api_key, 
                                   'user_name':self.username, 
                                   'password':self.password})
        logger.debug("params %s" %params)
        self.conn.request('POST', '/api/login/',params)
        response = self.conn.getresponse()
        logger.debug("response %s" %response)
        json_data = response.read()
        data = JSONDecoder().decode(json_data)
        try:
            self.secret = data['secret']
            self.sessionid = data['session_id']
            self.userid = data['user_id']
            self.loggedin = True
            return True
        except:
            raise Exception, "Login Filed"
        
class Exporter(ImportExport):
    """
    Class that implements the calls to make the export.
    """

    def _api_get_users(self):
        """ 
        Allows to get informations about all DAM users.
        - Method: GET
            - parameters: none
        -returns: {'users': [{'id':1, 'username': 'test', 'password': 'test', 'email': 'test@test.it', 'is_superuser': False}]}
        
        """
        return self._call_server('GET', '/api/get_users/')
    
    def _workspace_get_list(self):
        """
        Returns info about a given workspace.
        - method GET
            - parameters: none
        - returns:
            - JSON example:{'creator': 'test', 'description': '', 'name': 'test workspace', 'id': '2'}
        """
        return self._call_server('GET', '/api/workspace/get/')

    def _workspace_get(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get/' % workspace_id)

    def _workspace_get_items(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_items/' % workspace_id)

    def _workspace_get_renditions(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_renditions/' % workspace_id)

    def _workspace_get_collections(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_collections/' % workspace_id)

    def _workspace_get_smartfolders(self,param):
        return self._call_server('GET','/api/workspace/%s/get_smartfolders/'%param['workspace_id'] ,**param)

    def _workspace_get_keywords(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_keywords/' % workspace_id)

    def _workspace_get_members(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_members/' % workspace_id)
    
    def _item_rendition_get(self, param):
#        return self._call_server('GET', '/api/rendition/get/' ,**param)
        return self._call_server('GET', '/api/workspace/%s/get_renditions/' % param['workspace_id'],  **param)

    def _item_get(self, item_id, workspace_id=None):
        if workspace_id:
            return self._call_server('GET', '/api/item/%s/get/' % item_id, renditions_workspace=workspace_id)
        else:
            return self._call_server('GET', '/api/item/%s/get/' % item_id)

    def _collection_get_list(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_collections/'%workspace_id )

    def _collection_get(self, collection_id):
        return self._call_server('GET', '/api/collection/%s/get/' % collection_id)

    def _keyword_get_list(self, workspace_id):
        return self._call_server('GET', '/api/workspace/%s/get_keywords/'%workspace_id)

    def _keyword_get(self, keyword_id):
        return self._call_server('GET', '/api/keyword/%s/get/' % keyword_id)


    def write(self):
        pass

class Importer(ImportExport):
    """
    lass that implements the calls to make the import.
    """

    def _api_add_user(self,param):
        return self._call_server('POST', '/api/add_user/',**param)

    def _api_workspace_set_creator(self,id_workspace, param):
        return self._call_server('POST', '/api/workspace/%s/set_creator/' %id_workspace ,**param)

    def _workspace_new(self,param):
        return self._call_server('POST', '/api/workspace/new/',**param)

    def _workspace_set_name(self,id_workspace, param):
        return self._call_server('POST', '/api/workspace/%s/set_name/' % id_workspace, **param)

    def _workspace_set_description(self,id_workspace, param):
        return self._call_server('POST', '/api/workspace/%s/set_description/' % id_workspace, **param)

    def _workspace_add_members(self,id_workspace, param):
        return self._call_server('POST', '/api/workspace/%s/add_members/' % id_workspace, *param)

    def _renditions_edit(self,id_rendition, param):
        return self._call_server('POST', '/api/rendition/%s/edit/' % id_rendition, *param)

    def _renditions_new(self, param):
        return self._call_server('POST', '/api/rendition/new/', *param)

    def _renditions_upload_watermarking(self, param):
        return self._call_server('POST', '/api/rendition/get_watermarking_uri/', *param)

    def _keyword_new(self, param):
        return self._call_server('POST','/api/keyword/new/', **param)

    def _keyword_delete(self, id):
        return self._call_server('GET','/api/keyword/%s/delete/' % id)

    def _keyword_add(self, id_keywords, param):
        return self._call_server('POST','/api/keyword/%s/add_items/' % id_keywords, *param)

    def _collections_new(self, param):
        return self._call_server('POST','/api/collection/new/', **param)

    def _collections_add(self,id_collection, param):
        return self._call_server('POST','/api/collection/%s/add_items/' % id_collection, *param)

    def _smartfolders_add(self, param):
        return self._call_server('POST','/api/smartfolder/new/', **param)

    def _item_new(self,param):
        return self._call_server('POST','/api/item/new/', **param)
    
    def _item_get_type(self,param):
        return self._call_server('POST','/api/item/get_type/', **param)
    
    def _item_upload_rendition(self,item_id,param):
        return self._call_server('POST','/api/item/%s/upload/' % item_id, **param)
        
    def _item_add_to_ws(self,item_id,param):
        return self._call_server('POST','/api/item/%s/add_to_workspace/' % item_id, **param)

    def _item_set_metadata(self,item_id,param):
        return self._call_server('POST','/api/item/%s/set_metadata/' % item_id, **param)
    
    def _item_add_component(self,item_id,param):
        return self._call_server('POST','/api/item/%s/add_component/' % item_id, **param)
        
        
