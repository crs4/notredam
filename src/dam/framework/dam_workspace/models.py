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

from django.db.models import Q
from operator import and_, or_

class PermissionManager(models.Manager):
    """
    
    """
    def with_permissions(self, user, permissions):
        wss_1= super(PermissionManager,  self).filter(workspacepermissionassociation__permission__in = permissions,  workspacepermissionassociation__users = user)        
        wss_2 = super(PermissionManager,  self).filter(workspacepermissionsgroup__permissions__in = permissions,  workspacepermissionsgroup__users = user)
        wss = reduce(or_, [wss_1,  wss_2]).distinct()
        return wss

class WorkspaceManager(models.Manager):
    """
    
    """
    def create_workspace(self, name, description, creator):
        ws = self.model(None, name=name, description=description, creator=creator)
        ws.save()

        try:
            permission = WorkspacePermission.objects.get(name='admin')
            wspa = WorkspacePermissionAssociation.objects.get_or_create(workspace = ws, permission = permission)[0]
            wspa.users.add(creator)
            ws.members.add(creator)
        except:
            pass
            
        return ws

class Workspace(models.Model):
    """

    """
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=512)
    creator = models.ForeignKey(User)
    members = models.ManyToManyField(User, related_name="workspaces")    
    creation_date = models.DateTimeField(auto_now_add = True)
    last_update = models.DateTimeField(auto_now = True)
    objects = WorkspaceManager()
    permissions = PermissionManager()

    def __unicode__(self):
        return "%s" % (self.name)

    def add_member(self, user, permissions):

        self.members.add(user)

        self.remove_member_permissions(user)

        for perm in permissions:
            wspa = WorkspacePermissionAssociation.objects.get_or_create(workspace = self, permission = perm)[0]
            wspa.users.add(user)

    def remove_member(self, user):

        perms = self.ws_permissions.all()
        for p in perms:
            p.users.remove(user)
            
        self.members.remove(user)   

    def remove_member_permissions(self, user, permission=None):

        if permission:

            try:
                perm = self.ws_permissions.get(permission=permission)
                perm.users.remove(user)
            except:
                pass

        else:
            perms = self.ws_permissions.all()
            for p in perms:
                p.users.remove(user)
                        
    def get_members(self):
        return self.members.all()
        
    def has_member(self, user):
        return user in self.get_members()

    def has_permission(self, user, permission):
        return self.get_permissions(user).filter(Q(codename = 'admin') | Q(codename = permission)).count() > 0
        
    def get_permissions(self,  user):
        return WorkspacePermission.objects.filter(Q(workspacepermissionassociation__in = WorkspacePermissionAssociation.objects.filter(Q(users=user, workspace = self)) ) | Q(workspacepermissionsgroup__in= WorkspacePermissionsGroup.objects.filter(users = user, workspace = self) )).distinct()

class WorkspacePermission(models.Model):
    name = models.CharField(max_length=40)
    codename = models.CharField(max_length=40)
    
    class Meta:
        unique_together = (("codename", "name"))
        verbose_name_plural = "permissions"
        
    class Admin: pass
                
    def __unicode__(self):
        return unicode(self.name)

class WorkspacePermissionAssociation(models.Model):
    permission = models.ForeignKey('WorkspacePermission')
    workspace = models.ForeignKey('Workspace', related_name='ws_permissions')
    users = models.ManyToManyField(User)
    groups = models.ManyToManyField('WorkspacePermissionsGroup', blank = True)

    class Admin:pass
    
class WorkspacePermissionsGroup(models.Model):
    name = models.CharField(max_length=40)
    workspace = models.ForeignKey('Workspace')
    users = models.ManyToManyField(User, blank = True)
    permissions = models.ManyToManyField(WorkspacePermission, blank = True)
    
    def __unicode__(self):
        return unicode(self.name)
        
    class Meta:
        unique_together = (("workspace", "name"))
        verbose_name_plural = "groups"
    
    class Admin:
       fields = (
        (None, {
            'fields': ('name', 'workspace', 'permissions',  'users')
        }),       
    )
