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

# Ammissible values for classes and catalog entries visibility in
# workspaces
access_enum = ['owner', 'read-only', 'read-write']

metadata = MetaData()

## Django's user table placeholder
user = Table('auth_user', metadata,
             Column('id', Integer, primary_key=True),
             Column('username', String(30), nullable=False)
             )

## DAM item
item = Table('item', metadata,
             Column('id', Integer, primary_key=True),
             ## FIXME: possibly consider other fields here
             )

## Workspaces (the table funny name is due to Django model conventions)
workspace = Table('dam_workspace_workspace', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('name', String(512), nullable=False),
                  Column('creator',
                         ForeignKey('auth_user.id',
                                    onupdate='CASCADE',
                                    ondelete='RESTRICT'),
                         nullable=False),
                  )

## Item visibility in different workspaces
item_visibility = Table('workspace_damworkspace_items', metadata,
                        Column('id', Integer, primary_key=True),
                        ## FIXME: the actual field references the
                        ## "abstract" table workspace_damworkspace
                        Column('damworkspace_id',
                               ForeignKey('dam_workspace_workspace.id',
                                          onupdate='CASCADE',
                                          ondelete='RESTRICT')),
                        Column('item_id',
                               ForeignKey('item.id',
                                          onupdate='CASCADE',
                                          ondelete='RESTRICT')),
                        Column('access',
                               Enum(*access_enum,
                                    name='workspace_damworkspace_items_access_enum'),
                               nullable=False),

                        ## Actual primary key (the 'id' field is
                        ## redundant, and only required by Django
                        ## model)
                        UniqueConstraint('damworkspace_id', 'item_id',
                                         name='workspace_items_actual_pkey_constr')
                        )

## User-defined class for real-world objects
class_t = Table('class', metadata,
                Column('id', String(128), primary_key=True),
                Column('root', ForeignKey('class.id',
                                          onupdate='CASCADE',
                                          ondelete='RESTRICT'),
                       nullable=False),
                Column('parent', String(128), nullable=False),
                Column('parent_root', String(128), nullable=False),
                Column('name', String(64), nullable=False),
                Column('table', String(128), unique=True, nullable=False),
                Column('notes', String(4096)),
                
                ## Redundant column which simplifies SQLAlchemy
                ## inheritance mapping
                Column('is_root', Boolean, nullable=False),
                ## is_root <=> (root = id)
                CheckConstraint('(NOT (root = id) OR is_root)'
                                ' AND (NOT is_root OR (root = id))',
                                name='catalog_is_root_value_constr'),
                
                ## Redundant constraint needed for foreign key references
                UniqueConstraint('id', 'root',
                                 name='class_unique_id_root_constr'),

                ## Ensure that a class and its parent share the same root node
                ForeignKeyConstraint(['parent', 'parent_root'],
                                     ['class.id', 'class.root'],
                                     onupdate='CASCADE',
                                     ondelete='RESTRICT'),

                ## Ensure that a root class does not have a parent,
                ## and vice versa:   (root = id) <=> (parent = id)
                CheckConstraint('((NOT (root = id)) OR (parent = id))'
                                ' AND ((NOT (parent = id)) OR (root = id))',
                                name='class_root_iff_no_parent_constr')
                )

## Class visibility in workspaces
class_visibility = Table('class_visibility', metadata,
                         Column('workspace',
                                ForeignKey('dam_workspace_workspace.id',
                                           onupdate='CASCADE',
                                           ondelete='RESTRICT'),
                                primary_key=True),
                         Column('class', String(128), primary_key=True),
                         Column('class_root', String(128)),
                         Column('access',
                                Enum(*access_enum,
                                      name='class_visibility_access_enum'),
                                nullable=False),
                         
                         ## Redundant constraint needed for foreign
                         ## key references
                         UniqueConstraint('workspace', 'class_root',
                                          name='class_visibility_unique_class_root_ws_constr'),

                         ForeignKeyConstraint(['class',
                                               'class_root'],
                                              ['class.id',
                                               'class.root'],
                                              onupdate='CASCADE',
                                              ondelete='RESTRICT'),


                         ## Ensure that we only give visibility to
                         ## root classes
                         CheckConstraint('class = class_root',
                                         name='class_visibility_parent_root_constr')
                         )

## Known attribute types
attribute_type = Table('attribute_type', metadata,
                       Column('name', String(128), primary_key=True),
                       Column('notes', String(4096))
                       )

