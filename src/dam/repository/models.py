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
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission, Group

from dam.metadata.models import MetadataValue,MetadataProperty
from dam.workflow.models import State, StateItemAssociation
import sha
import random
import logger

def _get_parents(child_obj, parent_class,  rel_class, group_by_relation_name ):
    
    if not group_by_relation_name :
        condition = {rel_class._meta.db_table + '__child': child_obj}
        parents = parent_class.objects.filter(**condition)
        return parents
    result = {}
    i2is = self.parent_items.all()
    for i2i in i2is:
        rel_name = i2i.name
        parent = i2i.parent
        if not result.has_key(rel_name):
            parents = Item.objects.filter(items__name = rel_name, items__child = self, )
        result[rel_name] = parents
    return result

def _get_children(relations):
    result  = {}
    for rel in relations:
        name = rel.name
        child = rel.child      
        result[name] = child 
    return result
    
def _get_parents(relations, ):
    result  = {}
    for rel in relations:
        name = rel.name
        
        tmp = []
        name = rel.name
        parent = rel.parent
        tmp.append(name)
        tmp.append(parent)
        result.append(tmp)
    return result
    
def _add_object(parent, object, relation_label, class_relation):
    if parent == object:
        raise Exception('Cannot add an object to itself')
    n = class_relation.objects.filter(name = relation_label, parent = parent, ).count()
    if n > 0:
        raise Exception('A relation  named "%s" already exists'%( relation_label))
    
    class_relation.objects.create(name = relation_label, parent = parent, child = object)

class SearchManager(models.Manager):
    def filter(self, tags, user = None, and_ = True):
        """It is a facility for searching objects by a list of tags. 
        If an user is passed, search is performed only on his own tags. Moreover, search can be done with an 'AND' or a 'OR' logic.
        @param tags: a list of tags
        @type tags: list
        @param user: if passed, search is performed only on his own tags
        @type user: User
        @param and_: if True, search is done with an 'AND' logic. Otherwise, a 'OR' logic is used
        @type and_: boolean
        @return: a list of taggable object 
        @rtype: QuerySet
        """
        tags = [tag.lower() for tag in tags]
        format_string = "(%s)" % ','.join(['%s']*len(tags))
        ctype = ContentType.objects.get_for_model(self.model)
        table = self.model._meta.db_table
        if user == None:
            select = "select count(*) from (select  distinct %s.id as id, label from taggedobject,%s, tag where taggedobject.tag_id = tag.id and taggedobject.object_id = %s.id and label in %s and taggedobject.content_type_id = %s) as temp group by temp.id" %(table,table, table, format_string, ctype.id)
        else:
            select = "select count(*) from taggedobject,tag where taggedobject.tag_id = tag.id and taggedobject.object_id = %s.id and taggedobject.content_type_id = %s  and label in %s and user_id = %s group by %s.id" %(self.model._meta.db_table, ctype.id ,format_string, user.id ,self.model._meta.db_table, )
        if and_:
            result =  self.model.objects.extra(select={'count': select}, tables = ['taggedobject', 'tag'], where=['count >= %s' %(len(tags))], params = tags).distinct()
        else:
            result =  self.model.objects.extra(select={'count': select}, tables = ['taggedobject', 'tag'], where=['count >= 1' ], params = tags).distinct()
        if user != None:
            result = result.filter(tag_relation__user = user) 
        return result

