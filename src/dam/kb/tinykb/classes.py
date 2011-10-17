#########################################################################
#
# NotreDAM, Copyright (C) 2011, Sardegna Ricerche.
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
#
# Python classes used for handling the NotreDAM knowledge base.  This
# file is most likely going to be split into different modules.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

from sqlalchemy import ForeignKey, event
import sqlalchemy.orm as orm
import sqlalchemy.exc as exc
from sqlalchemy.orm import mapper, backref, relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.schema import Column, Table
from sqlalchemy.sql import and_

import schema
import access

from util import niceid

class Workspace(object):
    def __init__(self, name, creator):
        self.name = name
        self.creator = creator

    def __repr__(self):
        return "<Workspace('%s')>" % (self.name, )

    def add_item(self, item, access=access.READ_ONLY):
        self.visible_items.append(ItemVisibility(item, self, access))

    def add_catalog_tree(self, cat_entry, access=access.READ_ONLY):
        if not cat_entry.is_root():
            ## Just in case someone set self.parent != None
            raise ValueError('Cannot share a non-root catalog entry'
                             ' (%s)' % (cat_entry, ))
        self.visible_catalog_trees.append(CatalogTreeVisibility(cat_entry,
                                                                self, access))

    def add_root_class(self, klass, access=access.READ_ONLY):
        if not klass.is_root():
            ## Just in case someone set klass.superclass != None
            raise ValueError('Cannot share a non-root class (%s)' % (klass, ))
        self.visible_root_classes.append(KBClassVisibility(klass, self,
                                                           access))


class User(object):
    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return "<User('%s')>" % (self.username, )


class Item(object):
    def __init__(self):
        pass

    def __repr__(self):
        if self.id is not None:
            return "<Item(%d)>" % (self.id, )
        else:
            return "<Item()>"

    def add_to_workspace(self, workspace, access=access.READ_ONLY):
        workspace.add_item(self, access)


class ItemVisibility(object):
    def __init__(self, item, workspace, access):
        self.item = item
        self.workspace = workspace
        ## FIXME: check for access validity
        self.access = access

    def __repr__(self):
        return "<ItemVisibility('%s, %s, %s')>" % (self.item, self.workspace,
                                                   self.access)


