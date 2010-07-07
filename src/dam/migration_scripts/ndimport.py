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
import sys
import tarfile
import tempfile
from optparse import OptionParser
from django.utils.simplejson.decoder import JSONDecoder
from django.utils.simplejson.encoder import JSONEncoder
from urllib_uploader import StandardUploader
import logging
from ndutils import ImportExport, Exporter, Importer

logging.basicConfig(level=logging.DEBUG)

#CONFIGURATION GOES HERE
ERROR_STR= """Error removing %(path)s, %(error)s """
DEBUG = True

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
    json_dec = JSONDecoder()
    f = file(os.path.join(filepath, name), 'r')
    param = json_dec.decode(f.read())
    f.close()

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
    
    data['workspace_id'] = ws_origTows_new[str(data['workspace'])]
    if data["parent_id"] == None:
        del data["parent_id"]
    else:
        del data["workspace_id"]
        data["parent_id"] = returnkeywords['id']
        
    if data["associate_ancestors"] == False:
        del data["associate_ancestors"]
    if len(data["metadata_schema"]) == 0:
        del data["metadata_schema"]
    else:
        json_enc = JSONEncoder()
        data["metadata_schema"] = json_enc.encode(data["metadata_schema"])
    returnkeywords = i._keyword_new(data)
    #salvataggio del corrispettivo utile per le smartfolder
    keyColl_origTokeyColl_new[data['id']] = returnkeywords['id']
    #print "keyColl_origTokeyColl_new:%s, returnkeywords:%s" %(keyColl_origTokeyColl_new,returnkeywords['id'])
    if len(data['items']) > 0:
        #fare l'add degli item a questa keywords
        param = []
        for item in data['items']:
            param.append(('items',id_orig_itemToid_new_item[str(item)]))
#        print "param %s, returnkeywords['id'] %s" %(param,returnkeywords['id'])
        i._keyword_add(returnkeywords['id'], param)
    for data_children in data['children']:
        add_keywords(i,data_children, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new, returnkeywords)

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
    #print "keyColl_origTokeyColl_new:%s, returncollections:%s" %(keyColl_origTokeyColl_new,returncollections['id'])
    if len(data['items']) > 0:
        #fare l'add degli item a questa keywords
        param = []
        for item in data['items']:
            param.append(('items',id_orig_itemToid_new_item[str(item)]))
#        print "param %s, returncollections['id'] %s" %(param,returncollections['id'])
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

def upload_watermarking(namevariant,typevariant,current_workspace,oldvariants):
    """
    Allows to upload watermarking.
    parameters:
        namevariant: Name of variant
        Typevariant: type of variant (audio, video..)
        current_workspace: path of the current workspace
        oldvariants: dict with data read of the file variants.json
    return:
        if variant has watermarking return dict as "job_id": "e2f076bd89eac4f4397d5a89e0c32ef87f212158", "unique_key": "5bf3b0667a210bcafa4b38fa7f5453d75d0ae5ad", 
        "ip": "127.0.0.1", "port": 10000, "chunk_size": 524288, "chunks": 1, "res_id": "c8230f4147cd45a55032405b5401a962ae42733c", 
        "id": "d7faee99860c35f77e7c502bf47026c47d0cee10"} else None
    """
    if oldvariants[namevariant][typevariant]['preferences'].get('watermarking_url'):
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
            
            resp_upload_water = i._variants_upload_watermarking(data)
            
            resp_upload_water['watermarking_position'] = oldvariants[namevariant][typevariant]['preferences'].get('watermarking_position') 
            
            st = StandardUploader(current_water,resp_upload_water)
            st.uploadFile()
            
            return resp_upload_water
    else:
        return None