class Item(models.Model):
    """ Base model describing items. They can contain others items and components (see method 'add_child') and can be contained by containers """
    _id = models.CharField(max_length=41)
    owner =  models.CharField(max_length=50, null = True)
    uploader = models.ForeignKey(User)
    type =  models.CharField(max_length=20, null = True)
    privacy =  models.CharField(max_length=20, null = True)
    state = models.DecimalField(decimal_places=0, max_digits=10, null = True)
    creation_time = models.DateTimeField(  auto_now_add = True)
    update_time = models.DateTimeField( auto_now = True)
    is_public = models.BooleanField(default=False)
    tag_relation= generic.GenericRelation('TaggedObject',)    
    objects = models.Manager()   
    relations  = SearchManager()
    metadata = generic.GenericRelation(MetadataValue)
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    #properties

    def get_metadata_values(self, metadataschema=None):
        from dam.metadata.views import get_metadata_values
        values = []
        original_component = Component.objects.get(item=self, variant__name='original', workspace=self.workspaces.all()[0])
        if metadataschema:
            schema_value, delete, b = get_metadata_values([self.pk], metadataschema, set([self.type]), set([original_component.media_type.name]), [original_component.pk])
            if delete:
                return None
            if schema_value:
                if schema_value[self.pk]:
                    values = schema_value[self.pk]
                else:
                    values = None
            else:
                values = None
        else:
            for m in self.metadata.all().distinct('schema').values('schema'):
                prop = MetadataProperty.objects.get(pk=m['schema'])
                schema_value, delete, b = get_metadata_values([self.pk], prop, set([self.type]), set([original_component.media_type.name]), [original_component.pk])
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.pk]})

        return values

    def get_descriptors(self, workspace=None):
        from dam.metadata.models import MetadataDescriptorGroup

        if workspace:
            basic = MetadataDescriptorGroup.objects.filter(basic_summary=True, workspace=workspace)
            if basic.count() == 0:
                basic = MetadataDescriptorGroup.objects.filter(basic_summary=True)[0]
            else:
                basic = basic[0]
        else:
            basic = MetadataDescriptorGroup.objects.filter(basic_summary=True)[0]
        
        descriptors = {}
        for d in basic.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors

    def get_file_name(self):
        from dam.variants.models import Variant
        try:
            orig = self.component_set.get(variant__name = 'original')
            name = orig.file_name 
        except Component.DoesNotExist:
            name = ''
        return name

    def get_file_size(self):
        from dam.variants.models import Variant
        orig = self.component_set.get(variant = Variant.objects.get(name = 'original', media_type__name = self.type))
        return float(orig.size)

    def get_states(self, workspace=None):
        if workspace is None:
            return StateItemAssociation.objects.filter(item = self)
        else:
            return StateItemAssociation.get(item=self, workspace=workspace)
            
            
    def get_variants(self,  workspace):
        from dam.variants.models import Variant
        return self.component_set.filter(variant__in = Variant.objects.filter(Q(is_global = True,) | Q(variantassociation__workspace__pk = workspace.pk), media_type__name = self.type),  workspace = workspace)
                
    def description(self):
        mydescription = self.metadata.get(schema__is_description = True, language ="it-IT")
        return mydescription.value

    def keywords(self):
        self.node_set.filter(type = 'keyword' ).values('id','label')
