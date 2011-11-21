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

import types

from sqlalchemy import ForeignKey, event
import sqlalchemy.orm as orm
import sqlalchemy.exc as exc
from sqlalchemy.orm import mapper, backref, relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.schema import Column, Table
from sqlalchemy.sql import and_

import access

from util import niceid

class Classes(types.ModuleType):
    '''
    Container for the Python classes mapped to a knowledge base
    working session.

    When instantiated, this class configures the ORM machinery needed
    to bind the underlying knowledge base to a set of Python classes.

    :type  session: :py:class:`session.Session`
    :param session: KB session used for mapping the classes

    '''
    def __init__(self, session):
        types.ModuleType.__init__(self, 'tinykb.classes_%x' % (id(self), ))
        import session as kb_session
        assert(isinstance(session, kb_session.Session))

        self._session = session

        _init_base_classes(self)

    # self._attributes is set in _init_base_classes
    attributes = property(lambda self: self._attributes)
    '''
    Contains the knowledge base Attribute classes mapped to a
    working session.

    :type: :py:class:`attributes.Attributes`
    '''

    session = property(lambda self: self._session)
    '''
    The knowledge base session with which the attributes are bound

    :type: :py:class:`session.Session`
    '''


###############################################################################
# Mapped classes
###############################################################################
def _init_base_classes(o):
    '''
    Create the base classes and ORM mappings for a knowledge base
    working session (which must hold a 'session' attribute).  The
    classes will be attached as attributes to the "o" object,
    preserving their name.  Furthermore, o._attributes will contain
    the KB attribute classes mapped to the given schema.
    '''
    schema = o.session.schema
    engine = o.session.engine

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
                                                                    self,
                                                                    access))

        def setup_root_class(self, class_, access=access.READ_ONLY):
            if not class_.is_root():
                ## Just in case someone set class_.superclass != None
                raise ValueError('Cannot share a non-root class (%s)'
                                 % (class_, ))
            vis = [v for v in self.visible_root_classes
                   if getattr(v, 'class') is class_]
            if vis == []:
                # The class is not visible yet, let's add it
                self.visible_root_classes.append(KBClassVisibility(class_,
                                                                   self,
                                                                   access))
            else:
                # The class is still visible, let's just update its
                # access rules
                for v in vis:
                    v.access = access

    o.Workspace = Workspace

    class User(object):
        def __init__(self, username):
            self.username = username

        def __repr__(self):
            return "<User('%s')>" % (self.username, )

    o.User = User

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

    o.Item = Item

    class ItemVisibility(object):
        def __init__(self, item, workspace, access):
            self.item = item
            self.workspace = workspace
            ## FIXME: check for access validity
            self.access = access

        def __repr__(self):
            return "<ItemVisibility('%s, %s, %s')>" % (self.item,
                                                       self.workspace,
                                                       self.access)

    o.ItemVisibility = ItemVisibility

    class KBClass(object):
        def __init__(self, name, superclass, attributes=[], notes=None,
                     explicit_id=None):
            if explicit_id is None:
                self.id = niceid.niceid(name) # FIXME: check uniqueness!
            else:
                self.id = explicit_id

            self.table = (schema.prefix + 'object_'
                          + self.id).lower()
            self.name = name

            # FIXME: handle these fields with a SQLAlchemy mapper property?
            if superclass is None:
                self._root_id = self.id
                self.superclass = self
                inherited_attr_ids = []
            else:
                self.superclass = superclass
                self._root_id = superclass._root_id
                inherited_attr_ids = [a.id
                                      for a in superclass.all_attributes()]

            for a in attributes:
                if a.id in inherited_attr_ids:
                    raise RuntimeError('Cannot redefine inherited attribute'
                                       ' "%s"' % (a.id, ))
                self.attributes.append(a)
            self.notes = notes

            ## When created from scratch, no table on DB should exists
            self._sqlalchemy_table = None
            self.additional_sqlalchemy_tables = []

        @orm.reconstructor
        def __init_on_load__(self):
            self._sqlalchemy_table = None
            self.bind_to_table()

        sqlalchemy_table = property(lambda self: self._sqlalchemy_table)

        def is_root(self):
            return (self.id == self._root_id)

        def ancestors(self):
            '''
            Return a list of all the ancestor KBClass'es, starting from
            the immediate parent (if any).
            '''
            c = self.superclass
            prev_c = self
            ancestors = []
            while c is not prev_c:
                ancestors.append(c)
                prev_c = c
                c = c.superclass
            return ancestors

        def is_bound(self):
            return self._sqlalchemy_table is not None

        def all_attributes(self):
            '''
            Return all the class attributes, including the ones of
            ancestor classes (if any)
            '''
            classes = [self] + self.ancestors()
            nested_attrs = [c.attributes for c in classes]

            return [d for l in nested_attrs for d in l] # Flatten

        def _get_parent_table(self):
            if self.superclass is self:
                parent_table = schema.object_t.name
            else:
                parent_table = self.superclass.table

            return parent_table

        def _get_attributes_ddl(self):
            attr_nested_lst = [attr.ddl() for attr in self.attributes]
            attrs_ddl_list = [d for l in attr_nested_lst for d in l] # Flatten

            return attrs_ddl_list

        def _get_attributes_tables(self):
            tbl_nested_lst = [attr.additional_tables()
                              for attr in self.attributes]
            attrs_tbl_list = [t for l in tbl_nested_lst for t in l] # Flatten

            return attrs_tbl_list

        def create_table(self):
            if self.is_bound():
                ## We are already bound to a table
                raise AttributeError('%s is already bound to a SQL table (%s)'
                                     % (self, self._sqlalchemy_table.name))

            parent_table = self._get_parent_table()

            attrs_ddl = self._get_attributes_ddl()

            self._sqlalchemy_table = schema.create_object_table(self.table,
                                                                parent_table,
                                                                attrs_ddl,
                                                                engine)

            add_tables = self._get_attributes_tables()

            self.additional_sqlalchemy_tables = schema.create_attr_tables(
                add_tables, engine)

        def bind_to_table(self):
            parent_table = self._get_parent_table()
            attrs_ddl = self._get_attributes_ddl()

            if self.is_bound():
                raise AttributeError('KBClass.bind_to_table() was called twice'
                                     ' on %s' % (self, ))

            try:
                self._sqlalchemy_table = schema.get_object_table(self.table,
                                                                 parent_table,
                                                                 attrs_ddl,
                                                                 engine)

                # The following call is going to require
                # self.sqlalchemy_table (set above)
                attrs_tables = self._get_attributes_tables()

                self.additional_sqlalchemy_tables = schema.get_attr_tables(
                    attrs_tables, engine)
            except exc.InvalidRequestError:
                # FIXME: raise a meaningful (non SQLAlchemy-related)
                # exception here
                raise

        def _make_or_get_python_class(self):
            '''
            Return the Python class associated to a KB class.  The
            class will be built only once, and further calls will
            always return the same result
            '''
            ret = getattr(self, '_cached_pyclass', None)
            if ret is not None:
                return ret

            if not self.is_bound():
                self.bind_to_table()

            if not self.is_root():
                parent_class = self.superclass.python_class
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
                    "<%s('%s', '%s')>" % (self.name, instance.name,
                                          instance.id)),
                '__kb_class__' : self,
                '__class_id__' : self.id,
                '__class_root_id__': self._root_id
                }
            newclass = type(str(self.name), # FIXME: ensure valid class name
                            (parent_class, ),
                            classdict)

            # NOTE: the cached python class needs to be set *before*
            # generating the SQLAlchemy ORM mapper, because it will
            # access to self.python_class again, thus causing an
            # infinite recursion
            self._cached_pyclass = newclass

            # Let's now build the SQLAlchemy ORM mapper
            mapper_props = {}
            for r in self.attributes:
                mapper_props.update(r.mapper_properties())

            mapper(newclass, self._sqlalchemy_table, inherits=parent_class,
                   polymorphic_identity=self.id,
                   properties = mapper_props)

            # Also add event listeners for validating assignments
            # according to attribute types
            for a in self.attributes:
                a.make_proxies_and_event_listeners(newclass)

            return newclass

        python_class = property(_make_or_get_python_class)

        def workspace_permission(self, workspace):
            '''
            Return the access configuration for the given workspace, or
            None if nothing was set.

            :type workspace:  Workspace
            :param workspace: the workspace to configure
            '''
            # We actually ask for the permissions to our root class
            return self._root.workspace_permission(workspace)

        def __lt__(self, kb_cls):
            if not isinstance(kb_cls, KBClass):
                raise TypeError(('KBClass instances can only be compared with '
                                 + 'objects of the same type '
                                 + '(got "%s" of type "%s" instead)')
                                % (unicode(kb_cls), unicode(type(kb_cls))))
            return (kb_cls in self.ancestors())

        # Implement a partial order for describing KB classes inheritance
        def __gt__(self, kb_cls):
            return (self in kb_cls.ancestors())
        def __le__(self, kb_cls):
            return (kb_cls is self) or (self < kb_cls)
        def __ge__(self, kb_cls):
            return (kb_cls is self) or (self > kb_cls)

        def __repr__(self):
            return "<KBClass('%s', '%s')>" % (self.name, self.id)

    o.KBClass = KBClass

    class KBRootClass(KBClass):
        def __init__(self, name, attributes=[], notes=None, explicit_id=None):
            KBClass.__init__(self, name, None, attributes=attributes,
                             notes=notes, explicit_id=explicit_id)

        def setup_workspace(self, workspace, access=access.READ_ONLY):
            '''
            Setup the root class visibility on the given workspace.

            :type workspace:  Workspace
            :param workspace: the workspace to configure

            :type access:  Access mode (access.OWNER, access.READ_ONLY or
                           access.READ_WRITE)
            :param access: Access configuration for the class on the given
                           workspace
            '''
            workspace.setup_root_class(self, access)

        def restrict_to_workspaces(self, ws_list):
            '''
            Remove root class access configurations for workspaces which
            are not included in the given list.

            Note that the list could also contain workspaces without an
            actual class access configuration (their status will not be
            changed by this method).

            :type ws_list:  a list of Workspace objects
            :param ws_list: workspaces which could access to the root class
            '''
            # Collect visibility configurations whose workspaces does not
            # appear in ws_list...
            del_ws_vis = [v for v in self.visibility
                          if v.workspace not in ws_list]
            # ...and delete them.
            for v in del_ws_vis:
                self.visibility.remove(v)

        def workspace_permission(self, workspace):
            acc = [v for v in self.visibility if v.workspace == workspace]
            if len(acc) == 0:
                # No access rules for the given workspace
                return None
            else:
                assert(len(acc) == 1) # Just in case
                return acc[0].access

        def __repr__(self):
            return "<KBRootClass('%s', '%s')>" % (self.name, self.id)

    o.KBRootClass = KBRootClass

    class KBClassAttribute(object):
        def __init__(self, class_, name, attr_type):
            pass

    o.KBClassAttribute = KBClassAttribute

    class KBClassVisibility(object):
        def __init__(self, class_, workspace, access):
            setattr(self, 'class', class_)
            self.workspace = workspace
            ## FIXME: check for access validity
            self.access = access

        def __repr__(self):
            return "<KBClassVisibility('%s, %s, %s')>" % (getattr(self,
                                                                  'class'),
                                                          self.workspace,
                                                          self.access)

    o.KBClassVisibility = KBClassVisibility

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

    o.KBObject = KBObject

    # Former Keyword and Category definitions
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

    o.CatalogEntry = CatalogEntry

    class RootCatalogEntry(CatalogEntry):
        def __init__(self, type_obj):
            CatalogEntry.__init__(self, type_obj, None)

        def add_to_workspace(self, workspace, access=access.READ_ONLY):
            workspace.add_catalog_tree(self, access)

        def __repr__(self):
            return "<RootCatalogEntry('%s', %s')>" % (self.id, self.object)

    o.RootCatalogEntry = RootCatalogEntry

    class CatalogTreeVisibility(object):
        def __init__(self, catalog_entry, workspace, access=access.READ_ONLY):
            self.catalog_entry = catalog_entry
            self.workspace = workspace
            self.access = access

        def __repr__(self):
            return ("<CatalogTreeVisibility('%s, %s, %s')>"
                    % (self.catalog_entry, self.workspace, self.access))

    o.CatalogTreeVisibility = CatalogTreeVisibility

    ###########################################################################
    # Mappers
    ###########################################################################
    from attributes import Attributes
    o._attributes = Attributes(o)

    mapper(User, schema.user)

    mapper(Item, schema.item)

    mapper(ItemVisibility, schema.item_visibility,
           properties={
            'item' : relationship(Item, backref='visibility', cascade='all')
            })

    mapper(Workspace, schema.workspace,
           properties={
            '_creator_id' : schema.workspace.c.creator_id,
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
                                   cascade='all'),
            'attributes' : relationship(o._attributes.Attribute,
                                        back_populates='_class',
                                        cascade='save-update')
            })

    mapper(KBRootClass, inherits=KBClass,
           polymorphic_identity=True)

    mapper(KBClassVisibility, schema.class_visibility,
           properties={
            '_workspace' : schema.class_visibility.c.workspace,
            '_class_id' : schema.class_visibility.c['class'],
            '_class_root' : schema.class_visibility.c.class_root,
            'class' : relationship(KBRootClass,
                                   backref='visibility', cascade='all')
            })

    mapper(KBObject, schema.object_t,
           polymorphic_on=schema.object_t.c['class'],
           properties={
            '_class' : schema.object_t.c['class'],
            '_class_root' : schema.object_t.c.class_root,
            'class' : relationship(KBClass, backref='objects', cascade='all')
            })

    # Former Keyword and Category mappers
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


    ###########################################################################
    # Events
    ###########################################################################
    # Update related fields when the parent of a catalog entry is changed
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

    # Update related fields when the parent of a KB class is changed
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
                raise TypeError('Parent must be a KBClass (received: %s, '
                                'type: %s)'
                                % (str(value), str(type(value))))
            target._root_id = value._root_id
            target._parent_id = value.id
            target._parent_root = value._root_id
            target._is_root = (target.id == value.id)

    event.listen(KBClass.superclass, 'set', kbclass_update_superclass_attrs,
                 propagate=True, retval=False)

    # Bind an attribute to its owner class when it gets added to the
    # 'attributes' list
    # FIXME: it should happen automatically, shouldn't it?
    def kbclass_append_attribute(target, value, _initiator):
        if not isinstance(value, o._attributes.Attribute):
            raise TypeError('Expected an Attribute, got "%s" (type: %s)'
                            % (value, type(value)))
        if (value.multivalued and hasattr(value, '_sqlalchemy_mv_table')
            and (value._sqlalchemy_mv_table is not None)):
            raise RuntimeError('BUG: cannot reassign attribute "%s", '
                               'since it is still bound to table "%s"'
                               % (value.id,
                                  value._sqlalchemy_mv_table.name))        
        value._class_id = target.id
        value._class_root_id = target._root_id

        # FIXME: ensure uniqueness!
        # FIXME: it would be better to prefix the owner table name
        if value.multivalued:
            value._multivalue_table = ('%sclass_%s_attr_%s'
                                       % (schema.prefix,
                                          value._class_id,
                                          value.id))
            # Will be assigned after invoking the attribute table constructor
            value._sqlalchemy_mv_table = None

    event.listen(KBClass.attributes, 'append',
                 kbclass_append_attribute, propagate=True, retval=False)

    # Detach attributes from its (former) owner class when it gets removed from
    # the 'attributes' list
    # FIXME: it should happen automatically, shouldn't it?
    def kbclass_remove_attribute(target, value, _initiator):
        assert(isinstance(value, o._attributes.Attribute))
        value._class_id = None
        value._class_root_id = None
        value._multivalue_table = None
        # FIXME: decide what to do if a MV table is "orphaned" by attr removal

    event.listen(KBClass.attributes, 'remove',
                 kbclass_remove_attribute, propagate=True, retval=False)
