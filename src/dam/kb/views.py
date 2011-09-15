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
def index(request):
    '''
    Main URL, supporting 
    '''
    return _dispatch(request, {'PUT': index_put})


def index_get(request):
    '''
    Just a debugging function
    '''
    return HttpResponse(simplejson.dumps({'hello': 'world'}))


def index_put(request):
    '''
    Insert a new class definition in the knowledge base
    '''
    raise NotImplementedError


@login_required
def class_(request, **kwargs):
    return _dispatch(request, {'GET' : class_get}, kwargs)


def class_get(request, class_id):
    ses = _kb_session()
    try:
        cls = ses.class_(class_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    return HttpResponse(_kbclass_to_json(cls))


@login_required
def object_(request, **kwargs):
    return _dispatch(request, {'GET' : object_get}, kwargs)


def object_get(request, object_id):
    ses = _kb_session()
    try:
        cls = ses.object(object_id)
    except kb_exc.NotFound:
        return HttpResponseNotFound()

    return HttpResponse(_kbobject_to_json(cls))


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
    

def _kbclass_to_json(cls):
    '''
    Create a JSON representation of the given KB class
    '''
    clsattrs = {}
    for a in cls.attributes:
        clsattrs[a.id] = _kbattr_to_json(a)

    clsdict = {'id'          : cls.id,
               'name'        : cls.name,
               'superclass'  : cls.superclass.id,
               'can_catalog' : cls.can_catalog,
               'notes'       : cls.notes,
               'attributes'  : clsattrs}

    return simplejson.dumps(clsdict)


# Mapping between attribute type and functions returning a JSON
# representation of the attribute itself
_kb_attrs_json_map = {kb_attrs.Boolean : lambda a:
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

def _kbattr_to_json(attr):
    '''
    Create a string representation of a KB class attribute descriptor
    '''
    return _kb_attrs_json_map[type(attr)](attr)


def _std_attr_fields(a):
    '''
    Return the standard fields present in each KB attribute object
    (non-null, notes, etc.)
    '''
    return [['name',        a.name],
            ['maybe_empty', a.maybe_empty],
            ['notes',       a.notes]] 


def _kbobject_to_json(obj):
    '''
    Create a JSON representation of the given KB object
    '''
    objattrs = {}
    for a in getattr(obj, 'class').attributes:
        objattrs[a.id] = _kbobjattr_to_json(a, getattr(obj, a.id))

    objdict = {'id'          : obj.id,
               'name'        : obj.name,
               'class'       : getattr(obj, 'class').id,
               'notes'       : obj.notes,
               'attributes'  : objattrs}

    return simplejson.dumps(objdict)


# Mapping between object attribute type and functions returning a JSON
# representation of the attribute value
_kb_objattrs_json_map = {kb_attrs.Boolean : lambda a, v: v,
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

def _kbobjattr_to_json(attr, val):
    '''
    Create a string representation of a KB class attribute descriptor
    '''
    return _kb_objattrs_json_map[type(attr)](attr, val)