#        k = {}
#        mykeywords = self.metadata.filter(schema__keyword_target = True)
#        for i in mykeywords:
#            k.append(i.value)
#        return mykeywords
    
    

    def rating_values(self):   
        rating = self.rating            
        rating_values = [0]*5
        if rating > 0:
            rating_values = [ rating / (r+1)      for r in range(5) ]
        return rating_values
    
    def uploaded_by(self):
        try:
            return self.uploader.username
        except:
            return 'unknown'
    
    def get_creator(self):
        creator = MetadataValue.objects.filter(schema__field_name = 'creator',schema__namespace__prefix = 'dc', item__pk = self.pk)
        if not creator:
            return []     
        return creator
    
    def metadata_list(self):
        metadata = self.metadata.all()
    
    def tags(self, user = None):
        """Return a list of tags associated with the item. If a user is passed, only his tags are returned.
        @param user: a user
        @type user: User
        @return: a list of tags
        @rtype: QuerySet
        """
        return  Tag.relations.filter(self, user)
    
    def _get_id(self):
        return  self._id
    
    class Meta:
        db_table = 'item'
    ID = property(fget=_get_id)
        
    def save(self, force_insert=False):
        logger.debug("save called")
        if self._id == '':
            self._id = 'a' + sha.new(str(random.random())).hexdigest()
        try:
            models.Model.save(self, force_insert=force_insert)   
            logger.debug("after save")         
        except:
            logger.debug("after save except")         
            self._id = ''
            raise
            
    
    def __str__(self):
        return self.ID

    def remove_child(self, child,relation_label):
        """Remove the relation parent-child with the given child and the given label.
        @param child: a child of the current object
        @type child: a component or an Item
        """
        if isinstance(child, Item):
            rel = self.items.filter(name = relation_label)
        elif isinstance(child, Component):
            rel = self.components.filter(name = relation_label)
        else:
            raise Exception('child argument can be only an item or an component')
        rel.delete()

    def add_child(self, object, relation_label):
        """Create a parent-child relation with the given object. The label is associated to this relation.
        @param object: the object to be child 
        @type object: a Component or an Item
        @param relation_label: the label associated to the parent-child relation 
        @type relation_label: string
        """
        if isinstance(object, Component):
            _add_object(self, object, relation_label, Component2Item)
        elif isinstance(object, Item):
            _add_object(self, object, relation_label, Item2Item)
        else:
            raise Exception('you can add only an item or a component to an item') 

    def get_children(self,  child_class, group_by_relation_name =True):
        """Return the children of the container belonging to the given class. If  group_by_relation_name is true, a dictionary is returned, where keys are the labels of the relations parent-child, and values are  the parents associated with that label. Otherwise, if group_by_relation_name is set to false,  a Django QuerySet is returned, containing all the parents.
        
        @param child_class: the class of the requested children
        @type child_class: Item or Component
        @param group_by_relation_name: if True a dictionary is returned, otherwise a QuerySet containing all the parents        
        @type group_by_relation_name: boolean
        @return: a dictionary or a QuerySet
        
        """ 
        if child_class != Item and child_class != Component:
            raise Exception('children for items can be only items or components')
        if not group_by_relation_name:            
            children = child_class.objects.filter(parent_items__parent = self)            
            return children
        if child_class == Item:
            relations = self.items.all()
        else:
            relations = self.components.all()    
        return _get_children(relations)
            
            
    
    def get_parents(self, parent_class, group_by_relation_name = True):
        """Return the parents of the item belonging to the given class. If  group_by_relation_name is true, a dictionary is returned, where keys are the labels of the relations parent-child, and values are Django QuerySets containing all the parents associated with that label. Otherwise, if group_by_relation_name is set to false,  a QuerySet is returned, containing all the parents.
        @param parent_class: the class of the requested parents
        @type parent_class: Item or Component        
        @param group_by_relation_name: if True a dictionary is returned, otherwise a QuerySet containing all the parents
        @type group_by_relation_name: boolean
        @return: a dictionary or a QuerySet
        """
        if parent_class != Item and parent_class != Container:
            raise Exception('parents for items can be only items or containers')
        if not group_by_relation_name:            
            parents = parent_class.objects.filter(items__child = self)            
            return parents
        result = {}
        if parent_class == Item:
            relations = self.parent_items.all()
        else:
            relations = self.parent_containers.all()
        for rel in relations:
            rel_name = rel.name
            parent = rel.parent
            if not result.has_key(rel_name):
                parents = parent_class.objects.filter(items__name = rel_name, items__child = self, )
            result[rel_name] = parents
        return result
    
    def get_collections(self):
        return self.get_parents(Container, False)
    
    def get_sharing_info(self):
        from dam.workspace.models import Workspace
        wss = self.workspaces.all()
        ws = []
        users = []
        for w in wss:
            if len(w.members.all())>1 or not w.members.get(pk=self.uploader.pk):
                users.append( w.members.all().exclude(pk=self.uploader.pk) )
        return users


     
class Item2Item(models.Model):
    """@undocumented """
    name =  models.CharField(max_length=50)
    parent = models.ForeignKey('Item', related_name = 'items', db_column = 'parent_id')
    child= models.ForeignKey('Item', related_name  = 'parent_items', db_column = 'child_id')

    class Meta:
        db_table = 'item2item'
        unique_together = (("name", "parent"),)
    
    def __str__(self):
        return self.name
        
