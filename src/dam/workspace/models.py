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
from django.db.models import Q

from dam.repository.models import Item
from dam.workflow.models import State
from dam.core.dam_workspace.models import Workspace, WorkspaceManager
import dam.logger as logger

class WSManager(WorkspaceManager):

    """
    Workspace Manager
    """

    def create_workspace(self, name, description, creator):
        """
        Creates a new workspace
        @param name name of the new workspace (string)
        @param description description of the new workspace (optional string)
        @param creator an instance of auth.User
        """
        from dam.scripts.models import Pipeline
        from dam.scripts.views import _new_script
        from dam.treeview.models import Node, Category
        from dam.eventmanager.models import Event, EventRegistration

        ws = super(WSManager, self).create_workspace(name, description, creator)
        
        try:
            
            global_scripts = ScriptDefault.objects.all()
            upload = Event.objects.get(name = 'upload')
            for glob_script in global_scripts:
                _new_script(name = glob_script.name, description = glob_script.description, workspace = ws, pipeline = glob_script.pipeline, events = ['upload', 'item copy'],  is_global = True)
#                script = Script.objects.create(name = glob_script.name, description = glob_script.description, pipeline = glob_script.pipeline, workspace = ws )
#                EventRegistration.objects.create(event = upload, listener = script, workspace = ws)
            
            root = Node.objects.create(label = 'root', depth = 0,  workspace = ws,  editable = False,  type = 'keyword',  cls = 'keyword')
            col_root = Node.objects.create(label = 'root', depth = 0,  workspace = ws,  editable = False,  type = 'collection')
            inbox_root = Node.objects.create(label = 'root', depth = 0,  workspace = ws,  editable = False,  type = 'inbox')
            uploaded = Node.objects.create(parent = inbox_root, depth = 1, label = 'Uploaded', workspace = ws, editable = False,  type = 'inbox')
            imported = Node.objects.create(parent = inbox_root, depth = 1, label = 'Imported', workspace = ws, editable = False, type = 'inbox')
    
            for cat in Category.objects.all():
                Node.objects.create(workspace = ws, label = cat.label, depth = 1, type = root.type, parent = root,  is_drop_target = cat.is_drop_target,  is_draggable = cat.is_draggable,  editable = cat.editable,  cls = cat.cls)
        except Exception,  ex:
            logger.exception(ex)
            raise ex        
        
        return ws

class DAMWorkspace(Workspace):
    """
    Subclass of dam_workspace.Workspace,
    adds a many-to-many reference to the Item and State model 
    """
    items = models.ManyToManyField(Item, related_name="workspaces",  blank=True)
#    states = models.ManyToManyField(State)
    objects = WSManager()

    def remove_item(self, item):
        """
        Removes the given item from the current workspace and its inbox node
        Also deletes item's component bound to the current workspace
        @param item item to remove (an instance of repository.Item)
        """
        from dam.treeview.models import Node
        
        try:
            
            inbox_nodes = Node.objects.filter(type = 'inbox', workspace = self, items = item) #just to be sure, filter instead of get
            for inbox_node in inbox_nodes:
                inbox_node.items.remove(item)
                if inbox_node.items.all().count() == 0:
                    inbox_node.delete()
            
            logger.debug('item.workspaces %s'%item.workspaces.all())
            item.workspaces.remove(self)
            logger.debug('item.workspaces %s'%item.workspaces.all())
            item.component_set.all().filter(workspace = self).exclude(Q(variant__auto_generated = False)| Q(variant__shared = True)).delete()
            
        except Exception, ex:
            logger.exception(ex)
            raise ex        
    
    def get_variants(self):
        """
        Returns the list of variants for the current workspace
        """
        from dam.variants.models import Variant
        return Variant.objects.filter(Q(workspace = self) | Q(workspace__isnull = True,  )).distinct()    
    
