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
# Django views for interacting with the NotreDAM knowledge base
#
# Author: Alceste Scalas <alceste@crs4.it>
#
#########################################################################

from django.contrib.auth.decorators import login_required
from django.http import (HttpRequest, HttpResponse, HttpResponseNotFound,
                         HttpResponseNotAllowed, HttpResponseBadRequest)
from django.utils import simplejson

import tinykb.session as kb_ses
import tinykb.exceptions as kb_exc
import tinykb.attributes as kb_attrs
import util

@login_required
def class_index(request):
    '''
    GET: return the list of classes defined in the knowledge base.
    '''
    return _dispatch(request, {'GET' : class_index_get})


def class_index_get(request):
    ses = _kb_session()
    cls_dicts = [_kbclass_to_dict(c) for c in ses.classes()]

    return HttpResponse(simplejson.dumps(cls_dicts))


@login_required
def class_(request, **kwargs):
    '''
    GET: return a specific class from the knowledge base.
    POST: update an existing class in the knowledge base.
    DELETE: delete and existing class from the knowledge base.
    '''
    return _dispatch(request, {'GET'  : class_get,
                               'POST' : class_post}, kwargs)


def class_get(request, class_id):
    ses = _kb_session()
    try:
        cls = ses.class_(class_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    return HttpResponse(simplejson.dumps(_kbclass_to_dict(cls)))


def class_post(request, class_id):
    try:
        cls_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    ses = _kb_session()
    try:
        cls = ses.class_(class_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    # FIXME: right now, we only support updating a few fields
    updatable_fields = {'name'        : set([unicode, str]),
                        'notes'       : set([unicode, str]),
                        'can_catalog' : set([bool])}
    try:
        _assert_update_object_fields(cls, cls_dict, updatable_fields)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    ses.add(cls)
    ses.commit()

    return HttpResponse('ok')


@login_required
def object_index(request):
    '''
    GET: return the list of objects defined in the knowledge base.
    PUT: insert a new object in the knowledge base.
    '''
    return _dispatch(request, {'GET' : object_index_get,
                               'PUT' : object_index_put})


def object_index_get(request):
    ses = _kb_session()
    obj_dicts = [_kbobject_to_dict(o) for o in ses.objects()]

    return HttpResponse(simplejson.dumps(obj_dicts))


def object_index_put(request):
    try:
        obj_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    ses = _kb_session()
    object_class_id = obj_dict.get('class', None)
    if object_class_id is None:
        return HTTPResponseBadRequest('Object representation lacks a '
                                      +'"class" field')

    object_name = obj_dict.get('name', None)
    if object_name is None:
        return HTTPResponseBadRequest('Object representation lacks a '
                                      +'"name" field')
    
    explicit_id = obj_dict.get('id', None)
    
    try:
        ObjectClass = ses.python_class(object_class_id)
    except kb_exc.NotFound:
        return HTTPResponseBadRequest('Invalid object class: %s'
                                      % (object_class_id, ))

    obj = ObjectClass(object_name, explicit_id=explicit_id)

    # FIXME: right now, we only support updating a few fields
    updatable_fields = {'name'        : set([unicode, str]),
                        'notes'       : set([unicode, str])}

    try:
        _assert_update_object_fields(obj, obj_dict, updatable_fields)
        _assert_update_object_attrs(obj, obj_dict.get('attributes', {}), ses)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    ses.add(obj)
    ses.commit()

    return HttpResponse('ok')


@login_required
def object_(request, **kwargs):
    '''
    GET: return a specific object from the knowledge base.
    POST: update an existing object in the knowledge base.
    DELETE: delete and existing object from the knowledge base.
    '''
    return _dispatch(request, {'GET' :  object_get,
                               'POST' : object_post}, kwargs)


def object_get(request, object_id):
    ses = _kb_session()
    try:
        cls = ses.object(object_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    return HttpResponse(simplejson.dumps(_kbobject_to_dict(cls)))


def object_post(request, object_id):
    try:
        obj_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    ses = _kb_session()
    try:
        obj = ses.object(object_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    # FIXME: right now, we only support updating a few fields
    updatable_fields = {'name'        : set([unicode, str]),
                        'notes'       : set([unicode, str])}
    try:
        _assert_update_object_fields(obj, obj_dict, updatable_fields)
        _assert_update_object_attrs(obj, obj_dict.get('attributes', {}), ses)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    ses.add(obj)
    ses.commit()

    return HttpResponse('ok')


@login_required
def class_objects(request, class_id):
    '''
    GET: return the list of objects belonging to a given KB class.
    '''
    return _dispatch(request, {'GET' : class_objects_get},
                     {'class_id' : class_id})


def class_objects_get(request, class_id):
    ses = _kb_session()
    try:
        cls = ses.class_(class_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    objs = ses.objects(class_=cls.make_python_class())
    obj_dicts = [_kbobject_to_dict(o) for o in objs]

    return HttpResponse(simplejson.dumps(obj_dicts))


###############################################################################
# Internal helper functions
###############################################################################

def _dispatch(request, method_fun_dict, kwargs=None):
    '''
    Given a Django HttpRequest, choose the function associated to its
    HTTP method from method_fun_dict, and execute it.  If the third
    argument (kwargs) is not None, it is assumed to be a dictionary
    which will be expanded into additional keyword arguments for the
    function being called.

    The Django request passed to the function being invoked will also
    be enriched with an additional _vars attribute, containing the
    method-related variables (GET, POST, etc.)
    '''
    (method, mvars) = _infer_method(request)
    if (method not in method_fun_dict):
        return HttpResponseNotAllowed(method_fun_dict.keys())

    # Enrich request object with a new '._vars' attribute, containing
    # GET or POST variables
    request._vars = mvars

    if kwargs is None:
        return method_fun_dict[method](request)
    else:
        return method_fun_dict[method](request, **kwargs)


def _infer_method(req):
    '''
    Return a 2-tuple containing the "real" HTTP method of the given
    request (i.e. also considering whether the method encoding variable
    is set), and the method-related variables
    '''
    assert(isinstance(req, HttpRequest))

    encodable_methods = ('PUT', 'DELETE')
    encoding_get_var = '__REAL_HTTP_METHOD__'

    if (('POST' == req.method) and
        (encoding_get_var in req.GET)):
        enc_method = req.GET[encoding_get_var]
        assert(enc_method in encodable_methods)
        return (enc_method, req.POST)
    elif ('POST' == req.method):
        return ('POST', req.POST)
    elif ('GET' == req.method):
        return ('GET', req.GET)
    else:
        # Simply return the current method, with GET variables
        return (req.method, req.GET)


def _kb_session():
    '''
    Create a knowledge base session, using the NotreDAM connection parameters
    '''
    connstr = util.notredam_connstring()
    return kb_ses.Session(connstr)
    

def _kbclass_to_dict(cls):
    '''
    Create a JSON'able dictionary representation of the given KB class
    '''
    clsattrs = {}
    for a in cls.attributes:
        clsattrs[a.id] = _kbattr_to_dict(a)

    if (cls.superclass.id == cls.id):
        superclass = None
    else:
        superclass = cls.superclass.id

    clsdict = {'id'          : cls.id,
               'name'        : cls.name,
               'superclass'  : superclass,
               'can_catalog' : cls.can_catalog,
               'notes'       : cls.notes,
               'attributes'  : clsattrs}

    return clsdict


# Mapping between attribute type and functions returning a JSON'able
# dictionary representation of the attribute itself
_kb_attrs_dict_map = {kb_attrs.Boolean : lambda a:
                          dict([['type',   'bool'],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.Integer : lambda a:
                          dict([['type',    'int'],
                                ['min',     a.min],
                                ['max',     a.max],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.Real    : lambda a:
                          dict([['type',    'real'],
                                ['min',     a.min],
                                ['max',     a.max],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.String  : lambda a:
                          dict([['type',    'string'],
                                ['length',  a.length],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.Date    : lambda a:
                          dict([['type',    'date'],
                                ['min',     a.min],
                                ['max',     a.max],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.String  : lambda a:
                          dict([['type',    'string'],
                                ['length',  a.length],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.Uri  : lambda a:
                          dict([['type',    'uri'],
                                ['length',  a.length],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.Choice  : lambda a:
                          dict([['type',    'choice'],
                                ['choices', simplejson.loads(a.choices)],
                                ['default', a.default]]
                               + _std_attr_fields(a)),
                      kb_attrs.ObjectReference : lambda a:
                          dict([['type',         'objref'],
                                ['target_class', a.target.id]]
                               + _std_attr_fields(a)),
                      kb_attrs.ObjectReferencesList : lambda a:
                          dict([['type',         'objref-list'],
                                ['target_class', a.target.id]]
                               + _std_attr_fields(a))                         
                      }

def _kbattr_to_dict(attr):
    '''
    Create a string representation of a KB class attribute descriptor
    '''
    return _kb_attrs_dict_map[type(attr)](attr)


def _std_attr_fields(a):
    '''
    Return the standard fields present in each KB attribute object
    (non-null, notes, etc.)
    '''
    return [['name',        a.name],
            ['maybe_empty', a.maybe_empty],
            ['notes',       a.notes]] 


def _kbobject_to_dict(obj):
    '''
    Create a JSON'able dictionary representation of the given KB object
    '''
    objattrs = {}
    for a in getattr(obj, 'class').attributes:
        objattrs[a.id] = _kbobjattr_to_dict(a, getattr(obj, a.id))

    objdict = {'id'          : obj.id,
               'name'        : obj.name,
               'class'       : getattr(obj, 'class').id,
               'notes'       : obj.notes,
               'attributes'  : objattrs}

    return objdict


# Mapping between object attribute type and functions returning a
# JSON'able dictionary representation of the attribute value
_kb_objattrs_dict_map = {kb_attrs.Boolean : lambda a, v: v,
                         kb_attrs.Integer : lambda a, v: v,
                         kb_attrs.Real    : lambda a, v: v,
                         kb_attrs.String  : lambda a, v: v,
                         kb_attrs.Date    : lambda a, v: v,
                         kb_attrs.String  : lambda a, v: v,
                         kb_attrs.Uri     : lambda a, v: v,
                         kb_attrs.Choice  : lambda a, v: v,
                         kb_attrs.ObjectReference : lambda a, v: v.id,
                         kb_attrs.ObjectReferencesList : lambda a, v:
                             [o.id for o in v]
                         }

def _kbobjattr_to_dict(attr, val):
    '''
    Create a string representation of a KB class attribute descriptor
    '''
    return _kb_objattrs_dict_map[type(attr)](attr, val)


def _assert_return_json_data(request):
    '''
    Ensure that a Django request contains JSON data, and return it
    (taking care of its encoding).  Raise a ValueError if the content
    type is not supported.
    '''
    if ('application/json; charset=UTF-8' == request.META['CONTENT_TYPE']):
        print type(request.raw_post_data)
        return simplejson.loads(request.raw_post_data)
    else:
        # FIXME: we should support other charset encodings here
        raise ValueError('Unsupported content type: '
                         + request.META['CONTENT_TYPE'])


def _assert_update_object_fields(obj, obj_dict, updatable_fields):
    '''
    Update the fields (Python attributes) of an object, using the
    given dictionaries: one containing the new field/values, and
    another which associates each field name with the set of their
    expected type.  In case of error, a ValueError is raised (with an
    informative message).
    '''
    for f in updatable_fields:
        val = obj_dict.get(f, getattr(obj, f))
        expected_types = updatable_fields[f]
        if not type(val) in expected_types:
            raise ValueError(('Invalid type for attribute %s: '
                              + 'expected one of %s, got %s')
                             % (f, str(expected_types),
                                str(type(val))))
        setattr(obj, f, val)


def _assert_update_object_attrs(obj, obj_dict, sa_session):
    '''
    Almost like _assert_update_object_fields(), but applied to KB
    object attribute (i.e. with special care for object references and
    other "complex" types).
    '''
    obj_class_attrs = getattr(obj, 'class').attributes
    for a in obj_class_attrs:
        val = obj_dict.get(a.id, getattr(obj, a.id))
        print '*** ', obj, a.id, type(getattr(obj, a.id)), val
        expected_types = a.python_types()
        if not type(val) in expected_types:
            raise ValueError(('Invalid type for attribute %s: '
                              + 'expected one of %s, got %s')
                             % (a.id, str(expected_types),
                                str(type(val))))

        # Let's now perform validation checks on each possible
        # attribute type
        if (type(a) == kb_attrs.Choice):
            # Before updating, check whether the provided value is a
            # valid choice
            if val not in a.get_choices():
                raise ValueError(('Invalid value for attribute %s: '
                                  + 'expected one of %s, got \'%s\'')
                                 % (a.id, str(a.get_choices()), str(val)))
            setattr(obj, a.id, val)
        elif (type(a) == kb_attrs.ObjectReference):
            # We can't simply update the attribute: we need to
            # retrieve the referred object by its ID
            curr_obj = getattr(obj, a.id)
            if (val == curr_obj.id):
                # Nothing to be done here
                break
            else:
                try:
                    new_obj = sa_session.object(val)
                except kb_exc.NotFound:
                    raise ValueError('Unknown object id reference: %s'
                                     % val)
                # Actually perform the assignment
                setattr(obj, a.id, new_obj)
        elif (type(a) == kb_attrs.ObjectReferencesList):
            # We can't simply update the attribute: we need to
            # retrieve the referred objects by their ID, and
            # add/remove them from the list
            obj_lst = getattr(obj, a.id)
            # Objects to be removed (i.e. whose ID is not present in
            # the list provided by the client)
            rm_objects = [o for o in obj_lst if o.id not in val]
            # Objects to be added
            curr_oids = [o.id for o in obj_lst]
            add_oids = [x for x in val if x not in curr_oids]
            add_objects = []
            for x in add_oids:
                try:
                    add_objects.append(sa_session.object(x))
                except kb_exc.NotFound:
                    raise ValueError('Unknown object id reference: %s'
                                     % x)
            # Actually perform removals/additions
            for o in rm_objects:
                obj_lst.remove(o)
            for o in add_objects:
                obj_lst.append(o)
        else:
            # Simple case: just update the attribute
            setattr(obj, a.id, val)
