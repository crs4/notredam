#########################################################################
#
# NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
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

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.template import RequestContext, Context, loader
from django.contrib.contenttypes.models import ContentType

from dam.treeview.models import Node,  NodeMetadataAssociation,  SmartFolder,  SmartFolderNodeAssociation,  SiblingsWithSameLabel
from dam.core.dam_workspace.decorators import permission_required, membership_required
from dam.metadata.models import MetadataProperty,  MetadataValue
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item, Component
from dam.core.dam_repository.models import Type
from dam.kb.models import Object as KBObject

from django.utils import simplejson

import cPickle as pickle
import logging
logger = logging.getLogger('dam')

# Allowed values for the 'cls' field in JSON repr of catalog nodes
valid_object_node_classes = ('object-keyword', 'object-category')

@login_required
@permission_required('edit_taxonomy')
def move_node(request):
    """
    Moves a node to another parent
    """
    node_source = Node.objects.get(pk = request.POST['node_id'])
    node_dest = Node.objects.get(pk = request.POST['dest'])
    workspace = request.session['workspace']
    
    node_source.move_node(node_dest, workspace)
    
    response = simplejson.dumps({'success': True})
    return HttpResponse(response)
        
@permission_required('edit_collection')    
def rename_collection(request,  node, label, workspace):
    node.rename_node(label, workspace)
        
@login_required
def edit_node(request):
    """
    Edits the given nodes
    """
    workspace = request.session['workspace']
    user = User.objects.get(pk=request.session['_auth_user_id'])
    try:
        nodes= Node.objects.filter(pk__in = request.POST.getlist('node_id'))
    #    node =  Node.objects.getli(pk = request.POST['node_id'])
        label = request.POST.get('label')
        resp = {'success':True}
        for node in nodes:
            if node.type == 'keyword':
                node.edit_node(label, request.POST.getlist('metadata'), request.POST.get('add_metadata_parent',  False),  workspace, request.POST.get('kb_object',  False), request.POST.get('cls',  False), request.POST.get('representative_item', None))
                
            elif node.type == 'collection':
                rename_collection(request, node, label, workspace)
            else:
                resp = {'success': False}
        resp = simplejson.dumps(resp)
        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

@permission_required('edit_taxonomy')
def _add_keyword(request, node, label, workspace):
    metadata_schemas = request.POST.getlist('metadata')
    cls  = request.POST.get('cls')

    # Ensure that metadata mappings are only provided for 'keyword' nodes
    # FIXME: it's kludgy, heavy code refactoring would be advisable
    assert((metadata_schemas == []) or (cls == 'keyword'))

    obj = None
    if (cls in valid_object_node_classes):
        # The KB object name will override the label
        # FIXME: check that the provided label is equal to obj name?
        obj = KBObject.objects.get(id=request.POST['kb_object'])
        label = obj.name

    repr_item_id = request.POST.get('representative_item', None)
    if repr_item_id is not None:
        representative_item = Item.objects.get(pk=repr_item_id)
    else:
        representative_item = None

    node = Node.objects.add_node(node, label, workspace, cls, request.POST.get('add_metadata_parent', False), kb_object=obj, representative_item=None)

    # Just to trigger possible errors
    node.set_representative_item(representative_item)

    node.save_metadata_mapping(metadata_schemas)
    
    return node
    
@permission_required('edit_collection')
def _add_collection(request, node,  label,  workspace): 
    return Node.objects.add_node(node, label, workspace)

@login_required
def add(request = None,  workspace = None,  name = None, parent_id = None,
        representative_item = None):
    """
    Adds a new node to an existing one
    """
    if request:
        workspace = request.session['workspace']
        name = request.POST.get('name',  request.POST['label'])
        parent_id = request.POST['node_id']

    node  = Node.objects.get(pk = parent_id) 
    try:
        if node.type == 'keyword':
            new_node= _add_keyword(request, node,  name,  workspace)    
        else:
            new_node= _add_collection(request, node,  name,  workspace)    
    except SiblingsWithSameLabel, ex:        
        logger.exception(ex)
        resp = simplejson.dumps({'success':False,'errors': {'label': 'parent node has already a child with the given label'}})
        return HttpResponse(resp)
    except Exception, ex:
        logger.exception(ex)
        raise

    resp = simplejson.dumps({'success':True,'node_id':new_node.id})
    return HttpResponse(resp)
    
@permission_required('remove_collection')
def _delete_collection(request, node):
    node.delete()
    
@permission_required('edit_taxonomy')
def _delete_keyword(request,  node):
    n_as = NodeMetadataAssociation.objects.filter(node = node)
    for item in node.items.all():
        for n_a in n_as:
            MetadataValue.objects.filter(item = item, schema = n_a.metadata_schema, value = n_a.value).delete()
    node.delete()    
    
