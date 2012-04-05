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

def preinit_notredam_kb(connstring=None):
    '''
    Create knowledge base tables which are required *before* creating
    Django tables
    '''
    if connstring is None:
        connstring = notredam_connstring()
    # The 'object' table is also used by Django's models.Object, which
    # only references some columns.  Thus, we need to create the
    # complete table here --- and all the tables it depends from
    # FIXME: try to maintain schema isolation
    s = schema.Schema()
    tables = [s.class_t, s.object_t]
    s.create_tables(connstring, tables)


def init_notredam_kb(connstring=None):
    '''
    Initialize the knowledge base assuming that it is going to
    populate a NotreDAM database
    '''
    if connstring is None:
        connstring = notredam_connstring()
    s = schema.Schema()
    s.init_db(connstring)


def populate_test_kb(connstring=None):
    '''
    Create some testing KB classes and object on the NotreDAM database
    '''
    if connstring is None:
        connstring = notredam_connstring()
    kb_test.test_create_object_classes(connstring)
    kb_test.test_create_derived_classes(connstring)
    kb_test.test_create_derived_class_objects(connstring)

#########################################################################
# Command-line support
#########################################################################
import optparse

if __name__ == '__main__':
    parser = optparse.OptionParser(
        description='Initialize NotreDAM knowledge base.')
    parser.set_defaults(connstring=None, preinit=False,
                        populate_with_test_data=False)
    parser.add_option('-c', '--connstring',
                      dest='connstring', metavar='CONNSTRING',
                      help=('Use CONNSTRING for accessing the SQL DBMS '
                            + '(default: use NotreDAM connstring)'))
    parser.add_option('-p', '--preinit',
                      dest='preinit', action='store_true',
                      help=('Only perform KB pre-initialization, and exit '
                            + 'immediately (default: no)'))
    parser.add_option('-s', '--skip-regular-init',
                      dest='skip_regular_init', action='store_true',
                      help=('Skip regular init (e.g. when the KB is still '
                            'initialized, but the "-t" option is being used) '
                            + '(default: no)'))
    parser.add_option('-t', '--populate-with-test-data',
                      dest='populate_with_test_data', action='store_true',
                      help=('Create test classes and objects after KB '
                            + 'initialization (default: no)'))
    (options, args) = parser.parse_args()

    if options.preinit:
        print 'Pre-initializing knowledge base'
        preinit_notredam_kb(options.connstring)
    else:
        if not options.skip_regular_init:
            print 'Initializing knowledge base'
            init_notredam_kb(options.connstring)

        if options.populate_with_test_data:
            print 'Populating knowledge base with test classes and objects'
            populate_test_kb(options.connstring)
