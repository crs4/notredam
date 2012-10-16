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
import hashlib
import time
import random


class Application(models.Model):
    name = models.CharField(max_length = 50)
    api_key = models.CharField(max_length = 50,  unique = True)
    
    def save(self,  *args, **kwargs):        
        if not self.id and not self.api_key:            
            self.api_key = hashlib.sha1(unicode(time.time() * random.random())).hexdigest()
        super(Application, self).save(*args, **kwargs)

class Secret(models.Model):
    value = models.CharField(max_length = 50,  unique = True)
    application = models.ForeignKey(Application)
    user = models.ForeignKey(User)
    
    class Meta:
        unique_together = (("application", "user"),)

    
    def save(self,  *args, **kwargs):        
        if not self.id and not self.value:            
            self.value = hashlib.sha1(unicode(time.time() * random.random())).hexdigest()
        super(Secret, self).save(*args, **kwargs)
    

    
