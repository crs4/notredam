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

from dam.workspace.models import DAMWorkspace

import uuid

class UploadManager(models.Manager):

    def get_user_ws_from_url(self, url):
        """
        Retrieve user and workspace from the unique upload url
        """
    
        find_url = self.get(url=url)
        user = find_url.user
        workspace = find_url.workspace
    
        find_url.delete()
    
        return (user, workspace)

class UploadURL(models.Model):
    """ 
    Unique upload url for user (due to flash cookie bug) 
    """

    user = models.ForeignKey(User)
    url = models.CharField(max_length=40, unique = True)
    workspace = models.ForeignKey(DAMWorkspace)
    objects = UploadManager()
    
    def save(self,  *args, **kwargs):
        if not self.id and not self.url:
            self.url = uuid.uuid4().hex
        super(UploadURL, self).save(*args, **kwargs)




