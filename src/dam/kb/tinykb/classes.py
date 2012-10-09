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

import threading
import types
import weakref

from sqlalchemy import ForeignKey, event
import sqlalchemy.orm as orm
import sqlalchemy.exc as exc
from sqlalchemy.orm import mapper, backref, relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.schema import Column, Table
from sqlalchemy.sql import and_

import access

from util import niceid, decorators

# Number of random characters added for ID generation
RAND_SUFFIX_LENGTH = 8

class Classes(types.ModuleType):
    def __init__(self, session):
        types.ModuleType.__init__(self, 'tinykb_%s_classes'
                                  % (session.id_, ))
        import session as kb_session
        assert(isinstance(session, kb_session.Session))

        self._session_ref = weakref.ref(session)

        _init_base_classes(self)

        self.__all__ = ['attributes', 'session',
                        'KBClass', 'KBRootClass', 'KBClassVisibility',
                        'KBObject', 'User', 'Workspace']


    # self._attributes is set in _init_base_classes
    attributes = property(lambda self: self._attributes)

    session = property(lambda self: self._session_ref())


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

    # KBClass instance cache, used to keep the correspondence between
    # static and dynamically-generated classes.  The caching policy is:
    #
    #   1. KBClass'es retrieved from the DB will auto-cache themselves;
    #
    #   2. new KBClass'es will auto-cache themselves after they are realized;
    #
    #   3. the cache must be queried before accessing the underlying DB;
    #
    #   4. KBClass.python_class must first check the cache, and if an
    #      equivalent istance is found, then the actual python class must
    #      be retrieved from there
    # FIXME: we definitely need some locking on the cache!
    o._kb_class_cache = {}
    def cache_add(cls):
        # The class must not have been cached in advance
        assert(o._kb_class_cache.get(cls.id) is None)
        # Also cache all the ancestors, in order to keep the cached
        # classes linked
        for a in cls.ancestors():
            cached_a = cache_get(a.id, None)
            if cached_a is a:
                # We are done
                break
            if cached_a is None:
                # First time the ancestor enters the cache
                o._kb_class_cache[a.id] = a
            else:
                # Another equivalent KBClass was still cached: let's
                # substitute it
                cache_update(a)
        o._kb_class_cache[cls.id] = cls
    o.cache_add = cache_add

    def cache_get(cls_id, session):
        ret = o._kb_class_cache.get(cls_id, None)
        if session is None:
            # No need to fiddle with the session, just return the result
            return ret
        if ret is not None:
            obj_session = Session.object_session(ret)
            if obj_session is not session:
                # Return a copy of the KBClass merged with the current session
                return session.merge(ret)
            else:
                return ret
    o.cache_get = cache_get

    def cache_update(cls):
        old_cls = o._kb_class_cache.get(cls.id, None)
        # The class must have been cached in advance
        assert(old_cls is not None)
        if old_cls is cls:
            # Nothing to do here
            return

        # "Reparent" the Python class.
        # FIXME: create some internal API here!
        if hasattr(old_cls,  '_cached_pyclass_ref'):
            assert(not hasattr(cls, '_cached_pyclass_ref'))
            pyclass = old_cls._cached_pyclass_ref()
            cls._cached_pyclass_ref = weakref.ref(pyclass)
            pyclass.__kb_class__ = cls
        o._kb_class_cache[cls.id] = cls
    o.cache_update = cache_update

    def cache_del(cls_id):
        del o._kb_class_cache[cls_id]
    o.cache_del = cache_del

    class Workspace(object):
        '''
        Knowledge base workspace.

        .. warning:: This class is mapped to NotreDAM workspaces, and
                     it's also handled by Django through its models.

        :type name: string
        :param name: workspace name

        :type creator: :py:class:`User`
        :param creator: workspace creator
        '''
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
            '''
            Setup the access rules of the given KB class.

            :type class_: :py:class:`KBRootClass`
            :param class_: KB class to configure

            :type access: :py:mod:`access` constant
            :param access: Access rule for the given root class
            '''
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
        '''
        User which could own one or more workspaces.

        .. warning:: This class is mapped to NotreDAM users, and
                     it's also handled by Django through its models.

        :type username: string
        :param username: user name

        '''
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
        '''
        Knowledge base class.

        :type name: string
        :param name: human-readable name

        :type superclass: :py:class:`KBClass`
        :param superclass: parent class

        :type attributes: list of :py:class:`attributes.Attribute`
        :param attributes: list of class attributes

        :type notes: string
        :param notes: descriptive text with miscellaneous notes

        :type explicit_id: string
        :param explicit_id: KB class identifier.  It must be unique,
                            and it may be composed by ASCII letters, numbers
                            and underscores (i.e. the same characters which
                            are usually adopted for Python object attributes).
                            When left empty, the ID will be autogenerated from
                            the human-readable name.

        .. data:: <, <=, >=, >

            KB classes form a partial order based on their inheritance
            relations.  For example, consider the following inheritance
            hierarchy::

                c1
                 |
                 +---- c2
                 |
                 +---- c3

            where ``c2`` and ``c3`` inherit from ``c1``.  Then both
            ``c1 <= c2`` and ``c1 <= c3`` hold --- however, neither
            ``c2 <= c3`` nor ``c3 <= c2`` hold.
        '''
        def __init__(self, name, superclass, attributes=[], notes=None,
                     explicit_id=None):
            suffix = '_' + niceid.generate(length=RAND_SUFFIX_LENGTH)
            if explicit_id is None:
                clean_id = niceid.niceid(name, extra_chars=RAND_SUFFIX_LENGTH)
                # FIXME: check uniqueness!
                self.id = '%s%s' % (clean_id, suffix)
            else:
                clean_id = explicit_id.lower()
                self.id = explicit_id

            # Create a SQL table name, with proper prefixes and
            # suffixes, whithin schema.SQL_TABLE_NAME_LEN_MAX chars
            prefix = schema.prefix + 'object_'
            base_table_name_len = (schema.SQL_TABLE_NAME_LEN_MAX
                                   - len(prefix) - len(suffix))
            self.table = prefix + clean_id[0:base_table_name_len] + suffix
            assert(len(self.table) <= schema.SQL_TABLE_NAME_LEN_MAX)

            # Save suffix for later use (e.g. in attr table creation)
            self._table_suffix = suffix

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

            # When created from scratch, no table on DB should exists
            # NOTE: these must be set up before adding attributes, since
            # the event handlers require a properly-configured KBClass instance
            self._sqlalchemy_table = None
            self.additional_sqlalchemy_tables = []

            for a in attributes:
                if a.id in inherited_attr_ids:
                    raise RuntimeError('Cannot redefine inherited attribute'
                                       ' "%s"' % (a.id, ))
                self.attributes.append(a)
            self.notes = notes

        @orm.reconstructor
        def __init_on_load__(self):
            self._sqlalchemy_table = None
            self.bind_to_table()
            if cache_get(self.id, Session.object_session(self)) is None:
                cache_add(self)

            # Reconstruct table suffix
            suffix_chars = RAND_SUFFIX_LENGTH + 1 # Also count "_" character
            self._table_suffix = self.table[-suffix_chars:]

        sqlalchemy_table = property(lambda self: self._sqlalchemy_table)

        # FIXME: __del__ makes this class end up in GC's 'garbage' list
        # Anyway, this method is redundant, as long as the KB Session is
        # used properly
        # def __del__(self):
        #     # When a KBClass object is garbage collected, check
        #     # whether the DB instance was deleted, and in this case
        #     # also drop the related tables (by calling
        #     # self.unrealize()).
        #     #
        #     # It should be safe to invoke self.unrealize() here: if
        #     # this destructor is called, then this Python object is
        #     # not (anymore) involved in a transaction, and thus the
        #     # underlying tables should not be locked.
        #
        #     # FIXME: does SQLAlchemy allow to check whether we are deleted?
        #     if hasattr(self, '__kb_deleted__'):
        #         self.unrealize()
        
        def is_root(self):
            return (self.id == self._root_id)

        def refresh_(self, _session=None):
            '''
            Refresh this KB class with the values stored in the SQL DB.
            '''
            session = Session.object_session(self)
            if session is None:
                session = _session
            session.refresh(self)
            if self.superclass is self:
                self.superclass.refresh_(_session=_session)

        def ancestors(self):
            '''
            Return a list of all the ancestor KBClass'es, starting from
            the immediate parent (if any).

            :rtype: list of :py:class:`KBClass` instances
            :returns: the ancestor KB classes
            '''
            c = self.superclass
            prev_c = self
            ancestors = []
            while c is not prev_c:
                ancestors.append(c)
                prev_c = c
                c = c.superclass
            return ancestors

        def descendants(self, depth=None):
            '''
            Retrieve a list of all the descendant
            :py:class:`KBClass`'es, starting from the immediate
            children (if any).

            :type  depth: int or None
            :param depth: number of inheritance levels to descend.  When None,
                          all the descendants will be retrieved.

            :rtype: list of :py:class:`KBClass` instances
            :returns: the descendant KB classes
            '''
            assert((depth is None)
                   or (isinstance(depth, int) and (depth >= 0)))

            if depth == 0:
                return []

            children = [c for c in self.subclasses if c is not self]

            if depth is None:
                nextdepth = None
            else:
                nextdepth = depth - 1

            return children + [d for c in children
                               for d in c.descendants(depth=nextdepth)]

        def is_bound(self):
            return self._sqlalchemy_table is not None

        def all_attributes(self):
            '''
            Return all the class attributes, including the ones of
            ancestor classes (if any)

            :rtype: list of :py:class:`orm.attributes.Attribute` instances
            :returns: all the class attributes
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

        # Guard for KBClass (un)realization
        o._pyclass_realize_lock = threading.RLock()

        @decorators.synchronized(o._pyclass_realize_lock)
        def realize(self):
            '''
            Create the SQL table(s) necessary for storing instances of
            a KB class.

            See also :py:meth:`session.Session.realize`.
            '''
            if self.is_bound():
                ## We are already bound to a table
                raise AttributeError('%s is already realized (SQL table: %s)'
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

            # Finally, let's add ourselves to the class cache
            cache_add(self)

        @decorators.synchronized(o._pyclass_realize_lock)
        def unrealize(self):
            '''
            Remove the SQL tables created with :py:meth:`realize`.

            .. warning:: Maybe you should not call this method
                         directly, since it is automatically invoked
                         when a KB class is deleted from a session.
                         Furthermore, it may also cause a deadlock if
                         the tables being dropped are actually used in
                         the current transaction.  As a safer
                         alternative, you may simply delete a KBClass
                         using :py:meth:`session.Session.delete`.
            '''
            # FIXME: does SQLAlchemy allow to check whether we are deleted?
            if not hasattr(self, '__kb_deleted__'):
                raise RuntimeError('Trying to unrealize a KB class before '
                                   'deleting it: %s' % (self, ))

            if hasattr(self, '__kb_unrealized__'):
                return # Let's avoid unrealizing twice

            if not self.is_bound():
                self.bind_to_table()

            # Drop all the tables related to our attributes (if any)...
            for t in self.additional_sqlalchemy_tables:
                schema.metadata.remove(t)
                t.drop(engine)

            # ...and finally drop the main KB class table
            schema.metadata.remove(self._sqlalchemy_table)
            self._sqlalchemy_table.drop(engine)

            self.__kb_unrealized__ = True # Let's avoid unrealizing twice

        def bind_to_table(self):
            parent_table = self._get_parent_table()
            attrs_ddl = self._get_attributes_ddl()

            if self.is_bound():
                raise AttributeError('KBClass.bind_to_table() was called twice'
                                     ' on %s' % (self, ))

            try:
                self._sqlalchemy_table = schema.get_object_table(self.table,
                                                                 parent_table,
                                                                 attrs_ddl)

                # The following call is going to require
                # self.sqlalchemy_table (set above)
                attrs_tables = self._get_attributes_tables()

                self.additional_sqlalchemy_tables = schema.get_attr_tables(
                    attrs_tables)
            except exc.InvalidRequestError:
                # FIXME: raise a meaningful (non SQLAlchemy-related)
                # exception here
                raise

        @decorators.synchronized(o._pyclass_realize_lock)
        def unbind_from_table(self):
            # FIXME: what about unbinding descendant classes as well?
            # At the moment, _forget_python_class() takes care of it
            if not self.is_bound():
                raise AttributeError('Trying to unbind a KB class that was not'
                                     ' bound: %s' % (self, ))
            table = self._sqlalchemy_table
            add_tables = self.additional_sqlalchemy_tables

            self.additional_sqlalchemy_tables = []
            self._sqlalchemy_table = None
            schema.remove_attr_tables(add_tables)
            schema.remove_object_table(table)

        # Guard for Python class generation
        o._pyclass_gen_lock = threading.RLock()

        @decorators.synchronized(o._pyclass_gen_lock)
        def _forget_python_class(self, _visited=[]):
            '''
            Forget the Python class associated to this KBClass, in
            order to rebuild it at the next request.  The _visited argument
            will be enriched with the KB classes visited by the algorithm
            '''
            if self in _visited:
                # Avoid loops
                return
            _visited.append(self)

            if not self.is_bound():
                # If we are not bound, then no Python class has been built yet
                # (and the same goes for our descendants)
                return

            # We also need to forget the derived python classes
            for c in self.descendants(depth=1):
                c._forget_python_class(_visited=_visited)

            # ...and we also need to forget the classes which
            # reference to ourselves.
            # NOTE: avoid re-visiting classes, or their SQLAlchemy tables
            # may be recreated under the hood!
            for a in [r for r in self.references
                      if getattr(r, '__class_id') not in [c.id
                                                          for c in _visited]]:
                getattr(a, 'class')._forget_python_class(_visited=_visited)

            from sqlalchemy.orm.instrumentation import unregister_class

            if hasattr(self, '_cached_pyclass_ref'):
                pyclass = self._cached_pyclass_ref()
                if pyclass is not None:
                    unregister_class(pyclass)
                del self._cached_pyclass_ref
                self.unbind_from_table()

            # Also cleanup the cache (just in case)
            c = cache_get(self.id, None)
            if ((c is not None) and (c is not self)
                and hasattr(c, '_cached_pyclass_ref')):
                pyclass = c._cached_pyclass_ref()
                if pyclass is not None:
                    unregister_class(pyclass)
                del c._cached_pyclass_ref
                c.unbind_from_table()

        @decorators.synchronized(o._pyclass_gen_lock)
        def _make_or_get_python_class(self, _session=None,
                                      _only_if_cached=False):
            '''
            The Python class associated to a KB class.  This property
            can only be accessed after :py:meth:`realize` was invoked.

            The _session argument will cause the method queries to be
            bound to the given SQLAlchemy session.

            The _only_if_cached argument, if True, will cause this method
            to return None if the Python class was not already built and
            cached.
            '''
            # The class will be built only once, and further calls
            # will always return the same result
            ref = getattr(self, '_cached_pyclass_ref', None)
            if ref is not None:
                cls = ref()
                if cls is not None:
                    return cls

            # Establish in which session we're working in (and pass it
            # to further recursive calls)
            obj_session = Session.object_session(self)
            if _session is None:
                _session = obj_session
            if _session is obj_session:
                sself = self
            else:
                sself = _session.merge(self)
                _session.add(sself)

            # First of all, check whether an equivalent KBClass is still cached
            c = cache_get(sself.id, None)
            assert(c is not None) # The KBClass must have been cached

            if c is not self:
                return c._make_or_get_python_class(_session=_session,
                                               _only_if_cached=_only_if_cached)

            # If we are here, all the cache checks failed, and we are
            # going to build the Python class
            if _only_if_cached:
                return None

            if not sself.is_bound():
                sself.bind_to_table()

            if not sself.is_root():
                parent_class = sself.superclass._make_or_get_python_class(
                    _session=_session)
                init_method = lambda instance, name, notes=None, explicit_id=None, _rebind_session=None:(
                    parent_class.__init__(instance, name, notes=notes,
                                          explicit_id=explicit_id,
                                          _rebind_session=_rebind_session))
            else:
                parent_class = KBObject
                init_method = lambda instance, name, notes=None, explicit_id=None, _rebind_session=None:(
                    parent_class.__init__(instance, instance.__kb_class__,
                                          name, notes=notes,
                                          explicit_id=explicit_id,
                                          _rebind_session=_rebind_session))

            classdict = {
                '__init__' : init_method,
                '__repr__' : lambda instance: (
                    "<%s('%s', '%s')>" % (sself.name, instance.name,
                                          instance.id)),
                '__kb_class__' : sself,
                '__class_id__' : sself.id,
                '__class_root_id__': sself._root_id
                }
            newclass = type(str(niceid.niceid(sself.name,
                                              extra_chars=0)),
                            (parent_class, ),
                            classdict)

            # NOTE: the cached python class needs to be set *before*
            # generating the SQLAlchemy ORM mapper, because it will
            # access to self.python_class again, thus causing an
            # infinite recursion
            self._cached_pyclass_ref = weakref.ref(newclass)

            # Let's now build the SQLAlchemy ORM mapper
            mapper_props = {}
            for r in sself.attributes:
                mapper_props.update(r.mapper_properties())

            m = mapper(newclass, sself._sqlalchemy_table,
                       inherits=parent_class,
                       polymorphic_identity=sself.id,
                       properties = mapper_props)

            # Also add the mapper to the class dictionary, as weak ref
            newclass.__sql_mapper__ = weakref.ref(m)

            # Also add event listeners for validating assignments
            # according to attribute types
            for a in sself.attributes:
                a.make_proxies_and_event_listeners(newclass)

            return newclass

        python_class = property(_make_or_get_python_class)

        def workspace_permission(self, workspace):
            '''
            Return the access configuration for the given workspace, or
            None if nothing was set.

            :type workspace:  :py:class:`orm.Workspace`
            :param workspace: the workspace to configure
            '''
            # We actually ask for the permissions to our root class
            return self.root.workspace_permission(workspace)

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
        '''
        Knowledge base class without a parent.  The constructor
        arguments are the same of :py:class:`KBClass`.

        Even if a ``KBRootClass`` instance is always at the top of
        each KB class hierarchy, from the object-oriented point of
        view it is just a special case of :py:class:`orm.KBClass` ---
        thus, it is implemented as a derived Python class.
        '''
        def __init__(self, name, attributes=[], notes=None, explicit_id=None):
            KBClass.__init__(self, name, None, attributes=attributes,
                             notes=notes, explicit_id=explicit_id)

        def setup_workspace(self, workspace, access=access.READ_ONLY):
            '''
            Setup the root class visibility on the given workspace.

            :type workspace:  :py:class:`Workspace`
            :param workspace: the workspace to configure

            :type access:  :py:mod:`access` constant
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

            :type ws_list:  a list of :py:class:`Workspace` objects
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
            acc = [v for v in self.visibility if v._workspace == workspace.id]
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
        '''
        Visibility configuration of a :py:class:`KBRootClass` on a
        NotreDAM :py:class:`Workspace`.

        .. warning:: This is class may be changed or removed in the
           future.  Instead, you could (and should) use:

            * :py:meth:`KBRootClass.setup_workspace`

            * :py:meth:`KBRootClass.restrict_to_workspaces`

            * :py:meth:`Workspace.setup_root_class`

        :type class_:  :py:class:`KBRootClass`
        :param class_: KB class to be made visible

        :type workspace:  :py:class:`Workspace`
        :param workspace: workspace on which ``class_`` will be exposed

        :type access: :py:mod:`access` constant
        :param access: access rule for the given class
        '''
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

    class KBObject(object):
        '''
        Abstract base class for KB objects, sitting at the root of
        Python classes generated from :py:class:`KBClass`.

        .. note:: This constructor is only intended to be called
                  internally.
        '''
        def __init__(self, class_, name, notes=None, explicit_id=None,
                     _rebind_session=None):
            if explicit_id is None:
                # FIXME: check uniqueness!
                self.id = niceid.niceid(name, extra_chars=RAND_SUFFIX_LENGTH)
            else:
                self.id = explicit_id

            if _rebind_session is not None:
                kbclass = _rebind_session.merge(class_)
                _rebind_session.add(kbclass)
            else:
                kbclass = class_

            setattr(self, 'class', kbclass)
            self.name = name
            self.notes = notes

            # Give a default value to all attributes (when possible)
            for a in kbclass.all_attributes():
                if hasattr(a, 'default'):
                    val = a.default
                    if (val is not None) or a.maybe_empty:
                        if not a.multivalued:
                            setattr(self, a.id, val)

        
        def workspace_permission(self, ws):
            '''
            Return the access configuration of the object root class
            for the given workspace, or None if nothing was set.

            :type workspace:  :py:class:`orm.Workspace`
            :param workspace: the workspace to configure
            '''
            # First of all, we need to ensure that our KBClass is
            # bound to the same session we're using
            session = Session.object_session(self)
            self.__kb_class__ = session.merge(self.__kb_class__)
            session.add(self.__kb_class__)
            return self.__kb_class__.workspace_permission(ws)


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

    # FIXME: unused right now
    # mapper(ItemVisibility, schema.item_visibility,
    #        properties={
    #         'item' : relationship(Item, backref='visibility')
    #         })

    mapper(Workspace, schema.workspace,
           properties={
            '_creator_id' : schema.workspace.c.creator_id,
            'creator' : relationship(User, backref='workspaces'),
            # FIXME: unused right now
            # 'visible_items' : relationship(ItemVisibility, backref='workspace',
            #                                cascade='all, delete-orphan'),
            # FIXME: unused right now
            # 'visible_catalog_trees' : relationship(CatalogTreeVisibility,
            #                                        backref='workspace',
            #                                        cascade='all, delete-orphan'),
            'visible_root_classes' : relationship(KBClassVisibility,
                                                  backref='workspace',
                                                  cascade='all, delete-orphan')
            })

    mapper(KBClass, schema.class_t,
           polymorphic_on=schema.class_t.c.is_root,
           polymorphic_identity=False,
           properties={
            '_root_id' : schema.class_t.c.root,
            '_parent_id' : schema.class_t.c.parent,
            '_parent_root' : schema.class_t.c.parent_root,
            '_is_root' : schema.class_t.c.is_root,
            'superclass' : relationship(KBClass,
                                        backref=backref('subclasses',
                                                        cascade='all, delete-orphan',
                                                        lazy='select'),
                                        primaryjoin=(schema.class_t.c.parent
                                                     ==schema.class_t.c.id),
                                        remote_side=[schema.class_t.c.id],
                                        lazy='immediate',
                                        viewonly=True),
            'root' : relationship(KBRootClass,
                                  primaryjoin=(schema.class_t.c.root
                                               ==schema.class_t.c.id),
                                  remote_side=[schema.class_t.c.id],
                                  lazy='immediate',
                                  viewonly=True),
            'attributes' : relationship(o._attributes.Attribute,
                                        lazy='immediate',
                                        back_populates='class',
                                        cascade='all, delete-orphan')
            })

    mapper(KBRootClass, inherits=KBClass,
           polymorphic_identity=True,
           properties={
            'visibility' : relationship(KBClassVisibility,
                                        lazy='immediate',
                                        back_populates='class',
                                        cascade='all, delete-orphan')
            })

    mapper(KBClassVisibility, schema.class_visibility,
           properties={
            '_workspace' : schema.class_visibility.c.workspace,
            '_class_id' : schema.class_visibility.c['class'],
            '_class_root' : schema.class_visibility.c.class_root,
            'class' : relationship(KBRootClass,
                                   back_populates='visibility')
            })

    mapper(KBObject, schema.object_t,
           polymorphic_on=schema.object_t.c['class'],
           properties={
            '_class' : schema.object_t.c['class'],
            '_class_root' : schema.object_t.c.class_root,
            'class' : relationship(KBClass,
                                   lazy='immediate',
                                   backref='objects')
            })

    # FIXME: unused right now
    # mapper(CatalogEntry, schema.catalog_entry,
    #        polymorphic_on=schema.catalog_entry.c.is_root,
    #        polymorphic_identity=False,
    #        properties={
    #         '_root' : schema.catalog_entry.c.root,
    #         '_parent_id' : schema.catalog_entry.c.parent,
    #         '_parent_root' : schema.catalog_entry.c.parent_root,
    #         '_object_id' : schema.catalog_entry.c.object,
    #         '_object_class_root' : schema.catalog_entry.c.object_class_root,
    #         '_is_root' : schema.catalog_entry.c.is_root,
    #         'parent' : relationship(CatalogEntry, backref='children',
    #                                   primaryjoin=(schema.catalog_entry.c.parent
    #                                                ==schema.catalog_entry.c.id),
    #                                   remote_side=[schema.catalog_entry.c.id]),
    #         'object' : relationship(KBObject, backref='catalog_entries')
    #         })

    # FIXME: unused right now
    # mapper(RootCatalogEntry, inherits=CatalogEntry,
    #        polymorphic_identity=True)

    # FIXME: unused right now
    # mapper(CatalogTreeVisibility, schema.catalog_tree_visibility,
    #        properties={
    #         '_workspace' : schema.catalog_tree_visibility.c.workspace,
    #         '_catalog_entry' : schema.catalog_tree_visibility.c.catalog_entry,
    #         '_catalog_entry_root' : schema.catalog_tree_visibility.c.catalog_entry_root,
    #         '_catalog_entry_object_class_root' : schema.catalog_tree_visibility.c.catalog_entry_object_class_root,
    #         'catalog_entry' : relationship(RootCatalogEntry,
    #                                        backref='visibility'),
    #         'root_class_visibility' : relationship(KBClassVisibility,
    #                                                backref='catalog_tree_visibilities')
    #         })


    ###########################################################################
    # Events
    ###########################################################################
    # Update related fields when the parent of a catalog entry is changed
    # FIXME: unused right now
    # def catentry_update_parent_attrs(target, value, _oldvalue, _initiator):
    #     if value is None:
    #         target._root = target.id
    #         target._parent_id = target.id
    #         target._parent_root = target.id
    #         target._is_root = True
    #     else:
    #         if isinstance(target, RootCatalogEntry):
    #             raise AttributeError(
    #                 'Cannot change the parent of a root catalog entry')
    #         if not isinstance(value, CatalogEntry):
    #             raise TypeError('Parent must be a CatalogEntry (received: %s)'
    #                             % str(type(value)))
    #         target._root = value._root
    #         target._parent_id = value.id
    #         target._parent_root = value._root
    #         target._is_root = (target.id == value.id)
    #
    # event.listen(CatalogEntry.parent, 'set', catentry_update_parent_attrs,
    #              propagate=True, retval=False)

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

        if value.id in [a.id for a in target.all_attributes()]:
            raise RuntimeError('Cannot append already existing attribute'
                               ' "%s"' % (value.id, ))

        # Also mark the new attribute for addition, if necessary
        if target.is_bound():
            if not hasattr(target, '_new_attributes'):
                target._new_attributes = []
            target._new_attributes.append(value)

        value._class_id = target.id
        value._class_root_id = target._root_id

        # FIXME: ensure uniqueness!
        # FIXME: it would be better to prefix the owner table name
        if value.multivalued:
            # Create a SQL table name, with proper prefixes and
            # suffixes, whithin schema.SQL_TABLE_NAME_LEN_MAX chars
            prefix_max = min(len(target.table) - len(target._table_suffix),
                             (schema.SQL_TABLE_NAME_LEN_MAX
                              - (len(target._table_suffix) * 3)))
            prefix = (('%sobject_%s' % (schema.prefix,
                                       value._class_id))[0:prefix_max]
                      + target._table_suffix)
            table_name = ('%s_attr_%s' %
                          (prefix, value.id))[0:schema.SQL_TABLE_NAME_LEN_MAX]
            
            # FIXME: another unique suffix may be needed for long attr names
            value._multivalue_table = table_name

            # Will be assigned after invoking the attribute table constructor
            value._sqlalchemy_mv_table = None

    event.listen(KBClass.attributes, 'append',
                 kbclass_append_attribute, propagate=True, retval=False)

    # Detach attributes from its (former) owner class when it gets removed from
    # the 'attributes' list
    # FIXME: it should happen automatically, shouldn't it?
    def kbclass_remove_attribute(target, value, _initiator):
        assert(isinstance(value, o._attributes.Attribute))

        # Also mark the new attribute for removal, if necessary
        if target.is_bound():
            if (not hasattr(target, '_new_attributes')
                or (value not in target._new_attributes)):
                # Do not mark for removal attributes which were just
                # pending addition --- they are handled below
                if not hasattr(target, '_del_attributes'):
                    target._del_attributes = []
                target._del_attributes.append(value)

        # Remove the attribute from the list marked for addition
        if target.is_bound() and hasattr(target, '_new_attributes'):
            if value in target._new_attributes:
                target._new_attributes.remove(value)

    event.listen(KBClass.attributes, 'remove',
                 kbclass_remove_attribute, propagate=True, retval=False)

    # Take note when a KB class is deleted
    # FIXME: maybe there is some other way (see KBClass.__del__() comments)
    def kbclass_after_delete(_mapper, _connection, target):
        target.__kb_deleted__ = True
    event.listen(KBClass, 'after_delete', kbclass_after_delete, propagate=True)

    # Look for new attributes, and sync cache when a KB class is updated
    # Since we are going to fiddle with Python classes, let'acquire the lock
    @decorators.synchronized(o._pyclass_gen_lock)
    def kbclass_after_update(_mapper, connection, target):
        assert(target.is_bound()) # Should be always true after INSERT
        if hasattr(target, '_new_attributes'):
            table_name = target.table

            # Create additional tables (when needed)
            tbl_nested_lst = [attr.additional_tables()
                              for attr in target._new_attributes]
            add_tables = [t for l in tbl_nested_lst for t in l] # Flatten

            target.additional_sqlalchemy_tables += schema.create_attr_tables(
                add_tables, connection)

            # Extend the SQL object table
            attr_nested_lst = [a.ddl() for a in target._new_attributes]
            attrs_ddl_lst = [d for l in attr_nested_lst for d in l] # Flatten
            schema.extend_object_table(table_name, attrs_ddl_lst, connection)

            # Let's see whether the Python class already exists, and
            # needs to be updated as well
            pyclass = target._make_or_get_python_class(_only_if_cached=True)
            if pyclass is not None:
                # Ensure that the Python class points to the updated KB class
                pyclass.__kb_class__ = target
                pyclass_mapper = pyclass.__sql_mapper__()
                assert(pyclass_mapper is not None)
                for a in target._new_attributes:
                    props = a.mapper_properties()
                    pyclass_mapper.add_properties(props)

                # FIXME: maybe it is not necessary, but it should do no harm
                # Update SQLAlchemy mappers configuration
                orm.configure_mappers()

                # Finally add event listeners for validating assignments
                # according to attribute types
                for a in target._new_attributes:
                    a.make_proxies_and_event_listeners(pyclass)

            del target._new_attributes

            # Finally, we need to update the cache, because it may contain
            # descendant classes or referencing classes which point to the
            # old target, with a non up-to-date list of attributes
            cache_update(target)
            for d in target.descendants():
                d.refresh_(_session=Session.object_session(target))
                cache_update(d)

        if hasattr(target, '_del_attributes'):
            table_name = target.table

            parent_table_name = target._get_parent_table()
            valid_attrs_ddl = target._get_attributes_ddl()
            schema.remove_object_attrs(table_name,
                                       [a.id for a in target._del_attributes
                                        if not (a.multivalued)],
                                       connection)

            # FIXME: we would like to update class mapping/instrumentation
            # Since it does not seem to be possible, we rebuild the mapping
            # from scratch
            # FIXME: most likely, it is going to leak memory!
            # Unfortunately, unused ORM mappers are not properly collected,
            # possibly due to internal reference loops in SQLAlchemy
            
            # Forget the Python class, in order to force its
            # rebuilding on next request
            target._forget_python_class()

            del target._del_attributes

            # Finally, we need to update the cache, because it may contain
            # descendant classes or referencing classes which point to the
            # old target, with a non up-to-date list of attributes
            cache_update(target)
            for d in target.descendants():
                d.refresh_(_session=Session.object_session(target))
                cache_update(d)

    event.listen(KBClass, 'after_update', kbclass_after_update, propagate=True)

    # Cleanup new attributes
    def kbclass_after_insert(mapper, connection, target):
        # We need to manage new attributes
        kbclass_after_update(mapper, connection, target)
    event.listen(KBClass, 'after_insert', kbclass_after_insert, propagate=True)
