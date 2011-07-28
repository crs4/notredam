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
import os
import os.path
import urllib
#import urllib2_file
import urllib2
import sys
import tarfile
import tempfile
from optparse import OptionParser
from django.utils.simplejson.decoder import JSONDecoder
from django.utils.simplejson.encoder import JSONEncoder
from urllib_uploader import StandardUploader
from ndutils import ImportExport, Exporter, Importer
import time
import logging
logger = logging.getLogger('dam')

import string

#CONFIGURATION GOES HERE
ERROR_STR= """Error removing %(path)s, %(error)s """


def custom_listfiles(path):
    """
    Returns the content of a directory by showing files by ordering the names alphabetically
    """
    files = sorted([f for f in os.listdir(path) if os.path.isfile(path + os.path.sep + f)])

    return files

def custom_listdirs(path):
    """
    Returns the content of a directory by showing directories by ordering the names alphabetically
    """
    dirs = sorted([d for d in os.listdir(path) if os.path.isdir(path + os.path.sep + d)])

    return dirs

def custom_open_file(filepath, name):
    """
    Returns 
    """
    try:
        json_dec = JSONDecoder()
        f = file(os.path.join(filepath, name), 'r')
        param = json_dec.decode(f.read())
        f.close()
    except Exception, ex:
        logger.exception(ex)
        raise
                
    return param

def add_keywords(i,data, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new, returnkeywords = None):
    """
    Allows to create keywords into a workspace.
    parameters:
        i: class instance Importer logged at DAM
        data:data to insert new keyword
        ws_origTows_new:  dict with key 'id' ws read to file workspace.json end value 'id' workspace create .
        id_orig_itemToid_new_item: dict with key 'id' item read to file item.json end value 'id' item create .
        keyColl_origTokeyColl_new: dict with key 'id' read to file collections.json end value 'id' create for equivalent collection.
        returnkeywords: None if keyword haven't parent, else data of father 
    return:
    """
   
    logger.debug("-----ADD KEYWORD")

    data['workspace_id'] = ws_origTows_new[str(data['workspace'])]
    items_flag = True
    data_app = dict(data)
    try:
        if data["parent_id"] == None:
            del data["parent_id"]
        else:
            del data["workspace_id"]
            data["parent_id"] = returnkeywords['id']
            
        if data["associate_ancestors"] == False:
            del data["associate_ancestors"]
        if (len(data["items"]) == 0):
            del data["items"]
            items_flag = False
        else:
            del data["items"]
            
        if len(data["metadata_schema"]) == 0:
                del data["metadata_schema"]
        else:
            json_enc = JSONEncoder()
            data["metadata_schema"] = json_enc.encode(data["metadata_schema"])
    except Exception, ex:
        logger.exception(ex)
                
    returnkeywords = i._keyword_new(data)
    #salvataggio del corrispettivo utile per le smartfolder
    keyColl_origTokeyColl_new[data['id']] = returnkeywords['id']
   
    logger.debug( "keyColl_origTokeyColl_new:%s, returnkeywords:%s" %(keyColl_origTokeyColl_new,returnkeywords['id']))
    if (items_flag):
        #fare l'add degli item a questa keywords
        param = []
        for item in data_app['items']:
            
            logger.debug( "id_orig_itemToid_new_item %s" %id_orig_itemToid_new_item)
            
            logger.debug( "id_orig_itemToid_new_item[item] %s" %id_orig_itemToid_new_item[item])
            param.append(('items',id_orig_itemToid_new_item[item]))
#        logger.debug( "param %s, returnkeywords['id'] %s" %(param,returnkeywords['id']))
        i._keyword_add(returnkeywords['id'], param)

    try:
        for data_children in data['children']:
            add_keywords(i,data_children, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new, returnkeywords)
    except Exception, ex:
        logger.exception(ex)
           
    

