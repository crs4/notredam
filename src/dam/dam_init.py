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
# Initialization script for NotreDAM
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

import optparse
import os
import sys

parser = optparse.OptionParser(
    description='Initialize NotreDAM database.')
parser.set_defaults(populate_with_test_data=False)
parser.add_option('-t', '--populate-with-test-data',
                  dest='populate_with_test_data', action='store_true',
                  help=('Create test classes and objects after KB '
                        + 'initialization (default: no)'))
(options, args) = parser.parse_args()

# Pre-initialize the DAM knowledge base
print '* Pre-initializing knowledge base...'
cmdline = 'python kb/init_kb.py --preinit'
ret = os.system(cmdline)
if not 0 == ret:
    print '*** Error: command "%s" returned %d exit status' % (cmdline, ret)
    sys.exit(ret)

# Setup Django DB tables
print "\n* Setting up Django DB tables..."
cmdline = 'python manage.py syncdb --noinput'
ret = os.system(cmdline)
if not 0 == ret:
    print '*** Error: command "%s" returned %d exit status' % (cmdline, ret)
    sys.exit(ret)

# Finish KB initialization
cmdline = 'python kb/init_kb.py'
add_msg = '...'
if options.populate_with_test_data:
    cmdline += ' --populate-with-test-data'
    add_msg = ' (including test data)...'
print "\n* Completing knowledge base setup" + add_msg
ret = os.system(cmdline)
if not 0 == ret:
    print '*** Error: command "%s" returned %d exit status' % (cmdline, ret)
    sys.exit(ret)

# We're done!
print "\n* NotreDAM initialization completed."