## Generic class attributes
class_attribute = Table('class_attribute', metadata,
                        Column('class', String(128), nullable=False,
                               primary_key=True),
                        Column('class_root', String(128), nullable=False,
                               primary_key=True),
                        Column('id', String(128), nullable=False,
                               primary_key=True),
                        Column('name', String(128), nullable=False),
                        Column('type',
                               ForeignKey('attribute_type.name',
                                          onupdate='CASCADE',
                                          ondelete='RESTRICT'),
                               nullable=False),
                        Column('maybe_empty', Boolean, nullable=False),
                        Column('notes', String(4096)),

                        ForeignKeyConstraint(['class', 'class_root'],
                                             ['class.id', 'class.root'],
                                             onupdate='CASCADE',
                                             ondelete='RESTRICT'),

                        # An attribute name cannot appear twice
                        # whithin a class hierarchy
                        # FIXME: sibling classes w/ unrelated same-named attrs?
                        UniqueConstraint('class_root', 'name',
                                         name='class_attr_unique_root_id_constr')
                        )

###############################################################################
## Type-specific class attribute tables
###############################################################################
class_attribute_bool = Table('class_attribute_bool', metadata,
                             Column('class', String(128), nullable=False,
                                    primary_key=True),
                             Column('class_root', String(128), nullable=False,
                                    primary_key=True),
                             Column('id', String(128), nullable=False,
                                    primary_key=True),
                             Column('default', Boolean),

                             ForeignKeyConstraint(['class', 'class_root',
                                                   'id'],
                                                  ['class_attribute.class',
                                                   'class_attribute.class_root',
                                                   'class_attribute.id'],
                                                  onupdate='CASCADE',
                                                  ondelete='RESTRICT'),

                             # An attribute name cannot appear twice
                             # whithin a class hierarchy
                             UniqueConstraint('class_root', 'id',
                                              name='class_attr_bool_unique_root_id_constr')
                             )


class_attribute_int = Table('class_attribute_int', metadata,
                            Column('class', String(128), nullable=False,
                                   primary_key=True),
                            Column('class_root', String(128), nullable=False,
                                   primary_key=True),
                            Column('id', String(128), nullable=False,
                                   primary_key=True),
                            Column('min', Integer, default=None),
                            Column('max', Integer, default=None),
                            Column('default', Integer),
                            
                            ForeignKeyConstraint(['class', 'class_root',
                                                  'id'],
                                                 ['class_attribute.class',
                                                  'class_attribute.class_root',
                                                  'class_attribute.id'],
                                                 onupdate='CASCADE',
                                                 ondelete='RESTRICT'),
                            CheckConstraint('"min" IS NULL OR ("default" >= "min")',
                                            name='class_attr_int_min_constr'),
                            CheckConstraint('"max" IS NULL OR ("default" <= "max")',
                                            name='class_attr_int_max_constr'),

                            # An attribute name cannot appear twice
                            # whithin a class hierarchy
                            UniqueConstraint('class_root', 'id',
                                             name='class_attr_int_unique_root_id_constr')
                            )


class_attribute_real = Table('class_attribute_real', metadata,
                             Column('class', String(128), nullable=False,
                                    primary_key=True),
                             Column('class_root', String(128), nullable=False,
                                    primary_key=True),
                             Column('id', String(128), nullable=False,
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
                                                  ['class_attribute.class',
                                                   'class_attribute.class_root',
                                                   'class_attribute.id'],
                                                  onupdate='CASCADE',
                                                  ondelete='RESTRICT'),
                             CheckConstraint('precision >= 0',
                                             name='class_attr_real_precision_gt0_constr'),
                             CheckConstraint('"min" IS NULL OR ("default" >= "min")',
                                             name='class_attr_real_min_constr'),
                             CheckConstraint('"max" IS NULL OR ("default" <= "max")',
                                             name='class_attr_real_max_constr'),

                             
                             # An attribute name cannot appear twice
                             # whithin a class hierarchy
                             UniqueConstraint('class_root', 'id',
                                              name='class_attr_real_unique_root_id_constr')
                             )


