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
import types
import weakref

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
import sqlalchemy.ext.associationproxy as sa_proxy
import sqlalchemy.ext.orderinglist as sa_order
from sqlalchemy import (event, Column, CheckConstraint, ForeignKey,
                        ForeignKeyConstraint, PrimaryKeyConstraint, Table)
from sqlalchemy.orm import mapper, relationship

import errors as kb_exc
import schema as kb_schema

from util.niceid import niceid

# Used for DateLikeString validation (see below)
import re
DATE_LIKE_RE = re.compile(
    '^(?P<s>[\+-]?)(?P<y>\d{1,9})-(?P<m>\d{2})-(?P<d>\d{2})$')

# List of reserved attribute IDs.
# FIXME: reserved IDs depend on KBObject def. and SQLAlchemy properties
RESERVED_IDS = ['id', 'class', 'class_root', 'name', 'notes']

class Attributes(types.ModuleType):
    def __init__(self, classes):
        doc = '''
            Each knowledge base :py:class:`Session <session.Session>`
            instance provides a ``orm`` property: a dynamically
            generated Python module giving access to several class
            definitions, mapped to the knowledge base session itself.
            For more details, see the :py:mod:`orm` module documentation.

            The ``orm`` module, in turn, provides the ``attributes``
            property: another dynamically generated Python module
            giving access to KB class attribute types definitions.

            Those attribute types are documented below.
            '''
        types.ModuleType.__init__(self, 'tinykb_%s_classes_attributes'
                                  % (classes.session.id_, ), doc)
        import classes as kb_classes
        assert(isinstance(classes, kb_classes.Classes))

        self._classes_ref = weakref.ref(classes)

        _init_base_attributes(self)

        self.__all__ = ['Attribute', 'Boolean', 'Integer', 'Real', 'Choice',
                        'String', 'Date', 'Uri', 'ObjectReference',
                        'is_valid_id']

    def is_valid_id(_self, id_):
        '''
        Check whether the given ID can be used for a KB class attribute.
        
        :type  id_: string
        :param id_: identifier to be checked
        
        :rtype: bool
        :returns: True if the id is valid, False otherwise
        '''
        safe_id = niceid(id_, 0)
        
        return ((id_ == safe_id) and (id_[0] != '_')
                and (id_ not in RESERVED_IDS))
    
    classes = property(lambda self: self._classes_ref())
    '''
    The knowledge base classes with which the attributes are bound

    :type: :py:class:`classes.Classes`
    '''