def add_collections(i,data, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new, returncollections = None):
    """
    Allows to create collections into a workspace.
    parameters:
        i: class instance Importer logged at DAM
        data: data to insert new collection
        ws_origTows_new:  dict with key 'id' ws read to file workspace.json end value 'id' workspace create.
        id_orig_itemToid_new_item: dict with key 'id' item read to file item.json end value 'id' item create .
        keyColl_origTokeyColl_new: dict with key 'id' read to file collections.json end value 'id' create for equivalent collection.
        returncollections: None if collection haven't parent, else data of father
    return:
    """
    
    data['workspace_id'] = ws_origTows_new[str(data['workspace'])]
    if data["parent_id"] == None:
        del data["parent_id"]
    else:
        del data["workspace_id"]
        data["parent_id"] = returncollections['id']
    returncollections = i._collections_new(data)
    #salvataggio del corrispettivo utile per le smartfolder
    keyColl_origTokeyColl_new[data['id']] = returncollections['id']
    #logger.debug( "keyColl_origTokeyColl_new:%s, returncollections:%s" %(keyColl_origTokeyColl_new,returncollections['id']))
    if len(data['items']) > 0:
        #fare l'add degli item a questa keywords
        param = []
        for item in data['items']:
            param.append(('items',id_orig_itemToid_new_item[item]))
#        logger.debug( "param %s, returncollections['id'] %s" %(param,returncollections['id']))
        i._collections_add(returncollections['id'], param)
    for data_children in data['children']:
        add_collections(i,data_children, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new,returncollections)

def add_smartfolders(i,data,ws_origTows_new, keyColl_origTokeyColl_new):
    """
    Allows to create smartfolders into a workspace.
    parameters:
        i: class instance Importer logged at DAM
        data:
        ws_origTows_new: dict with key 'id' ws read to file workspace.json end value 'id' workspace create.
        keyColl_origTokeyColl_new: dict with key 'id' read to file collections.json end value 'id' create for equivalent collection.
    returns:
        empty string
    """
    json_enc = JSONEncoder()
    for q in data['queries']:
        q['id'] = keyColl_origTokeyColl_new[q['id']]
    data['queries'] = json_enc.encode(data['queries'])
    i._smartfolders_add(data)
    
    return ''
    
    
def delete_value_none(param):
    """
    Allows to delete key that has value 'None'.
    parameters:
        param: any dict 
    return:
        param: dict without key = None.
    """
    for key in param.keys():
        if param[key] == None:
            del param[key]
    
    return param

def upload_watermarking(namerendition,typerendition,current_workspace,oldrenditions):
    """
    Allows to upload watermarking.
    parameters:
        namerendition: Name of rendition
        Typerendition: type of rendition (audio, video..)
        current_workspace: path of the current workspace
        oldrenditions: dict with data read of the file renditions.json
    return:
        if rendition has watermarking return dict as "job_id": "e2f076bd89eac4f4397d5a89e0c32ef87f212158", "unique_key": "5bf3b0667a210bcafa4b38fa7f5453d75d0ae5ad", 
        "ip": "127.0.0.1", "port": 10000, "chunk_size": 524288, "chunks": 1, "res_id": "c8230f4147cd45a55032405b5401a962ae42733c", 
        "id": "d7faee99860c35f77e7c502bf47026c47d0cee10"} else None
    """
    if oldrenditions[namerendition][typerendition]['preferences'].get('watermarking_url'):
        #ha il watermarking
        current_water = current_workspace + '/watermarking'
        for water in custom_listfiles(current_water):
            current_water = current_water + '/' + water
            (filepath, filename) = os.path.split(current_water)
            data = []
            data.append(('file_name',filename))
            try:
                data.append(('fsize',os.path.getsize(current_water)))
            except:
                raise Exception, 'error getsize'
            
            resp_upload_water = i._renditions_upload_watermarking(data)
            
            resp_upload_water['watermarking_position'] = oldrenditions[namerendition][typerendition]['preferences'].get('watermarking_position') 
            
            st = StandardUploader(current_water,resp_upload_water)
            st.uploadFile()
            
            return resp_upload_water
    else:
        return None

def add_renditions(e,i,current_workspace, workspace_id):
    """
    Allows to create renditions into a workspace
    parameters:
        i: class instance Importer logged at DAM
        e: class instance Exporter logged at DAM
        current_workspace: path of the directory of the current item
        id_workspace: id workspace
    Returns:
        empty string
    """
    #prendere i vecchi dati delle renditioni
    oldrenditions = custom_open_file(current_workspace, 'renditions.json')
