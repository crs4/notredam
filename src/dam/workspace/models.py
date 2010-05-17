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
from dam.framework.dam_workspace.models import Workspace, WorkspaceManager

class WSManager(WorkspaceManager):

    def create_workspace(self, name, description, creator):

        from dam.scripts.models import ScriptDefault, Script
        from dam.treeview.models import Node, Category
        from dam.eventmanager.models import Event, EventRegistration

        ws = super(WSManager, self).create_workspace(name, description, creator)
        
        try:
            
            global_scripts = ScriptDefault.objects.all()
            upload = Event.objects.get(name = 'upload')
            for glob_script in global_scripts:
                script = Script.objects.create(name = glob_script.name, description = glob_script.description, pipeline = glob_script.pipeline, workspace = ws )
                EventRegistration.objects.create(event = upload, listener = script, workspace = ws)
            
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
    items = models.ManyToManyField(Item, related_name="workspaces",  blank=True)
    states = models.ManyToManyField(State)
    objects = WSManager()
    
    def remove_item(self, item):

        try:
            
            inbox_nodes = Node.objects.filter(type = 'inbox', workspace = self, items = item) #just to be sure, filter instead of get
            for inbox_node in inbox_nodes:
                inbox_node.items.remove(item)
                if inbox_node.items.all().count() == 0:
                    inbox_node.delete()
            
            item.workspaces.remove(self)
            item.component_set.all().filter(workspace = self).exclude(Q(variant__is_global= True,  variant__auto_generated = False)| Q(variant__shared = True)).delete()
            
        except Exception, ex:
            logger.exception(ex)
            raise ex        
    
    def get_variants(self):
        from dam.variants.models import Variant
        return Variant.objects.filter(Q(workspace = self) | Q(is_global = True,  )).distinct()
