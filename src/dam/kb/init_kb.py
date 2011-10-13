#!/usr/bin/env python
#########################################################################
#
# NotreDAM, Copyright (C) 2011, Sardegna Ricerche.
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
#
# Initialization script for NotreDAM knowledge base.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

from tinykb import schema
from tinykb import test as kb_test
from util import notredam_connstring

def init_notredam_kb():
    '''
    Initialize the knowledge base assuming that it is going to
    populate a NotreDAM database
    '''
    connstring = notredam_connstring()
    schema.init_db(connstring)


def populate_test_kb():
    '''
    Create some testing KB classes and object on the NotreDAM database
    '''
    connstring = notredam_connstring()
    kb_test.test_create_object_classes(connstring)
    kb_test.test_create_derived_classes(connstring)
    kb_test.test_create_derived_class_objects(connstring)

#########################################################################
# Command-line support
#########################################################################
import optparse

parser = optparse.OptionParser(
    description='Initialize NotreDAM knowledge base.')
parser.set_defaults(populate_with_test_data=False)
parser.add_option('-t', '--populate-with-test-data',
                  dest='populate_with_test_data', action='store_true',
                  help='Create test classes and objects (default: no)')
(options, args) = parser.parse_args()

if __name__ == '__main__':
    print 'Initializing knowledge base'
    init_notredam_kb()
    if options.populate_with_test_data:
        print 'Populating knowledge base with test classes and objects'
        populate_test_kb()
