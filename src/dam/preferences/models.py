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

"""
Preferences are dinamically managed by the developers. 
They can add settings for each DAM Component and they will be automatically displayed to the user.
It can be easily done by using the django admin.
"""

from django.db import models
from django.contrib.auth.models import User
from dam.workspace.models import Workspace

class SettingValue(models.Model):
    """
    Setting available choices (used only if the setting type is one between choice and multiple_choice)
    """
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=512)

    def __unicode__(self):
        return "%s" % (self.name)

class DAMComponent(models.Model):
    """
    DAM Component (for example, Metadata, Geo, Tree, and so on) 
    """
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=512)

    def __unicode__(self):
        return "%s" % (self.name)

class DAMComponentSetting(models.Model):
    """
    Setting of a DAM Component. The settings can be managed by the developers using the django admin. 
    You can add a user setting using the admin interface, it will be automatically displayed to the user when he opens the preferences page.
    You can choose between different types of setting: string, boolean, integer, email, choice or multiple choice. 
    In this way, you can ask the user to choose one or more values between a list of choices, or you can ask him to enter a string, an email, 
    an integer or choose between Yes or No. Finally you can read and use the value in your DAM component using the method get_user_setting 
    defined in dam.preferences.views module. 
    """
    name = models.CharField(max_length=64)
    caption = models.CharField(max_length=64)
    description = models.CharField(max_length=512)
    default_value = models.CharField(max_length=512)  #please give a default value for the setting
    choices = models.ManyToManyField(SettingValue, related_name="choices", blank=True, null=True) # if setting type is one between choice and multiple_choice, the available choices are stored inside SettingValue istances.   
    component = models.ForeignKey(DAMComponent)
    type = models.CharField(max_length=16, choices=(('choice', 'choice'), ('int', 'int'), ('string','string'), ('boolean', 'boolean'), ('email', 'email'), ('multiple_choice', 'multiple_choice')))
    setting_level = models.CharField(max_length=16, default="S", choices=(('S', 'System'), ('U', 'User'), ('W','Workspace')))

    def __unicode__(self):
        return "%s" % (self.name)

    def get_system_preference(self):
        try:
            pref = SystemSetting.objects.get(component_setting=self)
        except:
            pref = None

        return pref

    def get_user_preference(self, obj):
        try:
            if obj:
                pref = UserSetting.objects.get(component_setting=self, user=obj)
            else:
                pref = None
        except:
            pref = None

        return pref

    def get_ws_preference(self, obj):
        try:
            if obj:
                pref = WSSetting.objects.get(component_setting=self, user=obj)
            else:
                pref = None
        except:
            pref = None

        return pref

    def get_preferences_by_level(self, user, workspace):
        preferences = {}

        preferences['S'] = self.get_system_preference()
        preferences['U'] = self.get_user_preference(user)
        preferences['W'] = self.get_ws_preference(workspace)
            
        return preferences
        
class UserSetting(models.Model):
    """
    Value chosen by the user for the component_setting
    """ 
    component_setting = models.ForeignKey(DAMComponentSetting)
    user = models.ForeignKey(User)
    value = models.CharField(max_length=128, blank=True, null=True)
    user_choices = models.ManyToManyField(SettingValue, blank=True, null=True)
    
class WSSetting(models.Model):
    """
    Value chosen by the user for the component_setting
    """ 
    component_setting = models.ForeignKey(DAMComponentSetting)
    user = models.ForeignKey(Workspace)
    value = models.CharField(max_length=128, blank=True, null=True)
    user_choices = models.ManyToManyField(SettingValue, blank=True, null=True)

class SystemSetting(models.Model):
    """
    Value chosen by the user for the component_setting
    """ 
    component_setting = models.ForeignKey(DAMComponentSetting)
    value = models.CharField(max_length=128, blank=True, null=True)
    user_choices = models.ManyToManyField(SettingValue, blank=True, null=True)
