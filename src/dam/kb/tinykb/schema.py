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
# SQLAlchemy schema (and helper functions) defining the SQL
# representation of the NotreDAM knowledge base.  Some Table objects
# are just duplicate references to tables actually managed using
# Django models (e.g. user, item, workspace).
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

import sqlalchemy

from sqlalchemy.schema import *
from sqlalchemy.types import *

from sqlalchemy.sql.expression import insert

import access as kb_access

# Workaround for this long-standing MySQL bug:
#
#     http://bugs.mysql.com/bug.php?id=4541
#
# We ensure that the string columns involved in indexes (unique constraints,
# foreign keys, etc) will *not* have a UTF-8 encoding on MySQL.
from sqlalchemy.dialects import mysql
KeyString = String(128).with_variant(mysql.VARCHAR(128, charset='ascii'),
                                     'mysql')

# Admissible values for classes and catalog entries visibility in
# workspaces
access_enum = [kb_access.OWNER, kb_access.READ_ONLY, kb_access.READ_WRITE,
               kb_access.READ_WRITE_OBJECTS]

# Maximum length for a SQL table name
SQL_TABLE_NAME_LEN_MAX = 64

class Schema(object):
    '''
    Container for the SQL DB schema underlying a knowledge base
    working session.

    The schema is "stateless", in the sense that it does not bind
    itself to a specific :py:class:`Session <session.Session>`: all
    the methods interacting with the SQLDB expect to receive an
    explicit SQLAlchemy connection string or engine in order to
    perform their tasks.

    :type  prefix: string
    :param prefix: prefix used for naming the SQL DB schema objects
                   managed by the KB (tables, constraints...).
    '''
    # FIXME: document table names, and expose them as read-only properties
    def __init__(self, prefix='kb_'):
        self._metadata = MetaData()
        self._prefix = prefix

        _init_base_schema(self, self._metadata, self._prefix)

    metadata = property(lambda self: self._metadata)
    '''
    The SQLAlchemy MetaData object bound to the schema

    :type: SQLAlchemy MetaData
    '''

    prefix = property(lambda self: self._prefix)
    '''
    The prefix used for SQL DB schema objects managed by the KB
    (tables, constraints...).

    :type: string
    '''

    def init_db(self, connstr_or_engine):
        '''
        Initialize the KB database.  This function will check whether
        the KB tables still exist on the DB, and won't try to alter
        them.

        :type  connstr_or_engine: SQLAlchemy connection string or engine
        :param connstr_or_engine: used to access the knowledge base SQL DB
        '''
        engine = _get_engine(connstr_or_engine)

        self._metadata.create_all(engine)

        self._init_default_class_attr_types(engine)

        self._init_default_classes(engine)

    def reset_db(self, connstr_or_engine):
        '''
        Re-initialize the KB database.

        :type  connstr_or_engine: SQLAlchemy connection string or engine
        :param connstr_or_engine: used to access the knowledge base SQL DB
        '''
        eng = _get_engine(connstr_or_engine)

        # FIXME: we should load all the tables, including class and attr ones
        self._metadata.drop_all(engine)

        self.init_db(engine)

    def create_object_table(self, table_name, parent_table_name, attrs_ddl,
                            engine):
        '''
        Create a table for storing KB objects

        :type  table_name: string
        :param table_name: name of the new table (must be unique)

        :type  parent_table_name: string
        :param parent_table_name: name of the parent table used for building
                                  foreign key references

        :type  attrs_ddl: list of SQLAlchemy DDL objects
        :param attrs_ddl: describes the fields of the object table

        :type  engine: SQLALchemy engine
        :param engine: used for creating the table on the SQL DB

        :rtype: SQLAlchemy table
        :returns: the new SQLAlchemy table object
        '''
        newtable = self._get_or_build_object_table(table_name,
                                                   parent_table_name,
                                                   attrs_ddl)
        newtable.create(engine)

        return newtable

    def extend_object_table(self, table_name, attrs_ddl, connection):
        '''
        Extend the given table with new columns.

        :type  table_name: string
        :param table_name: table to be extended
        
        :type  attrs_ddl: list of SQLAlchemy DDL objects
        :param attrs_ddl: describes the new fields of the object table
        
        :type  connection: SQLALchemy connection
        :param connection: used for creating the table on the SQL DB
        '''

        from alembic.migration import MigrationContext
        from alembic.operations import Operations

        ctx = MigrationContext.configure(connection)
        op = Operations(ctx)

        # FIXME: streamline the following internal API
        # We are assuming that the table already exists in the metadata
        table = self._get_or_build_object_table(table_name, None, None)
        for a in attrs_ddl:
            if isinstance(a, Column):
                op.add_column(table.name, a)
                table.append_column(a.copy())
            elif isinstance(a, CheckConstraint):
                # FIXME: TODO
                pass
            elif isinstance(a, UniqueConstraint):
                # FIXME: TODO
                pass
            else:
                raise RuntimeError('BUG: unsupported object while adding '
                                   'column: ' + unicode(a))


    def get_object_table(self, table_name, parent_table_name, attrs_ddl):
        # '''
        # Return the table used for storing KB objects, raising an error
        # if the expected table does not exist yet, or does not match
        # the given description.
        #
        # :type  table_name: string
        # :param table_name: name of the table
        #
        # :type  parent_table_name: string
        # :param parent_table_name: name of the parent table, referred to the
        #                           object parent class, and used in foreign
        #                           key references
        #
        # :type  attrs_ddl: list of SQLAlchemy DDL objects
        # :param attrs_ddl: describes the fields of the object table
        #
        # :rtype: SQLAlchemy table
        # :returns: the SQLAlchemy table object
        # '''
        newtable = self._get_or_build_object_table(table_name,
                                                   parent_table_name,
                                                   attrs_ddl)
        return newtable

    def remove_object_attrs(self, table_name, attr_ids,
                            parent_table_name, valid_attrs_ddl, connection):
        '''
        Extend the given table with new columns.

        :type  table_name: string
        :param table_name: table to be extended
        
        :type  attr_ids: list of strings
        :param attr_ids: IDs to be removed

        :type  parent_table_name: string
        :param parent_table_name: name of the parent table, referred to the
                                  object parent class, and used in foreign
                                  key references
        
        :type  valid_attrs_ddl: list of SQLAlchemy DDL objects
        :param valid_attrs_ddl: surviving fields of the object table
        
        :type  connection: SQLALchemy connection
        :param connection: used for interacting with the SQL DB
        
        # :rtype: SQLAlchemy table
        # :returns: an updated SQLAlchemy table object
        '''

        from alembic.migration import MigrationContext
        from alembic.operations import Operations

        ctx = MigrationContext.configure(connection)
        op = Operations(ctx)

        # FIXME: streamline the following internal API
        # We are assuming that the table already exists in the metadata
        table = self._get_or_build_object_table(table_name, None, None)
        
        for col_id in attr_ids:
            op.drop_column(table.name, col_id)
            # FIXME: here we should update the metadata table as well!
            # However, there does not seem to be a standard API to do it...
        
        self._metadata.remove(table)
        newtable = self._get_or_build_object_table(table.name,
                                                   parent_table_name,
                                                   valid_attrs_ddl)
        return newtable

    def create_attr_tables(self, add_tables, engine):
        # '''
        # Create additional tables for storing KB object attributes
        # (e.g. multivalued ones).
        #
        # :type  add_tables: list of functions of type ``f(MetaData, **kwargs)``
        # :param add_tables: list of table DDL constructor functions
        #
        # :rtype: list of SQLAlchemy tables
        # :returns: the list of new SQLAlchemy table objects
        # '''
        newtables = self._build_attr_tables(add_tables)

        for t in newtables:
            t.create(engine)

        return newtables

    def get_attr_tables(self, add_tables):
        # '''
        # Retrieve the additional tables used for storing KB object
        # attributes (e.g. multivalued ones).
        #
        # :type  add_tables: list of functions of type ``f(MetaData, **kwargs)``
        # :param add_tables: list of table DDL constructor functions
        #
        # :rtype: list of SQLAlchemy tables
        # :returns: the list of new SQLAlchemy table objects
        # ''' 
        newtables = self._build_attr_tables(add_tables)
        return newtables

    def create_tables(self, connstr_or_engine, tables):
        '''
        Create a SQLAlchemy table on the DB, using the given connection
        string or engine

        :type  connstr_or_engine: SQLAlchemy connection string or engine
        :param connstr_or_engine: used to access the knowledge base SQL DB

        :type  tables: list of SQLAlchemy table objects
        :param tables: tables to create
        '''
        engine = _get_engine(connstr_or_engine)
        self._metadata.create_all(bind=engine, tables=tables)

    ###########################################################################
    # Internal functions
    ###########################################################################

    def _get_or_build_object_table(self, table_name, parent_table, attrs_ddl):
        # FIXME: this function should be split!
        for t in self._metadata.sorted_tables:
            if table_name == t.name:
                # The table already exists in the metadata
                return t

        return Table(table_name, self._metadata,
                     Column('id', KeyString,
                            ForeignKey('%s.id' % (parent_table, ),
                                       onupdate='CASCADE',
                                       ondelete='CASCADE'),
                            primary_key=True),
                     *attrs_ddl)

    def _build_attr_tables(self, add_tables):
        '''
        Create additional table(s) for class attribute storage.  The list
        must contain constructors expecting to be called with a mandatory
        argument (a SQLAlchemy MetaData object) followed by optional
        **kwargs.
        '''
        newtables = []

        for t in add_tables:
            newtables.append(t(self._metadata))

        return newtables

    # Default class attribute types
    def _init_default_class_attr_types(self, engine):
        default_attr_types = [
            {'name'  : 'bool',
             'notes' : 'Boolean value'},
            {'name'  : 'int',
             'notes' : 'Integer value (may be negative)'},
            {'name'  : 'real',
             'notes' : 'Real value (base 10)'},
            {'name'  : 'string',
             'notes' : 'Character string'},
            {'name'  : 'date',
             'notes' : 'ISO 8601 date'}, # FIXME: what about time and datetime?
            {'name'  : 'uri',
             'notes' : 'Uniform Resource Identifier'},
            {'name'  : 'choice',
             'notes' : 'Selection among multiple values'},
            {'name'  : 'objref',
             'notes' : 'Typed object reference'},
            {'name'  : 'date-like-string',
             'notes' : 'Date-like string'}
            ]

        # Insert attribute types, avoiding duplications
        for a in default_attr_types:
            cnt = engine.execute(self.attribute_type.count(
                    self.attribute_type.c.name == a['name'])).first()[0]
            assert((cnt == 0) or (cnt == 1))
            if cnt == 0:
                engine.execute(self.attribute_type.insert(), [a])

    def _init_default_classes(self, engine):
        default_classes = [
            # Keyword: this will be a default class if (when) the KB
            # will be fully implemented
            # {'id'          : 'keyword',
            #  'root'        : 'keyword',
            #  'parent'      : 'keyword',
            #  'parent_root' : 'keyword',
            #  'name'        : 'Keyword',
            #  'table'       : self.object_keyword.name,
            #  'notes'       : 'Simple keyword without attributes',
            #  'is_root'     : True}
            ]

        if len(default_classes) > 0: # Just to shut up SQLAlchemy warnings
            engine.execute(self.class_t.insert(), default_classes)