#    logger.debug('----------------oldrendition %s'%oldrenditions)
    newrenditions = e._workspace_get_renditions(workspace_id)
 #   logger.debug('----------------newrenditions %s'%newrenditions)              
    #creare source se non presenti --> auto_generated == False
    for dict_rendition in oldrenditions['renditions']:

        data = []
        data.append(('workspace_id', workspace_id))
        data.append(('name', dict_rendition['name']))
        data.append(('caption', dict_rendition['caption']))
        data.append(('media_type', dict_rendition['media_type']))
        data.append(('auto_generated', dict_rendition['auto_generated']))

        #verificare se esiste gia'
        if not (dict_rendition in newrenditions['renditions']):
            #se non esiste creo
            i._renditions_new(data)
        else:
            i._renditions_edit(dict_rendition['id'],data)

    return ''
                
def add_members(e,i,current_workspace, id_workspace):
    """
    Allows to add members of a workspace
    parameters:
        i: class instance Importer logged at DAM
        e: class instance Exporter logged at DAM
        current_workspace: path of the directory of the current workspace
        id_workspace: id workspace
    Returns:
        empty string
    """
    #lettura dati salvati
    members = custom_open_file(current_workspace, 'members.json')
    
    for member in members['members']:
        #preparazione dati
        params = []
        params.append(('users',member['username']))
        for permission in member['permissions']:
            params.append(('permissions',permission))
        #chiamata per add members
        i._workspace_add_members(id_workspace,params)
        
    
#crea tutti i workspace vuoti.
def add_workspaces(i,e,users,path_extract,ws_origTows_new):
    """
    Allows to create all workspace into the DAM.
    parameters:
        i: class instance Importer logged at DAM
        e: class instance Exporter logged at DAM
        path_extract: path where you extracted the file Ndar
        ws_origTows_new: dict with key 'id' ws read to file workspace.json end value 'id' workspace create.
    Returns:
        string empty
    """
    try:
        for workspacedir in custom_listdirs(path_extract):
            logger.debug( 'Add %s' % workspacedir)
            current_workspace = path_extract + '/' + workspacedir
            paramworkspace = custom_open_file(current_workspace, 'workspace.json')
            
            #workspace id=1 creato in maniera automatica usare solo i set
            if (paramworkspace['id'] != '1'):
                #creo il nuovo workspace
                returnworkspace = i._workspace_new(paramworkspace)
                #set creator
                try:
                    i._api_workspace_set_creator(returnworkspace['id'],{'creator_id' : users[paramworkspace['creator']]['id']})
                except Exception, ex:
                    logger.error('error set creator for %s'%workspacedir)
                    logger.error(ex)
            else:
                #set di tutti i parametri necessari per ws_id =1
                i._workspace_set_name(paramworkspace['id'],paramworkspace)
                i._workspace_set_description(paramworkspace['id'],paramworkspace)
                returnworkspace = {}
                returnworkspace['id'] = 1
                #creator null
            
            ws_origTows_new[paramworkspace['id']] = returnworkspace['id']
            
            #logger.debug( 'renditions.json for %s' %workspacedir)
            #add_renditions(e,i,current_workspace,returnworkspace['id'])
    
            logger.debug('members.json for %s' %workspacedir)
            add_members(e,i,current_workspace,returnworkspace['id'])
    
        return ''
    except:
        logger.exception('Error in add_workspaces current_workspace: %s' %current_workspace)
        raise Exception, 'Error in add_workspaces'     

def search_id_rendition(filepath,shortname, rendition_ws):
    """
    Allows to search the 'id' of the rendition
    parameters:
        filepath: path of file rendition.json
        shortname: value of id rendition to search
        rendition_ws: dict that contains rendition of workspace
    return:
        
    """
    
    try:
        paramrendition = custom_open_file(filepath, 'rendition.json')
        for p in paramrendition['renditions']:
            
            logger.debug('%s' %shortname)
            if p['name'] == shortname:
                return p['id']
    except:
        raise Exception, 'Error in search_id_rendition'

"TODO non utilizzata"
def search_original_shortname(current_item):
    """
    Allows to search the shortname (id) of the original rendition
    parameters:
        current_item: path folder of the item
    return:
        string with shortname
    """
   
    logger.debug("#########################inizio search original shortname") 
    try:
        for rendition in custom_listfiles(current_item):
            current_rendition = current_item + '/' + rendition
            (filepath, filename) = os.path.split(current_rendition)
            (shortname, extension) = os.path.splitext(filename)
            if extension[1:] != 'json':
                paramrendition = custom_open_file(filepath, 'rendition.json')
                for p in paramrendition['renditions']:
                    if p['name'].lower() == 'original':                        
                        logger.debug("shortname ORIGINALLLLL------ %s" %shortname)
                        return shortname
    except:
        logger.exception('Error in search_original_shortname')
        raise Exception, 'Error in search_original_shortname'
                        