def add_variants(e,i,current_workspace, workspace_id):
    """
    Allows to create variants into a workspace
    parameters:
        i: class instance Importer logged at DAM
        e: class instance Exporter logged at DAM
        current_workspace: path of the directory of the current item
        id_workspace: id workspace
    Returns:
        empty string
    """
    #prendere i vecchi dati delle varianti
    oldvariants = custom_open_file(current_workspace, 'variants.json')
    logging.debug('----------------oldvariant %s'%oldvariants)
    newvariants = e._workspace_get_variants(workspace_id)
    logging.debug('----------------newvariants %s'%newvariants)              
    #creare source se non presenti --> auto_generated == False
    for namevariant in oldvariants['variants']:

        if namevariant['auto_generated'] == False:
            
            #verificare se esiste gia'
            if not (namevariant in newvariants['variants']):
                #se non esiste creo
                data = []
                data.append(('workspace_id', workspace_id))
                data.append(('name', namevariant))
                data.append(('caption', oldvariants[namevariant][typevariant]['caption']))
                data.append(('media_type', oldvariants[namevariant][typevariant]['media_type']))
                i._variants_new(data)

    #solo quelli con autogenerated == True
    for namevariant in oldvariants['variants']:
        
        if  namevariant['auto_generated'] == True:
            
#            resp_upload_water = upload_watermarking(namevariant,typevariant,current_workspace,oldvariants)
            
            data = []
#            if resp_upload_water:
#                data.append(('watermark_uri', resp_upload_water['res_id'])) 
#                data.append(('watermarking', True))
#                data.append(('watermarking_position', resp_upload_water['watermarking_position']))

            data.append(('workspace_id', workspace_id))
            #se e' un video/audio presente key preset
#            if 'preset' in oldvariants[namevariant][typevariant]['preferences']:
#                data.append(('preset', oldvariants[namevariant][typevariant]['preferences']['preset']['name']))
#                for d in oldvariants[namevariant][typevariant]['preferences']['preset']['parameters']:
#                    data.append((d, oldvariants[namevariant][typevariant]['preferences']['preset']['parameters'][d]))
#            else:
#                data.append(('codec', oldvariants[namevariant][typevariant]['preferences']['codec']))
#                data.append(('max_dim', oldvariants[namevariant][typevariant]['preferences']['max_dim']))                
                
                #verificare che non sia gia' presente
            if not (namevariant in newvariants['variants']):
                data.append(('name', namevariant))
                data.append(('auto_generated', namevariant['auto_generated']))
                data.append(('media_type', namevariant['media_type']))
                data.append(('caption', namevariant['caption']))
#                for d in namevariant['sources']:
#                    data.append(('sources',newvariants[d['name']][oldvariants[namevariant][typevariant]['media_type']]['id']))
               
                i._variants_new(data)
#            else:
#                i._variants_edit(newvariants[namevariant][typevariant]['id'],data)
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
            print 'Add %s' % workspacedir
            current_workspace = path_extract + '/' + workspacedir
            paramworkspace = custom_open_file(current_workspace, 'workspace.json')
            
            #workspace id=1 creato in maniera automatica usare solo i set
            if (paramworkspace['id'] != '1'):
                #creo il nuovo workspace
                returnworkspace = i._workspace_new(paramworkspace)
                #set creator
                i._api_workspace_set_creator(returnworkspace['id'],{'creator_id' : users[paramworkspace['creator']]['id']})
            else:
                #set di tutti i parametri necessari per ws_id =1
                i._workspace_set_name(paramworkspace['id'],paramworkspace)
                i._workspace_set_description(paramworkspace['id'],paramworkspace)
                returnworkspace = {}
                returnworkspace['id'] = 1
                #creator null
            
            ws_origTows_new[paramworkspace['id']] = returnworkspace['id']
            
            print 'variants.json for %s' %workspacedir
            add_variants(e,i,current_workspace,returnworkspace['id'])
    
            print 'members.json for %s' %workspacedir
            add_members(e,i,current_workspace,returnworkspace['id'])
    
        return ''
    except:
        logging.exception('Error in add_workspaces')
        raise Exception, 'Error in add_workspaces'     

