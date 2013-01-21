#########################################################################
#
# NotreDAM, Copyright (C) 2012, Sardegna Ricerche.
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
# Some decorators
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

# Synchronize a function using the given lock
def synchronized(lock):
    def wrap(f):
        def locked_f(*args, **kwargs):
            with lock:
                return f(*args, **kwargs)
        return locked_f
    return wrap