def get_data_for_upload(current_rendition,id_workspace,file_name,filepath,shortname,rendition_ws):
    """
    Allows to get data for upload rendition
    parameters:
        current_rendition: path of the folder current rendition
        id_workspace: 'id' workspace
        file_name: name of the file by upload
        filepath: path of the filename
        shortname: name without extension of the filename
        rendition_ws: dict that contain data of rendition workspace
    return:
        dict with the data.
    """

    try:
        size = os.path.getsize(current_rendition)
    except:
        raise Exception, 'error getsize'
    param = {}
    param ['workspace_id'] = id_workspace
    param['fsize'] = int(size)
    param['file_name'] = file_name
    param['rendition_id'] = search_id_rendition(filepath,shortname,rendition_ws)
    
    logger.debug("get data for upload finished")
    return param

import itertools
import mimetools
import mimetypes
from cStringIO import StringIO
import urllib
import urllib2

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return
    
    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

def _send_file(current_rendition, param, shortname, extension, id_item):
    # Create the form with simple fields
    form = MultiPartForm()
    form.add_field('workspace_id', str(param ['workspace_id']))
    form.add_field('rendition_id', str(param['rendition_id']))
    form.add_field('user_id', str(i.userid))
    # Add a fake file
   
    logger.debug("form %s " %form)
    logger.debug("open %s " %current_rendition)
    file = open(current_rendition)
    filedata = shortname +'.'+ extension[1:]
    
    logger.debug("filedata: %s" %(shortname +'.'+ extension[1:]))
    form.add_file(filedata, shortname +'.'+ extension[1:], 
                  fileHandle=file)
    file.close() 
    # Build the request
    
    logger.debug("urlib2.Request : http://%s:%s/api/item/%s/upload/" %(i.host,i.port, id_item))
    request = urllib2.Request('http://%s:%s/api/item/%s/upload/' %(i.host,i.port, id_item))
    request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
    body = str(form)
    request.add_header('Content-type', form.get_content_type())
    request.add_header('Content-length', len(body))
    request.add_data(body)
    
    return urllib2.urlopen(request)
    
def upload_renditions(current_item,id_workspace,rendition_ws,id_item,file_name,shortname_original,upload_orig = False):
    """
    Allows to upload renditions
    parameters:
        current_item: path of the directory of the current item
        id_workspace: id workspace
        rendition_ws: dict read from rendition.json that is in workspace
        id_item: id item
        file_name: filename with extencion
        shortname_original: 
        metadata_only: Flag is True if import only metadata instead is False (default) if imported also the rendition 
        upload_orig: True if start upload original else False
    returns:
        empty string
    """
    
    #upload delle renditioni
   
    logger.debug("----------------------------------------------upload rendition")
    try:
        for rendition in custom_listfiles(current_item):
         
            logger.debug("dentro FORRRRR")
            current_rendition = current_item + '/' + rendition
            (filepath, filename) = os.path.split(current_rendition)
            (shortname, extension) = os.path.splitext(filename)
            #upload prima le renditioni per ultima l'original. 
           
            logger.info('#################################################\n####################################current rendition')
            logger.info(current_rendition)
            if extension[1:] != 'json' and shortname != shortname_original:
                
                param = get_data_for_upload(current_rendition,id_workspace,file_name,filepath,shortname,rendition_ws)
              
                logger.debug('param')
                logger.debug("%s" %param)
                
                logger.debug('SERVER RESPONSE: workspace_id: %s, rendition_id: %s' %(param['workspace_id'], param['rendition_id']))
                resp_upload_rendition = _send_file(current_rendition, param, shortname, extension, id_item)
    
               
                logger.debug('id_item = %s, resp = %s' %(id_item,resp_upload_rendition.read()))
                logger.debug('upload not original rendition finished')
            else:
                #logger.debug( "ELSEEEEEEEEEEEEEEEEEEEEEE %s" %extension[1:])
                if extension[1:] != 'json':
                    #logger.debug( "dentro extension")
                    param_orig = get_data_for_upload(current_rendition,id_workspace,file_name,filepath,shortname,rendition_ws)
                    param_orig['shortname'] = shortname
                    param_orig['extension'] = extension
                    #logger.debug( "PARAM ORIGINALL %s" %param_orig)
                    current_rendition_orig = current_rendition
        
        #upload original solo se sono nell'ultimo ws della lista workspaces
        if upload_orig:
          
            logger.debug("Original rendition")
            logger.debug(current_rendition_orig)
            logger.debug('SERVER RESPONSE ORIGINAL: workspace_id: %s, rendition_id: %s' %(param_orig['workspace_id'], param_orig['rendition_id']))
            resp_upload_rendition = _send_file(current_rendition_orig, param_orig, param_orig['shortname'], param_orig['extension'], id_item)

            logger.debug('id_item = %s, resp = %s' %(id_item,resp_upload_rendition.read()))
            logger.debug('upload original rendition finished')
    except Exception, ex:
        logger.exception(ex)    
        
    return ''

