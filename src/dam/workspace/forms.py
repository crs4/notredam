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
from django.forms import ModelForm  
from django.contrib.auth.models import User 
from dam.workspace.models import *
from itertools import chain
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from models import *
import logger
#from treeview import views as treeview

        
class AdmiUserExtraForm(forms.Form):
    def __init__(self,  user,   *args,  **kwargs):
        super(AdmiUserExtraForm,  self).__init__(*args,  **kwargs)
        self.user = user
        self.fields['workspaces'].widget.attrs= { 'onClick': 'update_workspace_permissions_form(%s);'%user.pk, }
        self.fields['available_workspaces'].widget.attrs= { 'id':'id_user_workspaces',  'class':"vSelectMultipleField",   }
        self.fields['available_workspaces'].initial = [ws.pk for ws in Workspace.objects.filter(members = user)] 
        print "self.fields['available_workspaces'].initial ",  self.fields['available_workspaces'].initial 
        self.fields['available_permissions'].widget.attrs= { 'id':'id_user_workspace_permissions',  'class':'vSelectMultipleField',  }
#        self.fields['ws_groups'].queryset = WorkspacePermissionsGroup.objects.filter(workspace = workspace)
#        self.fields['ws_groups'].initial = [perm.pk for perm in  WorkspacePermissionsGroup.objects.filter(users = user,  workspace = workspace)]
        self.fields['ws_groups'].widget.attrs = {'id':'ws_groups',  'class':'vSelectMultipleField',}
        
        
    workspaces = forms.ModelChoiceField(queryset = Workspace.objects.all(),  )    
    available_workspaces= forms.ModelMultipleChoiceField(queryset = Workspace.objects.all(),  )    
    available_permissions = forms.ModelMultipleChoiceField(queryset = WorkSpacePermission.objects.none())
    ws_groups = forms.ModelMultipleChoiceField(queryset = WorkspacePermissionsGroup.objects.none() )    


class AdminWorkspaceMembersForm(forms.Form):
    def __init__(self,  ws, user,    *args,  **kwargs):
        super(AdminWorkspaceMembersForm,  self).__init__(*args,  **kwargs)        
        
        self.fields['groups'].queryset = ws.workspacepermissionsgroup_set.all()  
        self.fields['groups'].initial = [g.pk for g in user.workspacepermissionsgroup_set.all()]
        self.fields['groups'].widget.attrs = {'id':'groups'}    
        
        self.fields['ws_permissions'].widget.attrs = {'id':'permissions'}   
        self.fields['ws_permissions'].initial = [perm.pk for perm in WorkSpacePermission.objects.filter(workspacepermissionassociation__workspace = ws, workspacepermissionassociation__users = user)]
        

    
    groups = forms.ModelMultipleChoiceField(queryset = WorkspacePermissionsGroup.objects.all(), required = False, widget = forms.CheckboxSelectMultiple)                  
    ws_permissions = forms.ModelMultipleChoiceField(queryset = WorkSpacePermission.objects.all(), required = False,  widget = forms.CheckboxSelectMultiple)    
    
    
    

class AdminWorkspaceGroupsForm(forms.Form):
    def __init__(self,   ws, group=None ,   *args,  **kwargs):
        super(AdminWorkspaceGroupsForm,  self).__init__(*args,  **kwargs)     
       
#        self.fields['members'] .widget.attrs = {'id':'members'}
#        self.fields['members'].queryset = ws.members.all()        
        self.fields['permissions'].widget.attrs = {'id':'permissions'}    
        if group .pk:
#            self.fields['members'].initial = [u.pk for u in group.users.all()]
            self.fields['name'].initial = group.name
            self.fields['permissions'].initial= [perm.pk for perm in group.permissions.all()] 
        
        
        
    
  
    name = forms.CharField(label="Name")        
#    members = forms.ModelMultipleChoiceField(queryset = User.objects.none(), required = False)    
    permissions = forms.ModelMultipleChoiceField(queryset = WorkSpacePermission.objects.all(), required = False,  widget = forms.CheckboxSelectMultiple,  label ="Permissions" )    
    


class WorkspaceName(forms.CharField):
    def __init__(self, id = None,  *args, **kwargs):
        super(WorkspaceName,  self).__init__(*args, **kwargs)
        self._id = id
        
        
    def clean(self, value):
        
        if not value:
            raise forms.ValidationError('This field is required')
        
        if self._id != None:
            
            if Workspace.objects.filter(name__iexact=value).exclude(id=self._id).count() > 0:
                logger.debug('name %s already used, please choose another value' %value)
                raise forms.ValidationError('name %s already used, please choose another value' %value)
        else:
            if Workspace.objects.filter(name__iexact=value).count() > 0:
                logger.debug('self._id %s'%self._id )
                logger.debug('name "%s" already used, please choose another value' %value)
                raise forms.ValidationError('name "%s" already used, please choose another value' %value)
        return value
    


class AdminWorkspaceForm(forms.Form):
    def __init__(self,  ws,   *args,  **kwargs):
        super(AdminWorkspaceForm,  self).__init__(*args,  **kwargs)
        self.ws = ws
        self.fields['name'] .initial= ws.name
        self.fields['name'] ._id = ws.pk
        self.fields['description'] .initial= ws.description        
        