class KBClass(object):
    def __init__(self, name, superclass, attributes=[], notes=None,
                 explicit_id=None):
        if explicit_id is None:
            self.id = niceid.niceid(name) # FIXME: check uniqueness!
        else:
            self.id = explicit_id

        self.table = ('object_' + self.id).lower()
        self.name = name

        if superclass is None:
            self._root_id = self.id
            superclass = self

        # FIXME: handle these fields with a SQLAlchemy mapper property?
        self.superclass = superclass
        self._root_id = superclass._root_id

        for a in attributes:
            self.attributes.append(a)
        self.notes = notes

        ## When created from scratch, no table on DB should exists
        self.sqlalchemy_table = None
        self.additional_sqlalchemy_tables = []
        self.python_class = None

    @orm.reconstructor
    def __init_on_load__(self):
        # Retrieve the session of the current object...
        ses = orm.Session.object_session(self)
        # ...and use it to bind to its SQL table
        self.bind_to_table(ses.get_bind(None))
        assert(hasattr(self, 'sqlalchemy_table'))

        self.python_class = None

    def is_root(self):
        return (self.id == self._root_id)

    def is_bound(self):
        return self.sqlalchemy_table is not None

    def _get_parent_table(self):
        if self.superclass is self:
            parent_table = 'object'
        else:
            parent_table = self.superclass.table

        return parent_table

    def _get_attributes_ddl(self):
        attr_nested_lst = [attr.ddl() for attr in self.attributes]
        attrs_ddl_list = [d for l in attr_nested_lst for d in l] # Flatten

        return attrs_ddl_list

    def _get_attributes_tables(self):
        tbl_nested_lst = [attr.additional_tables() for attr in self.attributes]
        attrs_tbl_list = [t for l in tbl_nested_lst for t in l] # Flatten

        return attrs_tbl_list

    def create_table(self, session_or_engine):
        if self.is_bound():
            ## We are already bound to a table
            raise AttributeError('%s is already bound to a SQL table (%s)'
                                 % (self, self.sqlalchemy_table.name))

        engine = _get_engine(session_or_engine)

        parent_table = self._get_parent_table()

        attrs_ddl = self._get_attributes_ddl()

        self.sqlalchemy_table = schema.create_object_table(self.table,
                                                           parent_table,
                                                           attrs_ddl,
                                                           engine)

        add_tables = self._get_attributes_tables()

        self.additional_sqlalchemy_tables = schema.create_attr_tables(
            add_tables, engine)

    def bind_to_table(self, session_or_engine):
        engine = _get_engine(session_or_engine)

        parent_table = self._get_parent_table()
        attrs_ddl = self._get_attributes_ddl()
        try:
            self.sqlalchemy_table = schema.get_object_table(self.table,
                                                            parent_table,
                                                            attrs_ddl,
                                                            engine)
            
            # The following call is going to require
            # self.sqlalchemy_table (set above)
            attrs_tables = self._get_attributes_tables()

            self.additional_sqlalchemy_tables = schema.get_attr_tables(
                attrs_tables, engine)
        except exc.InvalidRequestError:
            # FIXME: raise a meaningful (non SQLAlchemy-related) exception here
            raise

    def _get_object_references(self):
        from attributes import ObjectReference, ObjectReferencesList

        # FIXME: properly handle references cache, using a SQLAlchemy event
        if not hasattr(self, '_references_cache'):
            self._references_cache = [
                x for x in self.attributes
                if (isinstance(x, ObjectReference)
                    or isinstance(x, ObjectReferencesList))]

        return self._references_cache

    # Return the Python class corresponding to the KBClass.  Returns
    # None if self.make_python_class() was not invoked before
    def get_python_class(self):
        return self.python_class

    def make_python_class(self, session_or_engine=None):
        if self.python_class is not None:
            return self.python_class

        if session_or_engine is None:
            # See whether we're still bound to a session
            session_or_engine = orm.Session.object_session(self)
            assert(session_or_engine is not None)

        try:
            self.bind_to_table(session_or_engine)
        except exc.InvalidRequestError:
            raise AttributeError('KBClass must be bound to a SQL table in order to generate a Python class.  Maybe you should call KBClass.bind_to_table()?')

        if not self.is_root():
            parent_class = self.superclass.make_python_class(
                session_or_engine)
            init_method = lambda instance, name, notes=None, explicit_id=None:(
                parent_class.__init__(instance, name, notes=notes,
                                      explicit_id=explicit_id))
        else:
            parent_class = KBObject
            init_method = lambda instance, name, notes=None, explicit_id=None:(
                parent_class.__init__(instance, instance.__kb_class__,
                                      name, notes=notes,
                                      explicit_id=explicit_id))
           
        classdict = {
            '__init__' : init_method,
            '__repr__' : lambda instance: (
                "<%s('%s', '%s')>" % (self.name, instance.name, instance.id)),
            '__kb_class__' : self,
            '__class_id__' : self.id,
            '__class_root_id__': self._root_id
            }
        newclass = type(str(self.name), # FIXME: ensure it's a valid class name
                        (parent_class, ),
                        classdict)

        # NOTE: self.python_class needs to be set *before* generating
        # the SQLAlchemy ORM mapper, because it will invoke
        # self.get_python_class(), which cannot return None
        self.python_class = newclass

        # Let's now build the SQLAlchemy ORM mapper
        mapper_props = {}
        objrefs = self._get_object_references()
        for r in objrefs:
            mapper_props.update(r.mapper_properties())

        mapper(newclass, self.sqlalchemy_table, inherits=parent_class,
               polymorphic_identity=self.id,
               properties = mapper_props)

        return newclass

    def __repr__(self):
        return "<KBClass('%s', '%s')>" % (self.name, self.id)


class KBRootClass(KBClass):
    def __init__(self, name, attributes=[], notes=None, explicit_id=None):
        KBClass.__init__(self, name, None, attributes=attributes,
                         notes=notes, explicit_id=explicit_id)

    def add_to_workspace(self, workspace, access=access.READ_ONLY):
        workspace.add_root_class(self, access)

    def __repr__(self):
        return "<KBRootClass('%s', '%s')>" % (self.name, self.id)


class KBClassAttribute(object):
    def __init__(self, klass, name, attr_type):
        pass

class KBClassVisibility(object):
    def __init__(self, klass, workspace, access):
        self.klass = klass
        self.workspace = workspace
        ## FIXME: check for access validity
        self.access = access

    def __repr__(self):
        return "<KBClassVisibility('%s, %s, %s')>" % (self.item,
                                                      self.workspace,
                                                      self.access)