def search_id_variant(filepath,shortname, variant_ws):
    """
    Allows to search the 'id' of the variant
    parameters:
        filepath: path of file variant.json
        shortname: value of id variant to search
        variant_ws: dict that contains variant of workspace
    return:
        
    """
    try:
        paramvariant = custom_open_file(filepath, 'variant.json')
        for p in paramvariant['variants']:
            if int(p['id']) == int(shortname):
                return variant_ws[p['name'].lower()][p['media_type']]['id']
    except:
        raise Exception, 'Error in search_id_variant'

def search_original_shortname(current_item):
    """
    Allows to search the shortname (id) of the original variant
    parameters:
        current_item: path folder of the item
    return:
        string with shortname
    """
    
    try:
        for variant in custom_listfiles(current_item):
            current_variant = current_item + '/' + variant
            (filepath, filename) = os.path.split(current_variant)
            (shortname, extension) = os.path.splitext(filename)
            if extension[1:] != 'json':
                paramvariant = custom_open_file(filepath, 'variant.json')
                logging.debug('-----------paramvariant %s'%paramvariant)
                logging.debug('shortname %s'%shortname)
                for p in paramvariant['variants']:
                    if p['name'].lower() == 'original':
                        return p['id']
#                    if int(p['id']) == int(shortname) and p['name'].lower() == 'original':
#                        
#                        return shortname
    except:
        logging.exception('Error in search_original_shortname')
        raise Exception, 'Error in search_original_shortname'
                        
def get_data_for_upload(current_variant,id_workspace,file_name,filepath,shortname,variant_ws):
    """
    Allows to get data for upload variant
    parameters:
        current_variant: path of the folder current variant
        id_workspace: 'id' workspace
        file_name: name of the file by upload
        filepath: path of the filename
        shortname: name without extension of the filename
        variant_ws: dict that contain data of variant workspace
    return:
        dict with the data.
    """
    
    try:
        size = os.path.getsize(current_variant)
    except:
        raise Exception, 'error getsize'
    param = {}
    param ['workspace_id'] = id_workspace
    param['fsize'] = int(size)
    param['file_name'] = file_name
    param['variant_id'] = search_id_variant(filepath,shortname,variant_ws)

    return param

def upload_variants(current_item,id_workspace,variant_ws,id_item,file_name,shortname_original, upload_orig = False):
    """
    Allows to upload variants
    parameters:
        current_item: path of the directory of the current item
        id_workspace: id workspace
        variant_ws: dict read from variant.json that is in workspace
        id_item: id item
        file_name: filename with extencion
        shortname_original: 
        upload_orig: True if start upload original else False
    returns:
        empty string
    """
    
    #upload delle varianti
    for variant in custom_listfiles(current_item):
        current_variant = current_item + '/' + variant
        (filepath, filename) = os.path.split(current_variant)
        (shortname, extension) = os.path.splitext(filename)
        #upload prima le varianti per ultima l'original.
        if extension[1:] != 'json' and shortname != shortname_original:
            
            param = get_data_for_upload(current_variant,id_workspace,file_name,filepath,shortname,variant_ws)
            
            resp_upload_variant = i._item_upload_variant(id_item,param)
            #print 'id_item = %s, resp = %s' %(id_item,resp_upload_variant)
            st = StandardUploader(current_variant,resp_upload_variant)
            st.uploadFile()
#                print 'upload not original variant finished'
        else:
            if extension[1:] != 'json':
                param_orig = get_data_for_upload(current_variant,id_workspace,file_name,filepath,shortname,variant_ws)
                current_variant_orig = current_variant
    
    #upload original solo se sono nell'ultimo ws della lista workspaces
    if upload_orig:
        #print current_variant_orig
        resp_upload_variant = i._item_upload_variant(id_item,param_orig)
        #print 'id_item = %s, resp = %s' %(id_item,resp_upload_variant)
        st = StandardUploader(current_variant_orig,resp_upload_variant)
        st.uploadFile()
    
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
    i._item_add_to_ws(id_new_item,{'workspace_id':ws_origTows_new[id_old_ws]})
    
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
    
