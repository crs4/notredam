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
# Knowledge base session handling.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

import itertools
import weakref

import sqlalchemy
import sqlalchemy.orm as sa_orm
import sqlalchemy.engine.base as sa_base
import sqlalchemy.orm.exc as sa_exc
import sqlalchemy.schema as sa_schema
from sqlalchemy.sql.expression import and_

import attributes as kb_attrs
import classes as kb_cls
import errors as kb_exc
import schema as kb_schema

class Session(object):
    '''
    Access point for working with a TinyKB knowledge base.

    A session instance offers several query methods for retrieving
    classes and objects.  Under the hood, it handles SQL DB
    connections, transactions and object-relational mapping details.

    :type  connstr_or_engine: SQLAlchemy connection string or engine
    :param connstr_or_engine: used to access the knowledge base SQL DB

    :type  id_: string
    :param id_: an unique identifier for distinguishing the session.
                If not given, it will be auto-generated.

    :type  db_prefix: string
    :param db_prefix: prefix used for naming the KB schema objects
                      on the SQL DB (tables, constraints...).
    '''
    def __init__(self, sess_or_connstr_or_engine, id_=None, db_prefix='kb_',
                 _duplicate_from=None):
        if isinstance(sess_or_connstr_or_engine, str):
            self._engine = sqlalchemy.create_engine(sess_or_connstr_or_engine)
            self.session = sa_orm.Session(bind=self._engine, autoflush=False)
        elif isinstance(sess_or_connstr_or_engine, sa_base.Engine):
            self._engine = sess_or_connstr_or_engine
            self.session = sa_orm.Session(bind=self._engine, autoflush=False)
        else:
            # We assume that the parameter is a Session or ScopedSession
            try:
                self._engine = sess_or_connstr_or_engine.get_bind()
                self.session = sess_or_connstr_or_engine
            except:
                # Something went wrong
                # FIXME: we are masking the actual exception here
                raise TypeError('Unsupported value for Session initialization:'
                                ' %s (type: %s)'
                                % (sess_or_connstr_or_engine,
                                   type(sess_or_connstr_or_engine)))

        if id_ is None:
            id_ = '%x' % (id(self), )
        assert(isinstance(id_, str))
        self._id = id_
        
        if _duplicate_from is None:
            self._schema = kb_schema.Schema(db_prefix)
            self._orm = kb_cls.Classes(self)
        else:
            assert(isinstance(_duplicate_from, Session))
            assert(db_prefix == _duplicate_from._schema.prefix) # Coherency

            self._schema = _duplicate_from._schema
            self._orm = _duplicate_from._orm

        # List of KB classes to be unrealized as soon as the current
        # transaction is committed
        self._kb_classes_pending_unrealize = []

        # Let's use a direct reference in the following closures, in
        # order to avoid capturing 'self' in a reference cycle which
        # may cause memory leaks
        _kb_classes_pending_unrealize = self._kb_classes_pending_unrealize
        def session_after_commit(_session):
            # Unrealize classes after they've been deleted
            try:
                while True:
                    cls = _kb_classes_pending_unrealize.pop()
                    cls.unrealize()
            except IndexError: pass
        sqlalchemy.event.listen(self.session, 'after_commit',
                                session_after_commit)

        def session_after_rollback(_session):
            # Cleanup list of classes waiting to be unrealized
            try:
                while True:
                    _kb_classes_pending_unrealize.pop()
            except IndexError: pass
        sqlalchemy.event.listen(self.session, 'after_rollback',
                                session_after_rollback)

    id_ = property(lambda self: self._id)
    '''
    The session identifier

    :type: string
    '''

    engine = property(lambda self: self._engine)
    '''
    The SQLAlchemy engine used for connecting to the DBMS

    :type: SQLAlchemy engine
    '''

    schema = property(lambda self: self._schema)
    '''
    The SQL DB schema instance bound to the session

    :type: :py:class:`schema.Schema`
    '''

    orm = property(lambda self: self._orm)
    '''
    A dynamically generated Python module implementing the
    object-relational mapping for the session, and providing access to
    the knowledge base classes and objects.  For more details, see the
    :py:mod:`orm` module documentation.

    :type: Python module (dynamically generated)
    '''

    def duplicate(self, sess_or_connstr_or_engine=None, id_=None):
        '''
        Create a new Session object sharing the same schema and
        :py:mod:`orm` attribute with the original one.

        The new session will handle the underlying SQL DB using its
        own connections and transactions.

        :type  id_: string
        :param id_: an unique identifier for distinguishing the session.
                    If not given, it will be auto-generated.

        :rtype: Session
        :returns: a new Session instance
        '''
        if sess_or_connstr_or_engine is None:
            sce = self._engine
        else:
            sce = sess_or_connstr_or_engine
        return Session(sce, id_=id_, db_prefix=self._schema.prefix,
                       _duplicate_from=self)


    def close(self, invoke_gc=True):
        '''
        Close a Session, thus releasing the underlying SQL DBMS
        connections and other resources.

        :type  invoke_gc: bool
        :param invoke_gc: tells whether the garbage collector will be
                          explicitly invoked when closing the session
                          (default: True)
        '''
        # Since we may be duplicated, we simply NULL-ify several
        # resources, and then invoke the garbage collector
        self._orm = None
        self._engine = None
        self._schema = None

        self.session.close()
        self.session = None

        if invoke_gc:
            import gc
            gc.collect()

    def add(self, obj):
        '''
        Add an object to the knowledge base session, ready for later
        :py:meth:`commit`.

        .. note:: The object will be actually saved when :py:meth:`commit`
                  is invoked.

        :type  obj: one of the classes accessible through the :py:attr:`orm`
               property (:py:class:`orm.KBClass`, :py:class:`orm.KBObject`,
               :py:class:`orm.Workspace`...)
        :param obj: object to be added
        '''
        self.session.add(obj)

    def add_all(self, obj_list):
        '''
        Add a list of objects to the knowledge base session.  This
        method has the same effect of issuing one :py:meth:`add` call
        for each object in the list.

        .. note:: The objects will be actually saved only
                  when :py:meth:`commit` is invoked.

        :type  obj: list of instances, whose class must be accessible
               through the :py:attr:`orm` property
        :param obj: object to be added
        '''
        self.session.add_all(obj_list)

    def delete(self, obj_or_cls):
        '''
        Mark the given object or class for deletion from the knowledge
        base.

        This method will raise a :py:exc:`errors.PendingReferences`
        exception if the given element is referenced by other KB
        classes, objects, etc.

        .. note:: The actual deletion will be performed when :py:meth:`commit`
                  is invoked.

        :type  obj_or_cls: :py:class:`orm.KBClass` or :py:class:`orm.KBObject`
        :param obj_or_cls: KB object or class to be deleted
        '''
        if self.has_references(obj_or_cls):
            raise kb_exc.PendingReferences('Class/object is referenced '
                                           'within the knowledge base')

        # Perform the actual KB class/object deletion
        self.session.delete(obj_or_cls)

        if isinstance(obj_or_cls, self.orm.KBClass):
            # Expunge the class from the ORM cache
            self.orm.cache_del(obj_or_cls.id)

        # Let's not forget to unrealize the class after the current
        # transaction is committed
        if isinstance(obj_or_cls, self.orm.KBClass):
            self._kb_classes_pending_unrealize.append(obj_or_cls)

    def has_references(self, obj_or_cls):
        '''
        Check whether the given class is references within the knowledge base

        :type  obj_or_cls: :py:class:`orm.KBClass` or :py:class:`orm.KBObject`
        :param obj_or_cls: KB object or class to be checked for references
        
        :rtype: bool
        :returns: True if references are found, False otherwise
        '''
        orm_attrs = self.orm.attributes

        if isinstance(obj_or_cls, self.orm.KBObject):
            cls = getattr(obj_or_cls, 'class')

            # Check whether the class or one of its ancestors appears in
            # an object reference attribute
            cls_lst = [cls] + cls.ancestors()

            # FIXME: in_() not yet supported for relationships
            # Check whether it will change in the next versions of SQLAlchemy
            # cls_refs = self.session.query(orm_attrs.ObjectReference).filter(
            #     orm_attrs.ObjectReference.target.in_(cls_lst))
            cls_lst = [c.id for c in cls_lst]
            cls_refs = self.session.query(orm_attrs.ObjectReference).filter(
               and_((self.schema.class_attribute_objref.c.target_class_root
                     == cls.root.id),
                    (self.schema.class_attribute_objref.c.target_class.in_(
                            cls_lst))))

            # For each KB class with a reference to the object class
            # (or one of its ancestors), check whether one of the
            # instances contains an actual reference to the object
            # itself
            obj_refs_cnt = 0
            for r in cls_refs:
                referencing_cls = getattr(r, 'class').python_class
                if r.multivalued:
                    ref_attr = getattr(referencing_cls, r.id)
                    mv_table = r._sqlalchemy_mv_table # FIXME: encapsulation!
                    obj_refs_cnt = self.session.query(referencing_cls).filter(
                        ref_attr.any(mv_table.c.value == obj_or_cls.id)
                        ).count()
                else:
                    ref_attr = getattr(referencing_cls, r.column_name())
                    obj_refs_cnt = self.session.query(referencing_cls).filter(
                        ref_attr == obj_or_cls).count()

                if obj_refs_cnt > 0:
                    return True
        elif isinstance(obj_or_cls, self.orm.KBClass):
            pyclass = obj_or_cls.python_class
            objs = self.session.query(pyclass)
            if objs.count() > 0:
                return True
    
            # Check whether the class or one of its descendants
            # appears in an object reference attribute
            cls_lst = [obj_or_cls] + obj_or_cls.descendants()
    
            # FIXME: in_() not yet supported for relationships
            # Check whether it will change in the next versions of SQLAlchemy
            # cls_refs = self.session.query(orm_attrs.ObjectReference).filter(
            #     orm_attrs.ObjectReference.target.in_(cls_lst))
            cls_lst = [c.id for c in cls_lst]
            cls_refs = self.session.query(orm_attrs.ObjectReference).filter(
               and_((self.schema.class_attribute_objref.c.target_class_root
                     == obj_or_cls.root.id),
                    (self.schema.class_attribute_objref.c.target_class.in_(
                            cls_lst))))
            if cls_refs.count() > 0:
                return True
        else:
            raise TypeError('expected KB object or class, got "%s" (type: %s)'
                            % (obj_or_cls, type(obj_or_cls)))
        return False

    def expunge(self, obj):
        '''
        Remove an object from the current transaction, before it's
        committed to knowledge base.

        If :py:meth:`commit` is invoked after this method, the object
        status in the knowledge base will not be altered.

        :type obj: object
        :param obj: an object instance (previously used with :py:meth:`add`
                    or :py:meth:`add_all` or :py:meth:`delete`)
        '''
        if isinstance(obj, list):
            for o in obj:
                self.session.expunge(o)
        else:
            self.session.expunge(obj)
    
    def expunge_all(self):
        '''
        Remove all objects from the current transaction, before they
        are committed to knowledge base.

        If :py:meth:`commit` is invoked after this method, it will
        have no effects.
        '''
        self.session.expunge_all()

    def begin_nested(self):
        '''
        Start a nested transaction.

        This method creates a savepoint in case of :py:meth:`rollback`.
        '''
        self.session.begin_nested()

    def commit(self):
        '''
        Commit the current transaction.

        Depending on their status, all the pending objects will be
        created, updated or deleted to/from the knowledge base SQL DB.
        Furthermore, all newly-created :py:class:`orm.KBClass`
        instances will be realized (see :py:meth:`realize`) or
        unrealized as necessary.
        '''
        # Before committing, ensure that all KBClass-derived objects
        # have an associated table
        new_kb_cls = [a for a in self.session.new
                      if isinstance(a, self.orm.KBClass)]
        for c in new_kb_cls:
            if not c.is_bound():
                c.realize()
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback()
            raise

    def rollback(self):
        '''
        Undo the effects of the current transaction on the knowledge
        base SQL DB.

        .. note:: If :py:meth:`begin_nested` was used, the rollback
                  will stop at the last savepoint.
        '''
        self.session.rollback()

    def class_(self, id_, ws=None):
        '''
        Retrieve the :py:class:`orm.KBClass` instance with the given
        id from the knowledge base SQL DB.

        :type  id_: string
        :param id_: KB class identifier

        :type  ws: :py:class:`orm.Workspace`
        :param ws: KB workspace object used to filter classes (default: None)

        :rtype: :py:class:`orm.KBClass`
        :returns: a KB class

        :raises: :py:exc:`errors.NotFound` if a class with the given
                 ID does not exist in the knowledge base (or in the
                 specified workspace, when provided)
        '''
        cls = self.orm.cache_get(id_, self.session)
        if cls is not None:
            if not self._check_class_ws_access(cls, ws):
                raise kb_exc.NotFound('class.id == %s' % (id_, ))
            return cls

        query = self.session.query(self.orm.KBClass).filter(
            self.orm.KBClass.id == id_)
        if (ws is not None):
            query = self._add_ws_filter(query, ws)

        try:
            return query.one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('class.id == %s' % (id_, ))


    def classes(self, ws=None, parent=None, recurse=True):
        '''
        Return an iterator yielding all known classes from the
        knowledge base.

        :type  ws: :py:class:`orm.Workspace`
        :param ws: KB workspace object used to filter classes (default: None)

        :type  parent: string or :py:class:`orm.KBClass` or None
        :param parent: parent of the classes being retrieved.  When None
                       (default), retrieval will start from root classes

        :type  recurse: bool
        :param recurse: also retrieve derived classes (default: True)

        :rtype: iterator
        :returns: an iterator yielding :py:class:`orm.KBClass` instances
        '''
        query = self.session.query(self.schema.class_t.c['id'])
        if parent is None and recurse:
            # Just retrieve all the classes
            pass
        elif parent is None and not recurse:
            # Only retrieve root classes
            query = query.filter(self.schema.class_t.c['id']
                                 == self.schema.class_t.c['root'])
        elif parent is not None and not recurse:
            # Just get the derived classes (without recursion)
            if isinstance(parent, self.orm.KBClass):
                parent = parent.id
            query = query.filter(and_((self.schema.class_t.c['parent']
                                       == parent),
                                      (self.schema.class_t.c['id']
                                       != parent)))
        else:
            # Retrieve all the derived classes
            raise NotImplementedError('Cannot recursively retrieve subclasses '
                                      'of a given class (yet)')

        if ws is not None:
            query = self._add_ws_table_filter(query, ws)
        return itertools.imap(lambda x: self.class_(x[0]),
                              query)

    def realize(self, class_):
        '''
        Create all the SQL tables and structures necessary for storing
        instances of the given KB class in the underlying DB.

        The KB class itself will be automatically added to the set of
        objects managed by the Session.

        .. note:: KB classes will be realized automatically when they
                  are added to the session, and then :py:meth:`commit`
                  is invoked.

        :type  class_: :py:class:`orm.KBClass`
        :param class_: the knowledge base class to be realized
        '''
        assert(isinstance(class_, self.orm.KBClass))
        self.add(class_)
        class_.realize()

    def python_class(self, id_, ws=None):
        '''
        Retrieve the Python class built from the KB class with the
        given identifier.

        The returned class will be ORM-mapped and ready to be used for
        queries and object instantiations.

        :type  id_: string
        :param id_: the identifier of the required KB class

        :type  ws: :py:class:`orm.Workspace`
        :param ws: KB workspace object used to filter classes (default: None)

        :rtype: class
        :returns: a Python class (inheriting from :py:class:`orm.KBObject`)

        :raises: :py:exc:`errors.NotFound` if a class with the given
                 ID does not exist in the knowledge base (or in the
                 specified workspace, when provided)
        '''
        return self.class_(id_, ws=ws).python_class

    def python_classes(self, ws=None):
        '''
        Retrieve a list of Python classes built from all the classes
        composing the knowledge base.

        :type  ws: :py:class:`orm.Workspace`
        :param ws: KB workspace object used to filter classes (default: None)

        :rtype: list of classes
        :returns: a list of Python classes (inheriting from
                  :py:class:`orm.KBObject`)
        '''
        return [c.python_class for c in self.classes(ws=ws)]

    def object(self, id_, ws=None):
        '''
        Retrieve the Python object mapped to the KB object with the
        given id.

        :type  id_: string
        :param id_: the identifier of the required KB object

        :type  ws: :py:class:`orm.Workspace`
        :param ws: KB workspace object used to filter KB objects according to
                   the visibility of their class (default: None)

        :rtype: :py:class:`orm.KBObject`
        :returns: a Python object (mapped to the KB session)

        :raises: :py:exc:`errors.NotFound` if an object with the given
                 ID does not exist in the knowledge base (or in the
                 specified workspace, when provided)
        '''
        # Retrieve the class id of the required object (if any)...
        try:
            o = self.session.query(self.schema.object_t.c['class']).filter(
                self.schema.object_t.c.id == id_).one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('object.id == %s' % (id_, ))
        cls_id = o[0]

        # ...and then retrieve and ORMap its class (after checking the cache)
        try:
            c = self.python_class(cls_id)
        except kb_exc.NotFound:
            raise kb_exc.NotFound('object.id == %s' % (id_, ))

        # We can now retrieve the actual object
        obj = self.session.query(self.orm.KBObject).filter(
            self.orm.KBObject.id == id_).one()

        return obj

    def objects(self, class_=None, ws=None, recurse=True,
                filter_expr=None):
        '''
        Return an iterator yielding all known :py:class:`orm.KBObject`
        instances from the knowledge base.

        :type  class_: :py:class:`orm.KBObject`
        :param class_: the base class for selecting objects from SQL DB
                       (default: None, meaning :py:class:`orm.KBObject`)

        :type  ws: :py:class:`orm.Workspace`
        :param ws: KB workspace object used to filter KB objects according to
                   the visibility of their class (default: None)

        :type  recurse: bool
        :param recurse: retrieve objects of derived classes (default: True)

        :type  filter_expr: SQLAlchemy expression
        :param filter_expr: an optional SQLAlchemy filter expression for
                            selecting objects to be returned

        :rtype: iterator
        :returns: an iterator yielding Python objects
        '''
        if class_ is None:
            class_ = self.orm.KBObject

        obj_query = self.session.query(class_)
        cls_id_query = self.session.query(self.schema.object_t.c['class'])

        if ws is not None:
            obj_query = self._add_ws_filter(obj_query.join(self.orm.KBClass),
                                            ws)
            cls_id_query = self._add_ws_table_filter(
                cls_id_query.join(self.schema.class_t), ws)

        if not recurse:
            # Limit retrieval to the specified class
            if class_ is self.orm.KBObject:
                raise TypeError('KBObject is an abstract class: cannot '
                                'retrieve direct instances')
            obj_query = obj_query.filter(self.orm.KBObject._class
                                         == class_.__kb_class__.id)
        else:
            # We may need to instantiate the involved Python classes
            # before retrieving objects
            for x in cls_id_query:
                self.python_class(x[0])

        if filter_expr is not None:
            obj_query = obj_query.filter(filter_expr)

        # Just to mask SQLAlchemy query object
        return itertools.imap(lambda x: x, obj_query)

    def user(self, id_):
        '''
        Retrieve the user object with the given identifier.

        :type  id_: string
        :param id_: the identifier of the required user

        :rtype: :py:class:`orm.User`
        :returns: the requested user object

        :raises: :py:exc:`errors.NotFound` if a user with the given
                 ID does not exist in the knowledge base
        '''
        query = self.session.query(self.orm.User).filter(
            self.orm.User.id == id_)

        try:
            user = query.one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('user.id == %s' % (id_, ))

        return user

    def users(self, filter_expr=None):
        '''
        Return a query object yielding all known user objects from the
        knowledge base.

        :type  filter_expr: SQLAlchemy expression
        :param filter_expr: an optional SQLAlchemy filter expression for
                            selecting users to be returned

        :rtype: query object
        :returns: a query object yielding :py:class:`orm.User` instances
        '''
        query = self.session.query(self.orm.User)
        if filter_expr is not None:
            query = query.filter(filter_expr)

    def workspace(self, id_):
        '''
        Retrieve the Workspace object with the given id.

        An exception will be raised if the given id doesn't refer to
        any stored workspace.

        :type  id_: int
        :param id_: the identifier of the required Workspace

        :rtype: :py:class:`orm.Workspace`
        :returns: a workspace object

        :raises: :py:exc:`errors.NotFound` if a workspace with the
                 given ID does not exist in the knowledge base
        '''
        try:
            return self.session.query(self.orm.Workspace).filter(
                self.orm.Workspace.id == id_).one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('workspace.id == %d' % (id_, ))

    def workspaces(self, user=None):
        '''
        Return a query object yielding all the workspace objects.

        :type  user: :py:class:`orm.User`
        :param user: optional user object for filtering returned workspaces

        :rtype: query object
        :returns: a query object yielding :py:class:`orm.Workspace` objects
        '''
        query = self.session.query(self.orm.Workspace)
        if user is not None:
            query = query.filter(self.orm.Workspace.creator == user)
        return query

    # Support 'with' statement
    def __enter__(self):
        return self
    def __exit__(self, _type, _value, _traceback):
        self.close()
        return False

    ###########################################################################
    # Internal functions
    ###########################################################################

    # Add a workspace filter to the given SQLAlchemy query object
    def _add_ws_filter(self, query, ws):
        # FIXME: the following alias should really be inferred by SQLAlchemy
        rootcls_alias = sa_orm.aliased(self.orm.KBRootClass)
        return query.join(rootcls_alias,
                          self.orm.KBClass.root).join(
            self.orm.KBClassVisibility).filter(
                              self.orm.KBClassVisibility.workspace == ws)

    # Add a workspace filter to the given SQLAlchemy query object, but
    # assuming that we are working on tables (thus bypassing the ORM)
    def _add_ws_table_filter(self, query, ws):
        return query.join(self.schema.class_visibility,
                          self.schema.class_t.c.root
                          == self.schema.class_visibility.c.class_root).filter(
            self.schema.class_visibility.c.workspace
            == ws.id)

    # Check whether an access rule is defined for the given class ID
    # on the given workspace
    def _check_class_ws_access(self, cls, ws):
        if ws is None:
            return True

        try:
            self.session.query(
                self.schema.class_visibility).filter(
                and_((self.schema.class_visibility.c.class_root
                      == cls._root_id),
                     (self.schema.class_visibility.c.workspace
                      == ws.id))).one()
        except sa_exc.NoResultFound:
            return False

        return True
        
