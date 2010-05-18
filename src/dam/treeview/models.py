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
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.contrib.auth.models import User
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item, Component
from dam.framework.dam_repository.models import Type
from dam.framework.dam_tree.models import AbstractNode

import logger

class NodeManager(models.Manager):
    
    def get_from_path(self,  path, type = 'collection',   separator='/'):
        def _to_path(nodes):
            return separator.join([n.label for n in nodes])
            
        labels = path.split(separator)
        if labels:
            nodes = Node.objects.filter(label = labels.pop(),  type = type)
            for node in nodes:
                node_path = _to_path(node.get_ancestors().exclude(depth = 0)) 
                if node_path == path:
                    return node           
        
        return None
        
    def copy_tree(self, root, new_root, ):
        new_owner = new_root.content_object
        ctype = ContentType.objects.get_for_model(new_owner)
        tree = root.get_branch()
        
        relation_node = {}
        for  node in tree:
           
            if node == root:
                parent = new_root
            else:
                parent = relation_node[node.parent.pk]
                    
            new_node = Node.objects.create(content_type = ctype, object_id = new_owner.pk, label = node.label, parent = parent)
            new_node.type.add(*node.type.all())
            relation_node[node.pk] = new_node
        new_root.save()
        new_root.rebuild_tree(1)

    def get_root(self, ws,  type):        
        return Node.objects.get(workspace = ws, depth = 0,  type = type)
      
    def rebuild_tree(self, ws,  type):
        self.get_root(ws,  type).rebuild_tree(1)

    def get_tree(self, owner):
        root = Node.objects.get_or_create(workspace=  owner, label='root', parent__isnull = True)[0]         
           
        nodes = root.get_branch()
#        print nodes
        return nodes
   
class Category(models.Model):
    label = models.CharField(max_length= 200)
    position = models.IntegerField(unique = True)
    is_draggable = models.BooleanField(default = True)
    is_drop_target= models.BooleanField(default = True)
    editable = models.BooleanField(default = True)
    cls = models.CharField(max_length= 20,  default = 'keyword')
    
    def __unicode__(self):
        return self.label

class Node(AbstractNode):
    is_draggable = models.BooleanField(default = True)
    is_drop_target= models.BooleanField(default = True)
    editable = models.BooleanField(default = True)
    workspace = models.ForeignKey(Workspace, related_name='tree_nodes')
    objects = NodeManager()
    items = models.ManyToManyField('repository.Item')
    metadata_schema = models.ManyToManyField('metadata.MetadataProperty',  through = 'NodeMetadataAssociation',  blank=True, null=True)
    associate_ancestors = models.BooleanField(default = False)
    
    def get_ancestors(self):
        nodes = Node.objects.filter(type = self.type)
        nodes = nodes.extra(where=['lft <=%s and rgt>=%s', 'workspace_id = %s', ], params=[self.lft, self.rgt, self.workspace.pk]).order_by('lft')
        return nodes
    
    def get_branch(self, depth = None):
        nodes = Node.objects.filter(type = self.type)
        if depth:
            nodes = nodes.extra(where=['lft between %s and %s', 'workspace_id = %s and depth <=%s', ], params=[self.lft, self.rgt, self.workspace.pk, self.depth + depth ])
        else:
            nodes = nodes.extra(where=['lft between %s and %s', 'workspace_id = %s', ], params=[self.lft, self.rgt, self.workspace.pk])
       
        nodes = nodes.extra(select={'leaf': 'rgt-lft=1'})
        
#        return nodes.order_by('lft').distinct().exclude(pk = self.pk)
        return nodes.order_by('lft').distinct()
    
    def delete(self,  *args,  **kwargs):
        super(Node, self).delete(*args,  **kwargs)
        root = Node.objects.filter(depth= 0,  workspace = self.workspace,  type = self.type)
        root[0].rebuild_tree(1)

    def save(self,*args,  **kwargs):
        rebuild_tree = False
        if self.id:
            db_node = Node.objects.get(pk = self.pk)
            if db_node.parent != self.parent:
                rebuild_tree = True
        else:
#            just creating the node
            rebuild_tree = True
            
        models.Model.save(self, *args, **kwargs)
        
        if rebuild_tree:
            try:
                root = Node.objects.filter(depth= 0,  workspace = self.workspace,  type = self.type)
                logger.debug('root %s'%root)
                root[0].rebuild_tree(1)
            except Exception,  ex:
                logger.exception(ex)
                raise ex
                
    class Meta:        
        db_table = 'node'        

class NodeMetadataAssociation(models.Model):
    node = models.ForeignKey(Node)
    metadata_schema = models.ForeignKey('metadata.MetadataProperty')
    value = models.CharField(max_length= 100)
    
class SmartFolderNodeAssociation(models.Model):
    smart_folder = models.ForeignKey('SmartFolder')
    node = models.ForeignKey('Node')
    negated = models.BooleanField(default = False)
    
class SmartFolder(models.Model):
    label = models.CharField(max_length= 200)
    and_condition = models.BooleanField(default = True)
    workspace = models.ForeignKey(Workspace)
    nodes = models.ManyToManyField('Node',  through = 'SmartFolderNodeAssociation')

    def get_complex_query(self):
        if self.and_condition:
            condition = 'and'
        else:
            condition = 'or'
            
        cq = {'nodes': [],  'condition':condition}
        for sm_ass in self.smartfoldernodeassociation_set.all():
            cq['nodes'].append({'id': sm_ass.node.pk,  'negated':sm_ass.negated})
            
        return cq
         
            
    