def restore_rendition(current_item,id_workspace,rendition_ws,id_item,file_name,shortname_original, upload_orig = False):
    """
    Allows to upload renditions
    parameters:
        current_item: path of the directory of the current item
        id_workspace: id workspace
        rendition_ws: dict read from rendition.json that is in workspace
        id_item: id item
        file_name: filename with extencion
        shortname_original: 
        upload_orig: True if start upload original else False
    returns:
        empty string
    """

    logger.debug("RESTORE RENDITION")
    try:
        if "item.json" in custom_listfiles(current_item) and "rendition.json" in custom_listfiles(current_item):
            
            logger.info("\n\n AAAAAAAA ci sono.")
         
            fitem = custom_open_file(current_item, 'item.json')
            frendition = custom_open_file(current_item, 'rendition.json')
            
            for rendition in fitem['renditions']:
                param = {}
                param['workspace_id'] = id_workspace
                param['uri'] = fitem['renditions'][rendition]['url']
                param['file_name'] = fitem['renditions'][rendition]['file_name']
                #file_name can be NULL
                if not param['file_name']:
                    param['file_name'] = fitem['renditions']['original']['file_name']
                param['file_name'].decode('latin-1')
                param['rendition_id'] = search_id_rendition(current_item,rendition,rendition_ws)
                if string.lower(rendition) == 'original':
                    param_orig = param
                elif len(param['uri'])>0:
                        logger.info("params %s" %param)
                        i._item_add_component(id_item,param)

            logger.info("param_orig %s" %param_orig)
            i._item_add_component(id_item,param_orig)
                
            logger.info("/n/n param %s" %param)
        
    except Exception, ex:
        logger.exception(ex) 
        logger.info("/n/n param %s" %param)
   
    return ''

def add_to_ws(ws_origTows_new,id_old_ws,id_new_item):
    #aggiorno id_ws al ws_corrente
    """
    Aloows to add item in to workspace.
    parameters:
        ws_origTows_new: ws_origTows_new: dict with key 'id' ws read to file workspace.json end value 'id' workspace create.
        id_old_ws: id old workspace.
        id_new_item: id of new item
    return:
        empty string
    """
    try:
        i._item_add_to_ws(id_new_item,{'workspace_id':ws_origTows_new[id_old_ws]})
    except Exception, ex:
            logger.exception(ex) 
            logger.info("/n/n/n/n/n/n/n id_old_ws : %s" %id_old_ws)    

    return ''

def set_metadata(id_item,param):
    """
    Allows to set metadata of an item
    parameters:
        id_item: id of item
        param: dict with key 'metadata'
    return:
        empty string
    """
    
    json_enc = JSONEncoder()
    param['metadata'] = json_enc.encode(param['metadata'])
    #set_metadata
    i._item_set_metadata(id_item,param)
    
    return ''
    