## Abstract base class for real objects
class KBObject(object):
    def __init__(self, class_, name, notes=None, explicit_id=None):
        if explicit_id is None:
            self.id = niceid.niceid(name) # FIXME: check uniqueness!
        else:
            self.id = explicit_id

        setattr(self, 'class', class_)
        self.name = name
        self.notes = notes

    def __repr__(self):
        return "<KBObject(%s, '%s')>" % (self.__class__, self.name)


## Former Keyword and Category definitions
# class Keyword(KBObject):
#     def __init__(self, name, notes=None):
#         KBObject.__init__(self, 'keyword', 'keyword', name, notes)
#
#     def __repr__(self):
#         return "<Keyword('%s', '%s')>" % (self.name, self.id)
#
#
# class Category(KBObject):
#     def __init__(self, name, notes=None):
#         KBObject.__init__(self, 'category', 'category', name, notes)
#
#     def __repr__(self):
#         return "<Category('%s', '%s')>" % (self.name, self.id)


class CatalogEntry(object):
    def __init__(self, type_obj, parent):
        self.id = niceid.generate(32) # FIXME: ensure uniqueness!
        self.object = type_obj
        self.parent = parent

    def is_root(self):
        return (self.id == self._root)

    def __repr__(self):
        return "<CatalogEntry('%s', %s, %s')>" % (self.id, self.object,
                                                self.parent)


class RootCatalogEntry(CatalogEntry):
    def __init__(self, type_obj):
        CatalogEntry.__init__(self, type_obj, None)

    def add_to_workspace(self, workspace, access=access.READ_ONLY):
        workspace.add_catalog_tree(self, access)

    def __repr__(self):
        return "<RootCatalogEntry('%s', %s')>" % (self.id, self.object)


class CatalogTreeVisibility(object):
    def __init__(self, catalog_entry, workspace, access=access.READ_ONLY):
        self.catalog_entry = catalog_entry
        self.workspace = workspace
        self.access = access

    def __repr__(self):
        return "<CatalogTreeVisibility('%s, %s, %s')>" % (self.catalog_entry,
                                                          self.workspace,
                                                          self.access)


###############################################################################
## Mappers
###############################################################################

mapper(User, schema.user)

mapper(Item, schema.item)

mapper(ItemVisibility, schema.item_visibility,
       properties={
        'item' : relationship(Item, backref='visibility', cascade='all')
        })

mapper(Workspace, schema.workspace,
       properties={
        '_creator' : schema.workspace.c.creator,
        'creator' : relationship(User, backref='workspaces', cascade='all'),
        'visible_items' : relationship(ItemVisibility, backref='workspace',
                                       cascade='all'),
        'visible_catalog_trees' : relationship(CatalogTreeVisibility,
                                               backref='workspace',
                                               cascade='all'),
        'visible_root_classes' : relationship(KBClassVisibility,
                                              backref='workspace',
                                              cascade='all')
        })

mapper(KBClass, schema.class_t,
       polymorphic_on=schema.class_t.c.is_root,
       polymorphic_identity=False,
       properties={
        '_root_id' : schema.class_t.c.root,
        '_parent_id' : schema.class_t.c.parent,
        '_parent_root' : schema.class_t.c.parent_root,
        '_is_root' : schema.class_t.c.is_root,
        'superclass' : relationship(KBClass, backref='subclasses',
                                    primaryjoin=(and_((schema.class_t.c.parent
                                                       ==schema.class_t.c.id),
                                                      (schema.class_t.c.parent_root
                                                       ==schema.class_t.c.root))),
                                    remote_side=[schema.class_t.c.id,
                                                 schema.class_t.c.root],
                                    post_update=True,
                                    cascade='all'),
        '_root' : relationship(KBRootClass,
                               primaryjoin=(schema.class_t.c.root
                                            ==schema.class_t.c.id),
                               remote_side=[schema.class_t.c.id],
                               post_update=True,
                               cascade='all')
        })

mapper(KBRootClass, inherits=KBClass,
       polymorphic_identity=True)

mapper(KBClassVisibility, schema.class_visibility,
       properties={
        '_workspace' : schema.class_visibility.c.workspace,
        '_class_id' : schema.class_visibility.c['class'],
        '_class_root' : schema.class_visibility.c.class_root,
        'klass' : relationship(KBRootClass,
                               backref='visibility', cascade='all')
        })