class_attribute_string = Table('class_attribute_string', metadata,
                               Column('class', String(128), nullable=False,
                                      primary_key=True),
                               Column('class_root', String(128), nullable=False,
                                      primary_key=True),
                               Column('id', String(128), nullable=False,
                                      primary_key=True),
                               Column('length', Integer, default=128),
                               # FIXME: hardcoded default value size
                               Column('default', String(4096)),
                               
                               ForeignKeyConstraint(['class', 'class_root',
                                                     'id'],
                                                    ['class_attribute.class',
                                                     'class_attribute.class_root',
                                                     'class_attribute.id'],
                                                    onupdate='CASCADE',
                                                    ondelete='RESTRICT'),
                               
                               CheckConstraint('length >= 0',
                                               name='class_attr_string_length_gt0_constr'),

                               # An attribute name cannot appear twice
                               # whithin a class hierarchy
                               UniqueConstraint('class_root', 'id',
                                                name='class_attr_string_unique_root_id_constr')

                               )


class_attribute_date = Table('class_attribute_date', metadata,
                             Column('class', String(128), nullable=False,
                                    primary_key=True),
                             Column('class_root', String(128), nullable=False,
                                    primary_key=True),
                             Column('id', String(128), nullable=False,
                                    primary_key=True),
                             Column('min', Date, default=None),
                             Column('max', Date, default=None),
                             Column('default', Date),
                             
                             ForeignKeyConstraint(['class', 'class_root',
                                                   'id'],
                                                  ['class_attribute.class',
                                                   'class_attribute.class_root',
                                                   'class_attribute.id'],
                                                  onupdate='CASCADE',
                                                  ondelete='RESTRICT'),
                             
                             CheckConstraint('"min" IS NULL OR ("default" >= "min")',
                                             name='class_attr_date_min_constr'),
                             CheckConstraint('"max" IS NULL OR ("default" <= "max")',
                                             name='class_attr_date_max_constr'),
                             
                             # An attribute name cannot appear twice
                             # whithin a class hierarchy
                             UniqueConstraint('class_root', 'id',
                                              name='class_attr_date_unique_root_id_constr')

                             )


class_attribute_uri = Table('class_attribute_uri', metadata,
                            Column('class', String(128), nullable=False,
                                   primary_key=True),
                            Column('class_root', String(128), nullable=False,
                                   primary_key=True),
                            Column('id', String(128), nullable=False,
                                   primary_key=True),
                            Column('length', Integer, default=128),
                            # FIXME: hardcoded default value size
                            Column('default', String(4096)),
                            
                            ForeignKeyConstraint(['class', 'class_root',
                                                  'id'],
                                                 ['class_attribute.class',
                                                  'class_attribute.class_root',
                                                  'class_attribute.id'],
                                                 onupdate='CASCADE',
                                                 ondelete='RESTRICT'),
                            
                            CheckConstraint('length >= 0',
                                            name='class_attr_uri_length_gt0_constr'),

                            # An attribute name cannot appear twice
                            # whithin a class hierarchy
                            UniqueConstraint('class_root', 'id',
                                             name='class_attr_uri_unique_root_id_constr')
                            )


class_attribute_choice = Table('class_attribute_choice', metadata,
                               Column('class', String(128), nullable=False,
                                      primary_key=True),
                               Column('class_root', String(128), nullable=False,
                                      primary_key=True),
                               Column('id', String(128), nullable=False,
                                      primary_key=True),
                               # FIXME: hardcoded string lengths
                               # "choices" holds a JSON list of strings
                               Column('choices', String(8192), nullable=False),
                               Column('default', String(128)),
                               
                               ForeignKeyConstraint(['class', 'class_root',
                                                     'id'],
                                                    ['class_attribute.class',
                                                     'class_attribute.class_root',
                                                     'class_attribute.id'],
                                                    onupdate='CASCADE',
                                                    ondelete='RESTRICT'),

                               # Very simple check to ensure that the
                               # default choice is somehow contained
                               # in the JSON list of strings
                               CheckConstraint("choices LIKE '%\"' || \"default\" || '\"%'",
                                               name='class_attr_string_length_gt0_constr'),

                               # An attribute name cannot appear twice
                               # whithin a class hierarchy
                               UniqueConstraint('class_root', 'id',
                                                name='class_attr_choice_unique_root_id_constr')
                               )


