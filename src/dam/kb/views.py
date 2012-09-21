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

import datetime
from types import NoneType

from django.contrib.auth.decorators import login_required
from django.http import (HttpRequest, HttpResponse, HttpResponseNotFound,
                         HttpResponseNotAllowed, HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.utils import simplejson

from dam.core.dam_workspace.decorators import permission_required
from dam.treeview.models import Node as TreeviewNode
from models import Object as DjangoKBObject

import tinykb.access as kb_access
import tinykb.session as kb_ses
import tinykb.errors as kb_exc
from tinykb.util.niceid import niceid as kb_niceid
import util
from decorators import http_basic_auth

# FIXME: use the standard ModResource-based dispatch system here

@http_basic_auth
@login_required
@permission_required('admin', False)
def class_index(request, ws_id):
    '''
    GET: return the list of classes defined in the knowledge base.
    PUT: insert a new class in the knowledge base.
    '''
    return _dispatch(request, {'GET' : class_index_get,
                               'PUT' : class_index_put},
                     {'ws_id' : int(ws_id)})


def class_index_get(request, ws_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        cls_dicts = [_kbclass_to_dict(c, ses) for c in ses.classes(ws=ws)]

        return HttpResponse(simplejson.dumps(cls_dicts))


def class_index_put(request, ws_id):
    try:
        cls_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    if not isinstance(cls_dict, dict):
        return HttpResponseBadRequest('JSON class representation must be '
                                      'a dictionary')

    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        class_name = cls_dict.get('name', None)
        if class_name is None:
            return HttpResponseBadRequest('Class representation lacks a '
                                          +'"name" field')

        superclass = None
        superclass_id = cls_dict.get('superclass', None)
        if superclass_id is not None:
            try:
                superclass = ses.class_(superclass_id)
            except kb_exc.NotFound:
                return HttpResponseBadRequest('Unknown superclass id: "%s"'
                                              % (superclass_id, ))

            perm = superclass.workspace_permission(ws)
            if perm not in (kb_access.OWNER, kb_access.READ_WRITE):
                return HttpResponseForbidden()

        explicit_id = cls_dict.get('id', None)
        if explicit_id is not None:
            # Check for uniqueness
            try:
                ses.class_(explicit_id)
                return HttpResponseBadRequest('Class id "%s" already in use'
                                              % (explicit_id, ))
            except kb_exc.NotFound:
                pass

        # Build the list of attributes of the class
        json_attrs = cls_dict.get('attributes', [])

        # Remove inherited attributes.  We may raise an error when
        # inherited attribute IDs are are reused, but being more tolerant
        # we allow to create new KB classes by cut'n'pasting (and slightly
        # modifying) the JSON representation of existing ones
        if superclass is not None:
            inherited_attr_ids = [a.id for a in superclass.all_attributes()]
            for xid in inherited_attr_ids:
                if json_attrs.has_key(xid):
                    # FIXME: raise an error if the attr does not match existing one
                    del(json_attrs[xid])

        attrs = []
        for (attr_id, a) in json_attrs.iteritems():
            if not isinstance(a, dict):
                return HttpResponseBadRequest('Expected a dictionary for '
                                              'representing attribute "%s", got '
                                              '"%s"' % (attr_id, str(a)))
            try:
                attr_type = a['type']
            except KeyError:
                return HttpResponseBadRequest('Attribute "%s" lacks a "type" field'
                                              % (attr_id, ))

            try:
                attr_fn = _kb_dict_attrs_map(attr_type, ses)
            except KeyError:
                return HttpResponseBadRequest(('Attribute "%s" has an invalid '
                                               + 'type: "%s"')
                                              % (attr_id, attr_type))

            # Make a "safe" id, i.e. only composed by ASCII chars
            safe_attr_id = kb_niceid(attr_id, extra_chars=0)

            try:
                attr_obj = attr_fn(safe_attr_id, a, ses, ws)
            except KeyError as e:
                return HttpResponseBadRequest(('Attribute "%s" (type %s) lacks '
                                               + 'a required field: "%s"')
                                              % (attr_id, attr_type, str(e)))
            except ValueError, e:
                return HttpResponseBadRequest('Cannot create attribute "%s": %s'
                                              % (attr_id, str(e)))

            attrs.append(attr_obj)

        if superclass is None:
            cls = ses.orm.KBRootClass(class_name, explicit_id=explicit_id,
                                      attributes=attrs)
            # We also need to configure the visibility of the root class
            # on DAM workspaces
            resp = _setup_kb_root_class_visibility(request, ses, cls, cls_dict,
                                                   ws)

            if resp is not None:
                # An error has occurred
                return resp
        else:
            cls = ses.orm.KBClass(class_name, superclass=superclass,
                                  explicit_id=explicit_id, attributes=attrs)

        # FIXME: right now, we only support updating a few fields
        updatable_fields = {'name'        : set([unicode, str]),
                            'notes'       : set([NoneType, unicode, str])}
        try:
            _assert_update_object_fields(cls, cls_dict, updatable_fields)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        # FIXME: is it necessary to add the new KBClass instance to session?
        # ses.add(cls)

        ses.commit()

        return HttpResponse(cls.id)


@http_basic_auth
@login_required
@permission_required('admin', False)
def class_(request, ws_id, class_id):
    '''
    GET: return a specific class from the knowledge base.
    POST: update an existing class in the knowledge base.
    DELETE: delete and existing class from the knowledge base.
    '''
    return _dispatch(request, {'GET'  : class_get,
                               'POST' : class_post,
                               'DELETE' : class_delete},
                     {'ws_id' : int(ws_id),
                      'class_id' : class_id})


def class_get(request, ws_id, class_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            cls = ses.class_(class_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        return HttpResponse(simplejson.dumps(_kbclass_to_dict(cls, ses)))


def class_post(request, ws_id, class_id):
    try:
        cls_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    if not isinstance(cls_dict, dict):
        return HttpResponseBadRequest('JSON class representation must be '
                                      'a dictionary')

    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            cls = ses.class_(class_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        perm = cls.workspace_permission(ws)
        if perm not in (kb_access.OWNER, kb_access.READ_WRITE):
            return HttpResponseForbidden()

        # If the current workspace doesn't own the class root, then ignore
        # the new workspaces access configuration (if any)
        # FIXME: maybe check whether access rules changed, and raise an err?
        if perm != kb_access.OWNER:
            cls_dict['workspaces'] = _kb_class_visibility_to_dict(cls)

        # In case we're dealing with a root class, also consider its
        # visibility
        if isinstance(cls, ses.orm.KBRootClass):
            resp = _setup_kb_root_class_visibility(request, ses, cls, cls_dict,
                                                   ws)
            if resp is not None:
                # An error has occurred
                return resp

        # FIXME: right now, we only support updating a few fields
        updatable_fields = {'name'        : set([unicode, str]),
                            'notes'       : set([NoneType, unicode, str])}
        try:
            _assert_update_object_fields(cls, cls_dict, updatable_fields)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        # Let's now handle class attribute updates
        attrs_dict = cls_dict.get('attributes')
        client_attrs = set(attrs_dict.keys())
        existing_attrs = set(a.id for a in cls.attributes)
        existing_all_attrs = set(a.id for a in cls.all_attributes())
        
        new_attrs = client_attrs - existing_all_attrs
        removed_attrs = existing_all_attrs - client_attrs
        # Only edit attributes belonging to this class, ignoring its ancestors
        edited_attrs = existing_attrs.intersection(client_attrs)

        print 'new: %s; removed: %s; edited: %s' % (new_attrs, removed_attrs,
                                                    edited_attrs)

        # FIXME: right now, we only support updating a few fields
        updatable_attr_fields = {'name'        : set([unicode, str]),
                                 'notes'       : set([NoneType, unicode, str]),
                                 'order'       : set([int])}
        for attr_id in edited_attrs:
            attr_obj = [a for a in cls.attributes if a.id == attr_id][0]
            try:
                _assert_update_object_fields(attr_obj, attrs_dict[attr_id],
                                             updatable_attr_fields)
            except ValueError as e:
                return HttpResponseBadRequest(str(e))
            ses.add(attr_obj)
        
        # FIXME: here we should handle new_attrs and removed_attrs, too

        ses.add(cls)
        ses.commit()

        return HttpResponse('ok')


def class_delete(request, ws_id, class_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            cls = ses.class_(class_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        perm = cls.workspace_permission(ws)
        if perm not in (kb_access.OWNER, kb_access.READ_WRITE):
            return HttpResponseForbidden()

        try:
            ses.delete(cls)
        except kb_exc.PendingReferences:
            return HttpResponseBadRequest('Cannot delete class referenced from'
                                          ' other KB classes and/or objects')
        ses.commit()

        return HttpResponse('ok')


@http_basic_auth
@login_required
@permission_required('admin', False)
def object_index(request, ws_id):
    '''
    GET: return the list of objects defined in the knowledge base.
    PUT: insert a new object in the knowledge base.
    '''
    return _dispatch(request, {'GET' : object_index_get,
                               'PUT' : object_index_put},
                     {'ws_id' : int(ws_id)})


def object_index_get(request, ws_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        obj_dicts = [_kbobject_to_dict(o, ses) for o in ses.objects(ws=ws)]

        return HttpResponse(simplejson.dumps(obj_dicts))


def object_index_put(request, ws_id):
    try:
        obj_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    if not isinstance(obj_dict, dict):
        return HttpResponseBadRequest('JSON object representation must be '
                                      'a dictionary')

    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        object_class_id = obj_dict.get('class_id', None)
        if object_class_id is None:
            return HttpResponseBadRequest('Object representation lacks a '
                                          +'"class_id" field')

        object_name = obj_dict.get('name', None)
        if object_name is None:
            return HttpResponseBadRequest('Object representation lacks a '
                                          +'"name" field')

        explicit_id = obj_dict.get('id', None)

        if explicit_id is not None:
            # Check for uniqueness
            try:
                ses.object(explicit_id)
                return HttpResponseBadRequest('Object id "%s" already in use'
                                              % (explicit_id, ))
            except kb_exc.NotFound:
                pass

        try:
            cls = ses.class_(object_class_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseBadRequest('Invalid object class: %s'
                                          % (object_class_id, ))

        perm = cls.workspace_permission(ws)
        if perm not in (kb_access.OWNER, kb_access.READ_WRITE,
                        kb_access.READ_WRITE_OBJECTS):
            return HttpResponseForbidden()

        ObjectClass = cls.python_class
        # FIXME: avoid using _rebind_session here!
        obj = ObjectClass(object_name, explicit_id=explicit_id,
                          _rebind_session=ses.session)

        # FIXME: right now, we only support updating a few fields
        updatable_fields = {'name'        : set([unicode, str]),
                            'notes'       : set([NoneType, unicode, str])}

        try:
            _assert_update_object_fields(obj, obj_dict, updatable_fields)
            _assert_update_object_attrs(obj, obj_dict.get('attributes', {}),
                                        ses)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        ses.add(obj)
        ses.commit()

        return HttpResponse(obj.id)


@http_basic_auth
@login_required
@permission_required('admin', False)
def object_(request, ws_id, object_id):
    '''
    GET: return a specific object from the knowledge base.
    POST: update an existing object in the knowledge base.
    DELETE: delete and existing object from the knowledge base.
    '''
    return _dispatch(request, {'GET' :  object_get,
                               'POST' : object_post,
                               'DELETE' : object_delete},
                     {'ws_id' : int(ws_id),
                      'object_id' : object_id})


def object_get(request, ws_id, object_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            obj = ses.object(object_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        return HttpResponse(simplejson.dumps(_kbobject_to_dict(obj, ses)))


def object_post(request, ws_id, object_id):
    try:
        obj_dict = _assert_return_json_data(request)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    if not isinstance(obj_dict, dict):
        return HttpResponseBadRequest('JSON object representation must be '
                                      'a dictionary')

    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            obj = ses.object(object_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        perm = obj.workspace_permission(ws)
        if perm not in (kb_access.OWNER, kb_access.READ_WRITE,
                        kb_access.READ_WRITE_OBJECTS):
            return HttpResponseForbidden()

        # FIXME: right now, we only support updating a few fields
        updatable_fields = {'name'        : set([unicode, str]),
                            'notes'       : set([NoneType, unicode, str])}
        try:
            _assert_update_object_fields(obj, obj_dict, updatable_fields)
            _assert_update_object_attrs(obj, obj_dict.get('attributes', {}),
                                        ses)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        ses.commit()

        return HttpResponse('ok')


def object_delete(request, ws_id, object_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            obj = ses.object(object_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        perm = obj.workspace_permission(ws)
        if perm not in (kb_access.OWNER, kb_access.READ_WRITE,
                        kb_access.READ_WRITE_OBJECTS):
            return HttpResponseForbidden()

        # Before deleting, check whether the object is referenced from
        # the catalog
        dj_obj = DjangoKBObject.objects.get(id=object_id)
        catalog_refs_cnt =TreeviewNode.objects.filter(kb_object=dj_obj).count()
        if catalog_refs_cnt > 0:
            return HttpResponseBadRequest('Cannot delete object referenced '
                                          'from the catalog')

        try:
            ses.delete(obj)
        except kb_exc.PendingReferences:
            return HttpResponseBadRequest('Cannot delete object referenced '
                                          'from other KB objects')
        ses.commit()
        return HttpResponse('ok')


@http_basic_auth
@login_required
@permission_required('admin', False)
def class_objects(request, ws_id, class_id):
    '''
    GET: return the list of objects belonging to a given KB class.
    '''
    return _dispatch(request, {'GET' : class_objects_get},
                     {'ws_id' : int(ws_id),
                      'class_id' : class_id})


def class_objects_get(request, ws_id, class_id):
    with _kb_session() as ses:
        try:
            ws = ses.workspace(ws_id)
        except kb_exc.NotFound:
            return HttpResponseNotFound('Unknown workspace id: %s' % (ws_id, ))

        try:
            cls = ses.class_(class_id, ws=ws)
        except kb_exc.NotFound:
            return HttpResponseNotFound()

        objs = ses.objects(class_=cls.python_class)
        obj_dicts = [_kbobject_to_dict(o, ses) for o in objs]

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

    # FIXME: try to fine-tune the Python garbage collector
    # It seems that, on slow systems, the GC is not triggered frequently
    # enough, and this function in particular makes memory usage grow
    # rapidly.  This temporary fix eases the problem, but it is
    # definitely a workaround.
    import gc
    gc.disable()

    if kwargs is None:
        res = method_fun_dict[method](request)
    else:
        res = method_fun_dict[method](request, **kwargs)

    gc.enable()
    #gc.collect()

    # Remove contextual SQLAlchemy session
    # FIXME: not very clean
    KB_SQLALCHEMY_SCOPED_SESSION_CLS.remove()

    return res



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


# Global KB session, based on NotreDAM DBMS connection parameters
import sqlalchemy, sqlalchemy.orm as sa_orm
KB_SQLALCHEMY_ENGINE = sqlalchemy.create_engine(util.notredam_connstring())
KB_SQLALCHEMY_SESSION_CLS = sa_orm.sessionmaker(bind=KB_SQLALCHEMY_ENGINE,
                                                autoflush=False)
KB_SQLALCHEMY_SCOPED_SESSION_CLS = sa_orm.scoped_session(
    KB_SQLALCHEMY_SESSION_CLS)
KB_SESSION = kb_ses.Session(KB_SQLALCHEMY_SCOPED_SESSION_CLS)
def _kb_session():
    '''
    Create a knowledge base session
    '''
    return KB_SESSION.duplicate(
        sa_orm.scoped_session(KB_SQLALCHEMY_SESSION_CLS))
    

def _kbclass_to_dict(cls, ses):
    '''
    Create a JSON'able dictionary representation of the given KB class
    '''
    clsattrs = {}
    own_attrs = cls.attributes
    for a in cls.all_attributes():
        clsattrs[a.id] = _kbattr_to_dict(a, ses, a not in own_attrs)

    if (cls.superclass.id == cls.id):
        superclass = None
    else:
        superclass = cls.superclass.id

    clsdict = {'id'          : cls.id,
               'name'        : cls.name,
               'superclass'  : superclass,
               'notes'       : cls.notes,
               'attributes'  : clsattrs,
               'workspaces'  : _kb_class_visibility_to_dict(cls, ses),
               'subclasses'  : [c.id for c in cls.descendants(depth=1)]}

    return clsdict


# Return a dictionary describing the access rules of a workspace to
# the given KB class
def _kb_class_visibility_to_dict(cls, ses):
    # Internal mapping from access type to string
    access_str_map = {kb_access.OWNER      : 'owner',
                      kb_access.READ_ONLY  : 'read-only',
                      kb_access.READ_WRITE : 'read-write'}
    # Retrieve the root class
    while cls.superclass is not cls:
        cls = cls.superclass
    assert(isinstance(cls, ses.orm.KBRootClass)) # Just in case...

    vis_dict = {}
    for v in cls.visibility:
        vis_dict[v.workspace.id] = access_str_map[v.access]

    return vis_dict


# Mapping between attribute type and functions returning a JSON'able
# dictionary representation of the attribute itself
def _kb_attrs_dict_map(attr_type, ses, inherited):
    kb_attrs = ses.orm.attributes
    type_dict_map = {kb_attrs.Boolean : lambda a:
                         dict([['type',   'bool'],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.Integer : lambda a:
                         dict([['type',    'int'],
                               ['min',     a.min],
                               ['max',     a.max],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.Real    : lambda a:
                         dict([['type',    'real'],
                               ['min',     a.min],
                               ['max',     a.max],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.String  : lambda a:
                         dict([['type',    'string'],
                               ['length',  a.length],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.Date    : lambda a:
                         dict([['type',    'date'],
                               ['min',     (a.min is not None
                                            and a.min.isoformat()
                                            or None)],
                               ['max',     (a.max is not None
                                            and a.max.isoformat()
                                            or None)],
                               ['default_value', ((a.default is not None)
                                                  and a.default.isoformat()
                                                  or None)]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.Uri  : lambda a:
                         dict([['type',    'uri'],
                               ['length',  a.length],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.Choice  : lambda a:
                         dict([['type',    'choice'],
                               ['choices', simplejson.loads(a.choices)],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.ObjectReference : lambda a:
                         dict([['type',         'objref'],
                               ['target_class', a.target.id]]
                              + _std_attr_fields(a, inherited)),
                     kb_attrs.DateLikeString  : lambda a:
                         dict([['type',    'date-like-string'],
                               ['default_value', a.default]]
                              + _std_attr_fields(a, inherited))
                     }
    return type_dict_map[attr_type]

# Here is the "inverse" of the mapping above: it associates a string
# representing an attribute type with a function which takes the
# attribute JSON representation and returnins the actual Attribute
# object.  The returned function should raise a KeyError when a
# required dictionary field is missing, or a ValueError when the value
# is wrong
def _kb_dict_attrs_map(attr_type_str, ses):
    kb_attrs = ses.orm.attributes
    v = _kb_dict_validate_param # Just a shorthand

    # FIXME: missing checks: max >= min, max =< default =< min
    str_fn_map = {'bool' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.Boolean(id_=attr_id,
                                       default=d.get('default_value'),
                                       **(_std_attr_dict_fields(d))),
                  'int' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.Integer(id_=attr_id,
                                       min_=v(d, 'min', [NoneType, int]),
                                       max_=v(d, 'max', [NoneType, int]),
                                       default=v(d, 'default_value',
                                                 [NoneType, int]),
                                       **(_std_attr_dict_fields(d))),
                  'real' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.Real(id_=attr_id,
                                    min_=v(d, 'min', [NoneType, int, float]),
                                    max_=v(d, 'max', [NoneType, int, float]),
                                    default=v(d, 'default_value',
                                              [NoneType, int, float]),
                                    **(_std_attr_dict_fields(d))),
                  'string' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.String(id_=attr_id,
                                      length=v(d, 'length', [int],
                                               [('> 0', lambda x: x > 0)]),
                                      default=v(d, 'default_value',
                                                [NoneType, unicode, str]),
                                      **(_std_attr_dict_fields(d))),
                  'date' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.Date(id_=attr_id,
                                    min_=v(d, 'min', [NoneType, unicode, str]),
                                    max_=v(d, 'max', [NoneType, unicode, str]),
                                    default=v(d, 'default_value',
                                              [NoneType, unicode, str]),
                                    **(_std_attr_dict_fields(d))),
                  'uri' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.Uri(id_=attr_id,
                                   length=v(d, 'length', [int],
                                            [('> 0', lambda x: x > 0)]),
                                   default=v(d, 'default_value',
                                             [NoneType, unicode, str]),
                                   **(_std_attr_dict_fields(d))),
                  'choice' : _kb_dict_choice_fn,
                  'objref' : _kb_dict_objref_fn,
                  'date-like-string' : lambda attr_id, d, _ses, _ws:
                      kb_attrs.DateLikeString(id_=attr_id,
                                      default=v(d, 'default_value',
                                                [NoneType, unicode, str]),
                                      **(_std_attr_dict_fields(d))),

                  }
    return str_fn_map[attr_type_str]


# Some helper functions for _kb_dict_attr_mapps.  They are defined
# here because they don't need the session parameter.

def _kb_dict_validate_param(d, key, types, checks=[], default=None):
    # Retrieve a key from the given dictionary, ensuring that the
    # value has a type included in the given set, and running the
    # given checks.
    #
    # The checks are tuples with the form (name, fn), where "name" is
    # the descriptive name of the check, and "fn" is a function with
    # arity 1, receiving the value and returning a boolean.
    #
    # The function will return the value, or raise a meaningful
    # ValueError.
    val = d.get(key)

    if val is None and default is not None:
        return default

    val_type = type(val)
    if val_type not in types:
        raise ValueError('parameter "%s": got "%s" (type %s), '
                         'while expecting one of the types: %s'
                         % (key, val, val_type, types))
    for (name, ck) in checks:
        if not ck(val):
            raise ValueError('parameter "%s": validation failed on check: '
                             '"%s"' % (key, name))
    return val

def _kb_dict_choice_fn(attr_id, d, ses, ws):
    kb_attrs = ses.orm.attributes
    choices = d['choices']
    if (not isinstance(choices, list)
        or not all([(isinstance(x, str) or isinstance(x, unicode))
                    for x in choices])):
        raise ValueError('expected list of strings as choices, got "%s"'
                         % unicode(choices))
    return kb_attrs.Choice(id_=attr_id,
                           list_of_choices=choices,
                           default=d.get('default_value'),
                           **(_std_attr_dict_fields(d)))

def _kb_dict_objref_fn(attr_id, d, ses, ws):
    kb_attrs = ses.orm.attributes
    cls_id = d['target_class']
    try: target_class = ses.class_(cls_id, ws=ws)
    except kb_exc.NotFound: raise ValueError('invalid class id: %s'
                                             % (cls_id, ))
    return kb_attrs.ObjectReference(id_=attr_id,
                                    target_class=target_class,
                                    **(_std_attr_dict_fields(d)))


def _kbattr_to_dict(attr, ses, inherited):
    '''
    Create a string representation of a KB class attribute descriptor
    '''
    return _kb_attrs_dict_map(type(attr), ses, inherited)(attr)


def _std_attr_fields(a, inherited):
    '''
    Return the standard fields present in each KB attribute object
    (non-null, notes, etc.)
    '''
    return [['name',        a.name],
            ['maybe_empty', a.maybe_empty],
            ['order',       a.order],
            ['multivalued', a.multivalued],
            ['notes',       a.notes],
            ['inherited',   inherited]]


def _std_attr_dict_fields(d):
    '''
    This is the "inverse" of _std_attr_fields(): return a dictionary
    that, when used as **kwargs, will give a value to the keyword
    arguments common to each Attribute sub-class constructor
    '''
    v = _kb_dict_validate_param # Just a shorthand
    return {'name' : v(d, 'name', [unicode, str],
                       [('length > 0', lambda x: len(x) > 0)]),
            'maybe_empty' : v(d, 'maybe_empty', [bool], default=True),
            'order' : v(d, 'order', [NoneType, int], default=0),
            'multivalued' : v(d, 'multivalued', [bool], default=False),
            'notes' : v(d, 'notes', [NoneType, unicode, str])}


def _kbobject_to_dict(obj, ses):
    '''
    Create a JSON'able dictionary representation of the given KB object
    '''
    objattrs = {}
    for a in getattr(obj, 'class').all_attributes():
        objattrs[a.id] = _kbobjattr_to_dict(a, getattr(obj, a.id), ses)

    objdict = {'id'          : obj.id,
               'name'        : obj.name,
               'class_id'    : getattr(obj, 'class').id,
               'notes'       : obj.notes,
               'attributes'  : objattrs}

    return objdict


# Mapping between object attribute type and functions returning a
# JSON'able dictionary representation of the attribute value
def _kb_objattrs_dict_map(attr_type, ses):
    def _std_dict_fn(attr, val):
        if attr.multivalued: return [v for v in val]
        else: return val
    def _date_dict_fn(attr, val):
        if attr.multivalued: return [v.isoformat() for v in val]
        else: return (val is not None and val.isoformat()) or None
    def _objref_dict_fn(attr, val):
        if attr.multivalued: return [v.id for v in val]
        else: return (val is not None and val.id or None)

    kb_attrs = ses.orm.attributes
    type_fn_map = {kb_attrs.Boolean : _std_dict_fn,
                   kb_attrs.Integer : _std_dict_fn,
                   kb_attrs.Real    : _std_dict_fn,
                   kb_attrs.String  : _std_dict_fn,
                   kb_attrs.Date    : _date_dict_fn,
                   kb_attrs.String  : _std_dict_fn,
                   kb_attrs.Uri     : _std_dict_fn,
                   kb_attrs.Choice  : _std_dict_fn,
                   kb_attrs.ObjectReference: _objref_dict_fn,
                   kb_attrs.DateLikeString : _std_dict_fn
                   }
    return type_fn_map[attr_type]

def _kbobjattr_to_dict(attr, val, ses):
    '''
    Create a string representation of a KB class attribute descriptor
    '''
    return _kb_objattrs_dict_map(type(attr), ses)(attr, val)


import re
_content_type_re = re.compile('application/json; *charset=UTF-8',
                              re.IGNORECASE)
def _assert_return_json_data(request):
    '''
    Ensure that a Django request contains JSON data, and return it
    (taking care of its encoding).  Raise a ValueError if the content
    type is not supported.
    '''
    if (_content_type_re.match(request.META['CONTENT_TYPE'])):
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


def _assert_update_object_attrs(obj, obj_dict, ses):
    '''
    Almost like _assert_update_object_fields(), but applied to KB
    object attribute (i.e. with special care for object references and
    other "complex" types).
    '''
    kb_attrs = ses.orm.attributes

    obj_class_attrs = getattr(obj, 'class').all_attributes()
    for a in obj_class_attrs:
        val = obj_dict.get(a.id, getattr(obj, a.id))
        try:
            if a.multivalued:
                # We expect 'val' to be a list
                if not isinstance(val, list):
                    raise ValueError('Expected a list of values for '
                                     'multi-valued attribute, got "%s"'
                                     % (val, ))
                if (not a.maybe_empty) and (len(val) == 0):
                    raise ValueError('Got an empty list of values for '
                                     'an attribute which must not be empty')
                # Let's remove all the list elements.  We'll later
                # re-add them
                obj_l = getattr(obj, a.id)

                if (type(a) == kb_attrs.ObjectReference):
                    # We need to retrieve the referred objects by
                    # their ID, in order to spot errors.
                    
                    # Determine new objects
                    new_obj_lst = []
                    for xid in [x for x in val]:
                        try:
                            new_obj_lst.append(ses.object(xid))
                        except kb_exc.NotFound:
                            raise ValueError('Unknown object id reference: %s'
                                             % xid)
                    val = new_obj_lst

                # Time to re-add the elements to the list
                for _i in range(0, len(obj_l)):
                    obj_l.pop() # Cleanup old list
                for x in val:
                    obj_l.append(x)
            else: # not a.multivalued
                if type(a) == kb_attrs.ObjectReference:
                    # We can't simply update the attribute: we need to
                    # retrieve the referred object by its ID
                    curr_obj_id = getattr(obj, a.id)
                    if (val == curr_obj_id):
                        # Nothing to be done here
                        break
                    else:
                        try:
                            new_obj = ses.object(val)
                        except kb_exc.NotFound:
                            raise ValueError('Unknown object id reference: %s'
                                             % val)
                    # Actually perform the assignment
                    setattr(obj, a.id, new_obj)
                else:
                    # Simple case: just update the attribute
                    setattr(obj, a.id, val)
        except kb_exc.ValidationError, e:
            # One of the setattr() calls failed: re-raise the
            # exception with the proper error message
            raise ValueError(u'Error updating attribute "%s": %s'
                             % (a.id, unicode(e.parameter)))


# Configure the workspace visibility of the given KBRootClass (cls,
# with JSON'able representation cls_dict), using the given request and
# KB session.  'curr_ws' is the current workspace (which should appear
# among the class owners).  Return a HttpResponse object on failure,
# or None in case of success
def _setup_kb_root_class_visibility(request, ses, cls, cls_dict, curr_ws):
    cls_workspaces_dict = cls_dict.get('workspaces', None)
    if cls_workspaces_dict is None:
        return HttpResponseBadRequest('Root class representation lacks a '
                                      +'"workspaces" field')

    user = request.user

    # Retrieve all the workspace IDs we could actually work on
    # FIXME: with_permissions() seems broken
    # from dam.workspace.models import DAMWorkspace as WS
    # usr_ws_ids = [w.id
    #              for w in WS.permissions.with_permissions(request.user,
    #                                                       ('admin', ))]
    adm_ws = [w for w in user.workspaces.all()
              if w.has_permission(user, 'admin')]
    adm_ws_ids = [w.id for w in adm_ws]
    
    owner_ws_list = []  # List of owner workspaces
    ws_list = []
    for (ws_id, access_str) in cls_workspaces_dict.items():
        try:
            ws_id = int(ws_id)
        except ValueError:
            return HttpResponseBadRequest(('Workspace id "%s" does not appear '
                                           + 'to be an integer') % (ws_id, ))

        if ws_id not in adm_ws_ids:
            return HttpResponseBadRequest(('Current user "%s" cannot share '
                                           + 'classes on workspace %s')
                                          % (request.user.username, ws_id ))
        
        # Since we have the permissions to handle ws_id, the following
        # call should always succeed (unless something really wrong is
        # going on, and thus we let exceptions propagate)
        ws = ses.workspace(ws_id)
        
        ws_list.append(ws)
        
        # Translate the user-provided access string into a workspace
        # permission.  NOTE: this mapping MUST respect the one used in
        # _kb_class_visibility_to_dict()
        if (access_str == 'owner'):
            owner_ws_list.append(ws)
            access = kb_access.OWNER
        elif (access_str == 'read-only'):
            access = kb_access.READ_ONLY
        elif (access_str == 'read-write'):
            access = kb_access.READ_WRITE
        else:
            return HttpResponseBadRequest('Invalid permission for '
                                          'workspace %s: "%s"'
                                          % (ws_id, access_str))
        
        # Everything seems to be fine, let's share the class on
        # the given workspace(s)
        cls.setup_workspace(ws, access=access)
        
    # Also ensure that the current workspace is among the owners
    if curr_ws not in owner_ws_list:
        return HttpResponseBadRequest(('Root class representation does not'
                                       + ' report the current workspace (%d)'
                                       + ' as owner') % (ws_id, ))
        
    # Finally, remove the workspace visibilities which were not
    # mentioned in the class dictionary
    cls.restrict_to_workspaces(ws_list)

    # Everything is fine
    return None