class ContainerManager(models.Manager,):
        def with_component(self, component):
            """This is a facility to get all the containers that contain the given component (i.e. that contain items containing the component) 
            @param component: a  component
            @type component: Component
            @return: containers that contain the given component
            @rtype: QuerySet
            
            """
            return super(ContainerManager, self).get_query_set().filter(items__child__components__child = component).distinct()
    
class Container(models.Model):
    """ Base model describing containers. They can contain others containers and items."""
    name = models.CharField(max_length=50, null = True)
    objects = ContainerManager()
    relations = SearchManager()
    _id = models.CharField(max_length=41, primary_key = True, db_column = 'id')
    owner =  models.CharField(max_length=50, null = True)
    type =  models.CharField(max_length=20, null = True)
    privacy =  models.CharField(max_length=20, null = True)
    state = models.DecimalField( decimal_places=10, max_digits=10,  null = True)
    creation_time = models.DateTimeField(auto_now_add = True)
    update_time = models.DateTimeField(auto_now = True)
    tag_relation= generic.GenericRelation('TaggedObject',)
    #properties

    def _get_id(self):
        return self._id
    ID = property(fget=_get_id)
    
    def tags(self, user = None):
        """Return a list of tags associated with the container. If a user is passed, only his tags are returned.
        @param user: a user
        @type user: User
        @return: a list of tags
        @rtype: QuerySet
        """
        return  Tag.relations.filter(self, user)
    
    def __str__(self):
        return self.ID
        
    class Meta:
        db_table = 'container'
        
    def save(self, force_insert=False):
        if self._id == '':
            self._id = 'f' + sha.new(str(random.random())).hexdigest()
        try:
            models.Model.save(self, force_insert=force_insert)
        except:
            self._id = ''
            raise
    
    def get_children(self,  child_class, group_by_relation_name =True):
        """Return the children of the container belonging to the given class. If  group_by_relation_name is true, a dictionary is returned, where keys are the labels of the relations parent-child, and values are  the parents associated with that label. Otherwise, if group_by_relation_name is set to false,  a Django QuerySet is returned, containing all the parents.
        
        @param child_class: the class of the requested children
        @type child_class: Item or Component
        @param group_by_relation_name: if True a dictionary is returned, otherwise a QuerySet containing all the parents        
        @type group_by_relation_name: boolean
        @return: a dictionary or a QuerySet
        
        """
        if child_class != Item and child_class != Container:
            raise Exception('Wrong child class: children for items can be only items or containers')
        if not group_by_relation_name:            
            children = child_class.objects.filter(parent_containers__parent = self)            
            return children
        if child_class == Item:
            relations = self.items.all()
        else:
            relations = self.containers.all()    
        return _get_children(relations)
        
    def get_parents(self,  group_by_relation_name = True):
        """Return the parents of the container. If  group_by_relation_name is true, a dictionary is returned, where keys are the labels of the relations parent-child, and values are Django QuerySets containing all the parents associated with that label. Otherwise, if group_by_relation_name is set to false,  a QuerySet is returned, containing all the parents.
        @param group_by_relation_name: if True a dictionary is returned, otherwise a QuerySet containing all the parents
        @type group_by_relation_name: boolean
        @return: a dictionary or a QuerySet
        
        """
        if not group_by_relation_name:            
            parents = Container.objects.filter(containers__child = self)            
            return parents
        result = {}
        relations = self.parent_containers.all()
        for rel in relations:
            rel_name = rel.name
            parent = rel.parent
            if not result.has_key(rel_name):
                parents = Container.objects.filter(containers__name = rel_name, containers__child = self, )
            result[rel_name] = parents
        return result
        
    def add_child(self, object, relation_label):
        """Create a parent-child relation with the given object. The label is associated to this relation.
        @param object: the object to be child 
        @type object: a Container or an Item
        @param relation_label: the label associated to the parent-child relation 
        @type relation_label: string
        """
        if isinstance(object, Container):
            _add_object(self, object, relation_label, Container2Container)
        elif isinstance(object, Item):
            _add_object(self, object, relation_label, Item2Container)
        else:
            raise Exception('you can add only an item or a component to an item') 
            
    def remove_child(self, child,relation_label):
        """Remove the relation parent-child with the given child and the given label.
        @param child: a child of the current object
        @type child: a Container or an Item
        
        """
        if isinstance(child, Item):
            rel = self.items.filter(name = relation_label)
        elif isinstance(child, Container):
            rel = self.containers.filter(name = relation_label)
        else:
            raise Exception('child argument can be only an item or a container')
        rel.delete()
    
