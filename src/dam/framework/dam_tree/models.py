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
        
        for label in labels:
            nodes = self.filter(label = label)
            if nodes.count() == 1:
                return nodes[0]
            elif nodes.count() == 0:
                return None
            else:
                nodes
        
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
        root = Node.objects.get_or_create(workspace= owner, label='root', parent__isnull = True)[0]         
           
        nodes = root.get_branch()
        return nodes

class Node(models.Model):
    label = models.CharField(max_length= 200)
    parent    = models.ForeignKey('self', related_name="children", blank=True, null=True)
    depth  = models.IntegerField(default=0)
    type = models.CharField(max_length= 25)
    cls = models.CharField(max_length= 25)
    
    lft = models.PositiveIntegerField(editable=False,default=1)
    rgt  = models.PositiveIntegerField(editable=False,default=1)
    is_draggable = models.BooleanField(default = True)
    is_drop_target= models.BooleanField(default = True)
    editable = models.BooleanField(default = True)
    objects = NodeManager()
    creation_date = models.DateField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    def get_path(self):
        path = self.type + ':/'
        ancestors = self.get_ancestors()
        for anc in ancestors:
            if anc.depth == 0:
                continue
            path+=str(anc) + '/'
        return path
    
    def rebuild_tree(self, left):
        right = left+1
        for c in Node.objects.filter(parent=self,).order_by('depth'):
            right = c.rebuild_tree(right)
        
        self.lft = left
        self.rgt = right
        
        super(Node, self).save()
        return right+1
        
    def get_ancestors(self):
        nodes = Node.objects.filter(type = self.type)
        nodes = nodes.extra(where=['lft <=%s and rgt>=%s'], params=[self.lft, self.rgt]).order_by('lft')
        return nodes
    
    def get_branch(self, depth = None):
        nodes = Node.objects.filter(type = self.type)
        if depth:
            nodes = nodes.extra(where=['lft between %s and %s', 'depth <=%s'], params=[self.lft, self.rgt, self.depth + depth ])
        else:
            nodes = nodes.extra(where=['lft between %s and %s'], params=[self.lft, self.rgt])
       
        nodes = nodes.extra(select={'leaf': 'rgt-lft=1'})
        
        return nodes.order_by('lft').distinct()
    
    def delete(self,  *args,  **kwargs):
        super(Node, self).delete(*args,  **kwargs)
        root = Node.objects.filter(depth= 0, type = self.type)
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
        super(Node, self).save(*args,  **kwargs)
        
        if rebuild_tree:
            try:
                root = Node.objects.filter(depth= 0, type = self.type)
                root[0].rebuild_tree(1)
            except Exception,  ex:
                logger.exception(ex)
                raise ex
                
    def __str__(self):
        return unicode(self.label)
            
    def has_child(self):
        childrens=self.get_branch()
        if len(childrens) > 1:
            has_child = True
        else:
            has_child = False
        return has_child
