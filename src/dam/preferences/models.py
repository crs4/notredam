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
Preferences are dinamically managed by developers. 
They can add settings for each DAM Component and they will be automatically displayed to the user.
It can be easily done by using the django admin.
"""

from django.db import models
from django.contrib.auth.models import User
from dam.workspace.models import DAMWorkspace as Workspace

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

class SettingManager(models.Manager):

    def clear_preferences(self, obj, setting):
        """
        Clear the preferences for the given object (it can be a user, a workspace or None for system preferences)
        @param obj an instance of django.contrib.auth.User or dam.workspace.models.Workspace or None
        @param setting setting instance of dam.preference.models.DAMComponentSetting
        """
    
        if isinstance(obj, User):
            UserSetting.objects.filter(user=obj, component_setting=setting).delete()
        elif isinstance(obj, Workspace):
            WSSetting.objects.filter(user=obj, component_setting=setting).delete()
        else:
            SystemSetting.objects.filter(component_setting=setting).delete()
    
    def create_preferences(self, obj, setting, value, choices):
        """
        Save the preference of the given obj (it can be a user, a workspace or None for system preferences)
        @param obj an instance of django.contrib.auth.User or dam.workspace.models.Workspace or None
        @param setting setting instance of dam.preference.models.DAMComponentSetting
        @param value the value of the given setting
        @param choices a list of choice
        """
    
        if isinstance(obj, User):
            pref = UserSetting.objects.create(user=obj, component_setting=setting, value=value)
        elif isinstance(obj, Workspace):
            pref = WSSetting.objects.create(user=obj, component_setting=setting, value=value)
        else:
            pref = SystemSetting.objects.create(component_setting=setting, value=value)
        
        for c in choices:
            pref.user_choices.add(c)
    
    def save_preference(self, request, obj):
        """
        Get the preference value from request.POST and save it
        """
        for key in request.POST.keys():
            if key.startswith('pref__'):
                setting_id = key.split("__")[1]
                setting = self.get(pk=setting_id)
                self.clear_preferences(obj, setting)
            
                choices = []
                if setting.type == 'choice': 
                    setting_value = request.POST.get(key)
                    if setting_value :
                        choice = setting.choices.get(name = setting_value)
                        choices.append(choice)
                        value = choice.name
    
                elif setting.type == 'multiple_choice':
                    setting_value = request.POST.getlist(key)
                    for key in setting_value:
                        choice = setting.choices.get_or_create(name = key)[0]
                        
                        choices.append(choice)
                    value = ",".join([x.name for x in choices])	
                else:
                    setting_value = request.POST.get(key)
                    value = setting_value
    
                self.create_preferences(obj, setting, value, choices)

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
#    is_preferences = models.BooleanField(default = True)
    objects = SettingManager()

    def __unicode__(self):
        return "%s" % (self.name)
        
    def get_user_setting_by_level(self, workspace=None, user=None, force_priority=None):
        """
        Returns the user value of the given setting, or the default value if user didn't make a choice yet  . 
        @param user user instance of django.contrib.auth.User
        @param setting setting instance of dam.preference.models.DAMComponentSetting
        """
        
        preferences_list = self.get_preferences_by_level(user, workspace)
    
        if force_priority:
            priority_levels = force_priority
        elif self.setting_level == 'W':
            priority_levels = ['W', 'U', 'S']
        elif self.setting_level == 'U':
            priority_levels = ['U', 'S']
        else:
            priority_levels = ['S']
        
        for l in priority_levels:
            user_setting = preferences_list[l]
            if user_setting:
                break
    
        if self.type == 'choice' or self.type == 'multiple_choice': 
            if user_setting is None:
                value = self.default_value
            else:
                value = ",".join([x.name for x in user_setting.user_choices.all()])
        else:
            if user_setting is None:
                value = self.default_value
            else:
                value = user_setting.value
                
        return value
        
    def get_user_setting(self, user, workspace=None):
        """
        Returns the user value of the given setting, or the default value if user didn't make a choice yet  . 
        @param user user instance of django.contrib.auth.User
        """
    
        value = self.get_user_setting_by_level(workspace=workspace, user=user)
    
        return value        
    
    def get_system_preference(self):
        try:
            pref = SystemSetting.objects.get(component_setting=self)
        except SystemSetting.DoesNotExist:
            pref = None

        return pref

    def get_user_preference(self, obj):
        try:
            if obj:
                pref = UserSetting.objects.get(component_setting=self, user=obj)
            else:
                pref = None
        except UserSetting.DoesNotExist:
            pref = None

        return pref

    def get_ws_preference(self, obj):
        try:
            if obj:
                pref = WSSetting.objects.get(component_setting=self, user=obj)
            else:
                pref = None
        except WSSetting.DoesNotExist:
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
