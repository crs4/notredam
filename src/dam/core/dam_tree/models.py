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

class NodeManager(models.Manager):
    
    """ Node Manager """
    
    def get_from_path(self, path, type = 'collection', separator='/'):
        """
        Finds the node identified by the given path 
        """
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
                
    def get_root(self, type):        
        """
        Gets the root for the given type
        """
        return Node.objects.get(depth = 0,  type = type)
      
    def rebuild_tree(self, type):   
        """
        Rebuilds the tree
        """
        self.get_root(type).rebuild_tree(1)

    def get_tree(self, type):
        """
        Returns the tree
        """
        root = Node.objects.get_or_create(type = type, label = 'root', parent__isnull = True)[0]         
           
        nodes = root.get_branch()
        return nodes
   

class AbstractNode(models.Model):
    
    """
        Tree Node Implementation
        The root node of a tree is identified by (depth=0, type)
    """

    label = models.CharField(max_length= 200)
    parent    = models.ForeignKey('self', related_name="children", blank=True, null=True)
    depth  = models.IntegerField(default=0)
    type = models.CharField(max_length= 25)
    cls = models.CharField(max_length= 25)
    
    lft = models.PositiveIntegerField(editable=False,default=1)
    rgt  = models.PositiveIntegerField(editable=False,default=1)
    creation_date = models.DateField(auto_now_add=True)
    objects = NodeManager()
    
    class Meta:
        abstract = True
    
    def save(self,*args,  **kwargs):
        """
        Saves the node and checks if the tree needs to be rebuild
        """
        rebuild_tree = False
        if self.id:
            db_node = self.__class__.objects.get(pk = self.pk)
            if db_node.parent != self.parent:
                rebuild_tree = True
        else:
#            just creating the node
            rebuild_tree = True
        
        models.Model.save(self, *args, **kwargs)         
        
        if rebuild_tree:
            try:
                root = self.__class__.objects.filter(depth= 0, type = self.type)
                root[0].rebuild_tree(1)
            except Exception,  ex:
                raise ex    
    
    def get_path(self):
        """
        Returns the path for the current node
        """
        path = self.type + ':/'
        ancestors = self.get_ancestors()
        for anc in ancestors:
            if anc.depth == 0:
                continue
            path+=str(anc) + '/'
        return path
    
    def rebuild_tree(self, left):
        """
        Rebuilds tree
        """
        right = left+1
        for c in self.__class__.objects.filter(parent=self).order_by('depth'):
            right = c.rebuild_tree(right)
        
        self.lft = left
        self.rgt = right
        
        super(self.__class__, self).save()
        return right+1
        
    def get_ancestors(self):
        """
        Gets node ancestors
        """
        nodes = self.__class__.objects.filter(type = self.type)
        nodes = nodes.extra(where=['lft <=%s and rgt>=%s'], params=[self.lft, self.rgt]).order_by('lft')
        return nodes
    
    def get_branch(self, depth = None):
        """
        Gets node branch
        """
        nodes = self.__class__.objects.filter(type = self.type)
        if depth:
            nodes = nodes.extra(where=['lft between %s and %s', 'depth <=%s', ], params=[self.lft, self.rgt, self.depth + depth ])
        else:
            nodes = nodes.extra(where=['lft between %s and %s'], params=[self.lft, self.rgt])
       
        nodes = nodes.extra(select={'leaf': 'rgt-lft=1'})
        
        return nodes.order_by('lft').distinct()
    
    def delete(self,  *args,  **kwargs):
        """
        Deletes node
        """
        super(AbstractNode, self).delete(*args,  **kwargs)
        root = self.__class__.objects.filter(depth= 0, type = self.type)
        root[0].rebuild_tree(1)

    def __str__(self):
        return unicode(self.label)
    
    def has_child(self):
        """
        Checks if the node has children
        """
        childrens=self.get_branch()
        if len(childrens) > 1:
            has_child = True
        else:
            has_child = False
        return has_child    
