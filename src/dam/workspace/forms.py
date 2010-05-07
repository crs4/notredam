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

from django import forms
from django.contrib.auth.models import User 

class AdminWorkspaceForm(forms.Form):

    def __init__(self,  ws,   *args,  **kwargs):
        super(AdminWorkspaceForm,  self).__init__(*args,  **kwargs)
        self.ws = ws
        self.fields['name'] .initial= ws.name
        self.fields['name'] ._id = ws.pk
        self.fields['description'] .initial= ws.description        
        
    name = forms.CharField(required = True)    
    description = forms.CharField(required = False, widget=forms.Textarea(attrs={'rows':'5'}))    