def add_items(e,i,current_workspace,paramworkspace,ws_origTows_new,id_orig_itemToid_new_item):
    """
    Allows to create item and upload varinat into workspace.
    parameters:
        e: class instance Exporter logged at DAM
        i: class instance Importer logged at DAM
        current_workspace:  path of the directory of the current workspace
        paramworkspace: parameters read from workspace.json
        ws_origTows_new: ws_origTows_new: dict with key 'id' ws read to file workspace.json end value 'id' workspace create.
        id_orig_itemToid_new_item: dict with key 'id' item read to file item.json end value 'id' item create .
    return:
        empty string
    """
    for itemdir in custom_listdirs(current_workspace):
        current_item = current_workspace + '/' +  itemdir
        if DEBUG:
            print 'current_item'
            print current_item
        if os.path.isdir(current_item) and itemdir != 'watermarking':#exclude folder watermarking
            paramitem = custom_open_file(current_item, 'item.json')
            paramitem['workspace_id'] = ws_origTows_new[paramworkspace['id']]
            variant_ws = e._workspace_get_variants(paramitem['workspace_id'])
            
            #shortname original
            shortname_original = search_original_shortname(current_item)
            
            if len(paramitem['workspaces']) == 1:#NOT shared object

                #create item
                resp_new_item = i._item_new(paramitem)
                
                #update equivalent id_item_old con id_item_new
                id_orig_itemToid_new_item[paramitem['id']] = resp_new_item['id']

                #variant's upload
                upload_variants(current_item,paramitem['workspace_id'],variant_ws,resp_new_item['id'],paramitem['variants'][shortname_original]['file_name'],shortname_original,True)

                #set metadata
                set_metadata(resp_new_item['id'],paramitem)

            else:#shared object
                if (paramitem['workspaces'].index(int(paramworkspace['id'])) == 0):
                    #sono nel primo ws della lista quindi devo creare l'item nel upload_workspace.
                    #creo item nel upload_workspace
                    paramitem['workspace_id'] = ws_origTows_new[str(paramitem['upload_workspace'])] # aggiorno id ws in cui creare l'item
                    resp_new_item = i._item_new(paramitem)
    
                    #aggiorno corrispettivo id_item_old con id_item_new
                    id_orig_itemToid_new_item[paramitem['id']] = resp_new_item['id']

                    #add_to_workspace di questo item nel current_ws
                    if int(paramitem['workspaces'][0]) != int(paramitem['upload_workspace']):
                        paramitem['workspace_id'] = ws_origTows_new[paramworkspace['id']] # aggiorno al ws corrente
                        add_to_ws(ws_origTows_new,paramworkspace['id'],resp_new_item['id'])

                    #upload delle varianti
                    upload_variants(current_item,paramitem['workspace_id'],variant_ws,resp_new_item['id'],paramitem['variants'][shortname_original]['file_name'],shortname_original,False) # sempre false sono nel primo ws della lista

                    #set_metadata
                    set_metadata(resp_new_item['id'],paramitem)
                else:
#                    print '---condiviso nessuna NEW itemid %s---- paramworkspace[id] %s' %(paramitem['id'],paramworkspace['id'])
                    if int(paramitem['upload_workspace']) != int(paramworkspace['id']):
                        add_to_ws(ws_origTows_new,paramworkspace['id'],id_orig_itemToid_new_item[paramitem['id']])

                    #upload delle varianti
                    if int(paramitem['workspace_id']) == int(ws_origTows_new[str(paramitem['workspaces'][len(paramitem['workspaces'])-1])]):
                        #nell'ultimo della lista devo fare l'upload dell'original
                        upload_variants(current_item,paramitem['workspace_id'],variant_ws,id_orig_itemToid_new_item[paramitem['id']],paramitem['variants'][shortname_original]['file_name'],shortname_original,True)
                        #set_metadata
                        set_metadata(id_orig_itemToid_new_item[paramitem['id']],paramitem)
                    else:
                        upload_variants(current_item,paramitem['workspace_id'],variant_ws,id_orig_itemToid_new_item[paramitem['id']],paramitem['variants'][shortname_original]['file_name'],shortname_original,False)
                    
                    #set_metadata
                    set_metadata(id_orig_itemToid_new_item[paramitem['id']],paramitem)
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

    users = {}
    for u in fusers['users']:
        if u['username'] != 'demo':
            users[u['username']] = i._api_add_user(u)
            if not 'id' in users[u['username']]:
                raise Exception, "Error create user:%s responce:%s" %(u['username'],users[u['username']])
    users['demo'] = {'id' : 1}
    
    return users