class_attribute_objref = Table('class_attribute_objref', metadata,
                               Column('class', String(128), nullable=False,
                                      primary_key=True),
                               Column('class_root', String(128), nullable=False,
                                      primary_key=True),
                               Column('id', String(128), nullable=False,
                                      primary_key=True),
                               Column('target_class', String(128),
                                      nullable=False),
                               Column('target_class_root', String(128),
                                      nullable=False),

                               ForeignKeyConstraint(['class', 'class_root',
                                                     'id'],
                                                    ['class_attribute.class',
                                                     'class_attribute.class_root',
                                                     'class_attribute.id'],
                                                    onupdate='CASCADE',
                                                    ondelete='RESTRICT'),

                               ForeignKeyConstraint(['target_class',
                                                     'target_class_root'],
                                                    ['class.id',
                                                     'class.root'],
                                                    onupdate='CASCADE',
                                                    ondelete='RESTRICT'),

                               # An attribute name cannot appear twice
                               # whithin a class hierarchy
                               UniqueConstraint('class_root', 'id',
                                                name='class_attr_objref_unique_root_id_constr')
                               )


class_attribute_objref_list = Table('class_attribute_objref_list', metadata,
                                    Column('class', String(128),
                                           nullable=False, primary_key=True),
                                    Column('class_root', String(128),
                                           nullable=False, primary_key=True),
                                    Column('id', String(128), nullable=False,
                                           primary_key=True),
                                    Column('target_class', String(128),
                                           nullable=False),
                                    Column('target_class_root', String(128),
                                           nullable=False),
                                    Column('table', String(128),
                                           nullable=False, unique=True),

                                    ForeignKeyConstraint(['class',
                                                          'class_root',
                                                          'id'],
                                                         ['class_attribute.class',
                                                          'class_attribute.class_root',
                                                          'class_attribute.id'],
                                                         onupdate='CASCADE',
                                                         ondelete='RESTRICT'),
                                    
                                    ForeignKeyConstraint(['target_class',
                                                          'target_class_root'],
                                                         ['class.id',
                                                          'class.root'],
                                                         onupdate='CASCADE',
                                                         ondelete='RESTRICT'),

                                    # An attribute name cannot appear twice
                                    # whithin a class hierarchy
                                    UniqueConstraint('class_root', 'id',
                                                     name='class_attr_objref_list_unique_root_id_constr')
                               )


## Objects registry
object_t = Table('object', metadata,
                 Column('id', String(128), primary_key=True),
                 Column('class', String(128), nullable=False),
                 Column('class_root', String(128), nullable=False),
                 Column('name', String(128), nullable=False),
                 Column('notes', String(4096)),

                 ## Redundant constraint needed for foreign key references
                 UniqueConstraint('id', 'class',
                                  name='class_unique_id_class_constr'),

                 ## Redundant constraint needed for foreign key references
                 UniqueConstraint('id', 'class_root',
                                  name='class_unique_id_class_root_constr'),
                 
                 ForeignKeyConstraint(['class', 'class_root'],
                                      ['class.id', 'class.root'],
                                      onupdate='CASCADE', ondelete='RESTRICT')
                 )

## An entry in the catalog
catalog_entry = Table('catalog_entry', metadata,
                      Column('id', String(128), primary_key=True),
                      Column('root', ForeignKey('catalog_entry.id',
                                                onupdate='CASCADE',
                                                ondelete='RESTRICT'),
                             nullable=False),
                      Column('parent', String(128), nullable=False),
                      Column('parent_root', String(128), nullable=False),
                      Column('object', String(128), nullable=False),
                      Column('object_class_root', String(128), nullable=False),
                      
                      ## Redundant column which simplifies SQLAlchemy
                      ## inheritance mapping
                      Column('is_root', Boolean, nullable=False),
                      ## is_root <=> (root = id)
                      CheckConstraint('(NOT (root = id) OR is_root)'
                                      ' AND (NOT is_root OR (root = id))',
                                      name='catalog_is_root_value_constr'),
                      
                      ## Redundant constraint needed for foreign key references
                      UniqueConstraint('id', 'root',
                                       name='catalog_unique_id_root_constr'),

                      ## Redundant constraint needed for foreign key references
                      UniqueConstraint('id', 'root', 'object_class_root',
                                       name='catalog_unique_id_root_obj_root_constr'),

                      ## Redundant constraint needed for foreign key references
                      UniqueConstraint('id', 'object', 'object_class_root',
                                    name='catalog_unique_id_obj_class_constr'),

                      ## External reference to typing object (and its
                      ## root class)
                      ForeignKeyConstraint(['object', 'object_class_root'],
                                           ['object.id',
                                            'object.class_root'],
                                           onupdate='CASCADE',
                                           ondelete='RESTRICT'),

                      ## Ensure that a catalog entry and its parent
                      ## share the same root node
                      ForeignKeyConstraint(['parent', 'parent_root'],
                                           ['catalog_entry.id',
                                            'catalog_entry.root'],
                                           onupdate='CASCADE',
                                           ondelete='RESTRICT'),
                      
                      ## Ensure that a root class does not have a parent,
                      ## and vice versa:   (root = id) <=> (parent = id)
                      CheckConstraint('((NOT (root = id)) OR (parent = id))'
                                      ' AND ((NOT (parent = id))'
                                      '      OR (root = id))',
                                      name='catalog_root_iff_no_parent_constr')
                )

