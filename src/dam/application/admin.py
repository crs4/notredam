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

from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from dam.workspace.models import Workspace
from django import forms

from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.views.decorators.cache import never_cache
from django.shortcuts import render_to_response
from django import http, template

from django.template.loader import render_to_string

#TODO: import exceptions...
class ModAdmin(admin.sites.AdminSite):
    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all the installed
        apps that have been registered in this site.
        """
        app_dict = {}
        user = request.user
        for model, model_admin in self._registry.items():
            app_label = model._meta.app_label
            has_module_perms = user.has_module_perms(app_label)

            if has_module_perms:
                perms = {
                    'add': model_admin.has_add_permission(request),
                    'change': model_admin.has_change_permission(request),
                    'delete': model_admin.has_delete_permission(request),
                }

                # Check whether user has any perm for this module.
                # If so, add the module to the model_list.
                if True in perms.values():
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
                        'perms': perms,
                    }
                
                    try: 
                        label = model_admin.label
                    except:
                        label = app_label

                    
                    if label in app_dict:
                        app_dict[label]['models'].append(model_dict)
                    else:
                        app_dict[label] = {
#                            'name': app_label.title(),
                            'name': label.title(),
                            'app_url': app_label + '/',
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                        }

        # Sort the apps alphabetically.
        app_list = app_dict.values()
        app_list.sort(lambda x, y: cmp(x['name'], y['name']))

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(lambda x, y: cmp(x['name'], y['name']))

        context = {
            'title': _('Site administration'),
            'app_list': app_list,
            'root_path': self.root_path,
        }
        context.update(extra_context or {})
        return render_to_response(self.index_template or 'admin/index.html', context,
            context_instance=template.RequestContext(request)
        )
        
mod_admin = ModAdmin()
    
class WorkspaceInline(admin.StackedInline):  
    model = Workspace
    fieldsets = (
            (None, 
             {'fields': ('name',  'description')} ),)
    max_num = 0
    extra = 1
    verbose_name_plural = 'creator of workspaces'
    
    
class MultipleSelectWithPop(forms.SelectMultiple):
    def __init__(self, url,  *args,  **kwargs):
        super(MultipleSelectWithPop,  self).__init__(*args,  **kwargs)
        self.url = url
        
    def render(self, name, *args, **kwargs):
        html = super(MultipleSelectWithPop, self).render(name, *args, **kwargs)
        popupplus = render_to_string("admin/popup_plus.html", {'field': name,  'url':self.url})
        return html+popupplus
        
class UserForm(forms.ModelForm):
    
    def __init__(self,  *args,  **kwargs):
        super(UserForm,  self).__init__(*args,  **kwargs)
        if kwargs.has_key('instance'):
            wss = kwargs['instance'].workspaces.all()
            self.fields['member_of_workspaces'].initial = [ws.pk for ws in wss]        

#    member_of_workspaces = forms.ModelMultipleChoiceField(queryset=Workspace.objects.all(),  required = False)
    member_of_workspaces = forms.ModelMultipleChoiceField(queryset=Workspace.objects.all(),  required = False,  widget = MultipleSelectWithPop(url = '/mod_admin/workspace/workspace/add/'))

    class Meta:
        model = User
        
class ModUserAdmin(UserAdmin):    
        
    fieldsets = None
    form = UserForm
    label = 'main'
#    filter_horizontal = ('member_of_workspaces', )
  
    fields = ('username','password',  'first_name' ,  'last_name',  'email',  'is_superuser',  'last_login',  'date_joined',  'member_of_workspaces')   
#    
##    inlines = [WorkspaceInline]
    
    class Meta:
        js = ("/media/js/admin/RelatedObjectLookups.js",)


    
    def save_model(self, request, obj, form, change):
        obj.save()
        wss = form.cleaned_data['member_of_workspaces']
        obj.workspaces.remove(*obj.workspaces.all())
        obj.workspaces.add(*wss)
        
#admin.site.unregister(User)
#admin.site.register(User, ModUserAdmin)

mod_admin.register(User, ModUserAdmin)