###############################################################################
# Mapped KB attribute classes
###############################################################################
def _init_base_attributes(o):
    '''
    Create the base KB attribute classes and ORM mappings for a
    knowledge base working session, using the given object (which must
    contain a 'classes' attribute).  The classes will be attached as
    attributes to the "o" object, preserving their name.
    '''
    classes = o.classes
    schema = classes.session.schema

    # Base abstract class
    class Attribute(object):
        '''
        Abstract base class representing a KB class attribute.

        This constructor is not expected to be invoked directly, but
        shares a number of parameters with concrete attribute type
        constructors.

        :type name: string
        :param name: human-readable name

        :type maybe_empty: bool
        :param maybe_empty: establishes whether the attribute may be left empty
                            in instances of the related KB class

        :type order: int
        :param order: optional value used for ordering the attributes when
                      displaying their related KB class or objects

        :type multivalued: bool
        :param multivalued: establishes whether the attribute is scalar or
                            vectorial (i.e. it could hold a list of values)

        :type notes: string
        :param notes: descriptive text with miscellaneous notes

        :type id_: string
        :param id_: ID to use for the attribute.  It must be unique,
                    and it may be composed by ASCII letters, numbers
                    and underscores (i.e. the same characters which
                    are usually adopted for Python object attributes).
                    When left empty, the ID will be autogenerated from
                    the human-readable name, through simple normalization
                    (lowercasing, removal of forbidden characters,
                    substitution of spaces with underscores)
        '''
        def __init__(self, name, id_=None, maybe_empty=True, order=0,
                     multivalued=False, notes=None):
            if id_ is not None:
                self.id = id_
            else:
                self.id = niceid(name, 0) # FIXME: should we add random chars?

            assert(o.is_valid_id(self.id))

            self.name = name
            self.maybe_empty = maybe_empty
            self.multivalued = multivalued
            self.order = order
            self.notes = notes

            # Will be defined when the attribute will be attached to a KB class
            self._multivalue_table = None

        @sa_orm.reconstructor
        def __init_on_load__(self):
            if self._multivalue_table is not None:
                self.multivalued = True
                # Will be assigned after invoking the attribute table
                # constructor
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
            cls = getattr(self, 'class')
            obj_table = cls.sqlalchemy_table
            mvtable = self._sqlalchemy_mv_table
            if not hasattr(self, '_mvclass'):
                # The following code can be executed only once per
                # Attribute instance
                if mvtable is None:
                    raise RuntimeError('BUG: Attribute.mapper_properties() '
                                       'cannot be called before '
                                       'Attribute.additional_tables()')

                # Compute some information now, to avoid queries when
                # representing the MVClass below
                cached_cls = str(cls)
                cached_id = self.id

                class MVClass(object):
                    def __init__(self2, value):
                        self2.value = value

                    def __repr__(self2):
                        return ('<MVClass for %s.%s: object=%s, value=%s>'
                                % (cached_cls, cached_id, self2.object,
                                   self2.value))

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
                    primaryjoin=(obj_table.c.id
                                 == mvtable.c['object']),
                    remote_side=[mvtable.c['object']],
                    order_by=[mvtable.c.order],
                    cascade='all, delete-orphan')}

        # Internal routine for building properties related to the
        # attribute column on the KB object table.  This implementation
        # should work for most of the derived classes
        def _objtable_mapper_properties(self):
            assert(not self.multivalued)
            cls = getattr(self, 'class')
            obj_table = cls.sqlalchemy_table
            return {self.id : obj_table.c[self.id]}

        # Internal routine for building properties for the multivalue
        # table.  This implementation should work for most of the derived
        # classes: it will create a 'value' property (based on the 'value'
        # column itself), and mask the 'object' column
        def _mvtable_mapper_properties(self):
            assert(self.multivalued)
            mvtable = self._sqlalchemy_mv_table
            assert(mvtable is not None)

            return {'_object' : mvtable.c.object, # 'object' used for backref
                    'value'   : mvtable.c.value}

        # Return a list of closures with two arguments (metadata and
        # **kwargs), which (when invoked) will return additional
        # SQLAlchemy Table objects needed for storing the attribute
        # (i.e. when it's multivalued).  Each table will have a foreign
        # key dependency with the owner object table
        def additional_tables(self):
            # This implementation should work most of the times: if
            # the attribute is not multivalued, then no additional
            # table constructors are required; otherwise, build just
            # one of them using self._raw_ddl()
            if not self.multivalued:
                return []

            owner_table = getattr(self, 'class').sqlalchemy_table

            def table_builder(metadata, **kwargs):
                if self._multivalue_table is None:
                    raise RuntimeError('BUG: Attribute.additional_tables() '
                                       'was invoked on attribute "%s" before '
                                       'associating the attribute to a KB '
                                       'class (class_id = %s)'
                                       % (self.id, str(self._class_id)))
                # FIXME: move MV table construction details in schema.py
                mvt = None
                for t in metadata.sorted_tables:
                    if self._multivalue_table == t.name:
                        # The table still exists in the metadata
                        mvt = t
                        break
                if mvt is None:
                    raw_ddl = self._raw_ddl()
                    # We will configure a primary key composed by the
                    # KB object reference and the index (order) of the value.
                    # It will ensure uniqueness and (if necessary)
                    # allow external references
                    pk_cols = ['object', 'order']
                    raw_ddl_pk = raw_ddl + [PrimaryKeyConstraint(*pk_cols)]
                    mvt = Table(self._multivalue_table, metadata,
                                Column('object', kb_schema.KeyString,
                                       ForeignKey('%s.id'
                                                  % (owner_table.name, ),
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                                       nullable=False),
                                Column('order', sa.types.Integer,
                                       nullable=False,
                                       default=0,
                                       server_default=_server_default(0)),
                                *raw_ddl_pk, **kwargs)

                # When this table constructor closure is executed, it will
                # also update the object reference to the SQLAlchemy table
                # object (which will be needed by self.mapper_properties())
                self._sqlalchemy_mv_table = mvt

                return mvt

            return [table_builder]

        def make_proxies_and_event_listeners(self, cls):
            # Build one or more SQLAlchemy association proxies and/or event
            # listeners for the KB attribute, when it's used on the given
            # Python class.

            # This method can only be called after the Python class the
            # attribute belongs to has been properly initialized

            # :type cls:  Python class
            # :param cls: a class whose instances will contain KB attribute
            #             values

            # The following default implementation should work most of the
            # times.  We'll react to the 'set' event, unless the attribute
            # is multivalued (in this case, we'll react to 'append')
            if not self.multivalued:
                validator = self.validator()
                event.listen(getattr(cls, self.id), 'set',
                             lambda _target, val, _oldval, _init: (
                                 validator(val)),
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

            validator = self.validator()
            event.listen(self._mvclass.value, 'set',
                         lambda _target, val, _oldval,_init: validator(val),
                         propagate=True, retval=True)

        def validator(self):
            '''
            Return a validation closure  that checks  whether the given value
            (i.e. the closure argument) is compatible with the KB attribute
            type and configuration, and thus whether it could be safely
            assigned/appended to the corresponding field of a Python
            object.

            :rtype: Python function
            :returns: A closure taking one argument (the value to check),
                      returning the value to be assigned, and
                      raising a :py:exc:`errors.ValidationError` in case
                      of validation failure
            '''
            raise NotImplementedError

    o.Attribute = Attribute

    class Boolean(Attribute):
        '''
        Boolean KB class attribute.  The constructor arguments are the
        same of :py:class:`Attribute`, except for:

        :type default: bool
        :param default: default attribute value
        '''
        def __init__(self, name, id_=None, maybe_empty=True, default=None,
                     order=0, multivalued=False, notes=None):
            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)
            self.default = default

        def _raw_ddl(self):
            return [Column(self.column_name(), sa.types.Boolean,
                           nullable=self.maybe_empty and not self.multivalued,
                           default=self.default,
                           server_default=_server_default(self.default))]

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                if isinstance(value, bool):
                    return value
                elif isinstance(value, int) and value in (0, 1):
                    return bool(value)
                raise kb_exc.ValidationError('expected a boolean-like value, '
                                             'got "%s"' % (str(value), ))

            return validator_fun

        def __repr__(self):
            return ('<Boolean(id=%s, class=%s, default=%s)>'
                    % (self.id, getattr(self, 'class'), self.default))

    o.Boolean = Boolean

    class Integer(Attribute):
        '''
        Integer KB class attribute.  The constructor arguments are the
        same of :py:class:`Attribute`, except for:

        :type min_: int
        :param min_: minimum value allowed for the attribute instances

        :type max_: int
        :param max_: maximum value allowed for the attribute instances

        :type default: int
        :param default: default attribute value
        '''
        def __init__(self, name, id_=None, min_=None, max_=None,
                     maybe_empty=True, default=None, order=0,
                     multivalued=False, notes=None):
            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)
            self.default = default
            self.min = min_
            self.max = max_

        def _raw_ddl(self):
            colname = self.column_name()
            ret = [Column(colname, sa.types.Integer,
                          nullable=self.maybe_empty and not self.multivalued,
                          autoincrement=False,
                          default=self.default,
                          server_default=_server_default(self.default))]
            if self.min is not None:
                ret.append(CheckConstraint('"%s" >= %d' % (colname, self.min),
                                           name=('%sobject_%s_attr_%s_min_constr'
                                                 % (schema.prefix,
                                                    self._class_id,
                                                    self.id))))
            if self.max is not None:
                ret.append(CheckConstraint('"%s" <= %d' % (colname, self.max),
                                           name=('%sobject_%s_attr_%s_max_constr'
                                                 % (schema.prefix,
                                                    self._class_id,
                                                    self.id))))
            return ret

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            min_v = self.min
            max_v = self.max
            
            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                if not (isinstance(value, int) or isinstance(value, long)
                        or (isinstance(value, decimal.Decimal)
                            and value == int(value))):
                    raise kb_exc.ValidationError(('expected an integer-like '
                                                  'value, got "%s" (type: %s)')
                                                 % (str(value), type(value)))

                in_range = ((min_v is None or (value >= min_v))
                            and (max_v is None or (value <= max_v)))
                if not in_range:
                    str_min = (min_v is None and '-Inf') or str(min_v)
                    str_max = (max_v is None and 'Inf') or str(max_v)
                    raise kb_exc.ValidationError('Value %d is out of [%s,%s]'
                                                 ' range'
                                                 % (value, str_min, str_max))
                return int(value)

            return validator_fun

        def __repr__(self):
            return ('<Integer(id=%s, class=%s, min=%s, max=%s, default=%s)>'
                    % (self.id, getattr(self, 'class'),
                       self.min, self.max, self.default))

    o.Integer = Integer

    class Real(Attribute):
        '''
        Real KB class attribute.  The constructor arguments are the
        same of :py:class:`Attribute`, except for:

        :type min_: float or decimal
        :param min_: minimum value allowed for the attribute instances

        :type max_: float or decimal
        :param max_: maximum value allowed for the attribute instances

        :type default: float or decimal
        :param default: default attribute value
        '''
        def __init__(self, name, id_=None, precision=10, min_=None, max_=None,
                     maybe_empty=True, default=None, order=0,
                     multivalued=False, notes=None):
            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)
            self.default = default
            self.min = min_
            self.max = max_

        def _raw_ddl(self):
            colname = self.column_name()
            ret = [Column(colname,
                          sa.types.Numeric(precision=self.precision),
                          nullable=self.maybe_empty and not self.multivalued,
                          default=self.default,
                          server_default=_server_default(self.default))]
            if self.min is not None:
                ret.append(CheckConstraint('"%s" >= %d' % (colname, self.min),
                                           name=('%sobject_%s_attr_%s_min_constr'
                                                 % (schema.prefix,
                                                    self._class_id,
                                                    self.id))))
            if self.max is not None:
                ret.append(CheckConstraint('"%s" <= %d' % (colname, self.max),
                                           name=('%sobject_%s_attr_%s_max_constr'
                                                 % (schema.prefix,
                                                    self._class_id,
                                                    self.id))))
            return ret

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            min_v = self.min
            max_v = self.max

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                if not ((isinstance(value, float)
                         or isinstance(value, decimal.Decimal))):
                            raise kb_exc.ValidationError(('expected a '
                                                          'float-like value, '
                                                          'got "%s"')
                                                         % (str(value), ))

                in_range = ((min_v is None or (value >= min_v))
                            and (max_v is None or (value <= max_v)))
                if not in_range:
                    str_min = (min_v is None and '-Inf') or str(min_v)
                    str_max = (max_v is None and 'Inf') or str(max_v)
                    raise kb_exc.ValidationError('value %f is out of [%s,%s]'
                                                 ' range'
                                                 % (value, str_min, str_max))
                return decimal.Decimal(value)

            return validator_fun

        def __repr__(self):
            return ('<Real(id=%s, class=%s, min=%s, max=%s, default=%s)>'
                    % (self.id, getattr(self, 'class'),
                       self.min, self.max, self.default))

    o.Real = Real

    class String(Attribute):
        '''
        String KB class attribute.  The constructor arguments are the
        same of :py:class:`Attribute`, except for:

        :type length: int
        :param length: maximum length of the string

        :type default: int
        :param default: default attribute value
        '''
        def __init__(self, name, id_=None, length=256, maybe_empty=True,
                     default=None, order=0, multivalued=False, notes=None):
            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)
            self.length = length
            self.default = default

        def _raw_ddl(self):
            colname = self.column_name()
            return [Column(colname, sa.types.String(self.length),
                           nullable=self.maybe_empty and not self.multivalued,
                           default=self.default,
                           server_default=_server_default(self.default))]

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            length = self.length

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                if not (isinstance(value, str) or isinstance(value, unicode)):
                    raise kb_exc.ValidationError(('expected a string-like '
                                                  'value, got "%s"')
                                                 % (str(value), ))
                if len(value) > length:
                    raise kb_exc.ValidationError('string length (%d chars) is '
                                                 'above the maximum limit '
                                                 '(%d chars)'
                                                 % (len(value), length))
                return unicode(value)

            return validator_fun

        def __repr__(self):
            return ("<String(id=%s, class=%s, length=%d, default='%s')>"
                    % (self.id, getattr(self, 'class'),
                       self.length, self.default))

    o.String = String

    class Date(Attribute):
        '''
        Date KB class attribute.  The constructor arguments are the
        same of :py:class:`Attribute`, except for:

        :type min_: datetime
        :param min_: minimum value allowed for the attribute instances

        :type max_: datetime
        :param max_: maximum value allowed for the attribute instances

        :type default: datetime
        :param default: default attribute value
        '''
        def __init__(self, name, id_=None, min_=None, max_=None,
                     maybe_empty=True, default=None, order=0,
                     multivalued=False, notes=None):
            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)
            self.default = default
            self.min = min_
            self.max = max_

        def _raw_ddl(self):
            colname = self.column_name()
            ret = [Column(colname, sa.types.Date,
                          nullable=self.maybe_empty and not self.multivalued,
                          default=self.default,
                          server_default=_server_default(self.default))]
            if self.min is not None:
                ret.append(CheckConstraint('"%s" >= \'%s\'' % (colname,
                                                               self.min),
                                           name=('%sobject_%s_attr_%s_min_constr'
                                                 % (schema.prefix,
                                                    self._class_id,
                                                    self.id))))
            if self.max is not None:
                ret.append(CheckConstraint('"%s" <= \'%s\'' % (colname,
                                                               self.max),
                                           name=('%sobject_%s_attr_%s_max_constr'
                                                 % (schema.prefix,
                                                    self._class_id,
                                                    self.id))))
            return ret


        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            min_v = self.min
            max_v = self.max

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
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

                in_range = ((min_v is None or (value >= min_v))
                            and (max_v is None or (value <= max_v)))
                if not in_range:
                    str_min = (min_v is None and '-Inf') or unicode(min_v)
                    str_max = (max_v is None and 'Inf') or unicode(max_v)
                    raise kb_exc.ValidationError('value %f is out of [%s,%s] '
                                                 'range'
                                                 % (value, str_min, str_max))
                return value

            return validator_fun

        def __repr__(self):
            return ('<Date(id=%s, class=%s, min=%s, max=%s, default=%s)>'
                    % (self.id, getattr(self, 'class'),
                       self.min, self.max, self.default))
    o.Date = Date

    class Uri(String):
        '''
        Integer KB class attribute.  Inherits from :py:class:`String`, and
        shares its constructor arguments.
        '''
        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            length = self.length

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                if not (isinstance(value, str) or isinstance(value, unicode)):
                    raise kb_exc.ValidationError(('expected a URI-like value, '
                                                  + 'got "%s"')
                                                 % (str(value), ))
                if len(value) > length:
                    raise kb_exc.ValidationError(('URI length (%d chars) '
                                                  'is above the maximum '
                                                  'limit (%d chars)')
                                                 % (len(value), length))

                # FIXME: actually perform URI validation
                return unicode(value)

            return validator_fun

        def __repr__(self):
            return ("<Uri(id=%s, class=%s, length=%d, default='%s')>"
                    % (self.id, getattr(self, 'class'),
                       self.length, self.default))

    o.Uri = Uri

    class Choice(Attribute):
        '''
        String-like KB class attribute, restricted to predefined
        choices.  The constructor arguments are the same of
        :py:class:`Attribute`, except for:

        :type list_of_choices: list of strings
        :param list_of_choices: valid values for the attribute

        :type default: string
        
        :param default: default attribute value (bust be included in
                        ``list_of_choices``)
        '''

        def __init__(self, name, list_of_choices, id_=None, maybe_empty=True,
                     default=None, order=0, multivalued=False, notes=None):
            if default is not None:
                if not (default in list_of_choices):
                    raise ValueError("Default value '%s' is not a valid choice"
                                     " (possible values: %s)"
                                     % (default, list_of_choices))
            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)
            self._list_of_choices = list_of_choices
            self.choices = json.dumps(list_of_choices)
            self.default = default

        @sa_orm.reconstructor
        def __init_on_load__(self):
            # Don't forget to call superclass reconstructors
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
                                          name=('%sobject_%s_attr_%s_enum'
                                                % (schema.prefix,
                                                   self._class_id,
                                                   self.id))),
                           nullable=self.maybe_empty and not self.multivalued,
                           default=self.default,
                           server_default=_server_default(self.default))]

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            list_of_choices = self._list_of_choices

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                value = unicode(value)
                if value not in list_of_choices:
                    raise kb_exc.ValidationError('"%s" is not a valid '
                                                 'choice among %s'
                                                 % (value,
                                                    unicode(list_of_choices)))
                return value

            return validator_fun

        def __repr__(self):
            return ("<Choice(id=%s, class=%s, choices=%s, default='%s')>"
                    % (self.id, getattr(self, 'class'),
                       self.choices, self.default))

    o.Choice = Choice

    class ObjectReference(Attribute):
        '''
        KB class attribute referencing to another knowledge base
        object.  The constructor arguments are the same of
        :py:class:`Attribute`, except for:

        :type target_class: :py:class:`orm.KBClass` or Python class
                            obtained via :py:class:`orm.KBClass.python_class`
        :param target_class: class restriction for objects assigned to
                             this attribute (i.e. class instances will
                             only accept objects belonging to
                             ``target_class`` or one of its
                             descendants)
        '''
        def __init__(self, name, target_class, id_=None, maybe_empty=True,
                     order=0, multivalued=False, notes=None):
            if isinstance(target_class, classes.KBClass):
                self.target = target_class
            else:
                self.target = target_class.__kb_class__
            self._target_table = self.target.table

            Attribute.__init__(self, name, id_=id_, maybe_empty=maybe_empty,
                               order=order, multivalued=multivalued,
                               notes=notes)

        @sa_orm.reconstructor
        def __init_on_load__(self):
            # FIXME: why doesn't SQLAlchemy call superclass reconstructors?
            Attribute.__init_on_load__(self)

            # Populate the _target_table field
            self._target_table = self.target.table

        def _raw_ddl(self):
            colname = self.column_name()
            return [Column(colname, kb_schema.KeyString,
                           ForeignKey('%s.id' % (self._target_table, ),
                                      onupdate='CASCADE',
                                      ondelete='CASCADE'),
                           nullable=self.maybe_empty and not self.multivalued)]

        # Override the default internal method, configuring a KB object
        # relationship for the corresponding field of the KB Python object
        def _objtable_mapper_properties(self):
            assert(not self.multivalued)

            obj_table = getattr(self, 'class').sqlalchemy_table
            target_pyclass = self.target.python_class
            target_table = self.target.sqlalchemy_table
            colname = self.column_name()

            return {('_' + colname) : obj_table.c[colname], # "Hide" colname...
                    colname # ...and use "original" colname as a relationship
                    : relationship(target_pyclass,
                                   backref=('references_%s_%s'
                                            % (self._class_id,
                                               colname)),
                                   primaryjoin=(obj_table.c[colname]
                                                == target_table.c.id),
                                   remote_side=[target_table.c.id],
                                   # FIXME: foreign_keys should be redundant
                                   # However, without it, SQLAlchemy seems
                                   # to get confused when KB object tables
                                   # are extended with ObjectReference fields
                                   # (see NotreDAM issue #89)
                                   foreign_keys=[obj_table.c[colname]])}

        # Override the default internal method, configuring a KB object
        # relationship for the 'value' attribute of the multivalue table
        def _mvtable_mapper_properties(self):
            assert(self.multivalued)
            mvtable = self._sqlalchemy_mv_table
            assert(mvtable is not None)

            target_pyclass = self.target._make_or_get_python_class()
            target_table = self.target.sqlalchemy_table

            return {'_object' : mvtable.c.object, # 'object' used as backref
                    '_value'  : mvtable.c.value,  # "Hide" table field name
                    'value'   : relationship(target_pyclass,
                                             backref=('references_%s_%s'
                                                      % (self._class_id,
                                                         self.id)),
                                             primaryjoin=(mvtable.c.value
                                                          == target_table.c.id),
                                             remote_side=target_table.c.id)}

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            target_pyclass = self.target._make_or_get_python_class()

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value

                if not isinstance(value, target_pyclass):
                    raise kb_exc.ValidationError(('expected a value of '
                                                  'type "%s" '
                                                  '(or descendants), got "%s" '
                                                  + '(of type %s)')
                                                 % (unicode(target_pyclass),
                                                    unicode(value),
                                                    unicode(type(value))))
                return value

            return validator_fun

        def __repr__(self):
            return ("<ObjectReference(id=%s, class=%s, target_class=%s)>"
                    % (self.id, getattr(self, 'class'), self.target))

    o.ObjectReference = ObjectReference


    class DateLikeString(String):
        '''
        Date-like field.  Inherits from :py:class:`String`, and shares
        its constructor arguments.
        '''
        def __init__(self, name, id_=None, maybe_empty=True, default=None,
                     order=0, multivalued=False, notes=None):
            # We are actually a 16-characters string field
            String.__init__(self, name, id_=id_, length=16,
                            maybe_empty=maybe_empty, default=default,
                            order=order, multivalued=multivalued, notes=notes)

        def validator(self):
            # Cache some values to avoid queries at validation time
            maybe_empty = self.maybe_empty
            multivalued = self.multivalued
            length = self.length

            def validator_fun(value):
                if maybe_empty and not multivalued and value is None:
                    return value
                if not (isinstance(value, str) or isinstance(value, unicode)):
                    raise kb_exc.ValidationError(('expected a date-like '
                                                  'string, got "%s"')
                                                 % (str(value), ))
                if len(value) > length:
                    raise kb_exc.ValidationError(('Date length (%d chars) '
                                                  'is above the maximum '
                                                  'limit (%d chars)')
                                                 % (len(value), length))

                is_valid = False
                match = DATE_LIKE_RE.match(value)
                if match is not None:
                    (sign, year, month, day) = match.group('s', 'y', 'm', 'd')
                    (year, month, day) = (int(year), int(month), int(day))
                    if ((month > 0) and (month < 13) and (day > 0)
                        and (day < 32)):
                        is_valid = True

                    if not is_valid:
                        raise kb_exc.ValidationError(('"%s" does not appear '
                                                      'to be a valid date')
                                                     % (value, ))

                    # Let's normalize a bit more, i.e. by stripping redundant
                    # zero's and the leading "+" sign
                    if sign == '+':
                        sign = ''
                    return u'%s%d-%02d-%02d' % (sign, year, month, day)

                return validator_fun

        def __repr__(self):
            return ("<DateLikeString(id=%s, class=%s, length=%d, default='%s')>"
                    % (self.id, getattr(self, 'class'),
                       self.length, self.default))

    o.DateLikeString = DateLikeString

    ###########################################################################
    ## Mappers
    ###########################################################################

    mapper(Attribute, schema.class_attribute,
           polymorphic_on=schema.class_attribute.c['type'],
           properties={
            '_class_id' : schema.class_attribute.c['class'],
            '_class_root_id' : schema.class_attribute.c.class_root,
            'class' : relationship(classes.KBClass,
                                   back_populates='attributes'),
            '_multivalue_table' : schema.class_attribute.c.multivalue_table
            })

    mapper(Boolean, schema.class_attribute_bool, inherits=Attribute,
           polymorphic_identity='bool',
           properties={
            '__class_id' : schema.class_attribute_bool.c['class'],
            '__class_root_id' : schema.class_attribute_bool.c.class_root
            })

    mapper(Integer, schema.class_attribute_int, inherits=Attribute,
           polymorphic_identity='int',
           properties={
            '__class_id' : schema.class_attribute_int.c['class'],
            '__class_root_id' : schema.class_attribute_int.c.class_root
            })

    mapper(Real, schema.class_attribute_real, inherits=Attribute,
           polymorphic_identity='real',
           properties={
            '__class_id' : schema.class_attribute_real.c['class'],
            '__class_root_id' : schema.class_attribute_real.c.class_root
            },)

    mapper(String, schema.class_attribute_string, inherits=Attribute,
           polymorphic_identity='string',
           properties={
            '__class_id' : schema.class_attribute_string.c['class'],
            '__class_root_id' : schema.class_attribute_string.c.class_root
            })

    mapper(Date, schema.class_attribute_date, inherits=Attribute,
           polymorphic_identity='date',
           properties={
            '__class_id' : schema.class_attribute_date.c['class'],
            '__class_root_id' : schema.class_attribute_date.c.class_root
            })

    mapper(Uri, schema.class_attribute_uri, inherits=Attribute,
           polymorphic_identity='uri',
           properties={
            '__class_id' : schema.class_attribute_uri.c['class'],
            '__class_root_id' : schema.class_attribute_uri.c.class_root
            })

    mapper(Choice, schema.class_attribute_choice, inherits=Attribute,
           polymorphic_identity='choice',
           properties={
            '__class_id' : schema.class_attribute_choice.c['class'],
            '__class_root_id' : schema.class_attribute_choice.c.class_root
            })

    mapper(ObjectReference, schema.class_attribute_objref, inherits=Attribute,
           polymorphic_identity='objref',
           properties={
            '__class_id' : schema.class_attribute_objref.c['class'],
            '__class_root_id' : schema.class_attribute_objref.c.class_root,
            'target' : relationship(classes.KBClass, backref='references')
            })

    mapper(DateLikeString, schema.class_attribute_uri, inherits=Attribute,
           polymorphic_identity='date-like-string',
           properties={
            '__class_id' : schema.class_attribute_uri.c['class'],
            '__class_root_id' : schema.class_attribute_uri.c.class_root
            })

    ###########################################################################
    # Events
    ###########################################################################

    def attribute_after_delete(_mapper, connection, target):
        # Handle MV tables "orphaned" by attr removal
        if not target.multivalued:
            return
        # Unregister the autogenerated class for the multivalue table...
        if hasattr(target, '_mvclass'):
            from sqlalchemy.orm.instrumentation import unregister_class
            unregister_class(target._mvclass)
            del target._mvclass

        # ...and drop the autogenerated multivalue table itself
        schema.drop_attr_tables([target._multivalue_table], connection)

    event.listen(Attribute, 'after_delete', attribute_after_delete,
                 propagate=True)

###############################################################################
# Utility functions
###############################################################################
def _server_default(value):
    if value is None:
        return None
    # Return a value suitable to be used as server-side default
    if isinstance(value, bool):
        return (value and '1' or '0')
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, long):
        return str(value)
    elif isinstance(value, float):
        return str(value)
    elif isinstance(value, decimal.Decimal):
        return str(value)
    elif isinstance(value, basestring):
        return value
    else:
        raise RuntimeError('BUG: unsupported value for server-side default: '
                           '%s (type: %s)' % (unicode(value), type(value)))