## Class visibility in workspaces
catalog_tree_visibility = Table('catalog_tree_visibility', metadata,
                                Column('workspace',
                                       ForeignKey('dam_workspace_workspace.id',
                                                  onupdate='CASCADE',
                                                  ondelete='RESTRICT'),
                                       primary_key=True,
                                       nullable=False),
                                Column('catalog_entry', String(128),
                                       primary_key=True,
                                       nullable=False),
                                Column('catalog_entry_root', String(128),
                                       nullable=False),
                                Column('catalog_entry_object_class_root', String(128),
                                       nullable=False),
                                Column('access',
                                Enum(*access_enum,
                                     name='class_visibility_access_enum'),
                                     nullable=False),
                         
                                ## Redundant constraint needed for foreign
                                ## key references
                                UniqueConstraint('catalog_entry_root',
                                                 'workspace',
                                                 name='catalog_tree_visibility_unique_catalog_root_ws_constr'),

                                ForeignKeyConstraint(['catalog_entry',
                                                      'catalog_entry_root',
                                                      'catalog_entry_object_class_root'],
                                                     ['catalog_entry.id',
                                                      'catalog_entry.root',
                                                      'catalog_entry.object_class_root'],
                                                     onupdate='CASCADE',
                                                     ondelete='RESTRICT'),

                                ## Ensure that the catalog entry class
                                ## is actually visible on the target
                                ## workspace (NOTE: it does not forbid
                                ## child catalog entries to be
                                ## associated with non-visible
                                ## classes)
                                ForeignKeyConstraint(['workspace',
                                                      'catalog_entry_object_class_root'],
                                                     ['class_visibility.workspace',
                                                      'class_visibility.class_root'],
                                                     onupdate='CASCADE',
                                                     ondelete='RESTRICT'),

                                ## Ensure that we only give visibility to
                                ## root catalog entries
                                CheckConstraint('catalog_entry'
                                                ' = catalog_entry_root',
                                                name='catalog_parent_root_constr')
                         )

## Cataloging information.  Only associate items and catalog entries when:
##
##    1. both the item and the catalog entry are visibile in the same
##       workspace;
##
##    2. both the item and the catalog entry class are visibile in the
##       same workspace.
cataloging = Table('cataloging', metadata,
                   Column('item', Integer,
                          primary_key=True),
                   Column('workspace', Integer,
                          primary_key=True),
                   Column('catalog_entry', String(128),
                          primary_key=True),
                   Column('catalog_entry_root', String(128)),
                   Column('catalog_entry_object', String(128),
                          primary_key=True),
                   Column('catalog_entry_object_class_root', String(128)),

                   ForeignKeyConstraint(['item', 'workspace'],
                                        ['workspace_damworkspace_items.item_id',
                                         'workspace_damworkspace_items.damworkspace_id'],
                                        onupdate='CASCADE',
                                        ondelete='RESTRICT'),

                   ForeignKeyConstraint(['catalog_entry_root',
                                         'workspace'],
                                  ['catalog_tree_visibility.catalog_entry_root',
                                   'catalog_tree_visibility.workspace'],
                                        onupdate='CASCADE',
                                        ondelete='RESTRICT'),

                   ForeignKeyConstraint(['catalog_entry',
                                         'catalog_entry_object',
                                         'catalog_entry_object_class_root'],
                                  ['catalog_entry.id',
                                   'catalog_entry.object',
                                   'catalog_entry.object_class_root'],
                                        onupdate='CASCADE',
                                        ondelete='RESTRICT'),

                   ForeignKeyConstraint(['workspace',
                                         'catalog_entry_object_class_root'],
                                        ['class_visibility.workspace',
                                         'class_visibility.class_root'],
                                        onupdate='CASCADE',
                                        ondelete='RESTRICT')
                   )

###############################################################################
## Predefined object classes
###############################################################################