class Item2Container(models.Model):
    """@undocumented """
    name =  models.CharField(max_length=50)
    parent = models.ForeignKey('Container', related_name = 'items', db_column = 'parent_id')
    child = models.ForeignKey('Item', related_name  = 'parent_containers', db_column = 'child_id')
    class Meta:
        db_table = 'item2container'
        
class Container2Container(models.Model):
    """@undocumented """
    name =  models.CharField(max_length=50)
    parent = models.ForeignKey('Container', related_name = 'containers', db_column = 'parent_id')
    child= models.ForeignKey('Container', related_name  = 'parent_containers', db_column = 'child_id')

    class Meta:
        db_table = 'container2container'
        
    def save(self, force_insert=True):
        if self.parent == self.child:
            raise Exception('Cannot add an object to itself')
        models.Model.save(self, force_insert=force_insert)
        unique_together = (("name", "parent"),)
        
class Component2Item(models.Model):
    """@undocumented """
    name =  models.CharField(max_length=50)
    parent = models.ForeignKey('Item', related_name = 'components', db_column = 'parent_id')
    child= models.ForeignKey('Component', related_name  = 'parent_items', db_column = 'child_id')
    class Meta:
        db_table = 'component2item'
        
class ComponentManager(models.Manager):
        def in_container(self, container):
            """This is a facility to get all the components contained in a given container (i.e. that are contained in items contained themselves in the component) 
            @param container: a  container
            @type container: Container
            @return: components contained in a given container 
            @rtype: QuerySet
            
            """
            return super(ComponentManager, self).get_query_set().filter(parent_items__parent__parent_containers__parent = container).distinct()
        
def _new_md_id():
        return sha.new(str(random.random())).hexdigest()
        
class Component(models.Model):
    """ Base model describing components. They can be contained by items."""
    objects = ComponentManager()
    relations  = SearchManager()

    _id = models.CharField(max_length=40,  db_column = 'md_id')
    owner =  models.CharField(max_length=50, null = True)
    type =  models.CharField(max_length=20, null = True)
    state = models.DecimalField(decimal_places=0, max_digits=10, null = True)
    creation_time = models.DateTimeField(auto_now = True)
    update_time = models.DateTimeField(auto_now = True)

    format = models.CharField(max_length=50, null = True)
    width = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    height = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    bitrate = models.DecimalField(decimal_places=0, max_digits=10,default = 0)
    duration = models.DecimalField(decimal_places=0, max_digits=10,default = 0, null = True)
    size = models.DecimalField(decimal_places=0, max_digits=10, default = 0)
    embedded_license = models.BooleanField(default = False)
    condition_class = models.TextField( null = True)
    tag_relation= generic.GenericRelation('TaggedObject',)   
    metadata = generic.GenericRelation(MetadataValue)
    

    variant = models.ForeignKey('variants.Variant')
    workspace = models.ManyToManyField('workspace.Workspace')    