###############################################################################
# Utility functions
###############################################################################
def _get_engine(connstr_or_engine):
    '''
    Take either a SQLAlchemy engine or a connection string, and return
    a SQLAlchemy engine (possibly creating it).
    '''
    if isinstance(connstr_or_engine, str):
        engine = sqlalchemy.create_engine(connstr_or_engine)
    else:
        engine = connstr_or_engine

    return engine


###############################################################################
# SQL schema definition
###############################################################################
def _init_base_schema(o, metadata, prefix):
    '''
    Create the base knowledge base SQL schema, by attaching the new
    tables as attributes of the given Python object "o".  "metadata"
    will contain the new tables, and "prefix" will be used for
    creating the names of tables, constraints and other SQL DB objects
    '''
    _p = prefix # Just a shorthand

    # Let's make this information accessible
    o.SQL_TABLE_NAME_LEN_MAX = SQL_TABLE_NAME_LEN_MAX

    # DAM user (managed by Django)
    o.user = Table('auth_user', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('username', String(30), nullable=False)
                   )

    # DAM item (managed by Django)
    o.item = Table('item', metadata,
                   Column('id', Integer, primary_key=True),
                   # FIXME: possibly consider other fields here
                   )

    # DAM workspaces (managed by Django, which also causes the funny name)
    o.workspace = Table('dam_workspace_workspace', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('name', String(512), nullable=False),
                        Column('creator_id',
                               ForeignKey('auth_user.id',
                                          onupdate='CASCADE',
                                          ondelete='RESTRICT'),
                               nullable=False),
                        )

    # Item visibility in different workspaces
    # FIXME: unused: maybe some day it will replace NotreDAM/Django machinery
    # o.item_visibility = Table(_p+'workspace_damworkspace_items', metadata,
    #                           Column('id', Integer, primary_key=True),
    #                           # FIXME: the actual field references the
    #                           # "abstract" table workspace_damworkspace
    #                           Column('damworkspace_id',
    #                                  ForeignKey('dam_workspace_workspace.id',
    #                                             onupdate='CASCADE',
    #                                             ondelete='CASCADE')),
    #                           Column('item_id',
    #                                  ForeignKey('item.id',
    #                                             onupdate='CASCADE',
    #                                             ondelete='CASCADE')),
    #                           Column('access',
    #                                  Enum(*access_enum,
    #                                        name=_p+'workspace_damworkspace_items_access_enum'),
    #                                  nullable=False),

    #                           # Actual primary key (the 'id' field is
    #                           # redundant, and only required by Django
    #                           # model)
    #                           UniqueConstraint('damworkspace_id', 'item_id',
    #                                            name=_p+'workspace_items_actual_pkey_constr')
    #                           )

    # User-defined class for real-world objects
    o.class_t = Table(_p+'class', metadata,
                      Column('id', KeyString, primary_key=True),
                      Column('root', ForeignKey(_p+'class.id',
                                                onupdate='CASCADE',
                                                ondelete='CASCADE'),
                             nullable=False),
                      Column('parent', KeyString, nullable=False),
                      Column('parent_root', KeyString, nullable=False),
                      Column('name', String(512), nullable=False),
                      Column('table', KeyString, unique=True, nullable=False),
                      Column('notes', String(4096)),

                      # Redundant column which simplifies SQLAlchemy
                      # inheritance mapping
                      Column('is_root', Boolean, nullable=False),
                      # is_root <=> (root = id)
                      CheckConstraint('(NOT (root = id) OR is_root)'
                                      ' AND (NOT is_root OR (root = id))',
                                      name=_p+'catalog_is_root_value_constr'),

                      # Redundant constraint needed for foreign key references
                      UniqueConstraint('id', 'root',
                                       name=_p+'class_unique_id_root_constr'),

                      # Ensure that a class and its parent share the
                      # same root node
                      ForeignKeyConstraint(['parent', 'parent_root'],
                                           [_p+'class.id', _p+'class.root'],
                                           onupdate='CASCADE',
                                           ondelete='RESTRICT'),

                      # Ensure that a root class does not have a parent,
                      # and vice versa:   (root = id) <=> (parent = id)
                      CheckConstraint('((NOT (root = id)) OR (parent = id))'
                                      ' AND ((NOT (parent = id)) OR (root = id))',
                                      name=_p+'class_root_iff_no_parent_constr')
                      )

    # Class visibility in workspaces
    o.class_visibility = Table(_p+'class_visibility', metadata,
                               Column('workspace',
                                      ForeignKey('dam_workspace_workspace.id',
                                                 onupdate='CASCADE',
                                                 ondelete='CASCADE'),
                                      primary_key=True),
                               Column('class', KeyString, primary_key=True),
                               Column('class_root', KeyString),
                               Column('access',
                                      Enum(*access_enum,
                                            name=_p+'class_visibility_access_enum'),
                                      nullable=False),

                               # Redundant constraint needed for foreign
                               # key references
                               UniqueConstraint('workspace', 'class_root',
                                                name=_p+'class_visibility_unique_class_root_ws_constr'),

                               ForeignKeyConstraint(['class',
                                                     'class_root'],
                                                    [_p+'class.id',
                                                     _p+'class.root'],
                                                    onupdate='CASCADE',
                                                    ondelete='RESTRICT'),


                               # Ensure that we only give visibility to
                               # root classes
                               CheckConstraint('class = class_root',
                                               name=_p+'class_visibility_parent_root_constr')
                               )

    # Known attribute types
    o.attribute_type = Table(_p+'attribute_type', metadata,
                             Column('name', KeyString, primary_key=True),
                             Column('notes', String(4096))
                             )

    # Generic class attributes
    o.class_attribute = Table(_p+'class_attribute', metadata,
                              Column('class', KeyString, nullable=False,
                                     primary_key=True),
                              Column('class_root', KeyString, nullable=False,
                                     primary_key=True),
                              Column('id', KeyString, nullable=False,
                                     primary_key=True),
                              Column('name', String(512), nullable=False),
                              Column('type',
                                     ForeignKey(_p+'attribute_type.name',
                                                onupdate='CASCADE',
                                                ondelete='RESTRICT'),
                                     nullable=False),
                              Column('order', Integer, default=0, nullable=False),
                              Column('maybe_empty', Boolean, nullable=False),
                              Column('multivalue_table', KeyString,
                                     default=None, unique=True, nullable=True),
                              Column('notes', String(4096)),

                              ForeignKeyConstraint(['class', 'class_root'],
                                                   [_p+'class.id', _p+'class.root'],
                                                   onupdate='CASCADE',
                                                   ondelete='CASCADE')
                              )

    ###########################################################################
    # Type-specific class attribute tables
    ###########################################################################
    o.class_attribute_bool = Table(_p+'class_attribute_bool', metadata,
                                   Column('class', KeyString, nullable=False,
                                          primary_key=True),
                                   Column('class_root', KeyString,
                                          nullable=False,
                                          primary_key=True),
                                   Column('id', KeyString, nullable=False,
                                          primary_key=True),
                                   Column('default', Boolean),

                                   ForeignKeyConstraint(['class', 'class_root',
                                                         'id'],
                                                        [_p+'class_attribute.class',
                                                         _p+'class_attribute.class_root',
                                                         _p+'class_attribute.id'],
                                                        onupdate='CASCADE',
                                                        ondelete='CASCADE'),
                                   )


    o.class_attribute_int = Table(_p+'class_attribute_int', metadata,
                                  Column('class', KeyString, nullable=False,
                                         primary_key=True),
                                  Column('class_root', KeyString, nullable=False,
                                         primary_key=True),
                                  Column('id', KeyString, nullable=False,
                                         primary_key=True),
                                  Column('min', Integer, default=None),
                                  Column('max', Integer, default=None),
                                  Column('default', Integer),

                                  ForeignKeyConstraint(['class', 'class_root',
                                                        'id'],
                                                       [_p+'class_attribute.class',
                                                        _p+'class_attribute.class_root',
                                                        _p+'class_attribute.id'],
                                                       onupdate='CASCADE',
                                                       ondelete='CASCADE'),
                                  CheckConstraint('"min" IS NULL '
                                                  'OR ("default" >= "min")',
                                                  name=_p+'class_attr_int_min_constr'),
                                  CheckConstraint('"max" IS NULL '
                                                  'OR ("default" <= "max")',
                                                  name=_p+'class_attr_int_max_constr')
                                  )

    o.class_attribute_real = Table(_p+'class_attribute_real', metadata,
                                   Column('class', KeyString, nullable=False,
                                          primary_key=True),
                                   Column('class_root', KeyString,
                                          nullable=False, primary_key=True),
                                   Column('id', KeyString, nullable=False,
                                          primary_key=True),
                                   Column('precision', Integer, default=10),
                                   # FIXME: hardcoded Numeric precisions
                                   Column('min', Numeric(precision=64),
                                          default=None),
                                   Column('max', Numeric(precision=64),
                                          default=None),
                                   Column('default', Numeric(precision=64)),

                                   ForeignKeyConstraint(['class', 'class_root',
                                                         'id'],
                                                        [_p+'class_attribute.class',
                                                         _p+'class_attribute.class_root',
                                                         _p+'class_attribute.id'],
                                                        onupdate='CASCADE',
                                                        ondelete='CASCADE'),

                                   CheckConstraint('"precision" >= 0',
                                                   name=_p+'class_attr_real_precision_gt0_constr'),
                                   CheckConstraint('"min" IS NULL '
                                                   'OR ("default" >= "min")',
                                                   name=_p+'class_attr_real_min_constr'),
                                   CheckConstraint('"max" IS NULL '
                                                   'OR ("default" <= "max")',
                                                   name=_p+'class_attr_real_max_constr')
                                   )

    o.class_attribute_string = Table(_p+'class_attribute_string', metadata,
                                     Column('class', KeyString, nullable=False,
                                            primary_key=True),
                                     Column('class_root', KeyString,
                                            nullable=False, primary_key=True),
                                     Column('id', KeyString, nullable=False,
                                            primary_key=True),
                                     Column('length', Integer, default=128),
                                     # FIXME: hardcoded default value size
                                     Column('default', String(4096)),

                                     ForeignKeyConstraint(['class', 'class_root',
                                                           'id'],
                                                          [_p+'class_attribute.class',
                                                           _p+'class_attribute.class_root',
                                                           _p+'class_attribute.id'],
                                                          onupdate='CASCADE',
                                                          ondelete='CASCADE'),

                                     CheckConstraint('length >= 0',
                                                     name=_p+'class_attr_string_length_gt0_constr')
                                     )

    o.class_attribute_date = Table(_p+'class_attribute_date', metadata,
                                   Column('class', KeyString, nullable=False,
                                          primary_key=True),
                                   Column('class_root', KeyString,
                                          nullable=False, primary_key=True),
                                   Column('id', KeyString, nullable=False,
                                          primary_key=True),
                                   Column('min', Date, default=None),
                                   Column('max', Date, default=None),
                                   Column('default', Date),

                                   ForeignKeyConstraint(['class', 'class_root',
                                                         'id'],
                                                        [_p+'class_attribute.class',
                                                         _p+'class_attribute.class_root',
                                                         _p+'class_attribute.id'],
                                                        onupdate='CASCADE',
                                                        ondelete='CASCADE'),

                                   CheckConstraint('"min" IS NULL '
                                                   'OR ("default" >= "min")',
                                                   name=_p+'class_attr_date_min_constr'),
                                   CheckConstraint('"max" IS NULL '
                                                   'OR ("default" <= "max")',
                                                   name=_p+'class_attr_date_max_constr')
                                   )

    o.class_attribute_uri = Table(_p+'class_attribute_uri', metadata,
                                  Column('class', KeyString, nullable=False,
                                         primary_key=True),
                                  Column('class_root', KeyString, nullable=False,
                                         primary_key=True),
                                  Column('id', KeyString, nullable=False,
                                         primary_key=True),
                                  Column('length', Integer, default=128),
                                  # FIXME: hardcoded default value size
                                  Column('default', String(4096)),

                                  ForeignKeyConstraint(['class', 'class_root',
                                                        'id'],
                                                       [_p+'class_attribute.class',
                                                        _p+'class_attribute.class_root',
                                                        _p+'class_attribute.id'],
                                                       onupdate='CASCADE',
                                                       ondelete='CASCADE'),

                                  CheckConstraint('length >= 0',
                                                  name=_p+'class_attr_uri_length_gt0_constr')
                                  )

    o.class_attribute_choice = Table(_p+'class_attribute_choice', metadata,
                                     Column('class', KeyString, nullable=False,
                                            primary_key=True),
                                     Column('class_root', KeyString,
                                            nullable=False, primary_key=True),
                                     Column('id', KeyString, nullable=False,
                                            primary_key=True),
                                     # FIXME: hardcoded string lengths
                                     # "choices" holds a JSON list of strings
                                     Column('choices', String(8192),
                                            nullable=False),
                                     Column('default', KeyString),

                                     ForeignKeyConstraint(['class', 'class_root',
                                                           'id'],
                                                          [_p+'class_attribute.class',
                                                           _p+'class_attribute.class_root',
                                                           _p+'class_attribute.id'],
                                                          onupdate='CASCADE',
                                                          ondelete='CASCADE'),

                                     # Very simple check to ensure that the
                                     # default choice is somehow contained
                                     # in the JSON list of strings
                                     CheckConstraint("choices LIKE '%\"' || \"default\" || '\"%'",
                                                     name=_p+'class_attr_string_length_gt0_constr')
                                     )

    o.class_attribute_objref = Table(_p+'class_attribute_objref', metadata,
                                     Column('class', KeyString, nullable=False,
                                            primary_key=True),
                                     Column('class_root', KeyString,
                                            nullable=False, primary_key=True),
                                     Column('id', KeyString, nullable=False,
                                            primary_key=True),
                                     Column('target_class', KeyString,
                                            nullable=False),
                                     Column('target_class_root', KeyString,
                                            nullable=False),

                                     ForeignKeyConstraint(['class', 'class_root',
                                                           'id'],
                                                          [_p+'class_attribute.class',
                                                           _p+'class_attribute.class_root',
                                                           _p+'class_attribute.id'],
                                                          onupdate='CASCADE',
                                                          ondelete='CASCADE'),

                                     ForeignKeyConstraint(['target_class',
                                                           'target_class_root'],
                                                          [_p+'class.id',
                                                           _p+'class.root'],
                                                          onupdate='CASCADE',
                                                          ondelete='RESTRICT')
                                     )

    # Objects registry
    o.object_t = Table(_p+'object', metadata,
                       Column('id', KeyString, primary_key=True),
                       Column('class', KeyString, nullable=False),
                       Column('class_root', KeyString, nullable=False),
                       Column('name', String(512), nullable=False),
                       Column('notes', String(4096)),

                       # Redundant constraint needed for foreign key references
                       UniqueConstraint('id', 'class',
                                        name=_p+'class_unique_id_class_constr'),

                       # Redundant constraint needed for foreign key references
                       UniqueConstraint('id', 'class_root',
                                        name=_p+'class_unique_id_class_root_constr'),

                       ForeignKeyConstraint(['class', 'class_root'],
                                            [_p+'class.id', _p+'class.root'],
                                            onupdate='CASCADE',
                                            ondelete='RESTRICT')
                       )

    # An entry in the catalog
    # FIXME: unused: maybe some day it will replace NotreDAM/Django machinery
    # o.catalog_entry = Table(_p+'catalog_entry', metadata,
    #                         Column('id', KeyString, primary_key=True),
    #                         Column('root', ForeignKey(_p+'catalog_entry.id',
    #                                                   onupdate='CASCADE',
    #                                                   ondelete='CASCADE'),
    #                                nullable=False),
    #                         Column('parent', KeyString, nullable=False),
    #                         Column('parent_root', KeyString, nullable=False),
    #                         Column('object', KeyString, nullable=False),
    #                         Column('object_class_root', KeyString, nullable=False),
    #
    #                         # Redundant column which simplifies SQLAlchemy
    #                         # inheritance mapping
    #                         Column('is_root', Boolean, nullable=False),
    #                         # is_root <=> (root = id)
    #                         CheckConstraint('(NOT (root = id) OR is_root)'
    #                                         ' AND (NOT is_root OR (root = id))',
    #                                         name=_p+'catalog_is_root_value_constr'),

    #                         # Redundant constraint needed for foreign
    #                         # key references
    #                         UniqueConstraint('id', 'root',
    #                                          name=_p+'catalog_unique_id_root_constr'),

    #                         # Redundant constraint needed for foreign
    #                         # key references
    #                         UniqueConstraint('id', 'root', 'object_class_root',
    #                                          name=_p+'catalog_unique_id_root_obj_root_constr'),

    #                         # Redundant constraint needed for foreign
    #                         # key references
    #                         UniqueConstraint('id', 'object', 'object_class_root',
    #                                          name=_p+'catalog_unique_id_obj_class_constr'),

    #                         # External reference to typing object (and its
    #                         # root class)
    #                         ForeignKeyConstraint(['object', 'object_class_root'],
    #                                              [_p+'object.id',
    #                                               _p+'object.class_root'],
    #                                              onupdate='CASCADE',
    #                                              ondelete='RESTRICT'),
    #
    #                         # Ensure that a catalog entry and its parent
    #                         # share the same root node
    #                         ForeignKeyConstraint(['parent', 'parent_root'],
    #                                              [_p+'catalog_entry.id',
    #                                               _p+'catalog_entry.root'],
    #                                              onupdate='CASCADE',
    #                                              ondelete='CASCADE'),
    #
    #                         # Ensure that a root class does not have a parent,
    #                         # and vice versa:   (root = id) <=> (parent = id)
    #                         CheckConstraint('((NOT (root = id))'
    #                                         ' OR (parent = id))'
    #                                         'AND ((NOT (parent = id))'
    #                                         '     OR (root = id))',
    #                                         name=_p+'catalog_root_iff_no_parent_constr')
    #                         )

    # Class visibility in workspaces
    # FIXME: unused: maybe some day it will replace NotreDAM/Django machinery
    # o.catalog_tree_visibility = Table(_p+'catalog_tree_visibility', metadata,
    #                                   Column('workspace',
    #                                          ForeignKey('dam_workspace_workspace.id',
    #                                                     onupdate='CASCADE',
    #                                                     ondelete='CASCADE'),
    #                                          primary_key=True,
    #                                          nullable=False),
    #                                   Column('catalog_entry', KeyString,
    #                                          primary_key=True,
    #                                          nullable=False),
    #                                   Column('catalog_entry_root', KeyString,
    #                                          nullable=False),
    #                                   Column('catalog_entry_object_class_root',
    #                                          KeyString, nullable=False),
    #                                   Column('access',
    #                                          Enum(*access_enum,
    #                                                name=_p+'class_visibility_access_enum'),
    #                                          nullable=False),
    #
    #                                   # Redundant constraint needed for foreign
    #                                   # key references
    #                                   UniqueConstraint('catalog_entry_root',
    #                                                    'workspace',
    #                                                    name=_p+'catalog_tree_visibility_unique_catalog_root_ws_constr'),
    #
    #                                   ForeignKeyConstraint(['catalog_entry',
    #                                                         'catalog_entry_root',
    #                                                         'catalog_entry_object_class_root'],
    #                                                        [_p+'catalog_entry.id',
    #                                                         _p+'catalog_entry.root',
    #                                                         _p+'catalog_entry.object_class_root'],
    #                                                        onupdate='CASCADE',
    #                                                        ondelete='CASCADE'),
    #
    #                                   # Ensure that the catalog entry class
    #                                   # is actually visible on the target
    #                                   # workspace (NOTE: it does not forbid
    #                                   # child catalog entries to be
    #                                   # associated with non-visible
    #                                   # classes)
    #                                   ForeignKeyConstraint(['workspace',
    #                                                         'catalog_entry_object_class_root'],
    #                                                        [_p+'class_visibility.workspace',
    #                                                         _p+'class_visibility.class_root'],
    #                                                        onupdate='CASCADE',
    #                                                        ondelete='CASCADE'),
    #
    #                                   # Ensure that we only give visibility to
    #                                   # root catalog entries
    #                                   CheckConstraint('catalog_entry'
    #                                                   ' = catalog_entry_root',
    #                                                   name=_p+'catalog_parent_root_constr')
    #                                   )

    # Cataloging information.  Only associate items and catalog entries when:
    #
    #    1. both the item and the catalog entry are visibile in the same
    #       workspace;
    #
    #    2. both the item and the catalog entry class are visibile in the
    #       same workspace.
    # FIXME: unused: maybe some day it will replace NotreDAM/Django machinery
    # o.cataloging = Table(_p+'cataloging', metadata,
    #                      Column('item', Integer,
    #                             primary_key=True),
    #                      Column('workspace', Integer,
    #                             primary_key=True),
    #                      Column('catalog_entry', KeyString,
    #                             primary_key=True),
    #                      Column('catalog_entry_root', KeyString),
    #                      Column('catalog_entry_object', KeyString,
    #                             primary_key=True),
    #                      Column('catalog_entry_object_class_root', KeyString),

    #                      ForeignKeyConstraint(['item', 'workspace'],
    #                                           [_p+'workspace_damworkspace_items.item_id',
    #                                            _p+'workspace_damworkspace_items.damworkspace_id'],
    #                                           onupdate='CASCADE',
    #                                           ondelete='CASCADE'),

    #                      ForeignKeyConstraint(['catalog_entry_root',
    #                                            'workspace'],
    #                                           [_p+'catalog_tree_visibility.catalog_entry_root',
    #                                            _p+'catalog_tree_visibility.workspace'],
    #                                           onupdate='CASCADE',
    #                                           ondelete='CASCADE'),

    #                      ForeignKeyConstraint(['catalog_entry',
    #                                            'catalog_entry_object',
    #                                            'catalog_entry_object_class_root'],
    #                                           [_p+'catalog_entry.id',
    #                                            _p+'catalog_entry.object',
    #                                            _p+'catalog_entry.object_class_root'],
    #                                           onupdate='CASCADE',
    #                                           ondelete='CASCADE'),

    #                      ForeignKeyConstraint(['workspace',
    #                                            'catalog_entry_object_class_root'],
    #                                           [_p+'class_visibility.workspace',
    #                                            _p+'class_visibility.class_root'],
    #                                           onupdate='CASCADE',
    #                                           ondelete='RESTRICT')
    #                      )

    ###########################################################################
    # Predefined object classes
    ###########################################################################
    # These tables represent two base classes, and they are designed
    # according to these rules:
    #
    #    1. each table SHALL have a primary key which is also a reference
    #       to object(id)
    #
    #    2. IF a table represents a derived class, then it SHALL ALSO
    #       feature a ForeignKey constraint pointing to the (id,
    #       class_root) fields of the table representing the previous
    #       class in the inheritance hierarchy.
    #
    # For example, lets' say that we have the following class hierarchy:
    #
    #      Building  ->  Church  ->  Cathedral
    #
    # Then:
    #
    #    * 'Building' SHALL reference to the 'object' table (point 1);
    #
    #    * 'Church' SHALL ALSO reference to 'Building' (point 2);
    #
    #    * 'Cathedral' SHALL ALSO reference to 'Church' (point 2);
    #
    #    * When a record is added to 'Cathedral', then:
    #
    #          - object.id = Building.id = Church.id = Cathedral.id

    # Example: simple keyword (without attributes)
    # This will be a default class if (when) the KB will be fully implemented
    # o.object_keyword = Table(_p+'object_keyword', metadata,
    #                          Column('id', ForeignKey(_p+'object.id'),
    #                                 primary_key=True)
    #                          )
