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

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from dam.preferences.models import UserSetting, SettingValue, DAMComponent, DAMComponentSetting, SystemSetting, WSSetting 
from dam.workspace.models import DAMWorkspace as Workspace
from dam.metadata.models import MetadataLanguage

import logger

def get_metadata_default_language(user, workspace=None):
    """
    Returns default metadata language for the given user (or the application default)
    """
    component=DAMComponent.objects.get(name__iexact='metadata')
    setting=DAMComponentSetting.objects.get(component=component, name__iexact='default_metadata_language')
    comma_separated_languages = get_user_setting(user, setting, workspace)
    list_of_languages = comma_separated_languages.split(',')
    return list_of_languages[0]

@login_required
def get_lang_pref(request):
    """
    Returns the list of available metadata languages chosen by the given user
    """
    workspace = request.session['workspace']
    
    user = User.objects.get(pk=request.session['_auth_user_id'])
    component=DAMComponent.objects.get(name__iexact='metadata')
    setting=DAMComponentSetting.objects.get(component=component, name__iexact='supported_languages')
    comma_separated_languages = get_user_setting(user, setting, workspace)
    list_of_languages = comma_separated_languages.split(',')
    resp = {'languages':[]}
    default_language = get_metadata_default_language(user,workspace)
    languages = MetadataLanguage.objects.filter(code__in=list_of_languages).values('code', 'language', 'country')
    for l in languages:
        if l['code'] == default_language:
            l['default_value'] = True
        resp['languages'].append(l)
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_user_settings(request):
    """
    Returns the list of Settings and the values for the given user
    """
    user = User.objects.get(pk=request.session['_auth_user_id'])
    workspace = request.session.get('workspace')
    settings = DAMComponentSetting.objects.filter(setting_level__in=['U', 'W']).order_by('caption')
    data = {'prefs':[]}
    for s in settings:
        choices = [[c.name, c.description] for c in s.choices.all()]
        my_value = get_user_setting_by_level(s, workspace, user, ['U', 'W', 'S'])
        data['prefs'].append({'id':'pref__%d' % s.id, 'name':s.name,'caption': s.caption,'name_component': s.component.name,  'type': s.type,  'value': my_value,  'choices':choices})
    return HttpResponse(simplejson.dumps(data))    

def get_user_setting_by_level(setting, workspace=None, user=None, force_priority=None):
    """
    Returns the user value of the given setting, or the default value if user didn't make a choice yet  . 
    @param user user instance of django.contrib.auth.User
    @param setting setting instance of dam.preference.models.DAMComponentSetting
    """
    
    preferences_list = setting.get_preferences_by_level(user, workspace)

    if force_priority:
        priority_levels = force_priority
    elif setting.setting_level == 'W':
        priority_levels = ['W', 'U', 'S']
    elif setting.setting_level == 'U':
        priority_levels = ['U', 'S']
    else:
        priority_levels = ['S']
    
    for l in priority_levels:
        user_setting = preferences_list[l]
        if user_setting:
            break

    if setting.type == 'choice' or setting.type == 'multiple_choice': 
        if user_setting is None:
            value = setting.default_value
        else:
            value = ",".join([x.name for x in user_setting.user_choices.all()])
    else:
        if user_setting is None:
            value = setting.default_value
        else:
            value = user_setting.value
    return value
    
def get_user_setting(user, setting, workspace=None):
    """
    Returns the user value of the given setting, or the default value if user didn't make a choice yet  . 
    @param user user instance of django.contrib.auth.User
    @param setting setting instance of dam.preference.models.DAMComponentSetting
    """

    value = get_user_setting_by_level(setting, workspace=workspace, user=user)

    return value
 
def _clear_preferences(obj, setting):
    """
    Returns the user value of the given setting, or the default value if user didn't make a choice yet  . 
    @param user user instance of django.contrib.auth.User
    @param setting setting instance of dam.preference.models.DAMComponentSetting
    """

    if isinstance(obj, User):
        UserSetting.objects.filter(user=obj, component_setting=setting).delete()
    elif isinstance(obj, Workspace):
        WSSetting.objects.filter(user=obj, component_setting=setting).delete()
    else:
        SystemSetting.objects.filter(component_setting=setting).delete()

def _create_preferences(obj, setting, value, choices):
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

def _save_preference(request, obj):
    """
    Get the preference value from request.POST and save 
    """
    for key in request.POST.keys():
        if key.startswith('pref__'):
            setting_id = key.split("__")[1]
            setting = DAMComponentSetting.objects.get(pk=setting_id)
            _clear_preferences(obj, setting)
        
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

            _create_preferences(obj, setting, value, choices)

@login_required
def save_pref(request):
    """
    Save user preference
    """

    try:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        
        _save_preference(request, user)
                            
        return HttpResponse(simplejson.dumps({'success': True}))
    except Exception,  ex:
        logger.exception(ex)
        raise ex
    
@login_required
def save_system_pref(request):
    """
    Save system preference (dam admin)
    """
    try:

        _save_preference(request, None)
                            
        return HttpResponse(simplejson.dumps({'success': True}))
    except Exception,  ex:
        logger.exception(ex)
        raise ex    

@login_required
def save_ws_pref(request):
    """
    Save workspace preference
    """
    try:

        workspace = request.session.get('workspace')

        _save_preference(request, workspace)
                            
        return HttpResponse(simplejson.dumps({'success': True}))
    except Exception,  ex:
        logger.exception(ex)
        raise ex 
    
@login_required
def get_ws_settings(request):
    """
    Get workspace settings
    """
    workspace = request.session.get('workspace')
    settings = DAMComponentSetting.objects.filter(setting_level='W')
    data = {'prefs':[]}
    for s in settings:
        choices = [[c.name, c.description] for c in s.choices.all()]
        value = get_user_setting_by_level(s, workspace)
        data['prefs'].append({'id': 'pref__%d'%s.id, 'name':s.name,'caption': s.caption,'name_component': s.component.name,  'type': s.type,  'value': value,  'choices':choices})
    return HttpResponse(simplejson.dumps(data))    