@login_required
def delete(request):
    """
    Deletes an existing node
    """
    node = Node.objects.get(pk = int(request.POST['node_id']))
    if node.type == 'collection':
        _delete_collection(request, node)
    elif node.type == 'keyword':
       _delete_keyword(request, node)
    resp = simplejson.dumps({'success':True})
    return HttpResponse(resp)
    
@permission_required('edit_metadata')
def _save__keyword_association(request, node, items):
    node.save_keyword_association(items)
    
@permission_required('edit_collection')
def _save__collection_association(request, node, items):
    node.save_collection_association(items)
    
@login_required
def save_association(request):
    """
    Saves association between the given items and node
    """
    items = request.POST.getlist('items')

    node= request.POST['node']
    
    node= Node.objects.get(pk = node)    
    
    if node.type == 'keyword':
        _save__keyword_association(request, node, items)
    
    elif node.type == 'collection':
        _save__collection_association(request, node, items)
        
    resp = simplejson.dumps({'success': True, 'errors': []})
        
    return HttpResponse(resp)    

def _get_representative_url(representative_item_pk, workspace):
    component_list = Component.objects.filter(item__pk = representative_item_pk, workspace = workspace)
    for c in component_list:
        if c.get_variant().name == "thumbnail":
            return c.get_url()

def get_representative_url(request):
    workspace = request.session['workspace']
    representative_item = request.POST.get('representative_item', None)
    try:
        if representative_item:
            return HttpResponse(_get_representative_url(long(representative_item), workspace))
    except:
        print "EXCEPTIUO"
        return None

def get_nodes(request):
    """
    Retrieves the requested nodes
    """
    workspace = request.session['workspace']
    node_id = request.POST.get('node',  'root')
    last_added = request.POST.get('last_added')
    child = request.POST.get('child')
    user = User.objects.get(pk=request.session['_auth_user_id'])
    items = request.POST.getlist('items')
    logger.debug('items %s'%items)
    try:
        items.remove('')
    except:
        pass
   
    if node_id == 'root':
        node = Node.objects.get_root(workspace, type = 'keyword')
    else:
        node = Node.objects.get(pk = node_id)
#    nodes = node.get_branch(depth=1).exclude(pk = node.pk)
    nodes = node.children.all().extra(select={'leaf': 'rgt-lft=1'})
#    if last_added:
#        nodes = [nodes[nodes.count()-1]]
    
    if node.type == 'inbox':
        nodes = nodes.order_by('-creation_date')
    
    if child:
        nodes = [nodes.get(label = child)]

#        getting number of items  
#    if node.type == 'keyword':
#        nodes = nodes.extra(select={'n_items': "select count(distinct metadata_metadata.object_id) from metadata_metadata where metadata_metadata.value in (select node2.label from node as node2 where lft between node.lft and node.rgt )"})
    result = []
    if node.type == 'keyword':
        can_edit = workspace.has_permission(user, 'edit_taxonomy')
    else:
        can_edit = workspace.has_permission(user, 'edit_collection')

    for n in nodes:
        if (n.cls == 'object-category'):
            allowDrag = False
            editable = True
            n.is_drop_target = True
            allowDrop = True
        elif (n.cls == 'object-keyword'):
            allowDrag = True
            editable = True
            n.is_drop_target = True
            allowDrop = True
        elif can_edit:
            allowDrag = n.is_draggable
            editable = n.editable
            allowDrop = n.is_drop_target
        else:
            allowDrag = False
            editable = False
            allowDrop = n.is_drop_target

        tmp = {'text' : n.label,  'id':n.id, 'leaf': n.leaf,  'allowDrag':allowDrag,  'allowDrop': allowDrop,  'editable': editable,  'type': n.type, 'iconCls': n.cls,'isCategory': n.cls == 'category', 'isNewKeywords': n.cls == 'new_keyword',  'isNoKeyword': n.cls == 'no_keyword', 'uiProvider': 'MyNodeUI', }
        
        if n.type == 'keyword':
            tmp['add_metadata_parent'] = n.associate_ancestors        
        if n.cls == 'object-category':
            tmp['isCategory'] = True

        if n.cls != 'object-category' and n.cls != 'category' and n.cls != 'new_keyword' and n.cls!= 'no_keyword' and n.type != 'inbox' :
            n_items = n.items.filter(pk__in = items) 
            n_items_count = n_items.count()
            tmp['checked'] =  n_items_count > 0
            if len(items) > 1 and n_items_count > 0 and  n_items_count< len(items) :
                tmp['tristate'] = True
                tmp['items'] = [item.pk for item in n_items]

        if n.representative_item:
            tmp['representative_item'] = _get_representative_url(n.representative_item.pk, workspace)
        else:
            tmp['representative_item'] = None

        result.append(tmp)
    return HttpResponse(simplejson.dumps(result))
    
