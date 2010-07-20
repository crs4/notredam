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
from django.contrib.auth.forms import UserCreationForm

class Registration(UserCreationForm):

    """
    Form for user registration
    """

    email = forms.EmailField()
    
    def __init__(self,  *args,  **kwargs):
        super(Registration,  self).__init__(*args,  **kwargs)
        self.fields['username'].help_text = "30 characters or fewer. Alphanumeric characters only (letters, digits and underscores). "
   
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name",  "email",)
        
    def get_ordered_fields(self):
        return [self.fields['username']]
