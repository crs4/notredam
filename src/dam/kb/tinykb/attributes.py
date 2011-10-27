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
# Objects and SQLalchemy mappers for managing class attributes in the
# knowledge base.
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

import datetime
import decimal
import json

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from sqlalchemy import event, Column, CheckConstraint, ForeignKey, Table
from sqlalchemy.orm import mapper, relationship

import schema
import classes

from util.niceid import niceid

# Base abstract class
class Attribute(object):
    def __init__(self, name, maybe_empty=True, order=0, notes=None,
                 explicit_id=None):
        if explicit_id is not None:
            self.id = explicit_id
        else:
            self.id = niceid(name, 0) # FIXME: should we add random chars?
        self.name = name
        self.maybe_empty = maybe_empty
        self.order = order
        self.notes = notes

    def column_name(self):
        # The id is assumed to be safe to use as column name
        return self.id

    def python_types(self):
        '''
        Return a set of Python types which could be used when giving a
        value to the attribute.
        '''
        raise NotImplementedError

    # Return a list of SQLAlchemy DDL objects (type,
    # CheckConstraint, etc.) describing the Type object
    def ddl(self):
        raise NotImplementedError

    # Return a dictionary containing the SQLAlchemy mapper properties
    # required to make the attribute work
    def mapper_properties(self):
        return {}

    # Return a list of closures with two arguments (metadata and
    # **kwargs), which (when invoked) will return additional
    # SQLAlchemy Table objects needed for storing the attribute.  Each
    # table will have a foreign key dependency with the owner object
    # table
    def additional_tables(self):
        return []


class Boolean(Attribute):
    def __init__(self, name, maybe_empty=True, default=None, order=0,
                 notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)
        self.default = default

    def python_types(self):
        return set([bool]
                   + ([type(None)] if self.maybe_empty else []))

    def ddl(self):
        return [Column(self.column_name(), sa.types.Boolean,
                       nullable=self.maybe_empty,
                       default=self.default)]

    def __repr__(self):
        return '<Boolean(default=%s)>' % (self.default)