@permission_required('edit_metadata')
def _remove_keyword_association(request,  node,  items):
    node.remove_keyword_association(items)
    
@permission_required('edit_collection')
def _remove_collection_association(request,  node,  items):
    node.remove_collection_association(items)

@login_required
def remove_association(request):
    items = request.POST.getlist('items')
    items_commas = items[0].split(',')

    if len(items_commas) > 1:
        items = items_commas

    node= request.POST['node']
    
    node= Node.objects.get(pk = node)
    if node.type == 'keyword':
        _remove_keyword_association(request,  node,  items)
    
    elif node.type == 'collection':
        _remove_collection_association(request,  node,  items)        
        
    resp = simplejson.dumps({'success': True, 'errors': []})
        
    return HttpResponse(resp)

def get_metadataschema_keyword_target(request):
    node_id = request.POST.getlist('node_id')
    node = Node.objects.filter(pk__in = node_id).exclude(cls = 'category')
    schemas = MetadataProperty.objects.filter(keyword_target = True)
    resp = {'metadataschema': []}
    for schema in schemas:
#        selected = node.metadata_schema.filter(pk = schema.pk).count() > 0
#        selected = schema.node_set.filter(pk__in = node_id).count() > 0
        node_association = NodeMetadataAssociation.objects.filter(node__pk__in = node_id,  metadata_schema = schema)
        if node_association.count() > 0:
            selected = True
            
        if node_association.count() == 1:
            value = node_association[0].value
        else:
            selected = False
            value = ''
        resp['metadataschema'].append({'pk': schema.pk,  'name': '%s:%s'%(schema.namespace.prefix, schema.field_name), 'selected': selected,  'value':value})
        
    return HttpResponse(simplejson.dumps(resp))

def _get_item_nodes(items):
    item_ids = ','.join([ i for i in items])
    query = 'select count(*) from node_items where node_items.node_id = node.id and item_id in (%s)'%item_ids
    nodes = Node.objects.filter(items__pk__in = items).extra({'count': query})

    return nodes

@login_required    
def get_item_nodes(request):
    items = request.POST.getlist('items')
    nodes = _get_item_nodes(items)
    resp = {'nodes': []}
    for node in nodes:
        node_info = {'id': node.id,  'type': node.type}
        node_items = node.items.all()
        if node.count < len(items) and (node.type == 'keyword' or node.type == 'collection'):
            node_info['tristate'] = True
            node_info['items'] = [item.pk for item in node_items]
            
        resp['nodes'].append(node_info)    

    
    return HttpResponse(simplejson.dumps(resp))

@login_required
def save_smart_folder(request):
    workspace = request.session['workspace']
    label = request.POST.get('label')
    smart_folder_id= request.POST.get('smart_folder_id')

    if smart_folder_id:
        sm_fold = SmartFolder.objects.get(pk= smart_folder_id)
        if(request.POST.get('only_label_edit')):
            sm_fold.label = label            
    else:
        sm_fold = SmartFolder(label = label,  workspace = workspace)
    
    if request.POST['condition']== 'and':
        sm_fold.and_condition = True
    else:
        sm_fold.and_condition = False

    sm_fold.save()
    
    if(request.POST.get('only_label_edit') is None):
        SmartFolderNodeAssociation.objects.filter(smart_folder = sm_fold).delete()
        node_ids = request.POST.get('node_id')
        node_ids = simplejson.loads(node_ids)
        for node_id in node_ids:
            sm_ass = SmartFolderNodeAssociation.objects.create(smart_folder = sm_fold,  node = Node.objects.get(pk = node_id['pk']),  negated= node_id['negated'])
    
    return HttpResponse(simplejson.dumps({'success': True}))
    
@login_required
def get_smart_folders(request):
    workspace = request.session['workspace']
    sm_fold = SmartFolder.objects.filter(workspace = workspace)
    resp = {'smart_folders': []}
    for folder in sm_fold:
        if folder.and_condition:
            condition = 'and'
        else:
            condition = 'or'
        resp['smart_folders'].append({'pk': folder.pk,  'label': folder.label,  'condition':condition})
    
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_query_smart_folder(request):
    node_id = request.POST['pk']
    sm_fold = SmartFolder.objects.get(pk = node_id)
    sm_ass = SmartFolderNodeAssociation.objects.filter(smart_folder = sm_fold)
    resp = {'queries':[]}
    for query in sm_ass:
        resp['queries'].append({'pk': query.node.pk,  'label': query.node.label,  'negated': query.negated,  'path': query.node.get_path()})
    
    return HttpResponse(simplejson.dumps(resp))
    

@login_required
def delete_smart_folder(request):
    smart_folder_id = request.POST['smart_folder_id']
    sm_fold = SmartFolder.objects.get(pk = smart_folder_id)
    sm_fold.delete()
    return HttpResponse(simplejson.dumps({'success': True}))