#    media_type = models.ForeignKey('application.Type')
    item = models.ForeignKey('Item',  )
    source_id = models.CharField(max_length=40,  null = True,  blank = True)
    preferences = generic.GenericForeignKey()
    content_type = models.ForeignKey(ContentType,  null = True, blank = True)
    object_id = models.PositiveIntegerField(null = True, blank = True)
    
    uri = models.URLField(max_length=512,  verify_exists = False,  blank = True,  null = True)
    imported = models.BooleanField(default = False) # if true related variant must not be regenarated from the original
    #properties

    file_name = models.CharField(max_length=128, null=True, blank=True)
    
    
    def _get_id(self):
        return self._id
    ID = property(fget=_get_id)
    
    def _get_media_type(self):
        if self.variant.auto_generated:
            pref = self.variant.get_preferences(workspace = self.workspace.all()[0])
            return pref.media_type
            
        else:
            return self.variant.media_type
    media_type = property(fget=_get_media_type)
    
    def __str__(self):
        return self.ID

    def get_formatted_filesize(self):
        from dam.metadata.views import format_filesize
        return format_filesize(self.size)
    
    def get_metadata_values(self, metadataschema=None):
        from dam.metadata.views import get_metadata_values
        values = []
        if metadataschema:
            schema_value, delete, b = get_metadata_values([self.item.pk], metadataschema, set([self.item.type]), set([self.media_type.name]), [self.pk], self)
            if delete:
                return None
            if schema_value:
                if schema_value[self.item.pk]:
                    values = schema_value[self.item.pk]
                else:
	                values = None
            else:
                values = None
        else:
            for m in self.metadata.all().distinct('schema').values('schema'):
                prop = MetadataProperty.objects.get(pk=m['schema'])
                schema_value, delete, b = get_metadata_values([self.item.pk], prop, set([self.item.type]), set([self.media_type.name]), [self.pk], self)
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.item.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.item.pk]})

        return values

    def get_descriptors(self, desc_group):

        item_list = [self.item.pk]
        descriptors = {}
        desc_group    
        for d in desc_group.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors

    
    def get_variant(self):
        return self.variant
    
    
    
    
    def new_md_id(self):
        self._id = _new_md_id()
        self.save()
    
    
        
    class Meta:
        db_table = 'component'
#        unique_together = (("workspace", "variant", 'item'),)
        
    def save(self, *args,  **kwargs):
        if self._id == '':
            self._id = sha.new(str(random.random())).hexdigest()
        try:
            models.Model.save(self,*args,  **kwargs)
        except:
            self._id = ''
            raise
            
    def tags(self, user = None):
        """Return a list of tags associated with the component. If a user is passed, only his tags are returned.
        @param user: a user
        @type user: User
        @return: a list of tags
        @rtype: QuerySet
        """
        return  Tag.relations.filter(self, user)

    def get_parents(self,  group_by_relation_name = True):
        """Return the parents of the component. If  group_by_relation_name is true, a dictionary is returned, where keys are the labels of the relations parent-child, and values are Django QuerySets containing all the parents associated with that label. Otherwise, if group_by_relation_name is set to false,  a QuerySet is returned, containing all the parents.
        @param group_by_relation_name: if True a dictionary is returned, otherwise a QuerySet containing all the parents
        @type group_by_relation_name: boolean
        @return: a dictionary or a QuerySet
        
        """
        if not group_by_relation_name:            
            parents = Item.objects.filter(components__child = self)            
            return parents
        result = {}
        relations = self.parent_items.all()
        for rel in relations:
            rel_name = rel.name
            parent = rel.parent
            if not result.has_key(rel_name):
                parents = Item.objects.filter(components__name = rel_name, components__child = self, )
            result[rel_name] = parents
        return result

