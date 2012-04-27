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
# Access level definitions for KB class and catalog hierarchies.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

'''
This module contains several constants describing in which way a
:py:class:`Workspace <orm.Workspace>` is allowed to access a KB class
hierarchy (starting from a :py:class:`KBRootClass <orm.KBRootClass>`
instance).

.. note:: The access rules are not enforced by TinyKB: they are
          merely stored an retrieved to/from the knowledge base.
'''

__all__ = ['OWNER', 'READ_ONLY', 'READ_WRITE', 'READ_WRITE_OBJECTS']

## Valid access types for items, class hierarchies and root catalog
## entries
OWNER = 'owner'
'''
A workspace owns a class hierarchy, and thus it is allowed to delete
it.
'''

READ_ONLY = 'read-only'
'''
A workspace can access a class hierarchy in read-only mode.
'''

READ_WRITE = 'read-write'
'''
A workspace can access a class hierarchy and modify it, but it is
not allowed to delete it.
'''

READ_WRITE_OBJECTS = 'read-write-objects'
'''
A workspace can access a class hierarchy in read-only mode, but it is
allowed to modify its objects.
'''