def add_items(e,i,current_workspace,paramworkspace,ws_origTows_new,id_orig_itemToid_new_item, metadata_only):
    """
    Allows to create item and upload varinat into workspace.
    parameters:
        e: class instance Exporter logged at DAM
        i: class instance Importer logged at DAM
        current_workspace:  path of the directory of the current workspace
        paramworkspace: parameters read from workspace.json
        ws_origTows_new: ws_origTows_new: dict with key 'id' ws read to file workspace.json end value 'id' workspace create.
        id_orig_itemToid_new_item: dict with key 'id' item read to file item.json end value 'id' item create .
        metadata_only: Flag is True if import only metadata instead is False (default) if imported also the rendition 
    return:
        empty string
    """
    try:
        logger.debug('ITEMS %s'% custom_listdirs(current_workspace))
        len_items = len(custom_listdirs(current_workspace))
        
        
        for itemdir in custom_listdirs(current_workspace):
            if options.item:
                if custom_listdirs(current_workspace).index(itemdir) < options.item:
                    continue
                
            logger.info('items %s/%s'%(custom_listdirs(current_workspace).index(itemdir), len_items))
            current_item = current_workspace + '/' +  itemdir
           
            logger.info('\ncurrent_item %s' %current_item)
            if os.path.isdir(current_item) and itemdir != 'watermarking':#exclude folder watermarking
                paramitem = custom_open_file(current_item, 'item.json')
                #change media_type for compatibility with older version of NotreDAM
                if paramitem['media_type'].find('/') == -1:
                    logger.debug('fnameToType: %s,/n  paramItem: %s' %(paramitem['renditions']['original']['file_name'], paramitem))
#                    fnameToType = {'file_name':paramitem['renditions']['original']['file_name'].decode('latin-1')}
#                    if fnameToType == None:
                    fnameToType = {'file_name':paramitem['renditions']['original']['url']}
                    logger.debug("fnameToType: %s" %fnameToType)
                    media_type = i._item_get_type(fnameToType)
                    paramitem['media_type'] = media_type['media_type']
                
                paramitem['workspace_id'] = ws_origTows_new[paramworkspace['id']]
                rendition_ws = e._workspace_get_renditions(paramitem['workspace_id'])
                
                #shortname original
                #shortname_original = search_original_shortname(current_item)
                shortname_original = 'original'
           
                logger.debug("param item")
                logger.debug(paramitem)
                if len(paramitem['workspaces']) == 1:#NOT shared object
    
                    #create item
                    logger.info('\n\n\n\n paramitem %s' %paramitem)
                    resp_new_item = i._item_new(paramitem)
                    
                    #update equivalent id_item_old con id_item_new
                    id_orig_itemToid_new_item[paramitem['id']] = resp_new_item['id']
           
                    logger.debug("id_orig_itemToid_new_item %s" %id_orig_itemToid_new_item)
    
                    #rendition's upload
                    logger.debug("\n\n\n\nupload renditioni")
                    if not metadata_only:
                        upload_renditions(current_item,paramitem['workspace_id'],rendition_ws,resp_new_item['id'],shortname_original,shortname_original,True)
                    else:
                        restore_rendition(current_item,paramitem['workspace_id'],rendition_ws,resp_new_item['id'],shortname_original,shortname_original,True)
    
                    #set metadata
                    set_metadata(resp_new_item['id'],paramitem)
                else:#shared object
                  
                    logger.debug("prima %s " %paramitem['workspaces'])
                    paramitem['workspaces'].sort()

                    logger.debug("dopo %s" %paramitem['workspaces'])
                    if (paramitem['workspaces'].index(int(paramworkspace['id'])) == 0):
                        #sono nel primo ws della lista quindi devo creare l'item nel upload_workspace.
                        #creo item nel upload_workspace

                        logger.debug("sono nel primo ws della lista quindi devo creare l'item nel upload_workspace. ---- paramworkspace[id] %s" %paramworkspace['id'])
                        paramitem['workspace_id'] = ws_origTows_new[str(paramitem['upload_workspace'])] # aggiorno id ws in cui creare l'item
                        resp_new_item = i._item_new(paramitem)
        
                        #aggiorno corrispettivo id_item_old con id_item_new
                        id_orig_itemToid_new_item[paramitem['id']] = resp_new_item['id']
    
                        #add_to_workspace di questo item nel current_ws
                        if int(paramitem['workspaces'][0]) != int(paramitem['upload_workspace']):
                            paramitem['workspace_id'] = ws_origTows_new[paramworkspace['id']] # aggiorno al ws corrente
                            add_to_ws(ws_origTows_new,paramworkspace['id'],resp_new_item['id'])
    
                        #upload delle renditioni
                        shortname_original = 'original'
                        if not metadata_only:
                            upload_renditions(current_item,paramitem['workspace_id'],rendition_ws,resp_new_item['id'],shortname_original,shortname_original,False) # sempre false sono nel primo ws della lista
                        else:
                            restore_rendition(current_item,paramitem['workspace_id'],rendition_ws,resp_new_item['id'],shortname_original,shortname_original,False)
    
                        #set_metadata
                        set_metadata(resp_new_item['id'],paramitem)
                    else:

                        logger.debug('---condiviso nessuna NEW itemid %s---- paramworkspace[id] %s' %(paramitem['id'],paramworkspace['id']))
                        if id_orig_itemToid_new_item.has_key(paramitem['id']):
                            if int(paramitem['upload_workspace']) != int(paramworkspace['id']):
                                    add_to_ws(ws_origTows_new,paramworkspace['id'],id_orig_itemToid_new_item[paramitem['id']])
                            #upload delle renditioni
                            if int(paramitem['workspace_id']) == int(ws_origTows_new[str(paramitem['workspaces'][len(paramitem['workspaces'])-1])]) and id_orig_itemToid_new_item.has_key(paramitem['id']):
                                #nell'ultimo della lista devo fare l'upload dell'original
                                if not metadata_only:
                                    upload_renditions(current_item,paramitem['workspace_id'],rendition_ws,id_orig_itemToid_new_item[paramitem['id']],shortname_original,shortname_original,True)
                                else:
                                    restore_rendition(current_item,paramitem['workspace_id'],rendition_ws,id_orig_itemToid_new_item[paramitem['id']],shortname_original,shortname_original,True)
                                #set_metadata
                                set_metadata(id_orig_itemToid_new_item[paramitem['id']],paramitem)
                            else:
                                if not metadata_only:
                                    upload_renditions(current_item,paramitem['workspace_id'],rendition_ws,id_orig_itemToid_new_item[paramitem['id']],shortname_original,shortname_original,False)
                                else:
                                    restore_rendition(current_item,paramitem['workspace_id'],rendition_ws,id_orig_itemToid_new_item[paramitem['id']],shortname_original,shortname_original,False)
                            
                            #set_metadata
                            set_metadata(id_orig_itemToid_new_item[paramitem['id']],paramitem)
                        else:
                            logger.error("item not recognized")
                        
            if not metadata_only:
                time.sleep(0.5)
            else:
                time.sleep(0.1)
            
                        
    except Exception, ex:
        logger.exception(ex)
        logger.debug('%s' %id_orig_itemToid_new_item)
        raise     

    logger.debug( "FINISHHHHHHHHHHHHHHHH add_items")
    return ''