def rmgeneric(path, __func__):

    try:
        __func__(path)
        if DEBUG:
            print 'Removed ', path
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
                      action="store",dest="user",type="string",default='demo',
                      help="Username for DAM")
    op.add_option("-p", "--password", 
                      action="store",dest="password",type="string",default='demo',
                      help="Password for DAM")
    
    (options, args) = op.parse_args()

    return options

if __name__ == '__main__':

    options = main()
    
    if (tarfile.is_tarfile(options.path_tar) and os.path.exists(options.path_extract) 
        and os.access(options.path_extract,os.W_OK)):
        try:
            path_tar = options.path_tar
            path_extract = options.path_extract
    
            tar = tarfile.open(path_tar)
            
            if os.path.exists(path_extract + tar.getmembers()[0].name):
                removeall(path_extract + tar.getmembers()[0].name)
            
            for tarinfo in tar:
                tar.extract(tarinfo, path=path_extract)
            tar.close()
            #scompattato il file tar. scorrere la cartella path_extract/backup
            path_extract += 'backup'
        
        
            i = Importer(options.host, options.port, options.api_key, options.user, options.password)
            i.login() 
            e = Exporter(options.host, options.port, options.api_key, options.user, options.password)
            e.login()
            users = add_users(i,path_extract)
            
            #ws_origTows_new {'id_ws_orig': id_ws_new}
            ws_origTows_new = {}
            add_workspaces(i,e,users,path_extract,ws_origTows_new)
 
            #corrispettivo id_item_old con id_item_new
            id_orig_itemToid_new_item = {}
            
            #creazione item e risorse relative agli item.
            for workspacedir in custom_listdirs(path_extract):
                current_workspace = path_extract + '/' + workspacedir
                paramworkspace = custom_open_file(current_workspace, 'workspace.json')
                add_items(e,i,current_workspace,paramworkspace,ws_origTows_new,id_orig_itemToid_new_item)
                
    
    
            keyColl_origTokeyColl_new = {}
            for workspacedir in custom_listdirs(path_extract):
                current_workspace = path_extract + '/' + workspacedir
                #creazione e associazione delle keywords agli item
                paramkeywords = custom_open_file(current_workspace, 'keywords.json')
                
                #FIXME: read e poi delete all forse si puo' evitare
                param = e._keyword_get_list(ws_origTows_new[str(paramkeywords['keywords'][0]['workspace'])])
                for data in param['keywords']:
                    i._keyword_delete(data['id'])
                
                print 'keywords.json for %s' % workspacedir
                for data in paramkeywords['keywords']:
                    add_keywords(i,data, ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new)
    
                print 'collections.json for %s' % workspacedir
                paramcollection = custom_open_file(current_workspace, 'collections.json')
                for data in paramcollection['collections']:
                    add_collections(i,data,ws_origTows_new, id_orig_itemToid_new_item,keyColl_origTokeyColl_new)
    
                print 'smartfolders.json for %s' % workspacedir
                paramsmartfolders = custom_open_file(current_workspace, 'smartfolders.json')
                for data in paramsmartfolders['smart_folders']:
                        add_smartfolders(i,data,ws_origTows_new, keyColl_origTokeyColl_new)
                
            print "DONE"
        except Exception, ex:
            print '%s' %ex
    
    else:
        print "insert path of ndar file, or not tarfile."
            #backup_file = sys.argv[-1]