class Integer(Attribute):
    def __init__(self, name, min_=None, max_=None, maybe_empty=True,
                 default=None, order=0, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)
        self.default = default
        self.min = min_
        self.max = max_

    def python_types(self):
        return set([int]
                   + ([type(None)] if self.maybe_empty else []))

    def ddl(self):
        ret = [Column(self.column_name(), sa.types.Integer,
                      nullable=self.maybe_empty,
                      default=self.default)]
        if self.min is not None:
            ret.append(CheckConstraint('"%s" >= %d' % (self.id, self.min),
                                       name=('%s_%s_%s_min_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        if self.max is not None:
            ret.append(CheckConstraint('"%s" <= %d' % (self.id, self.min),
                                       name=('%s_%s_%s_max_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        return ret

    def __repr__(self):
        return '<Integer(min=%s, max=%s, default=%s)>' % (self.min_,
                                                          self.max_,
                                                          self.default)


class Real(Attribute):
    def __init__(self, name, precision=10, min_=None, max_=None,
                 maybe_empty=True, default=None, order=0, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)
        self.default = default
        self.min = min_
        self.max = max_

    def python_types(self):
        return set([decimal.Decimal]
                   + ([type(None)] if self.maybe_empty else []))

    def ddl(self):
        ret = [Column(self.column_name(),
                      sa.types.Numeric(precision=self.precision),
                      nullable=self.maybe_empty, default=self.default)]
        if self.min is not None:
            ret.append(CheckConstraint('"%s" >= %d' % (self.id, self.min),
                                       name=('%s_%s_%s_min_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        if self.max is not None:
            ret.append(CheckConstraint('"%s" <= %d' % (self.id, self.min),
                                       name=('%s_%s_%s_max_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        return ret

    def __repr__(self):
        return '<Real(min=%s, max=%s, default=%s)>' % (self.min_,
                                                       self.max_,
                                                       self.default)


class String(Attribute):
    def __init__(self, name, length=256, maybe_empty=True, default=None,
                 order=0, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, notes=notes)
        self.length = length
        self.default = default

    def python_types(self):
        return set([unicode, str]
                   + ([type(None)] if self.maybe_empty else []))

    def ddl(self):
        return [Column(self.column_name(), sa.types.String(self.length),
                       nullable=self.maybe_empty, default=self.default)]

    def __repr__(self):
        return "<String(length=%d, default='%s')>" % (self.length,
                                                      self.default)


class Date(Attribute):
    def __init__(self, name, min_=None, max_=None, maybe_empty=True,
                 default=None, order=0, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)
        self.default = default
        self.min = min_
        self.max = max_

    def python_types(self):
        return set([unicode, str, datetime.date]
                   + ([type(None)] if self.maybe_empty else []))

    def ddl(self):
        ret = [Column(self.column_name(), sa.types.Date,
                      nullable=self.maybe_empty,
                      default=self.default)]
        if self.min is not None:
            ret.append(CheckConstraint('"%s" >= %d' % (self.id, self.min),
                                       name=('%s_%s_%s_min_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        if self.max is not None:
            ret.append(CheckConstraint('"%s" <= %d' % (self.id, self.min),
                                       name=('%s_%s_%s_max_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        return ret


    def __repr__(self):
        return '<Date(min=%s, max=%s, default=%s)>' % (self.min_,
                                                       self.max_,
                                                       self.default)

class Uri(String):
    def __repr__(self):
        return "<Uri(length=%d, default='%s')>" % (self.length,
                                                   self.default)


class Choice(Attribute):
    def __init__(self, name, list_of_choices, maybe_empty=True, default=None,
                 order=0, notes=None):
        if default is not None:
            if not (default in list_of_choices):
                raise ValueError("Default value '%s' is not a valid choice"
                                 " (possible values: %s)" % (default,
                                                             list_of_choices))
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)
        self._list_of_choices = list_of_choices
        self.choices = json.dumps(list_of_choices)
        self.default = default

    @sa_orm.reconstructor
    def __init_on_load__(self):
        # Populate the _init_on_load field from the JSON value read
        # from the DB
        self._list_of_choices = json.loads(self.choices)
        assert(isinstance(self._list_of_choices, list))

    def get_choices(self):
        '''
        Return the list of available choices
        '''
        return self._list_of_choices

    def python_types(self):
        return set([unicode, str]
                   + ([type(None)] if self.maybe_empty else []))

    def ddl(self):
        return [Column(self.column_name(),
                       sa.types.Enum(*self._list_of_choices,
                                      name=('%s_%s_%s_enum'
                                            % (self._class_root_id,
                                               self._class_id,
                                               self.column_name()))),
                       nullable=self.maybe_empty, default=self.default)]
    
    def __repr__(self):
        return "<Choice(choices=%s, default='%s')>" % (self.choices,
                                                       self.default)

                                                
class ObjectReference(Attribute):
    def __init__(self, name, target_class, maybe_empty=True, order=0,
                 notes=None):
        if isinstance(target_class, classes.KBClass):
            self._target_table = target_class.table
            self.target = target_class
        else:
            sa_mapper = sa.orm.class_mapper(target_class)
            ## FIXME: is it correct to take the first table below?
            # if len(sa_mapper.tables) > 1:
            #     raise ValueError('Target class %s is mapped to multiple'
            #                      ' tables: %s' % (target_class,
            #                                       sa_mapper.tables))
            self._target_table = sa_mapper.tables[0].name
            self.target = target_class.__kb_class__

        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)

    def python_types(self):
        # FIXME: an event handler would be necessary for obj id assignments
        return set([unicode, str, # In case an object ID is provided
                    type(self.target_class)]
                   + ([type(None)] if self.maybe_empty else []))

    @sa_orm.reconstructor
    def __init_on_load__(self):
        # Populate the _target_table field
        self._target_table = self.target.table

    def ddl(self):
        return [Column(self.column_name(), sa.types.String(128),
                       ForeignKey('%s.id' % (self._target_table, )),
                       nullable=self.maybe_empty)]

    def mapper_properties(self):
        # Build a relationship to the target python class, using the
        # id of the attribute
        table = self._class.sqlalchemy_table

        target_pyclass = self.target.make_python_class() 

        target_table = self.target.sqlalchemy_table

        colname = self.column_name()
        return {('_' + colname) : table.c[colname], # "Hide" column name...
                colname # ...and use "original" column name as a relationship
                : relationship(target_pyclass,
                               backref=('references_%s_%s'
                                        % (self.target.id,
                                           colname)),
                               cascade='all',
                               primaryjoin=(table.c[colname]
                                            == target_table.c.id))}

    def __repr__(self):
        return "<ObjectReference(target_class=%s)>" % (self.target, )


class ObjectReferencesList(Attribute):
    def __init__(self, name, target_class, maybe_empty=True, order=0,
                 notes=None):
        if isinstance(target_class, classes.KBClass):
            self._target_table = target_class.table
            self.target = target_class
        else:
            sa_mapper = sa.orm.class_mapper(target_class)
            ## FIXME: is it correct to take the first table below?
            self._target_table = sa_mapper.tables[0].name
            self.target = target_class.__kb_class__

        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           notes=notes)

        # FIXME: ensure uniqueness!
        # FIXME: it would be better to prefix the owner table name
        self.table = niceid(self.id)

        # Will be assigned after invoking the attribute table constructor
        self._sqlalchemy_table = None

    @sa_orm.reconstructor
    def __init_on_load__(self):
        # Populate the _target_table field
        self._target_table = self.target.table

        # Will be assigned after invoking the attribute table constructor
        self._sqlalchemy_table = None

    def python_types(self):
        return set([list,
                    sa_orm.collections.InstrumentedList])

    def ddl(self):
        return []

    def additional_tables(self):
        owner_table = self._class.sqlalchemy_table
        
        def table_builder(metadata, autoload=False, **kwargs):
            if autoload:
                t = Table(self.table, metadata, autoload=True, **kwargs)
            else:
                t = Table(self.table, metadata,
                          Column('object', sa.types.String(128),
                                 ForeignKey('%s.id' % (owner_table.name, ))),
                          Column('reference', sa.types.String(128),
                                 ForeignKey('%s.id' % (self._target_table, ))),
                          #Column('order', sa.types.Integer, default=0,
                          #       nullable=False),
                          **kwargs)

            # When the constructor is executed, update the object
            # reference to the SQLAlchemy table object (will be needed
            # by self.mapper_properties())
            self._sqlalchemy_table = t

            return t
        
        return [table_builder]

    def mapper_properties(self):
        # Build a relationship to the target python class, using the
        # name of the attribute

        table = self._class.sqlalchemy_table

        mytable = self._sqlalchemy_table

        # This assertion will fail if this method is invoked before
        # additional_tables()
        assert(mytable is not None)

        target_pyclass = self.target.make_python_class() 

        target_table = self.target.sqlalchemy_table
        
        return {self.id
                : relationship(target_pyclass,
                               backref=('references_list_%s_%s'
                                        % (self.target.name,
                                           self.name)),
                               cascade='all',
                               secondary=mytable,
                               primaryjoin=(table.c.id == mytable.c.object),
                               secondaryjoin=(mytable.c.reference
                                              == target_table.c.id))}

    def __repr__(self):
        return "<ObjectReferencesList(target_class=%s)>" % (self.target, )

                                                
###############################################################################
## Mappers
###############################################################################

mapper(Attribute, schema.class_attribute,
       polymorphic_on=schema.class_attribute.c['type'],
       properties={
        '_class_id' : schema.class_attribute.c['class'],
        '_class_root_id' : schema.class_attribute.c.class_root,
        '_class' : relationship(classes.KBClass, backref='attributes',
                                cascade='all')
        })

mapper(Boolean, schema.class_attribute_bool, inherits=Attribute,
       polymorphic_identity='bool')

mapper(Integer, schema.class_attribute_int, inherits=Attribute,
       polymorphic_identity='int')

mapper(Real, schema.class_attribute_real, inherits=Attribute,
       polymorphic_identity='real')

mapper(String, schema.class_attribute_string, inherits=Attribute,
       polymorphic_identity='string')

mapper(Date, schema.class_attribute_date, inherits=Attribute,
       polymorphic_identity='date')

mapper(Uri, schema.class_attribute_uri, inherits=Attribute,
       polymorphic_identity='uri')

mapper(Choice, schema.class_attribute_choice, inherits=Attribute,
       polymorphic_identity='choice')

mapper(ObjectReference, schema.class_attribute_objref, inherits=Attribute,
       polymorphic_identity='objref',
       properties={
        'target' : relationship(classes.KBClass, backref='references',
                                cascade='all')
        })

mapper(ObjectReferencesList, schema.class_attribute_objref_list,
       inherits=Attribute,
       polymorphic_identity='objref-list',
       properties={
        'target' : relationship(classes.KBClass, backref='references_lists',
                                cascade='all')
        })
