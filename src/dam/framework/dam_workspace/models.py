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
    def with_permissions(self, user, permissions):
        wss_1= super(PermissionManager,  self).filter(workspacepermissionassociation__permission__in = permissions,  workspacepermissionassociation__users = user)        
        wss_2 = super(PermissionManager,  self).filter(workspacepermissionsgroup__permissions__in = permissions,  workspacepermissionsgroup__users = user)
        wss = reduce(or_, [wss_1,  wss_2]).distinct()
        return wss

class Workspace(models.Model):
    name = models.CharField(max_length=512)
    description = models.CharField(max_length=512)
    creator = models.ForeignKey(User,  blank = True,  null = True)
    members = models.ManyToManyField(User, related_name="workspaces",  blank=True)    
    creation_date = models.DateTimeField(auto_now_add = True)
    last_update = models.DateTimeField(auto_now = True)
    objects = models.Manager()
    permissions = PermissionManager()

    def __unicode__(self):
        return "%s" % (self.name)
        
    def has_member(self, user):
        if user in self.members.all():
            return True
        else:
            return False

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
    workspace = models.ForeignKey('Workspace')
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