def add_users(i,path_extract):
    """
    Allows to add Users into the DAM.
    parameters:
        i: class instance Importer logged at DAM
        path_extract: path where you extracted the file Ndar
    returns:
        dict with key 'user' and value 'id'
    """
    fusers = custom_open_file(path_extract, 'users.json')
    logger.debug('fusers %s'%fusers)
    users = {}
    for u in fusers['users']:
        if u['username'] != 'admin':
            users[u['username']] = i._api_add_user(u)
            if not 'id' in users[u['username']]:
                raise Exception, "Error create user:%s responce:%s" %(u['username'],users[u['username']])
#    users['admin'] = {'id' : 1}
    
    return users


def rmgeneric(path, __func__):

    try:
        __func__(path)
      
        logger.debug( 'Removed %s' %path)
    except OSError, (errno, strerror):
        print ERROR_STR % {'path' : path, 'error': strerror }
            
def removeall(path):
    """
    Allows to remove all the directories and files given a path.
    parameters:
        path: path in which to delete all folders and files
    """
    if not os.path.isdir(path):
        return
    
    files=os.listdir(path)

    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            f=os.remove
            rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            removeall(fullpath)
            f=os.rmdir
            rmgeneric(fullpath, f)

def usage():
    return '\n'.join((
        "Import all data in your DAM",
        "example: python ndimport.py -i /home/{user}/Desktop/{name}.ndar -t /tmp/ -o 127.0.0.1 -r 8000",))

