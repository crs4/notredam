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

from django.db import models
from django.contrib.auth.models import User
import time
import hashlib

class VerificationUrl(models.Model):
    """ 
    Confirmation url sent to the user's email 
    address during user registration process
    """
    user = models.ForeignKey(User, unique = True)
    url = models.CharField(max_length=40,  unique = True)
    
    def save(self,  *args, **kwargs):
        if not self.id and not self.url:            
            self.url = hashlib.sha1(unicode(time.time() )).hexdigest()
        super(VerificationUrl, self).save(*args, **kwargs)