mapper(KBObject, schema.object_t,
       polymorphic_on=schema.object_t.c['class'],
       properties={
        '_class' : schema.object_t.c['class'],
        '_class_root' : schema.object_t.c.class_root,
        'class' : relationship(KBClass, backref='objects', cascade='all')
        })

## Former Keyword and Category mappers
# mapper(Keyword, schema.object_keyword, inherits=KBObject,
#        polymorphic_identity='keyword')
#
# mapper(Category, schema.object_category, inherits=KBObject,
#        polymorphic_identity='category')

mapper(CatalogEntry, schema.catalog_entry,
       polymorphic_on=schema.catalog_entry.c.is_root,
       polymorphic_identity=False,
       properties={
        '_root' : schema.catalog_entry.c.root,
        '_parent_id' : schema.catalog_entry.c.parent,
        '_parent_root' : schema.catalog_entry.c.parent_root,
        '_object_id' : schema.catalog_entry.c.object,
        '_object_class_root' : schema.catalog_entry.c.object_class_root,
        '_is_root' : schema.catalog_entry.c.is_root,
        'parent' : relationship(CatalogEntry, backref='children',
                                  primaryjoin=(schema.catalog_entry.c.parent
                                               ==schema.catalog_entry.c.id),
                                  remote_side=[schema.catalog_entry.c.id],
                                  cascade='all'),
        'object' : relationship(KBObject, backref='catalog_entries',
                                cascade='all')
        })

mapper(RootCatalogEntry, inherits=CatalogEntry,
       polymorphic_identity=True)

mapper(CatalogTreeVisibility, schema.catalog_tree_visibility,
       properties={
        '_workspace' : schema.catalog_tree_visibility.c.workspace,
        '_catalog_entry' : schema.catalog_tree_visibility.c.catalog_entry,
        '_catalog_entry_root' : schema.catalog_tree_visibility.c.catalog_entry_root,
        '_catalog_entry_object_class_root' : schema.catalog_tree_visibility.c.catalog_entry_object_class_root,
        'catalog_entry' : relationship(RootCatalogEntry,
                                       backref='visibility', cascade='all'),
        'root_class_visibility' : relationship(KBClassVisibility,
                                               backref='catalog_tree_visibilities',
                                               cascade='all')
        })


###############################################################################
## Events
###############################################################################

## Update related fields when the parent of a catalog entry is changed
def catentry_update_parent_attrs(target, value, _oldvalue, _initiator):
    if value is None:
        target._root = target.id
        target._parent_id = target.id
        target._parent_root = target.id
        target._is_root = True
    else:
        if isinstance(target, RootCatalogEntry):
            raise AttributeError(
                'Cannot change the parent of a root catalog entry')
        if not isinstance(value, CatalogEntry):
            raise TypeError('Parent must be a CatalogEntry (received: %s)'
                            % str(type(value)))
        target._root = value._root
        target._parent_id = value.id
        target._parent_root = value._root
        target._is_root = (target.id == value.id)

event.listen(CatalogEntry.parent, 'set', catentry_update_parent_attrs,
             propagate=True, retval=False)

## Update related fields when the parent of a KB class is changed
def kbclass_update_superclass_attrs(target, value, _oldvalue, _initiator):
    if value is None:
        target._root_id = target.id
        target._parent_id = target.id
        target._parent_root = target.id
        target._is_root = True
    else:
        if isinstance(target, KBRootClass) and (value != target):
            raise AttributeError(
                'Cannot change the parent of a root class')
        if not isinstance(value, KBClass):
            raise TypeError('Parent must be a KBClass (received: %s, type: %s)'
                            % (str(value), str(type(value))))
        target._root_id = value._root_id
        target._parent_id = value.id
        target._parent_root = value._root_id
        target._is_root = (target.id == value.id)

event.listen(KBClass.superclass, 'set', kbclass_update_superclass_attrs,
             propagate=True, retval=False)


###############################################################################
## Utility methods
###############################################################################
def _get_engine(session_or_engine):
    import session
    if isinstance(session_or_engine, session.Session):
        return session_or_engine.session.get_bind(None)
    if isinstance(session_or_engine, Session):
        return session_or_engine.get_bind(None)
    else:
        return session_or_engine