def main():
    op = OptionParser(usage = usage())
    op.add_option("-i", "--inputp",
                      action="store",dest="path_tar",type="string",
                      help="path tar by extract")
    op.add_option("-t", "--temp",
                      action="store", dest="path_extract",type="string", default='/tmp/',
                      help="path temporany folder to extract tar file")
    op.add_option("-o", "--iphost",
                      action="store",dest="host",type="string",default='127.0.0.1',
                      help="ip run notredam, default 127.0.0.1")
    op.add_option("-r", "--port",
                      action="store", dest="port",type="string", default='8000',
                      help="port notredam, default 8000")
    op.add_option("-k", "--key", 
                      action="store",dest="api_key",type="string",default='c3dfbc0331175f01f6464683c7ecce05c7bad60f',
                      help="api_key")
    op.add_option("-u", "--user", 
                      action="store",dest="user",type="string",default='admin',
                      help="Username for DAM")
    op.add_option("-p", "--password", 
                      action="store",dest="password",type="string",default='notredam',
                      help="Password for DAM")
    op.add_option("-w", "--workspace", 
                      action="store",dest="workspace",type="string",default='',
                      help="workspace")
    
    op.add_option("-I", "--item", 
                      action="store",dest="item",type="int",default=0,
                      help="item")
    op.add_option("-m", "--metadata-only",
                  action="store_true", dest="metadata_only",default=False,
                      help="Set option if you want only metadata backup." )
    
    
    
    op.add_option("-f", "--force", 
                      action="store_false",dest="force", default=False,
                      help="force")
    (options, args) = op.parse_args()

    return options

if __name__ == '__main__':

    options = main()
    logger.debug('options %s'%options)
        
    if (tarfile.is_tarfile(options.path_tar) and os.path.exists(options.path_extract) 
        and os.access(options.path_extract,os.W_OK)):
        try:
            path_tar = options.path_tar
            path_extract = options.path_extract
            tar = tarfile.open(path_tar)
            logger.debug('tar opened')
            if os.path.exists(path_extract + tar.getmembers()[0].name):
                logger.info('removing all')
                removeall(path_extract + tar.getmembers()[0].name)
            logger.info('extracting tar...')
            for tarinfo in tar:
                tar.extract(tarinfo, path=path_extract)
            tar.close()
            logger.info('tar extracted!')
            #unzip tar file into path_extract/backup
            path_extract += 'backup'
        
            i = Importer(options.host, options.port, options.api_key, options.user, options.password)
            i.login() 
            logger.debug('login ok')
            e = Exporter(options.host, options.port, options.api_key, options.user, options.password)
            e.login()
            logger.info( "add users")
            try:
                users = add_users(i,path_extract)
                logger.info('added user')
            except:
                if not options.force:
                    raise
                else:
                    logger.info('error in adding users... passing by')

            #ws_origTows_new {'id_ws_orig': id_ws_new}
            ws_origTows_new = {}
            add_workspaces(i,e,users,path_extract,ws_origTows_new)
            #match between id_item_old and id_item_new
            id_orig_itemToid_new_item = {}
            
            #creation item and item's resource.
            for workspacedir in custom_listdirs(path_extract):
                if options.workspace:
                    if workspacedir != options.workspace:
                        continue
                try:
                    current_workspace = path_extract + '/' + workspacedir
                    paramworkspace = custom_open_file(current_workspace, 'workspace.json')
                    add_items(e,i,current_workspace,paramworkspace,ws_origTows_new,id_orig_itemToid_new_item, options.metadata_only)
                    
                except Exception, ex:
                    logger.error(ex)
                    raise
    
            keyColl_origTokeyColl_new = {}
            try:
                for workspacedir in custom_listdirs(path_extract):
                    current_workspace = path_extract + '/' + workspacedir
                    #creation and assosiation of the keywords at the item
                    paramkeywords = custom_open_file(current_workspace, 'keywords.json')
                    
                    #FIXME: read and after delete all. Maybe should to be avoided
                    param = e._keyword_get_list(ws_origTows_new[str(paramkeywords['keywords'][0]['workspace'])])
                    for data in param['keywords']:
                        i._keyword_delete(data['id'])
                    
                    logger.info('keywords.json for %s' % workspacedir)
                    for data in paramkeywords['keywords']:
                        add_keywords(i,data, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new)
                    
                    logger.info('collections.json for %s' % workspacedir)
                    paramcollection = custom_open_file(current_workspace, 'collections.json')
                    for data in paramcollection['collections']:
                        add_collections(i,data,ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new)
        
                    logger.info('smartfolders.json for %s' % workspacedir)
                    paramsmartfolders = custom_open_file(current_workspace, 'smartfolders.json')
    
                    for data in paramsmartfolders['smartfolders']:
                            add_smartfolders(i,data,ws_origTows_new, keyColl_origTokeyColl_new)               

            except Exception, ex:
                logger.error(ex)
             
            logger.info("DONE")

        except Exception, ex:
            logger.exception(ex)
    
    else:
        logger.debug( "insert path of ndar file, or not tarfile.")
            #backup_file = sys.argv[-1]
    logger.info('DONE!')