## These tables represent two base classes, and they are designed
## according to these rules:
##
##    1. each table SHALL have a primary key which is also a reference
##       to object(id)
##
##    2. IF a table represents a derived class, then it SHALL ALSO
##       feature a ForeignKey constraint pointing to the (id,
##       class_root) fields of the table representing the previous
##       class in the inheritance hierarchy.
##
## For example, lets' say that we have the following class hierarchy:
##
##      Building  ->  Church  ->  Cathedral
##
## Then:
##
##    * 'Building' SHALL reference to the 'object' table (point 1);
##
##    * 'Church' SHALL ALSO reference to 'Building' (point 2);
##
##    * 'Cathedral' SHALL ALSO reference to 'Church' (point 2);
##
##    * When a record is added to 'Cathedral', then:
##
##          - object.id = Building.id = Church.id = Cathedral.id

## Simple keyword (without attributes)
object_keyword = Table('object_keyword', metadata,
                       Column('id', ForeignKey('object.id'),
                              primary_key=True)
                       )

# Category: almost like keyword, but it cannot catalog objects
object_category = Table('object_category', metadata,
                        Column('id', ForeignKey('object.id'),
                               primary_key=True)
                        )

def _build_object_table(table_name, parent_table, attrs_ddl, engine=None,
                        load_existing=False):
    if load_existing:
        # FIXME: try to use class attributes to check table columns
        # FIXME: ensure that it raises an error if the table does not exist yet
        return Table(table_name, metadata, autoload=True,
                     autoload_with=engine)
    else:
        return Table(table_name, metadata,
                     Column('id', String(128),
                            ForeignKey('%s.id' % (parent_table, )),
                            primary_key=True),
                     *attrs_ddl)

def create_object_table(table_name, parent_table, attrs_ddl, engine):
    newtable = _build_object_table(table_name, parent_table, attrs_ddl)
    newtable.create(engine)

    return newtable

def get_object_table(table_name, parent_table, attrs_ddl, engine):
    newtable = _build_object_table(table_name, parent_table, attrs_ddl,
                                   engine=engine, load_existing=True)
    return newtable

def _build_attr_tables(add_tables, engine=None, load_existing=False):
    '''
    Create additional table(s) for class attribute storage.  The list
    must contain constructors expecting to be called with a mandatory
    argument (a SQLAlchemy MetaData object) followed by optional
    **kwargs.
    '''
    newtables = []

    if load_existing:
        for t in add_tables:
            newtables.append(t(metadata, autoload=True, autoload_with=engine))
    else:
        for t in add_tables:
            newtables.append(t(metadata))
    
    return newtables

def create_attr_tables(add_tables, engine):
    newtables = _build_attr_tables(add_tables, engine)

    for t in newtables:
        t.create(engine)

    return newtables

def get_attr_tables(ddl_tables, engine):
    newtables = _build_attr_tables(ddl_tables, engine, load_existing=True)
    return newtables

###############################################################################
# Initialization and test functions
###############################################################################

def create_tables(connstr_or_engine, tables):
    '''
    Create a SQLAlchemy table on the DB, using the given connection
    string or engine
    '''
    engine = _get_engine(connstr_or_engine)
    metadata.create_all(bind=engine, tables=tables)


def init_db(connstr_or_engine):
    '''
    Initialize the KB database using the given SQLAlchemy connection
    string or engine.  This function will check whether the KB tables
    still exist on the DB, and won't try to alter them if they do.
    '''
    engine = _get_engine(connstr_or_engine)

    metadata.create_all(engine)

    _init_default_class_attr_types(engine)
    
    _init_default_classes(engine)


## Re-initialize the database using the given SQLAlchemy engine or
## connection string
def reset_db(connstr_or_engine):
    eng = _get_engine(connstr_or_engine)
    metadata.drop_all(engine)

    init_db(engine)


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


## Default class attribute types
def _init_default_class_attr_types(engine):
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
         'notes' : 'Typed object referece'},
        {'name'  : 'objref-list',
         'notes' : 'List of typed object refereces'}
        ]

    engine.execute(attribute_type.insert(), default_attr_types)


def _init_default_classes(engine):
    default_classes = [
        ## Keyword
        {'id'          : 'keyword',
         'root'        : 'keyword',
         'parent'      : 'keyword',
         'parent_root' : 'keyword',
         'name'        : 'Keyword',
         'table'       : 'object_keyword',
         'notes'       : 'Simple keyword without attributes',
         'is_root'     : True}]

    engine.execute(class_t.insert(), default_classes)
