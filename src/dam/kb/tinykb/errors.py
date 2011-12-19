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
# Exceptions raised by NotreDAM knowledge base routines.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

class NotFound(Exception):
    '''
    Raised when a class or object is not found in the knowledge base.
    '''
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class ValidationError(Exception):
    '''
    Raised when trying to assign an incompatible value to an object
    attribute managed by the knowledge base.
    '''
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class PendingReferences(Exception):
    '''
    Raised when trying to delete an element which is referenced by
    other objects, classes, etc.
    '''
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)
