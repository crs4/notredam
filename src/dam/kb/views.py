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
                         HttpResponseNotAllowed)
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
    return _dispatch(request, {'GET' : class_get}, kwargs)


def class_get(request, class_id):
    ses = _kb_session()
    try:
        cls = ses.class_(class_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    return HttpResponse(simplejson.dumps(_kbclass_to_dict(cls)))


@login_required
def object_index(request):
    '''
    GET: return the list of objects defined in the knowledge base.
    '''
    return _dispatch(request, {'GET' : object_index_get})


def object_index_get(request):
    ses = _kb_session()
    obj_dicts = [_kbobject_to_dict(o) for o in ses.objects()]

    return HttpResponse(simplejson.dumps(obj_dicts))


@login_required
def object_(request, **kwargs):
    '''
    GET: return a specific object from the knowledge base.
    POST: update an existing object in the knowledge base.
    DELETE: delete and existing object from the knowledge base.
    '''
    return _dispatch(request, {'GET' : object_get}, kwargs)


def object_get(request, object_id):
    ses = _kb_session()
    try:
        cls = ses.object(object_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    return HttpResponse(simplejson.dumps(_kbobject_to_dict(cls)))


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
    encoding_post_var = '__REAL_HTTP_METHOD__'

    if (('POST' == req.method) and
        (encoding_post_var in req.POST)):
        enc_method = req.POST[encoding_post_var]
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