#    ws_name = WorkspaceName()    
    name = forms.CharField(required = True)    
    description = forms.CharField(required = False, widget=forms.Textarea(attrs={'rows':'5'}))    




#    def clean_public(self):
#        value = self.cleaned_data['public']
#        if self.ws.pk:
#            if value and not self.ws.public:
#                public_items = self.ws.items.all().filter(workspaces__in = Workspace.objects.filter(public = True).exclude(pk = self.ws.pk))
#                n_public_items = public_items.count()
#                
#                if n_public_items > 0:
#                    print 'raising error'
#                    item_ids = ''
#                    for item in public_items:
#                        item_ids += 'item_id=%s&'%item.pk
#                    html = """
#                    <script>
#                    function move_items(remove, move_public){
#                        new Ajax.Request('/add_items_to_ws/', {parameters:'%s&ws_id=%s&remove=' +remove+ '&current_ws_id=%s&move_public=' +move_public, 
#                        onComplete: function(o){ $('save_button').click();}});  
#                    }
#                  
#                    </script>
#                    the workspace cannot be set public since some of its items is already in a public workspace. Choose an action:
#                    
#                    <br>
#                    <ul> 
#                        <li>
#                            <a href="#" onclick="move_items(true, false)">Remove the items from the this workspace</a>
#                        </li> 
#                        <li>
#                            <a href="#" onclick="move_items(false, true)">Remove the items from the public workspace</a>
#                        </li> 
#                        <li>
#                            <a href="#"onclick="window.parent.adminwin.close(); new Ajax.Updater(window.parent.document.getElementById(\'content\'),\'/public_items/\', {evalScripts: true})">See the items</a>
#                        </li>
#                    </ul>
#                    
#                    """%(item_ids, self.ws.pk,  self.ws.pk)
#                    
#                    
#                    raise forms.ValidationError(html)
#                
#        return value
  
class AddMembersForm(forms.Form):
    def __init__(self,  ws,  *args,  **kwargs):
        super(AddMembersForm,  self).__init__(*args, **kwargs)
        self.ws = ws
        self.fields['members_to_add'].queryset =  User.objects.exclude(pk__in = [m.pk for m in ws.members.all()]).order_by('username')
        self.fields['members_to_add'].widget.attrs=  {'style':'height:290; min-width:100',  }

    members_to_add = forms.ModelMultipleChoiceField(queryset = None, required = False)                 
   

class MyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        from django.utils.safestring import mark_safe
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<ul>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li style="text-align:left"><label%s><div id="%s" style="z-index:100;  position:relative; width:10px; height:10px;  top:15px"></div>%s %s</label></li>' % (label_for, option_value,rendered_cb, option_label))
        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))

class SetPermissionsForm(forms.Form):
    def __init__(self,  ws,  *args,  **kwargs):
        super(SetPermissionsForm,  self).__init__(*args, **kwargs)
        self.ws = ws        
        self.fields['permissions'].queryset =  WorkSpacePermission.objects.all()
        self.fields['permissions'].widget.attrs=   {'class':'visible_checkbox',}
        self.fields['hidden'].widget.attrs=   {'class':'hidden_checkbox'}
        
        
        
      

    permissions = forms.ModelMultipleChoiceField(queryset = None, required = False, widget = MyCheckboxSelectMultiple )                 
    hidden = forms.ModelMultipleChoiceField(queryset = WorkSpacePermission.objects.all(), required = False, widget = forms.CheckboxSelectMultiple ,  )                 
    remove = forms.CharField( required = False, widget = forms.HiddenInput)                 
    
    
class SetGroupsForm(forms.Form):
    def __init__(self,  ws,    *args,  **kwargs):
        super(SetGroupsForm,  self).__init__(*args, **kwargs)
        self.ws = ws    
        self.fields['groups'].queryset = ws.workspacepermissionsgroup_set.all()
        self.fields['groups'].widget.attrs= {'class':'visible_checkbox'}
        self.fields['hidden'].queryset = ws.workspacepermissionsgroup_set.all()
        self.fields['hidden'].widget.attrs=   {'class':'hidden_checkbox'}
        
        
        
    groups = forms.ModelMultipleChoiceField(queryset = None, required = False, widget = MyCheckboxSelectMultiple )     
    hidden = forms.ModelMultipleChoiceField(queryset = None, required = False, widget = forms.CheckboxSelectMultiple ,  )
    remove = forms.CharField( required = False, widget = forms.HiddenInput)                                
    
    
#    permissions = forms.ModelMultipleChoiceField(queryset = WorkSpacePermission.objects.all(), required = False, widget = forms.CheckboxSelectMultiple )                 
               
            
            
            
    
class AddMembersToGroupForm(forms.Form):
    def __init__(self,  group ,  *args,  **kwargs):
        super(AddMembersToGroupForm,  self).__init__(*args, **kwargs)
        if group:
            self.fields['members'].queryset =  User.objects.exclude(workspacepermissionsgroup = group)
        else:
            self.fields['members'].queryset =  User.objects.all()
    
    members = forms.ModelChoiceField(queryset = None, required = False)                 
