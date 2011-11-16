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

import sqlalchemy
import sqlalchemy.orm as sa_orm
import sqlalchemy.engine.base as sa_base
import sqlalchemy.orm.exc as sa_exc
import sqlalchemy.schema as sa_schema

import attributes as kb_attrs
import classes as kb_cls
import errors as kb_exc
import schema as kb_schema

class Session(object):
    '''
    A working session of the knowledge base, which handles SQL DB
    connection and object-relational mapping details.
    '''
    def __init__(self, connstr_or_engine, db_prefix='kb_'):
        '''
        Create a knowledge base session instance.

        @type  connstr_or_engine: SQLAlchemy connection string or engine
        @param connstr_or_engine: used to access the knowledge base SQL DB

        @type  db_prefix: string
        @param db_prefix: prefix used for naming the SQL DB schema objects
                          managed by the KB (tables, constraints...).
        '''
        if isinstance(connstr_or_engine, str):
            self.engine = sqlalchemy.create_engine(connstr_or_engine)
        elif isinstance(sqlalchemy.Engine):
            self.engine = connstr_or_engine
        else:
            raise TypeError('Unsupported type for Session initialization: '
                             % (connstr_or_engine, ))

        self.session = sa_orm.Session(bind=self.engine)

        self._schema = kb_schema.Schema(db_prefix)
        self._orm = kb_cls.Classes(self._schema)

        # Known python classes
        self._python_classes_cache = {}
        self._rebuild_python_classes_cache_after_commit = False

    schema = property(lambda self: self._schema)
    '''
    The SQL DB schema instance bound to the session

    @type: L{schema.Schema}
    '''

    orm = property(lambda self: self._orm)
    '''
    The ORM configuration associated to the session.  All the
    knowledge base classes can be accessed as attributes of this
    property, almost like a dynamic namespace.

    @type: L{classes.Classes}
    '''

    def add(self, obj):
        '''
        Add an object to the knowledge base session, ready for later
        commit.

        @type  obj: one of the classes accessible through the L{orm} property
        @param obj: object to be added
        '''
        if isinstance(obj, self.orm.KBClass):
            # We will need to invalidate the Python classes cache
            self._rebuild_python_classes_cache_after_commit = True

        self.session.add(obj)

    def add_all(self, obj_list):
        '''
        Add a list of objects to the knowledge base session, ready for
        later commit.

        @type  obj: list of instances, whose class must be accessible
               through the L{orm} property
        @param obj: object to be added
        '''
        if any([isinstance(obj, self.orm.KBClass) for obj in obj_list]):
            # We will need to invalidate the Python classes cache
            self._rebuild_python_classes_cache_after_commit = True

        self.session.add_all(obj_list)
    
    def expunge(self, obj):
        '''
        Remove an object from the set handled by the knowledge base
        session.

        @param obj: an object instance (previously added with L{add}() or
        L{add_all}())
        '''
        if isinstance(obj, list):
            for o in obj:
                self.session.expunge(o)
        else:
            self.session.expunge(obj)
    
    def expunge_all(self):
        '''
        Empty the set of objects handled by the knowledge base
        session.
        '''
        self.session.expunge_all()

    def begin_nested(self):
        '''
        Start a nested transaction.

        This method creates a savepoint in case of L{rollback}.
        '''
        self.session.begin_nested()

    def commit(self):
        '''
        Commit the current transaction.

        All the pending objects will be saved on the knowledge base
        SQL DB.
        '''
        # Before committing, ensure that all KBClass-derived objects
        # have an associated table
        new_kb_cls = [a for a in self.session.new
                      if isinstance(a, self.orm.KBClass)]
        for c in new_kb_cls:
            if not c.is_bound():
                # FIXME: really do it automatically?  Or raise an error?
                c.create_table(self.session)
        
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback()
            raise

        if self._rebuild_python_classes_cache_after_commit:
            self._python_classes_cache = {}
            self._rebuild_python_classes_cache_after_commit = False

    def rollback(self):
        '''
        Undo the effects of the current transaction on the knowledge
        base SQL DB.

        If L{begin_nested}() was used, the rollback will stop at the last
        savepoint.
        '''
        self.session.rollback()

    def class_(self, id_, ws=None):
        '''
        Retrieve the KBClass instance with the given id from the
        knowledge base SQL DB.

        An exception will be raised if the given id is not used by any
        stored class.

        @type  id_: string
        @param id_: the identifier of the required KBClass

        @return: a KBClass instance
        '''
        query = self.session.query(self.orm.KBClass).filter(
            self.orm.KBClass.id == id_)
        if ws is not None:
            query = self._add_ws_filter(query, ws)

        try:
            cls = query.one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('class.id == %s' % (id_, ))

        return cls

    def classes(self, ws=None):
        '''
        Return an iterator yielding all known KBClass instances from
        the SQL DB.

        @type  ws: Workspace
        @param ws: KB workspace object used to filter classes (default: None)

        @return: an iterator yielding KBClass instances
        '''
        query = self.session.query(self.orm.KBClass)
        if ws is not None:
            query = self._add_ws_filter(query, ws)
        return query

    def create_table(self, class_):
        '''
        Create the SQL table(s) necessary for storing instances of the
        given KB class.

        The KBClass instance itself will be automatically added to the
        set of objects managed by the Session.

        @type  class_: KBClass
        @param class_: a knowledge base class instance, the tables of which
                       will be created on the DB
        '''
        assert(isinstance(class_, self.orm.KBClass))
        self.add(class_)
        class_.create_table(self.session)

    def python_class(self, id_, ws=None):
        '''
        Retrieve the Python class corresponding to the KBClass object
        with the given identifier.

        The returned class will be ORM-mapped and ready to be used for
        queries and object instantiations.

        An exception will be raised if the given id doesn't refer to
        any stored class.

        @type  id_: string
        @param id_: the identifier of the required KBClass

        @type  ws: Workspace
        @param ws: KB workspace object used to filter classes (default: None)

        @return: a Python class (inheriting from KBObject)
        '''
        # It will cause the Python classes to be instantiated and ORM-mapped
        self.python_classes(ws=ws)
        cls = [x for x in self._python_classes_cache[ws]
               if x.__class_id__ == id_]

        # FIXME: decide how to handle the 'id not found' error
        assert(len(cls) == 1)

        return cls[0]

    def python_classes(self, ws=None):
        '''
        Retrieve a list of the Python classes corresponding to all the
        KBClass objects stored on the SQL DB.

        @type  ws: Workspace
        @param ws: KB workspace object used to filter classes (default: None)

        @return: a list of Python classes (inheriting from KBObject)
        '''
        if not self._python_classes_cache.has_key(ws):
            self._python_classes_cache[ws] = [c.make_python_class(self.session)
                                              for c in self.classes(ws=ws)]
        return self._python_classes_cache[ws]

    def object(self, id_, ws=None):
        '''
        Retrieve the Python object mapped to the KB object with the
        given id.

        An exception will be raised if the given id doesn't refer to
        any stored object.

        @type  ws: Workspace
        @param ws: KB workspace object used to filter KB objects according to
                   the visibility of their class (default: None)

        @type  id_: string
        @param id_: the identifier of the required KBObject

        @return: a Python object
        '''
        # It will cause the Python classes to be instantiated and ORM-mapped
        self.python_classes()

        query = self.session.query(self.orm.KBObject).filter(
            self.orm.KBObject.id == id_)
        if ws is not None:
            query = self._add_ws_filter(query.join(self.orm.KBClass), ws)
            
        try:
            obj = query.one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('object.id == %s' % (id_, ))

        return obj

    def objects(self, class_=None, ws=None, filter_expr=None):
        '''
        Return an iterator yielding all known KBObject instances from
        the SQL DB.

        @type  class_: class.KBObject
        @param class_: the base class for selecting objects from SQL DB
                       (default: None, meaning self.orm.KBObject)

        @type  ws: Workspace
        @param ws: KB workspace object used to filter KB objects according to
                   the visibility of their class (default: None)

        @type  filter_expr: SQLAlchemy expression
        @param filter_expr: an optional SQLAlchemy filter expression for
                            selecting objects to be returned

        @return: an iterator yielding Python objects
        '''
        if class_ is None:
            class_ = self.orm.KBObject

        # It will cause the Python classes to be instantiated and ORM-mapped
        self.python_classes()

        query = self.session.query(class_)

        if ws is not None:
            query = self._add_ws_filter(query.join(self.orm.KBClass), ws)

        if filter_expr is not None:
            query = query.filter(filter_expr)

        return query

    def user(self, id_):
        '''
        Retrieve the User object with the given id.

        An exception will be raised if the given id doesn't refer to
        any stored user.

        @type  id_: string
        @param id_: the identifier of the required User

        @return: an User object
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
        Return an iterator yielding all known KB user objects from the
        SQL DB.

        @type  filter_expr: SQLAlchemy expression
        @param filter_expr: an optional SQLAlchemy filter expression for
                            selecting users to be returned

        @return: an iterator yielding User objects
        '''
        query = self.session.query(self.orm.User)
        if filter_expr is not None:
            query = query.filter(filter_expr)

    def workspace(self, id_):
        '''
        Retrieve the Workspace object with the given id.

        An exception will be raised if the given id doesn't refer to
        any stored workspace.

        @type  id_: string
        @param id_: the identifier of the required Workspace

        @return: a Workspace object
        '''
        try:
            return self.session.query(self.orm.Workspace).filter(
                self.orm.Workspace.id == id_).one()
        except sa_exc.NoResultFound:
            raise kb_exc.NotFound('workspace.id == %d' % (id_, ))

    def workspaces(self, user=None):
        '''
        Return an iterator yielding all the workspaces for the given
        user (when provided).

        @type  user: User
        @param user: optional User object for filtering returned workspaces

        @return: an iterator yielding Workspace objects
        '''
        query = self.session.query(self.orm.Workspace)
        if user is not None:
            query = query.filter(self.orm.Workspace.creator == user)
        return query


    ###########################################################################
    # Internal functions
    ###########################################################################

    # Add a workspace filter to the given SQLAlchemy query object
    def _add_ws_filter(self, query, ws):
        # FIXME: the following alias should really be inferred by SQLAlchemy
        rootcls_alias = sa_orm.aliased(self.orm.KBRootClass)
        return query.join(rootcls_alias,
                          self.orm.KBClass._root).join(
            self.orm.KBClassVisibility).filter(
                              self.orm.KBClassVisibility.workspace == ws)
