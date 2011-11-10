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
import sqlalchemy.ext.associationproxy as sa_proxy
import sqlalchemy.ext.orderinglist as sa_order
from sqlalchemy import (event, Column, CheckConstraint, ForeignKey,
                        PrimaryKeyConstraint, Table)
from sqlalchemy.orm import mapper, relationship

import errors as kb_exc
import schema
import classes

from util.niceid import niceid

# Base abstract class
class Attribute(object):
    def __init__(self, name, maybe_empty=True, order=0, multivalued=False,
                 notes=None, explicit_id=None):
        if explicit_id is not None:
            self.id = explicit_id
        else:
            self.id = niceid(name, 0) # FIXME: should we add random chars?
        self.name = name
        self.maybe_empty = maybe_empty
        self.multivalued = multivalued
        self.order = order
        self.notes = notes

        # FIXME: ensure uniqueness!
        # FIXME: it would be better to prefix the owner table name
        if self.multivalued:
            self._multivalue_table = niceid(self.id)
            # Will be assigned after invoking the attribute table constructor
            self._sqlalchemy_mv_table = None
        else:
            self._multivalue_table = None

    @sa_orm.reconstructor
    def __init_on_load__(self):
        if self._multivalue_table is not None:
            self.multivalued = True
            # Will be assigned after invoking the attribute table constructor
            self._sqlalchemy_mv_table = None
        else:
            self.multivalued = False

    def column_name(self):
        if not self.multivalued:
            # The id is assumed to be safe to use as column name
            return self.id
        else:
            # The column name is used in the additional multivalue
            # table: 'reference' is also used in self.mapper_properties()
            return 'value'

    # Return a list of SQLAlchemy DDL objects (type, CheckConstraint,
    # etc.) aimed at building the main object table for the class
    # containing the attribute
    def ddl(self):
        # This implementation should work most of the times: if the
        # attribute is multivalued, return an empty list --- otherwise
        # call the low-level _raw_ddl() method (which may also be used
        # by self.additional_tables()
        if self.multivalued:
            return []
        else:
            return self._raw_ddl()

    # Return a list of SQLAlchemy DDL objects which may be used to
    # build either the main object table for the class containing the
    # attribute, or its associated tables (e.g. when the attribute is
    # multivalued)
    def _raw_ddl(self):
        raise NotImplementedError

    # Return a dictionary containing the SQLAlchemy mapper properties
    # required to make the attribute work
    def mapper_properties(self):
        if not self.multivalued:
            return self._objtable_mapper_properties()

        # In case of a multivalued attribute, we will create an
        # intermediate mapper class to use with an SQLAlchemy
        # Association Proxy.  It will allow to handle the multivalued
        # attribute of the Python class as a simple list of values
        mvtable = self._sqlalchemy_mv_table
        if not hasattr(self, '_mvclass'):
            # The following code can be executed only once per
            # Attribute instance
            table = self._class.sqlalchemy_table
            if mvtable is None:
                raise RuntimeError('BUG: Attribute.mapper_properties() cannot '
                                   'be called before '
                                   'Attribute.additional_tables()')

            class MVClass(object):
                def __init__(self, value):
                    self.value = value

            mapper(MVClass, mvtable,
                   properties=self._mvtable_mapper_properties())
        
            self._mvclass = MVClass # See enclosing 'if' statement

        # Associate the KB object to the multivalued attribute table.
        # The "plain" attribute id is used to establish a SQLAlchemy
        # association proxy.  The underlying relation will be mapped
        # on an "hidden" attribute (i.e. prefixed with an underscore)
        hidden_id = '_' + self.id
        return {hidden_id : relationship(
                self._mvclass, backref='object',
                collection_class=sa_order.ordering_list('order'),
                order_by=[mvtable.c.order],
                cascade='all')}

    # Internal routine for building properties related to the
    # attribute column on the KB object table.  This implementation
    # should work for most of the derived classes
    def _objtable_mapper_properties(self):
        # Since the column is a "pure" value, it can be mapped by
        # SQLAlchemy without further issues
        assert(not self.multivalued)

        return {}

    # Internal routine for building properties for the multivalue
    # table.  This implementation should work for most of the derived
    # classes: it will create a 'value' property (based on the 'value'
    # column itself), and mask the 'object' column
    def _mvtable_mapper_properties(self):
        assert(self.multivalued)
        mvtable = self._sqlalchemy_mv_table
        assert(mvtable is not None)

        return {'_object' : mvtable.c.object, # 'object' field will be backref
                'value'   : mvtable.c.value}

    # Return a list of closures with two arguments (metadata and
    # **kwargs), which (when invoked) will return additional
    # SQLAlchemy Table objects needed for storing the attribute
    # (i.e. when it's multivalued).  Each table will have a foreign
    # key dependency with the owner object table
    def additional_tables(self):
        # This implementation should work most of the times: if the
        # attribute is not multivalued, then no additional table
        # constructors are required; otherwise, build just one of them using
        # self._raw_ddl()
        if not self.multivalued:
            return []
        
        owner_table = self._class.sqlalchemy_table

        def table_builder(metadata, autoload=False, **kwargs):
            if autoload:
                t = Table(self._multivalue_table, metadata, autoload=True,
                          **kwargs)
            else:
                raw_ddl = self._raw_ddl()
                # We will also configure a primary key composed by all
                # the columns of the multivalue table.  It will ensure
                # uniqueness and (if necessary) allow external references
                pk_cols = (['object'] # See table definition below
                           + [c.name for c in raw_ddl if isinstance(c,Column)])
                raw_ddl_pk = raw_ddl + [PrimaryKeyConstraint(*pk_cols)]
                t = Table(self._multivalue_table, metadata,
                          Column('object', sa.types.String(128),
                                 ForeignKey('%s.id' % (owner_table.name, )),
                                 nullable=False),
                          Column('order', sa.types.Integer, nullable=False),
                          *raw_ddl_pk, **kwargs)

            # When this table constructor closure is executed, it will
            # also update the object reference to the SQLAlchemy table
            # object (which will be needed by self.mapper_properties())
            self._sqlalchemy_mv_table = t

            return t
        
        return [table_builder]

    def make_proxies_and_event_listeners(self, cls):
        '''
        Build one or more SQLAlchemy association proxies and/or event
        listeners for the KB attribute, when it's used on the given
        Python class.

        This method can only be called after the Python class the
        attribute belongs to has been properly initialized

        @type cls:  a Python class
        @param cls: a class whose instances will contain KB attribute values
        '''
        # The following default implementation should work most of the
        # times.  We'll react to the 'set' event, unless the attribute
        # is multivalued (in this case, we'll react to 'append')
        if not self.multivalued:
            event.listen(getattr(cls, self.id), 'set',
                         lambda _target, val, _oldval, _init: (
                             self.validate(val)),
                         propagate=True, retval=True)
            return

        # If the attribute is multivalued, we're going to configure a
        # SQLAlchemy association proxy, and listen to the 'set' event
        # on the related MV class
        if not hasattr(self, '_mvclass'):
            raise RuntimeError('BUG: '
                               'Attribute.make_proxies_and_event_listeners() '
                               'cannot be called before '
                               'Attribute.mapper_properties()')

        # This association proxy is based on the "hidden" attribute id
        # and 'value' property of the MV class.  All this stuff must
        # have been configured in .mapper_properties()
        hidden_id = '_' + self.id
        setattr(cls, self.id,
                sa_proxy.association_proxy(hidden_id, 'value'))

        event.listen(self._mvclass.value, 'set',
                     lambda _target, val, _oldval, _init: self.validate(val),
                     propagate=True, retval=True)

    def validate(self, value):
        '''
        Check whether the given value is compatible with KB attribute
        type and configuration, and thus whether it could be safely
        assigned/appended to the corresponding field of a Python
        object.  Raise a ValidationError in case of mismatch, or just
        return the value itself (possibly with some ad-hoc type
        casting) in case of success.

        @type value:  a Python term
        @param value: the value to check
        '''
        raise NotImplementedError


