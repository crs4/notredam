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
from django.utils import simplejson
from django.contrib.auth.models import User

from dam.repository.models import Item
from dam.core.dam_tree.models import AbstractNode

from dam import logger

class InvalidNode(Exception):
    pass

class NotEditableNode(Exception):
    pass

class WrongWorkspace(Exception):
    pass
    
class NotMovableNode(Exception):
    pass

class SiblingsWithSameLabel(Exception):
    pass

class NodeManager(models.Manager):

    def add_node(self, node, label, workspace, cls = 'collection', associate_ancestors = None):
    #    if not node.parent:
    #        raise InvalidNode
            
        node.check_ws(workspace)
    
        logger.debug('label %s'%label)
        if node.children.filter(label = label).count():
            raise SiblingsWithSameLabel
        logger.debug('node.cls %s'%node.cls)
    
    #    if node.type == 'keyword':
    #        cls = 'keyword'
    #    else:
    #        cls = node.cls
            
        new_node = self.create(workspace= workspace, label = label,  type = node.type)
        if cls:
            new_node.cls = cls
        
        if associate_ancestors:
            new_node.associate_ancestors = associate_ancestors      
        
        new_node.parent = node
        new_node.depth = (node.depth)+1
        new_node.count = 0
        new_node.save()
        
    #    Node.objects.get_root(workspace).rebuild_tree(1)
        return new_node
    
    def get_from_path(self,  path, workspace, type = 'collection',   separator='/'):
        def _to_path(nodes):
            return separator.join([n.label for n in nodes])
            
        labels = path.split(separator)
        if labels:
            logger.debug('labels %s '%labels)
            nodes = Node.objects.filter(label = labels.pop(),  type = type, workspace = workspace)
            logger.debug(nodes)
            for node in nodes:
                logger.debug('node.get_ancestors() %s'%node.get_ancestors())
                node_path = _to_path(node.get_ancestors().exclude(depth = 0)) 
                logger.debug('node_path %s'%node_path)
                if node_path == path:
                    logger.debug('node.pk %s'%node.pk)
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
    workspace = models.ForeignKey('workspace.DAMWorkspace', related_name='tree_nodes')
    objects = NodeManager()
    items = models.ManyToManyField('repository.Item')
    metadata_schema = models.ManyToManyField('metadata.MetadataProperty',  through = 'NodeMetadataAssociation',  blank=True, null=True)
    associate_ancestors = models.BooleanField(default = False)
    
    def check_ws(self, ws):
        if self.workspace != ws:
            raise WrongWorkspace

    def edit_node(self, label, metadata_schemas, associate_ancestors, workspace):
    
        if label :
            self.rename_node(label, workspace)
        
        if self.cls != 'category':
            if metadata_schemas:
                self.save_metadata_mapping(metadata_schemas)        
                self.save_metadata()
            
            self.associate_ancestors = associate_ancestors
            self.save()

    def remove_keyword_association(self, items):
        items = Item.objects.filter(pk__in = items)
        self.items.remove(*items)
        self.remove_metadata(items)

    def remove_collection_association(self, items):
        logger.debug('items %s'%items)
        try:
            items = self.items.filter(pk__in = items)
            logger.debug('items %s'%items)
            logger.debug('self.items %s'%self.items.all())
            self.items.remove(*items)
            logger.debug('self.items %s'%self.items.all())
        except Exception, ex:
            logger.exception(ex)
            raise ex    

    def save_keyword_association(self, items):
        items = Item.objects.filter(pk__in = items)
        if self.associate_ancestors:
            nodes = self.get_ancestors().filter(depth__gt = 0)
        else:
            nodes = [self]
            
        for n in nodes:
    
            if n.cls != 'category':
                n.items.add(*items)
    
            n.save_metadata(items)

    def save_collection_association(self, items):
        items = Item.objects.filter(pk__in = items)
        self.items.add(*items)

    def save_metadata_mapping(self, metadata_schemas):
        from dam.metadata.models import MetadataProperty
        
        node_associations_to_delete = NodeMetadataAssociation.objects.filter(node = self)
       
        for item in self.items.all():
            for n_a in node_associations_to_delete:
                metadata = item.metadata.filter(schema = n_a.metadata_schema,  value = n_a.value)
                if metadata.count() >0:
                    metadata[0].delete()
                    
        node_associations_to_delete.delete()
        logger.debug('metadata_schemas %s'%metadata_schemas)
        for ms in metadata_schemas:
            if not isinstance(ms,  dict):
                logger.debug('ms %s'%ms)
                ms = simplejson.loads(ms)
            NodeMetadataAssociation.objects.create(node = self,  value = ms['value'],  metadata_schema = MetadataProperty.objects.get(pk = ms['id']))
    #    node.metadata_schema.add(*MetadataProperty.objects.filter(pk__in = metadata_schemas))

    def save_metadata(self, items=None):
        from dam.metadata.models import MetadataValue

        ctype = ContentType.objects.get_for_model(Item)

        if items is None:
            items = self.items.all()
        
        for item in items: 
            schema = self.metadata_schema.all()
            for s in schema:
                node_association= NodeMetadataAssociation.objects.get(node = self,  metadata_schema = s)
                keyword = node_association.value
                
                m = MetadataValue.objects.get_or_create(schema=s, value=keyword, object_id= item.pk, content_type = ctype)

    def remove_metadata(self, items):
        from dam.metadata.models import MetadataValue
        
        ctype = ContentType.objects.get_for_model(Item)

        for item in items: 
            schema = self.metadata_schema.all()
            for s in schema:
                n_a = NodeMetadataAssociation.objects.get(node = self,  metadata_schema = s)
                MetadataValue.objects.filter(schema=s, value=n_a.value, object_id= item.pk, content_type = ctype).delete()

    def rename_node(self, label, workspace):
    #    if not node.parent:
    #        raise InvalidNode
        if not self.editable:
            raise NotEditableNode
        self.check_ws(workspace)
        self.label = label
        self.save()
    
    def move_node(self, node_dest, workspace):
        if not self.parent :
            raise InvalidNode
        
    #    TODO: check move parent to children
        self.check_ws(node_dest.workspace)
        self.check_ws(workspace)
        self.check_ws(workspace)
        
    #    if node_source.depth <= 2:
    #        raise NotEditableNode
        self.parent = node_dest
        self.depth = node_dest.depth+1
        self.save()
    #    Node.objects.get_root(workspace).rebuild_tree(1)
    
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
    workspace = models.ForeignKey('workspace.DAMWorkspace')
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
         
            
    
