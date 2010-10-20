import os
import inspect
from twisted.internet import reactor
from mediadart import log
from mediadart.config import Configurator
from mediadart.storage import Storage
from mediadart.mqueue.mqserver import MQServer, RPCError
from mediadart.utils import default_start_mqueue
from libxmp import XMPFiles, XMPError, files, XMPMeta
from libxmp.consts import *

class XMPEmbedder(MQServer):

    _id = 'urn:uuid:a7da26e7-f37b-4c88-a80a-3f46b58f1fa9'   # required by jsonrpc

    def __init__(self):
        MQServer.__init__(self)
        self.__impl = XMPEmbedderImpl()

    def mq_metadata_synch(self, resource_id, metadata_dict):
        ""
        return self.__impl.metadata_synch(resource_id, metadata_dict)

class XMPEmbedderImpl:

    def __init__(self):
        self._fc = Storage()
   

    def metadata_synch(self, component_id, changes):
    
        # get xmp 
        
        # the filename is needed because the extension is unknown, the following line of code is
        # tmp code because c.ID will include extension file (not only basename) 
        # in the new MediaDART release
        #print 'MediaDART resource path: ', md_res_path
        try:
            myxmpfilename = str(self._fc.abspath(component_id))
        except Exception, err:
            print '\n    found some problems getting filename, err: ', err, '\n'

        xmpfile = XMPFiles(file_path=myxmpfilename, open_forupdate=files.XMP_OPEN_FORUPDATE)
        xmp = xmpfile.get_xmp()

        if not xmp:
            xmp = XMPMeta()
        
        for ns in changes.keys():
            #print 'Property ', str(i[0]),':', str(i[1])
            # first of all check if namespace str(i[0]) and property name str(i[1]) exist
            prefix = None
            try:
                prefix = xmp.get_prefix_for_namespace(str(ns))
            except XMPError, err:
                print 'Error in get_prefix_for_namespace: ',err
            if prefix == None:
                #print 'prefix ', prefix[:-1] , ' does not exist.'
                try:
                    log.debug('%s %s' % (str(ns), str(changes[ns]['prefix'])))
                    res = xmp.register_namespace(str(ns), str(changes[ns]['prefix'])) # CHANGE ME
                    #print 'register_namespace gave res = ', res
                except XMPError, err:
                    print 'Error in register_namespace: ',err
            for i in changes[ns]['fields'].keys():
                try:
                    property_exists = xmp.does_property_exist(str(ns), str(i))
                    #print 'property_exists = ', property_exists
                except XMPError, err:
                    print 'Error in does_property_exist: ',err
                #if property_exists == False:
                    #print 'prorperty ', str(i[0]) , ':',str(i[1]),' does not exist.'
                if changes[ns]['fields'][i]['is_array'] == 'not_array':
                    #print '**************** NOT ARRAY - Property ', str(i[0]),':', str(i[1]),' = ', str(changes[i]['value'][0]) , ' *****************************'
                    if changes[ns]['fields'][i]['xpath'] != []: # so it is a structure 
                        if property_exists == False:
                            # if it is a structure and the property does not exist, it must be created, otherwise, it will not be set.
                            try:
                                res = xmp.set_property(str(ns), str(i),'',prop_value_is_struct = XMP_PROP_VALUE_IS_STRUCT) 
                            except XMPError, err:
                                print 'XMPError in set_property in case of structure: ',err
                            except Exception, err:
                                print 'Error in set_property in case of structure: ',err
                        for index, elem in enumerate(changes[ns]['fields'][i]['value']):
                            cleaned_xpath = re.sub( r"\[.\]", "", str(changes[ns]['fields'][i]['xpath'][index]) )
                            #print 'cleaned xpath: ',cleaned_xpath
                            try:
                                xmp.set_property( str(ns), cleaned_xpath, str(elem) )
                            except XMPError, err:
                                print 'Error in set_property in case of structure: ',err
                            except Exception, err:
                                print 'Error in set_property in case of structure: ',err
                    elif changes[ns]['fields'][i]['type'] == 'date': 
                        mydate = DateTimeFromString(changes[ns]['fields'][i]['value'][0])
                        mydate1 = datetime(mydate.year, mydate.month, mydate.day, mydate.hour, mydate.minute, int(mydate.second))
                        try:
                            xmp.set_property_datetime( str(ns), str(i), mydate1)
                        except XMPError, err:
                            print 'XMPError in set_property_datetime: ',err
                        except Exception, err:
                            print 'Error in set_property_datetime: ',err
                    elif changes[ns]['fields'][i]['type'] == 'bool': 
                        try:
                            xmp.set_property_bool( str(ns), str(i), bool(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            print 'Error in set_property_bool: ',err
                    elif changes[ns]['fields'][i]['type'] == 'int': 
                        try:
                            xmp.set_property_int( str(ns), str(i), int(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            print 'Error in set_property_int: ',err
                    elif changes[ns]['fields'][i]['type'] == 'float': 
                        try:
                            xmp.set_property_float( str(ns), str(i), float(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            print 'Error in set_property_float: ',err
                    elif changes[ns]['fields'][i]['type'] == 'long': 
                        try:
                            xmp.set_property_long( str(ns), str(i), long(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            print 'Error in set_property_long: ',err
                    else:
                        try:
                            log.debug('%s %s %s' % (str(ns), str(i), str(changes[ns]['fields'][i]['value'][0])))
                            xmp.set_property( str(ns), str(i), str(changes[ns]['fields'][i]['value'][0]))
                        except XMPError, err:
                            print 'Error in set_property: ',err
                else:
         
                    #print '**************** Property IS ARRAY ', str(i[0]),':', str(i[1]) , ' *****************************'
                    if changes[ns]['fields'][i]['xpath'] != []: # so it is a structure 
                        print 'array of structures is not supported by xmplib'
                        continue
                    if property_exists == False:
                        # if it is an array and the property does not exist, it must be created, otherwise, it will not be set.
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
                            print 'Error in set property: ',err
                    if changes[ns]['fields'][i]['type'] == 'lang':
                        for index,elem in enumerate(changes[ns]['fields'][i]['value']):
                            qual_value =  str(changes[ns]['fields'][i]['qualifier'][index])
                            general = qual_value[:2]
                            try:
                                append_res = xmp.set_localized_text( str(ns), str(i), general ,qual_value, str(elem), )
                            except XMPError, err:
                                print 'Error in set_localized_text: ',err
                    else: 
                        try:
                            number_of_items = xmp.count_array_items( str(ns), str(i)) 
                        except XMPError, err:
                            print 'Error in xmp count_array_items: ',err
                        item_list = []
                        for idx in xrange(number_of_items):
                            item_list.append(xmp.get_array_item( str(ns), str(i), idx + 1).keys()[0])
                        for index,elem in enumerate(changes[ns]['fields'][i]['value']):
                            # method does_array_item_exist seems to work as expected
                            # so, it is NECESSARY to get all items already in array and to check new items with
                            # this list
                            if str(elem) not in item_list:
                                try:
                                    append_res = xmp.append_array_item( str(ns), str(i), str(elem), {'prop_value_is_array':XMP_PROP_VALUE_IS_ARRAY})
                                except XMPError, err:
                                    print 'Error: ',err
        
        if xmpfile.can_put_xmp(xmp):
            try:
                log.debug('before put_xmp %s' % xmp)
                xmpfile.put_xmp(xmp)
                print 'Wrote xmp into file'
            except XMPError, err:
                print 'Error while writing xmp into file: ', err

        xmpfile.close_file()

        return True
        
def start_server(broker_ip=None, broker_port=None, username=None, password=None, args=[], vhost='/'):
    default_start_mqueue(XMPEmbedder, broker_ip, broker_port, username, password, args, vhost)

if __name__=='__main__':
    import sys
    start_server(
        '127.0.0.1',
        5672,
        'guest',
        'guest',
        )
    reactor.run()