class TagManager(models.Manager):
    """Specific Manager for Tag Model. It provides a set of facilities to manage tag and tag relation """
    def popular(self):
        """Return the most used tags ordered by decreasing popularity. Each tag has an attribute 'count' which is the number of times it has been used. 
        @return: a list of the most popular tags
        @rtype: QuerySet
        """
        result = self.extra(select={'count' : 'select count(*) from taggedobject   where taggedobject.tag_id = tag.id group by tag.id' }).order_by('-count').distinct()
        return result
        
    def recent(self, user = None):
        """Return the most recent tags, ordered by decreasing date. Each tag has an attribute 'count' which is the number of times it has been used, and an attribute 'last_use', which is the date of the last time it has been used. If a user is passed, only his tags are considered.
        @param user: a user
        @type user: User        
        @return: a list of the most recent tags
        @rtype: QuerySet
        """
        if user == None:
            result = Tag.objects.extra(select={'last_use':'select max(creation_time) from taggedobject where tag.id = taggedobject.tag_id'}).extra(select={'count': 'select count(*) from taggedobject   where taggedobject.tag_id = tag.id group by tag.id'}).order_by('-last_use').distinct()
        else:
            result = Tag.objects.filter(taggedobject__user = user).extra(select={'last_use':'select max(creation_time) from taggedobject where tag.id = taggedobject.tag_id and taggedobject.user_id = %s'}, params = [user.id]).extra(select={'count': 'select count(*) from taggedobject   where taggedobject.tag_id = tag.id and taggedobject.user_id = %s group by tag.id'}, params = [user.id]).order_by('-last_use').distinct()
        return result
        
    def add(self,user, content_object, labels):
        """Allow to associate a list of tags to an object, i.e. an item, a container or a component.
        @param user: a user
        @type user: User
        @param content_object: an item, a container or a component
        @type content_object: Item, Container or Component
        @param labels: a list of label
        @type labels: a list of strings
        """
        tag_list = []
        for label in labels:
            label = label.lower()
            tag = super(TagManager, self).get_or_create(label = label)[0]
            try:
                tag_relation = TaggedObject.objects.create(tag = tag, content_object = content_object, user = user)
                tag_list.append(tag)
            except:
                pass
        return tag_list
        
    def filter(self,content_object = None, user = None):
        """Allow to retrieve the tags associated to a given object. If a user is passed, only his tags are considered.
        @param content_object: an item, a container or a component
        @type content_object: Item, Container or Component
        @param user: a user
        @type user: User     
        """
        if content_object == None and user == None:
            raise Exception('Specify at least an object or an user')
        
        if content_object != None and user == None:
            if isinstance(content_object, Item):                
                ctype = ContentType.objects.get_for_model(Item)
                result = super(TagManager, self).filter(taggedobject__item = content_object )
                
            
            elif isinstance(content_object, Component):                
                ctype = ContentType.objects.get_for_model(Component)
                result = super(TagManager, self).filter(taggedobject__component = content_object )
                
            elif isinstance(content_object, Container):                
                ctype = ContentType.objects.get_for_model(Container)
                result = super(TagManager, self).filter(taggedobject__container = content_object )
            
            result = result.extra(select={'count' : 'select count(*) from taggedobject  where taggedobject.tag_id = tag.id and taggedobject.content_type_id = %s and object_id = %s  group by tag.id' } , params = [ctype.id, content_object._id],).order_by('-count').distinct()
    
            
        elif content_object == None and user != None:    
            result = super(TagManager, self).filter(taggedobject__user = user ).extra(select={'count' : 'select count(*) from taggedobject  where taggedobject.tag_id = tag.id  and taggedobject.user_id = %s group by tag.id' }, params=[user.id]).order_by('-count').distinct()
##            result = result.
      
            
        elif content_object != None and user != None:    
            if isinstance(content_object, Item):               
                result = super(TagManager, self).filter(taggedobject__user = user, taggedobject__item = content_object)
                
            elif isinstance(content_object, Component):               
                result = super(TagManager, self).filter(taggedobject__user = user, taggedobject__component = content_object)
            
            elif isinstance(content_object, Container):               
                result = super(TagManager, self).filter(taggedobject__user = user, taggedobject__container = content_object)
    
        
        return result
    
    def rename(self,tag,  new_label, user , content_object = None):
        """Rename the tag  associated by the given user . If  no content object (ie items, containers or components) is specified all objects previously associated to that tag by the given user will be tagged with the new label.
        @param tag: the tag to rename
        @type tag: Tag
        @param new_label: the new tag label
        @type new_label: string        
        @param user: a user
        @type user: User     
        @param content_object: an item, a container or a component
        @type content_object: Item, Container or Component
        @return: the new tag
        @rtype: Tag
        
        """
        new_label = new_label.lower()
        new_tag, created = Tag.objects.get_or_create(label = new_label)
        if user == None and content_object == None:
            pass
            
        elif user != None and content_object == None:
            tag_relations = TaggedObject.objects.filter( user = user, tag = tag,)
            for tag_relation in tag_relations:
                tag_relation.tag = new_tag
                tag_relation.save()
            
        elif user != None and content_object != None:            
            if isinstance(content_object, Item): 
                tag_relation = TaggedObject.objects.get( user = user, tag =tag, item= content_object)
            elif isinstance(content_object, Component): 
                tag_relation = TaggedObject.objects.get( user = user, tag =tag, component =  content_object)
            
            else:
                tag_relation = TaggedObject.objects.get( user = user, tag = tag, container =  content_object)
            
            tag_relation.tag = new_tag
            tag_relation.save()
            
        elif user == None and content_object != None:
            pass
        
        return new_tag
    
    def delete(self, tag, user, content_object, ):
        """Delete the relation tag - user - content object.
        @param tag: a tag
        @type tag: Tag
        @param user: a user
        @type user: User     
        @param content_object: an item, a container or a component
        @type content_object: Item, Container or Component
       """
        if isinstance(content_object, Item): 
            TaggedObject.objects.get( user = user, tag=tag, item= content_object).delete()
        elif isinstance(content_object, Component): 
            TaggedObject.objects.get( user = user, tag=tag, component =  content_object).delete()
            
        else:
            TaggedObject.objects.get( user = user, tag=tag, container =  content_object).delete()
        
        occurrence = TaggedObject.objects.filter(tag=tag).count()
        if occurrence == 0:
            tag.delete()
        
        
        
        
