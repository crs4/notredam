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

from django.utils.simplejson.decoder import JSONDecoder
from django.utils.simplejson.encoder import JSONEncoder
from hashlib import sha1 
from optparse import OptionParser

from ndutils import ImportExport, Exporter, Importer
#CONFIGURATION GOES HERE
DEBUG = False

def usage():
    return '\n'.join((
        "Export all data in your DAM",
        "example: python ndexport.py -o 127.0.0.1 -r 8000 -a home/{user}/Desktop -f dam_export",))

def main():
    op = OptionParser(usage = usage())
    op.add_option("-o", "--iphost",
                      action="store",dest="host",type="string",default='127.0.0.1',
                      help="ip run notredam, default 127.0.0.1")
    op.add_option("-r", "--port",
                      action="store", dest="port",type="string", default='8000',
                      help="port notredam, default 8000")
    op.add_option("-a", "--path",
                      action="store", dest="path",type="string", default='/home/',
                      help="path")
    op.add_option("-f", "--file", 
                      action="store",dest="filename",type="string",default='demo_export',
                      help="filname", metavar="FILE")
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
    
    archive_name = options.filename + '.ndar'    
    backup_file = os.path.join(options.path,archive_name)
    
    basedir = tempfile.mkdtemp()
    try:
        e = Exporter(options.host, options.port, options.api_key, options.user, options.password)
        e.login()
        json_enc = JSONEncoder()    
    
        #backup degli utenti
        f = file(os.path.join(basedir, 'users.json'), 'w')
        f.write(json_enc.encode(e._api_get_users()))
        f.close()
        
        
        for w in e._workspace_get_list():
            #Backup workspace
            print "Export workspace %s" % w['id']
            workspacedir = os.path.join(basedir,'w_' + str(w['id']))
            os.mkdir(workspacedir)
            items = e._workspace_get_items(w['id'])
    
    
            print "workspace.json"
            f = file(os.path.join(workspacedir, 'workspace.json'), 'w')
            f.write(json_enc.encode(e._workspace_get(w['id'])))
            f.close()
    
            #Backup collections
            print "collections.json"
            f = file(os.path.join(workspacedir, 'collections.json'),'w')
            f.write(json_enc.encode(e._collection_get_list(w['id'])))    
            f.close()
    
            #Backup keywords
            print "keywords.json"
            f = file(os.path.join(workspacedir, 'keywords.json'),'w')
            f.write(json_enc.encode(e._keyword_get_list(w['id'])))
            f.close()
            
            #Backup variants configuration
            print "variants.json"
            f = file(os.path.join(workspacedir, 'variants.json'),'w')
            variant = e._workspace_get_variants(w['id'])
            f.write(json_enc.encode(variant))
            f.close()

            #Backup watermarking
#            waterdir = os.path.join(workspacedir, 'watermarking')
#            os.mkdir(waterdir) 
#            for v in variant.keys():
#                for v_type in variant[v].keys():
#                    if variant[v][v_type].get('preferences') and variant[v][v_type]['preferences'].get('watermarking_url') != None: 
#                        filename = os.path.join(waterdir,variant[v][v_type]['preferences']['watermark_uri'] + os.path.splitext(variant[v][v_type]['preferences'].get('watermarking_url'))[-1])
##                        print 'file_name: %s , url water: %s' %(variant[v][v_type]['preferences']['watermark_uri'],variant[v][v_type]['preferences'].get('watermarking_url'))
#                        urllib.urlretrieve(variant[v][v_type]['preferences'].get('watermarking_url'), filename)

            #Backup smartfolder configuration
            print "smartfolders.json"
            f = file(os.path.join(workspacedir, 'smartfolders.json'),'w')
            f.write(json_enc.encode(e._workspace_get_smartfolders({'workspace_id': w['id']})))
            f.close()
    
            #_workspace_get_members
            print "members.json"
            f = file(os.path.join(workspacedir, 'members.json'),'w')
            f.write(json_enc.encode(e._workspace_get_members(w['id'])))
            f.close()
    
            
            #Backup items
            print "items %s" %items
            for i in items:
                #Backup item's metadata
                item = e._item_get(i, workspace_id=w['id'])
                print "==========="
                print item['id']
    

                itemdir = os.path.join(workspacedir, 'i_' + str(item['id']))
                os.mkdir(itemdir)    
                itemjson = json_enc.encode(item)
                f = file(os.path.join(itemdir,'item.json'),'w')
                f.write(itemjson)
                f.close()
    
                #read item's variant
                variant = e._item_variant_get({'workspace_id': w['id']})
                variantjson = json_enc.encode(variant)
                f = file(os.path.join(itemdir,'variant.json'),'w')
                f.write(variantjson)
                f.close()
                                
                #Backup item's resources/variants
                for v_id, data in item['variants'].items():
                    print "v_id %s" %v_id
                    print "data %s" %data
                    try:
                        filename = os.path.join(itemdir,str(v_id) + os.path.splitext(data['url'])[-1])
                    except AttributeError: #Some resource is None
                        print "%s WAS None" % str(v_id)                    
                        continue
                   
                        urllib.urlretrieve(data['url'], filename)
        

        t = tarfile.open(backup_file, 'w')
        t.add(basedir,arcname='backup')
        t.close()
    
    
        print "DONE"
    except Exception, ex:
        print '%s' %ex