class Boolean(Attribute):
    def __init__(self, name, maybe_empty=True, default=None, order=0,
                 multivalued=False, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           multivalued=multivalued, notes=notes)
        self.default = default

    def _raw_ddl(self):
        return [Column(self.column_name(), sa.types.Boolean,
                       nullable=self.maybe_empty and not self.multivalued,
                       default=self.default)]

    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        if isinstance(value, bool):
            return value
        elif isinstance(value, int) and value in (0, 1):
            return bool(value)
        raise kb_exc.ValidationError('expected a boolean-like value, got "%s"'
                                     % (str(value), ))

    def __repr__(self):
        return '<Boolean(default=%s)>' % (self.default)


class Integer(Attribute):
    def __init__(self, name, min_=None, max_=None, maybe_empty=True,
                 default=None, order=0, multivalued=False, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           multivalued=multivalued, notes=notes)
        self.default = default
        self.min = min_
        self.max = max_

    def _raw_ddl(self):
        colname = self.column_name()
        ret = [Column(colname, sa.types.Integer,
                      nullable=self.maybe_empty and not self.multivalued,
                      default=self.default)]
        if self.min is not None:
            ret.append(CheckConstraint('"%s" >= %d' % (colname, self.min),
                                       name=('%s_%s_%s_min_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        if self.max is not None:
            ret.append(CheckConstraint('"%s" <= %d' % (colname, self.max),
                                       name=('%s_%s_%s_max_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        return ret

    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        if not (isinstance(value, int) or (isinstance(value, decimal.Decimal)
                                           and value == int(value))):
            raise kb_exc.ValidationError(('expected an integer-like value, '
                                          + 'got "%s"')
                                         % (str(value), ))

        in_range = ((self.min is None or (value >= self.min))
                    and (self.max is None or (value <= self.max)))
        if not in_range:
            str_min = (self.min is None and '-Inf') or str(self.min)
            str_max = (self.max is None and 'Inf') or str(self.max)
            raise kb_exc.ValidationError('Value %d is out of [%s,%s] range'
                                         % (value, str_min, str_max))

        return int(value)

    def __repr__(self):
        return '<Integer(min=%s, max=%s, default=%s)>' % (self.min,
                                                          self.max,
                                                          self.default)


class Real(Attribute):
    def __init__(self, name, precision=10, min_=None, max_=None,
                 maybe_empty=True, default=None, order=0, multivalued=False,
                 notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           multivalued=multivalued, notes=notes)
        self.default = default
        self.min = min_
        self.max = max_

    def _raw_ddl(self):
        colname = self.column_name()
        ret = [Column(colname,
                      sa.types.Numeric(precision=self.precision),
                      nullable=self.maybe_empty and not self.multivalued,
                      default=self.default)]
        if self.min is not None:
            ret.append(CheckConstraint('"%s" >= %d' % (colname, self.min),
                                       name=('%s_%s_%s_min_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        if self.max is not None:
            ret.append(CheckConstraint('"%s" <= %d' % (colname, self.max),
                                       name=('%s_%s_%s_max_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        return ret

    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        if not (isinstance(value, float) or isinstance(value,
                                                       decimal.Decimal)):
            raise kb_exc.ValidationError(('expected a float-like value, '
                                          + 'got "%s"')
                                         % (str(value), ))

        in_range = ((self.min is None or (value >= self.min))
                    and (self.max is None or (value <= self.max)))
        if not in_range:
            str_min = (self.min is None and '-Inf') or str(self.min)
            str_max = (self.max is None and 'Inf') or str(self.max)
            raise kb_exc.ValidationError('value %f is out of [%s,%s] range'
                                         % (value, str_min, str_max))

        return decimal.Decimal(value)

    def __repr__(self):
        return '<Real(min=%s, max=%s, default=%s)>' % (self.min,
                                                       self.max,
                                                       self.default)


class String(Attribute):
    def __init__(self, name, length=256, maybe_empty=True, default=None,
                 order=0, multivalued=False, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           multivalued=multivalued, notes=notes)
        self.length = length
        self.default = default

    def _raw_ddl(self):
        colname = self.column_name()
        return [Column(colname, sa.types.String(self.length),
                       nullable=self.maybe_empty and not self.multivalued,
                       default=self.default)]

    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        if not (isinstance(value, str) or isinstance(value, unicode)):
            raise kb_exc.ValidationError(('expected a string-like value, '
                                          + 'got "%s"')
                                         % (str(value), ))
        if len(value) > self.length:
            raise kb_exc.ValidationError(('string length (%d chars) is above '
                                          + 'the maximum limit (%d chars)')
                                         % (len(value), self.length))
        
        return unicode(value)

    def __repr__(self):
        return "<String(length=%d, default='%s')>" % (self.length,
                                                      self.default)


class Date(Attribute):
    def __init__(self, name, min_=None, max_=None, maybe_empty=True,
                 default=None, order=0, multivalued=False, notes=None):
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           multivalued=multivalued, notes=notes)
        self.default = default
        self.min = min_
        self.max = max_

    def _raw_ddl(self):
        colname = self.column_name()
        ret = [Column(colname, sa.types.Date,
                      nullable=self.maybe_empty and not self.multivalued,
                      default=self.default)]
        if self.min is not None:
            ret.append(CheckConstraint('"%s" >= %d' % (colname, self.min),
                                       name=('%s_%s_%s_min_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        if self.max is not None:
            ret.append(CheckConstraint('"%s" <= %d' % (colname, self.max),
                                       name=('%s_%s_%s_max_constr'
                                             % (self._class_root_id,
                                                self._class_id,
                                                self.id))))
        return ret


    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        if (isinstance(value, str) or isinstance(value, unicode)):
            try:
                dt = datetime.datetime.strptime(value, '%Y-%m-%d')
                value = datetime.date(dt.year, dt.month, dt.day)
            except ValueError, e:
                raise kb_exc.ValidationError('cannot parse date: %s'
                                             % unicode(e))
        elif isinstance(value, datetime.datetime):
            value = datetime.date(value.year, value.month, value.day)
        elif not isinstance(value, datetime.date):
            raise kb_exc.ValidationError(('expected a date-like value, '
                                          + 'got "%s"')
                                         % (unicode(value), ))

        in_range = ((self.min is None or (value >= self.min))
                    and (self.max is None or (value <= self.max)))
        if not in_range:
            str_min = (self.min is None and '-Inf') or unicode(self.min)
            str_max = (self.max is None and 'Inf') or unicode(self.max)
            raise kb_exc.ValidationError('value %f is out of [%s,%s] range'
                                         % (value, str_min, str_max))

        return value

    def __repr__(self):
        return '<Date(min=%s, max=%s, default=%s)>' % (self.min,
                                                       self.max,
                                                       self.default)

class Uri(String):
    def __repr__(self):
        return "<Uri(length=%d, default='%s')>" % (self.length,
                                                   self.default)

    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        if not (isinstance(value, str) or isinstance(value, unicode)):
            raise kb_exc.ValidationError(('expected a URI-like value, '
                                          + 'got "%s"')
                                         % (str(value), ))
        if len(value) > self.length:
            raise kb_exc.ValidationError(('URI length (%d chars) is above '
                                          + 'the maximum limit (%d chars)')
                                         % (len(value), self.length))

        # FIXME: actually perform URI validation
        return unicode(value)


class Choice(Attribute):
    def __init__(self, name, list_of_choices, maybe_empty=True, default=None,
                 order=0, multivalued=False, notes=None):
        if default is not None:
            if not (default in list_of_choices):
                raise ValueError("Default value '%s' is not a valid choice"
                                 " (possible values: %s)" % (default,
                                                             list_of_choices))
        Attribute.__init__(self, name, maybe_empty=maybe_empty, order=order,
                           multivalued=multivalued, notes=notes)
        self._list_of_choices = list_of_choices
        self.choices = json.dumps(list_of_choices)
        self.default = default

    @sa_orm.reconstructor
    def __init_on_load__(self):
        # FIXME: why doesn't SQLAlchemy call superclass reconstructors?
        Attribute.__init_on_load__(self)

        # Populate the _init_on_load field from the JSON value read
        # from the DB
        self._list_of_choices = json.loads(self.choices)
        assert(isinstance(self._list_of_choices, list))

    def get_choices(self):
        '''
        Return the list of available choices
        '''
        return self._list_of_choices

    def _raw_ddl(self):
        colname = self.column_name()
        return [Column(colname,
                       sa.types.Enum(*self._list_of_choices,
                                      name=('%s_%s_%s_enum'
                                            % (self._class_root_id,
                                               self._class_id,
                                               self.id))),
                       nullable=self.maybe_empty and not self.multivalued,
                       default=self.default)]
    
    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value
        value = unicode(value)
        if value not in self._list_of_choices:
            raise kb_exc.ValidationError('"%s" is not a valid choice among %s'
                                         % (value,
                                            unicode(self._list_of_choices)))
        return value

    def __repr__(self):
        return "<Choice(choices=%s, default='%s')>" % (self.choices,
                                                       self.default)

                                                
class ObjectReference(Attribute):
    def __init__(self, name, target_class, maybe_empty=True, order=0,
                 multivalued=False, notes=None):
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
                           multivalued=multivalued, notes=notes)

    @sa_orm.reconstructor
    def __init_on_load__(self):
        # FIXME: why doesn't SQLAlchemy call superclass reconstructors?
        Attribute.__init_on_load__(self)

        # Populate the _target_table field
        self._target_table = self.target.table

    def _raw_ddl(self):
        colname = self.column_name()
        return [Column(colname, sa.types.String(128),
                       ForeignKey('%s.id' % (self._target_table, )),
                       nullable=self.maybe_empty and not self.multivalued)]

    # Override the default internal method, configuring a KB object
    # relationship for the corresponding field of the KB Python object
    def _objtable_mapper_properties(self):
        assert(not self.multivalued)

        obj_table = self._class.sqlalchemy_table
        target_pyclass = self.target.make_python_class()
        target_table = self.target.sqlalchemy_table
        colname = self.column_name()

        return {('_' + colname) : obj_table.c[colname], # "Hide" column name...
                colname # ...and use "original" col name as a relationship
                : relationship(target_pyclass,
                               backref=('references_%s_%s'
                                        % (self.target.id,
                                           colname)),
                               cascade='all',
                               primaryjoin=(obj_table.c[colname]
                                            == target_table.c.id))}

    # Override the default internal method, configuring a KB object
    # relationship for the 'value' attribute of the multivalue table
    def _mvtable_mapper_properties(self):
        assert(self.multivalued)
        mvtable = self._sqlalchemy_mv_table
        assert(mvtable is not None)

        target_pyclass = self.target.make_python_class()
        target_table = self.target.sqlalchemy_table

        return {'_object' : mvtable.c.object, # 'object' field will be backref
                '_value'  : mvtable.c.value,  # "Hide" object id
                'value'   : relationship(target_pyclass,
                                         backref=('references_%s_%s'
                                                  % (self._class.id,
                                                     self.id)),
                                         cascade='all',
                                         primaryjoin=(mvtable.c.value
                                                      == target_table.c.id))}
    
    def validate(self, value):
        if self.maybe_empty and not self.multivalued and value is None:
            return value

        target_pyclass = self.target.make_python_class()
        if not isinstance(value, target_pyclass):
            raise kb_exc.ValidationError(('expected a value of type "%s" '
                                          + '(or descendants), got "%s" '
                                          + '(of type %s)')
                                         % (unicode(target_pyclass),
                                            unicode(value),
                                            unicode(type(value))))
        return value

    def __repr__(self):
        return "<ObjectReference(target_class=%s)>" % (self.target, )


###############################################################################
## Utility functions
###############################################################################

# Check whether the given value is compatible with the given target
# KBClass instance.
# FIXME: should be an ObjectReference method: refactor ObjectReferencesList!

###############################################################################
## Mappers
###############################################################################

mapper(Attribute, schema.class_attribute,
       polymorphic_on=schema.class_attribute.c['type'],
       properties={
        '_class_id' : schema.class_attribute.c['class'],
        '_class_root_id' : schema.class_attribute.c.class_root,
        '_class' : relationship(classes.KBClass, backref='attributes',
                                cascade='all'),
        '_multivalue_table' : schema.class_attribute.c.multivalue_table
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