class Tag(models.Model):
    """Model for tags. It has a specific Manager, called 'relations', that provides a set of facilities for creating, deleting, renaming  tags. """
    label = models.CharField(unique = True, max_length=255)
    relations = TagManager()
    objects = models.Manager()
    
    class Meta:
        db_table = 'tag'
    
    def __str__(self):
        return self.label
        
    def _get_items(self):
        return Item.objects.filter(tag_relation__tag = self).distinct()
    items =  property(fget =_get_items, )
    
    def _get_components(self):
        return Component.objects.filter(tag_relation__tag = self).distinct()
    components =  property(fget =_get_components, )
    
    def _get_containers(self):
        return Container.objects.filter(tag_relation__tag = self).distinct()
    
    containers = property(fget =_get_containers, )
    
    def _get_users(self):
        return User.objects.filter(taggedobject__tag = self).distinct()
        
    users = property(fget =_get_users, )
    
    def get_related(self, user = None):
        """Return a list of tags related to the tag. A tag is related to another when they are associated to the same items. Each returned tag has an attribute 'count' that represents the number of items that share these tags. If a user is passed, only his tags are considered. 
        @param user: a user
        @type user: User
        @return: list of related tags with the current tag
        @rtype: QuerySet
        """
        if user == None:
            return Tag.objects.extra(select={'count': ' select count(*) from taggedobject, (select object_id, content_type_id  from taggedobject where tag_id =%s)as temp where tag.id = taggedobject.tag_id and taggedobject.object_id = temp.object_id and taggedobject.content_type_id = temp.content_type_id  group by tag.id'
    }, params = [self.id] ).extra(where=['count > 0', 'id != %s'], params = [self.id]).order_by('-count')
        else:
            return Tag.objects.extra(select={'count': ' select count(*) from taggedobject, (select object_id, content_type_id  from taggedobject where tag_id =%s and user_id = %s)as temp where tag.id = taggedobject.tag_id and taggedobject.object_id = temp.object_id and taggedobject.content_type_id = temp.content_type_id and user_id  = %s group by tag.id'
    }, params = [self.id, user.id, user.id] ).extra(where=['count > 0', 'id != %s'], params = [self.id]).order_by('-count')
    
    
    
class TaggedObject(models.Model):    
    """This class models the relation between user, tags and objects as items, containers and components """
    content_type = models.ForeignKey(ContentType)
    object_id =models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    user = models.ForeignKey(User)
    tag = models.ForeignKey('Tag')
    creation_time = models.DateTimeField(auto_now = True)
    
    class Meta:
        
        db_table = 'taggedobject'
        unique_together = (("content_type", "tag", "user", "object_id"),)
    
    def __str__(self):
        return 'user:%s tag: %s content:%s' %(self.user.id, self.tag.label, self.content_object.ID)

