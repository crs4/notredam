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

from django.contrib.auth.decorators import login_required
from django.http import (HttpRequest, HttpResponse, HttpResponseNotFound,
                         HttpResponseNotAllowed, HttpResponseBadRequest)
from django.utils import simplejson
import tinykb.session as kb_ses
import tinykb.errors as kb_exc
import util
from dam.core.dam_workspace.models import WorkspacePermission, WorkspacePermissionsGroup, WorkspacePermissionAssociation
from dam.workspace.models import DAMWorkspace as Workspace
import dam.kb.views as views_kb
import dam.treeview.views as tree_view
from dam.treeview.models import Node
from django.contrib.auth.models import User


import logging
logger = logging.getLogger('dam')

def _get_root_tree(request,ws_id):
    result = []
    spr = []    

    cls_dicts = views_kb.class_index_get(request, ws_id)
    cls_dicts = simplejson.loads(cls_dicts.content)   

    for n in cls_dicts:
        if not n['superclass']:
            tmp = {'text' : n['name'],  
               'id': n['id'], 
               'leaf': False,
               'iconCls' : 'object-class',
            }  
            result.append(tmp)
    
    return result 

def _get_child_cls_obj(request,ws_id, parent):

    result = []
    spr = []
    try:
        cls_dicts = views_kb.class_index_get(request, ws_id)
        cls_dicts = simplejson.loads(cls_dicts.content)   
        for n in cls_dicts:
            if n['superclass']:
                spr.append({'namesuper':n['superclass']}) 
            if parent.lower() == n['superclass']:
                tmp = {'text' : n['name'],  
                       'id': n['id'], 
                       'leaf': False,
                       'iconCls' : 'object-class',

                    }  
                result.append(tmp)
        logger.debug("class result")
        logger.debug(result)
    except Exception, ex:
        logger.debug(ex)

    obj_dicts = views_kb.object_index_get(request, ws_id)
    obj_dicts = simplejson.loads(obj_dicts.content)   
    for o in obj_dicts:
        if parent.lower() == o['class_id'].lower():
            tmp = {'text' : o['name'],  
                   'id': o['id'], 
                   'leaf': True,
                }  
            result.append(tmp)
    
    logger.info("result---:  %s" %result)
            
    return result

@login_required
def get_nodes_real_obj(request):
    '''
    Views to return data to viewstree.
    treeloader needs :
    [{
        id: 1,
        text: 'A leaf Node',
        leaf: true
    },{
        id: 2,
        text: 'A folder Node',
        children: [{
            id: 3,
            text: 'A child Node',
            leaf: true
        }]
   }]
    '''
    parent = request.POST.get('node',  'root')
    if parent == 'root_obj_tree':
        result = _get_root_tree(request,request.session['workspace'].pk)
    else:
        result = _get_child_cls_obj(request,request.session['workspace'].pk, parent)

    return HttpResponse(simplejson.dumps(result))

def _add_attribute(name, value, groupname):
    
    tmp = {'name'       :name,
           'value'      :value,
           'groupname'  :groupname
          }
    return tmp

def _put_attributes(cls_obj, rtr):
    rtr['rows'].append(_add_attribute('notes', cls_obj['notes'],cls_obj['name']))
    for c in cls_obj['attributes']:
        tmp = _add_attribute(c,cls_obj['attributes'][c],cls_obj['name'])
        rtr['rows'].append(tmp)

def get_specific_info_obj(request, obj_id):
    ses = views_kb._kb_session()
    ws = ses.workspace(request.session['workspace'].pk)
    cls = ses.object(obj_id, ws=ws)
    rtr = {"rows":[]}
    rtr['rows'].append(views_kb._kbobject_to_dict(cls, ses))
    resp = simplejson.dumps(rtr)
    return HttpResponse(resp)

def get_object_attributes_hierarchy(request):
    nodes = tree_view._get_item_nodes(request.POST.getlist('items'))
    ses = views_kb._kb_session()
    rtr = {"rows":[]}
    for node in nodes:
        n = Node.objects.get(pk = node.id)
        while n.parent_id:
            if n.kb_object_id:
                cls = views_kb._kbobject_to_dict(ses.object(n.kb_object_id), ses)
                _put_attributes(cls,rtr)
            n = Node.objects.get(pk = n.parent_id)
    logger.debug(rtr)
    resp = simplejson.dumps(rtr)
    
    return HttpResponse(resp)

def get_object_attributes(request):

    class_id = request.POST.getlist('class_id')[0]
    obj_id = request.POST.getlist('obj_id')[0]
    if (obj_id):
        cls_obj = views_kb.object_get(request, request.session['workspace'].pk,obj_id)
        cls_obj = simplejson.loads(cls_obj.content)
    cls_dicts = views_kb.class_get(request, request.session['workspace'].pk,class_id)
    cls_dicts = simplejson.loads(cls_dicts.content) 
    rtr = {"rows":[]}
    for attribute in cls_dicts['attributes']:
        tmp = {}
        tmp['id'] = attribute
        if (obj_id):
            tmp['value'] = cls_obj['attributes'][attribute]
        else:
            tmp['value'] = None
        for specific_field in cls_dicts['attributes'][attribute]:
            tmp[specific_field] = cls_dicts['attributes'][attribute][specific_field]
        rtr['rows'].append(tmp)
    resp = simplejson.dumps(rtr)
    
    return HttpResponse(resp)

def get_class_attributes(request, class_id):
    cls_dicts = views_kb.class_get(request, request.session['workspace'].pk,class_id)
    cls_dicts = simplejson.loads(cls_dicts.content) 
    rtr = {"rows":[]}
    for attribute in cls_dicts['attributes']:
        tmp = {}
        tmp['id'] = attribute
        for specific_field in cls_dicts['attributes'][attribute]:
            tmp[specific_field] = cls_dicts['attributes'][attribute][specific_field]
        rtr['rows'].append(tmp)
    resp = simplejson.dumps(rtr)
    return HttpResponse(resp)
    
    
def get_specific_info_class(request, class_id):
    cls_dicts = views_kb.class_get(request, request.session['workspace'].pk,class_id)
    cls_dicts = simplejson.loads(cls_dicts.content) 
    rtr = {"rows":[]}
    rtr['rows'].append(cls_dicts)
    resp = simplejson.dumps(rtr)
    return HttpResponse(resp)

def get_workspaces_with_edit_vocabulary(request):
# return all ws for specific user where user can edit vocabulary.    
    user = User.objects.get(pk=request.session['_auth_user_id'])

    wp = WorkspacePermission.objects.get(name= 'edit vocabulary')

    ws_all = Workspace.objects.all()
    rtr = {"workspaces":[]}
    for ws in ws_all:
        ws_tmp = {}
        if (ws.has_permission(user, 'edit_vocabulary')):
            ws_tmp = {
                'pk': ws.pk,
                'name': ws.name,
                'description': ws.description
            }
            rtr['workspaces'].append(ws_tmp)
        
    return HttpResponse(simplejson.dumps(rtr))    