import os
import inspect
from mx.DateTime.Parser import DateTimeFromString
from datetime import datetime
from dam.mprocessor import log
from dam.mprocessor.config import Configurator
from dam.mprocessor.storage import Storage
from dam.libxmp import XMPFiles, XMPError, files, XMPMeta
from dam.libxmp.consts import *

class XMPEmbedder(object):

    def __init__(self):
        self._fc = Storage()

    def metadata_synch(self, component_id, changes):

        # get xmp 
        
        # the filename is needed because the extension is unknown, the following line of code is
        # tmp code because c.ID will include extension file (not only basename) 
        # in the new MediaDART release

        try:
            myxmpfilename = str(self._fc.abspath(component_id))
        except Exception, err:
            log.error('Found some problems getting filename: %s' % err)

        xmpfile = XMPFiles(file_path=myxmpfilename, open_forupdate=files.XMP_OPEN_FORUPDATE)
        xmp = xmpfile.get_xmp()

        if not xmp:
            xmp = XMPMeta()
        
        for ns in changes.keys():
            # first of all check if namespace str(i[0]) and property name str(i[1]) exist
            prefix = None
            try:
                prefix = xmp.get_prefix_for_namespace(str(ns))
            except XMPError, err:
                log.debug('Error in get_prefix_for namespace: %s' % str(ns))
            if prefix == None:
                # prefix does not exist so it must be created 
                try:
                    log.debug('%s %s' % (str(ns), str(changes[ns]['prefix'])))
                    res = xmp.register_namespace(str(ns), str(changes[ns]['prefix'])) # CHANGE ME
                except XMPError, err:
                    log.error('Error in register_namespace: %s' % err)
            for i in changes[ns]['fields'].keys():
                try:
                    property_exists = xmp.does_property_exist(str(ns), str(i))
                except XMPError, err:
                    log.error('Error in does_property_exist: %s' % err)
                if changes[ns]['fields'][i]['is_array'] == 'not_array':
                    if changes[ns]['fields'][i]['xpath'] != []: # so it is a structure 
                        if property_exists == False:
                            # if it is a structure and the property does not exist, 
                            # it must be created, otherwise, it will not be set.
                            try:
                                res = xmp.set_property(str(ns), str(i),'',prop_value_is_struct = XMP_PROP_VALUE_IS_STRUCT) 
                            except XMPError, err:
                                log.error( 'XMPError in set_property in case of structure: %s ' % err)
                            except Exception, err:
                                log.error( 'Error in set_property in case of structure: %s ' % err)
                        for index, elem in enumerate(changes[ns]['fields'][i]['value']):
                            cleaned_xpath = re.sub( r"\[.\]", "", str(changes[ns]['fields'][i]['xpath'][index]) )
                            try:
                                xmp.set_property( str(ns), cleaned_xpath, str(elem) )
                            except XMPError, err:
                                log.error( 'XMPError in set_property in case of structure: %s ' % err)
                            except Exception, err:
                                log.error( 'Error in set_property in case of structure: %s ' % err)
                    elif changes[ns]['fields'][i]['type'] == 'date': 
                        mydate = DateTimeFromString(changes[ns]['fields'][i]['value'][0])
                        mydate1 = datetime(mydate.year, mydate.month, mydate.day, mydate.hour, mydate.minute, int(mydate.second))
                        try:
                            xmp.set_property_datetime( str(ns), str(i), mydate1)
                        except XMPError, err:
                            log.error('XMPError in set_property_datetime: %s' % err)
                        except Exception, err:
                            log.error('Error in set_property_datetime: %s' % err)
                    elif changes[ns]['fields'][i]['type'] == 'bool': 
                        try:
                            xmp.set_property_bool( str(ns), str(i), bool(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            log.error('XMPError in set_property_bool: %s' % err)
                    elif changes[ns]['fields'][i]['type'] == 'int': 
                        try:
                            xmp.set_property_int( str(ns), str(i), int(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            log.error('XMPError in set_property_int: %s' % err)
                    elif changes[ns]['fields'][i]['type'] == 'float': 
                        try:
                            xmp.set_property_float( str(ns), str(i), float(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            log.error('XMPError in set_property_float: %s' % err)
                    elif changes[ns]['fields'][i]['type'] == 'long': 
                        try:
                            xmp.set_property_long( str(ns), str(i), long(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            log.error('XMPError in set_property_long: %s' % err)
                    else:
                        try:
                            log.debug('%s %s %s' % (str(ns), str(i), str(changes[ns]['fields'][i]['value'][0])))
                            xmp.set_property( str(ns), str(i), str(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            log.error('XMPError in set_property: %s' % err)
                else:
         
                    # Property IS ARRAY 
                    if changes[ns]['fields'][i]['xpath'] != []: # so it is a structure 
                        log.error('Sorry. Array of structures is not supported by xmplib')
                        continue
                    if property_exists == False:
                        # if it is an array and the property does not exist, 
                        # it must be created, otherwise, it will not be set.
                        try:
                            if changes[ns]['fields'][i]['is_array'] == 'alt' and  changes[ns]['fields'][i]['type'] == 'lang' :
                                res = xmp.set_property(str(ns), str(i),'',prop_value_is_array = XMP_PROP_VALUE_IS_ARRAY,  
                                                                               prop_array_is_alt = XMP_PROP_ARRAY_IS_ALT,
                                                                               prop_array_is_alttext = XMP_PROP_ARRAY_IS_ALTTEXT,
                                                                               prop_array_is_ordered = XMP_PROP_ARRAY_IS_ORDERED)
                            elif changes[ns]['fields'][i]['is_array'] == 'seq': #array type is seq
                                res = xmp.set_property(str(ns), str(i),'',prop_value_is_array = XMP_PROP_VALUE_IS_ARRAY, 
                                                                               prop_array_is_ordered = XMP_PROP_ARRAY_IS_ORDERED)
                            elif changes[ns]['fields'][i]['is_array'] == 'bag': #array type is bag
                                res = xmp.set_property(str(ns), str(i),'',prop_value_is_array = XMP_PROP_VALUE_IS_ARRAY, 
                                                                              prop_array_is_unordered = XMP_PROP_ARRAY_IS_UNORDERED)
                            else: 
                                res = xmp.set_property(str(ns), str(i),'',prop_value_is_array = XMP_PROP_VALUE_IS_ARRAY) 
                        except XMPError, err:
                            log.error('XMPError in set_property: %s' % err)
                    if changes[ns]['fields'][i]['type'] == 'lang':
                        for index,elem in enumerate(changes[ns]['fields'][i]['value']):
                            qual_value =  str(changes[ns]['fields'][i]['qualifier'][index])
                            general = qual_value[:2]
                            try:
                                append_res = xmp.set_localized_text( str(ns), str(i), general ,qual_value, elem.encode('utf-8'), )
                            except XMPError, err:
                                log.error('XMPError in set_localized_text: %s' % err)
                    else: 
                        try:
                            number_of_items = xmp.count_array_items( str(ns), str(i)) 
                        except XMPError, err:
                            log.error('XMPError in count_array_items: %s' % err)
                        item_list = []
                        for idx in xrange(number_of_items):
                            item_list.append(xmp.get_array_item( str(ns), str(i), idx + 1).keys()[0])
                        for index,elem in enumerate(changes[ns]['fields'][i]['value']):
                            # method does_array_item_exist seems to work as expected
                            # so, it is NECESSARY to get all items already in array 
                            # and to check new items with this list
                            if elem.encode('utf-8') not in item_list:
                                try:
                                    append_res = xmp.append_array_item( str(ns), str(i), elem.encode('utf-8'), {'prop_value_is_array':XMP_PROP_VALUE_IS_ARRAY})
                                except XMPError, err:
                                    log.error('XMPError in append_array_items: %s' % err)
        
        if xmpfile.can_put_xmp(xmp):
            try:
                xmpfile.put_xmp(xmp)
                log.debug('Success. Wrote xmp into file.')
            except XMPError, err:
                log.error('Error while writing xmp into file: %s' % err)

        xmpfile.close_file()

        return True

###############################################################################
# Celery task setup
from celery.task import task as celery_task
_SERVER_SINGLETON = XMPEmbedder()
@celery_task
def metadata_synch(component_id, changes):
    return _SERVER_SINGLETON.metadata_synch(component_id, changes)
