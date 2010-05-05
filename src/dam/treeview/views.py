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

from dam.treeview.models import Node,  NodeMetadataAssociation,  SmartFolder,  SmartFolderNodeAssociation
from dam.workspace.decorators import permission_required, membership_required
from dam.metadata.models import MetadataProperty,  MetadataValue
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item, Component
from dam.framework.dam_repository.models import Type

from django.utils import simplejson

import cPickle as pickle
import logger


class InvalidNode(Exception):
    pass

class NotEditableNode(Exception):
    pass

class WrongWorkspace(Exception):
    pass
    
class NotMovableNode(Exception):
    pass

class SiblingsWithSameLabel(Exception):
    pass
    
def _check_ws(ws,  node):
    if node.workspace != ws:
        raise WrongWorkspace

@login_required
@permission_required('edit_taxonomy')
def move_node(request):
    node_source = Node.objects.get(pk = request.POST['node_id'])
    node_dest = Node.objects.get(pk = request.POST['dest'])
    
    logger.debug('node_source  %s'%node_source )
    logger.debug('node_dest %s'%node_dest )
    
    workspace = request.session['workspace']
    _move_node(node_source ,  node_dest,  workspace)    
    response = simplejson.dumps({'success': True})
    return HttpResponse(response)
    
def _move_node(node_source ,  node_dest,  workspace):
    if not node_source.parent :
        raise InvalidNode
    
#    TODO: check move parent to children
    if node_source.workspace != node_dest.workspace or node_source.workspace  != workspace or node_dest.workspace  != workspace :
        raise WrongWorkspace
    
#    if node_source.depth <= 2:
#        raise NotEditableNode
    node_source.parent = node_dest
    node_source.depth = node_dest.depth+1
    node_source.save()      
#    Node.objects.get_root(workspace).rebuild_tree(1)
    

@permission_required('edit_taxonomy')    
def rename_keyword(request,  node, label, workspace):
    for item in node.items.all():
        metadata = item.metadata.filter(schema__keyword_target = True,  value = node.label)
        for m in metadata:
            m.value = label
            m.save()
    if label:
        _rename_node(node, label, workspace)
    
@permission_required('edit_collection')    
def rename_collection(request,  node, label, workspace):
    _rename_node(node, label, workspace)

def _rename_node(node, label, workspace):
#    if not node.parent:
#        raise InvalidNode
    if not node.editable:
        raise NotEditableNode
    _check_ws(workspace,  node)
    node.label = label
    node.save()

def _save_metadata_mapping(node, metadata_schemas,):
    logger.debug('metadata_schemas %s'%metadata_schemas)        
    node_associations_to_delete = NodeMetadataAssociation.objects.filter(node = node)
   
    
    
    for item in node.items.all():
        for n_a in node_associations_to_delete:
            metadata = item.metadata.filter(schema = n_a.metadata_schema,  value = n_a.value)
            logger.debug('metadata %s'%metadata)
            logger.debug('metadata[0].value %s'%metadata[0].value)
            if metadata.count() >0:
                metadata[0].delete()
                
    node_associations_to_delete.delete()
    for ms in metadata_schemas:
        if not isinstance(ms,  dict):
            ms = simplejson.loads(ms)
        NodeMetadataAssociation.objects.create(node = node,  value = ms['value'],  metadata_schema = MetadataProperty.objects.get(pk = ms['id']))
#    node.metadata_schema.add(*MetadataProperty.objects.filter(pk__in = metadata_schemas))


def _edit_node(node,  label,  metadata_schemas, associate_ancestors,  workspace ):
    if label :
        _rename_node(node, label, workspace)
    
    if node.cls != 'category':
        if metadata_schemas:
            _save_metadata_mapping(node, metadata_schemas)        
            _save_metadata(node,  node.items.all())
        
        node.associate_ancestors = associate_ancestors
        logger.debug('node.associate_ancestors %s'%node.associate_ancestors)
        node.save();


@login_required
def edit_node(request):
    logger.debug('edit_node')
    workspace = request.session['workspace']
    try:
        nodes= Node.objects.filter(pk__in = request.POST.getlist('node_id'))
    #    node =  Node.objects.getli(pk = request.POST['node_id'])
        label = request.POST.get('label')
        resp = {'success':True}
        for node in nodes:
            if node.type == 'keyword':
                _edit_node(node,  label,  request.POST.getlist('metadata'), request.POST.get('add_metadata_parent',  False),  workspace)
                
                
            elif node.type == 'collection':
                rename_collection(request,  node, label, workspace)
            else:
                    resp = {'success': False}
            
        resp = simplejson.dumps(resp)
        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

@permission_required('edit_taxonomy')
def add_keyword(request, node,  label,  workspace):
    logger.debug('add_keyword')
    metadata_schemas = request.POST.getlist('metadata')
    cls  = request.POST.get('cls')
    node = _add_node(node,  label,  workspace,  cls,  request.POST.get('add_metadata_parent',  False))
    _save_metadata_mapping(node, metadata_schemas)
    
    return node
    
@permission_required('edit_collection')
def add_collection(request, node,  label,  workspace):
    logger.debug('add_collection')
    return _add_node(node,  label,  workspace)


def _add_node(node,  label,  workspace,  cls = 'collection',  associate_ancestors = None):
#    if not node.parent:
#        raise InvalidNode
        
    _check_ws(workspace,  node)

    logger.debug('label %s'%label)    
    if node.children.filter(label = label).count():
        raise SiblingsWithSameLabel
    logger.debug('node.cls %s'%node.cls)

#    if node.type == 'keyword':
#        cls = 'keyword'
#    else:
#        cls = node.cls
        
    new_node = Node.objects.create(workspace= workspace, label = label,  type = node.type)
    if cls:
        new_node.cls = cls
    
    if associate_ancestors:
        new_node.associate_ancestors = associate_ancestors
  
    
    new_node.parent = node
    new_node.depth = (node.depth)+1
    new_node.count = 0
    new_node.save()   
    
#    Node.objects.get_root(workspace).rebuild_tree(1)
    return new_node

@login_required
def add(request = None,  workspace = None,  name = None, parent_id = None):
    if request:
        workspace = request.session['workspace']
        name = request.POST.get('name',  request.POST['label'])    
        parent_id = request.POST['node_id']
    logger.debug('workspace %s'%workspace)
    node  = Node.objects.get(pk = parent_id) 
    logger.debug('node.workspace %s'%node.workspace)
    logger.debug('node.type %s'%node.type)
    try:
        if node.type == 'keyword':
            new_node= add_keyword(request, node,  name,  workspace)    
        else:
            new_node= add_collection(request, node,  name,  workspace)    
    except SiblingsWithSameLabel, ex:        
        logger.exception(ex)
        resp = simplejson.dumps({'success':False,'errors': {'label': 'parent node has already a child with the given label'}})
        return HttpResponse(resp)
    except:
        raise
    resp = simplejson.dumps({'success':True,'node_id':new_node.id})
    return HttpResponse(resp)
    
@login_required
def delete(request):
    node = Node.objects.get(pk = int(request.POST['node_id']))
    if node.type == 'collection':
        _delete_collection(request,node)
    elif node.type == 'keyword':    
       _delete_keyword(request, node)
    resp = simplejson.dumps({'success':True})
    return HttpResponse(resp)
    

@permission_required('remove_collection')
def _delete_collection(request, node):  
    node.delete()
    
@permission_required('edit_taxonomy')
def _delete_keyword(request,  node):  
    n_as = NodeMetadataAssociation.objects.filter(node = node)
    for item in node.items.all():
        for n_a in n_as:
            MetadataValue.objects.filter(item = item,  schema = n_a.metadata_schema,  value = n_a.value).delete()
    node.delete()

@login_required
def edit(request, node_id, node_type):
   if node_type== 'keyword' or node_type== 'category':
        return _edit_keyword(request, node_id, node_type)
   else:
        return _edit_collection(request, node_id, node_type)
    
@permission_required('edit_metadata')
def save__keyword_association(request, node, items):
    _save__keyword_association( node, items)
    
def _save__keyword_association( node, items):    
    items = Item.objects.filter(pk__in = items)
    if node.associate_ancestors:
        nodes = node.get_ancestors().filter(depth__gt = 0)      
    else:
        nodes = [node]
        
    for n in nodes:
        if n.cls != 'category':
            n.items.add(*items)
        _save_metadata(n,  items)
    

def _remove_metadata(node,  items):
    
    for item in items: 
        schema = node.metadata_schema.all()
        logger.debug('schema %s'%schema)
        ctype = ContentType.objects.get_for_model(item)
        for s in schema:
            n_a = NodeMetadataAssociation.objects.get(node = node,  metadata_schema = s)
            MetadataValue.objects.filter(schema=s, value=n_a.value, object_id= item.pk, content_type = ctype).delete()

def _save_metadata(node,  items):
    
    for item in items: 
        schema = node.metadata_schema.all()
        logger.debug('schema %s'%schema)
        ctype = ContentType.objects.get_for_model(item)
        for s in schema:
            node_association= NodeMetadataAssociation.objects.get(node = node,  metadata_schema = s)
            keyword = node_association.value
            
            m = MetadataValue.objects.get_or_create(schema=s, value=keyword, object_id= item.pk, content_type = ctype)
            logger.debug('m[0].pk %s'%m[0].pk)

@permission_required('edit_collection')
def save__collection_association(request, node, items):
    _save__collection_association( node, items)
    
def _save__collection_association( node, items):
    items = Item.objects.filter(pk__in = items)
    node.items.add(*items)
    
@login_required
def save_association(request):
    items = request.POST.getlist('items')
    items_commas = items[0].split(',')

    if len(items_commas) > 1:
        items = items_commas

    node= request.POST['node']
    
    node= Node.objects.get(pk = node)    
    
    if node.type == 'keyword':
        save__keyword_association(request, node, items)
    
    elif node.type == 'collection':
        save__collection_association(request, node, items)
        
    resp = simplejson.dumps({'success': True, 'errors': []})
        
    return HttpResponse(resp)

    

def get_nodes(request):
    workspace = request.session['workspace']
    node_id = request.POST.get('node',  'root')
    last_added = request.POST.get('last_added')
    child = request.POST.get('child')
    user = User.objects.get(pk=request.session['_auth_user_id'])
    items = request.POST.get('items',  [])
#    TODO: omg!
    if items:
        items = items.split(',') 
   
    if node_id == 'root':
        node = Node.objects.get( workspace = workspace,  depth = 0)
    else:
        node = Node.objects.get( pk = node_id)
#    nodes = node.get_branch(depth=1).exclude(pk = node.pk)
    nodes = node.children.all().extra(select={'leaf': 'rgt-lft=1'})
    
#    if last_added:
#        nodes = [nodes[nodes.count()-1]]
    
    if node.type == 'inbox':
        nodes = nodes.order_by('-creation_date')
    
    if child:
        nodes = [nodes.get(label = child)]

    logger.debug('nodes %s'%nodes)
#        getting number of items  
#    if node.type == 'keyword':
#        nodes = nodes.extra(select={'n_items': "select count(distinct metadata_metadata.object_id) from metadata_metadata where metadata_metadata.value in (select node2.label from node as node2 where lft between node.lft and node.rgt )"})
    logger.debug('nodes %s'%nodes)
    result = []
    if node.type == 'keyword':
        can_edit = workspace.get_permissions(user).filter(Q(codename = 'admin') | Q(codename = 'edit_taxonomy') ).count() > 0
    else:
        can_edit = workspace.get_permissions(user).filter(Q(codename = 'admin') | Q(codename = 'edit_collection') ).count() > 0
    for n in nodes:
        logger.debug('node: %s'%n)
        logger.debug('n.is_drop_target %s'%n.is_drop_target)
        if can_edit:
            allowDrag = n.is_draggable
            editable = n.editable
        else:
            allowDrag = False
            editable = False
            
        tmp = {'text' : n.label,  'id':n.id, 'leaf': n.leaf,  'allowDrag':allowDrag,  'allowDrop': n.is_drop_target,  'editable': editable,  'type': n.type, 'iconCls': n.cls,'isCategory': n.cls == 'category', 'isNewKeywords': n.cls == 'new_keyword',  'isNoKeyword': n.cls == 'no_keyword', 'uiProvider': 'MyNodeUI', }
        
        if n.type == 'keyword':
            tmp['add_metadata_parent'] = n.associate_ancestors
        
        
#        if n.type == 'keyword':
        if n.cls != 'category' and n.cls != 'new_keyword' and n.cls!= 'no_keyword' and n.type != 'inbox' :
            n_items = n.items.filter(pk__in = items) 
            logger.debug('n.items.all() %s' %n.items.all())
            logger.debug('n_items %s' %n_items)
            logger.debug('items %s' %items)
            logger.debug('n_items.count() %s'%n_items.count())
            n_items_count = n_items.count()
            tmp['checked'] =  n_items_count > 0
            if len(items) > 1 and n_items_count > 0 and  n_items_count< len(items) :
                logger.debug('tristateeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
                tmp['tristate'] = True
                tmp['items'] = [item.pk for item in n_items]
        
        result.append(tmp)
    return HttpResponse(simplejson.dumps(result))
    


def _remove_keyword_association(node,  items):
    items = Item.objects.filter(pk__in = items)
    logger.debug('items %s'%items)
    node.items.remove(*items)    
    _remove_metadata(node,  items)
            
@permission_required('edit_metadata')
def remove_keyword_association(request,  node,  items):
    _remove_keyword_association(node,  items)
    
    
    
def _remove_collection_association(node,  items):
    logger.debug('items %s'%items)
    try:
        items = Item.objects.filter(pk__in = items)
        logger.debug('items %s'%items)
        node.items.remove(*items)
    except Exception, ex:
        logger.exception(ex)
        raise ex
        
@permission_required('edit_collection')
def remove_collection_association(request,  node,  items):
    _remove_collection_association(node,  items)    

@login_required
def remove_association(request):
    items = request.POST.getlist('items')
    items_commas = items[0].split(',')

    if len(items_commas) > 1:
        items = items_commas

    node= request.POST['node']
    
    node= Node.objects.get(pk = node)
    if node.type == 'keyword':
        remove_keyword_association(request,  node,  items)
    
    elif node.type == 'collection':
        remove_collection_association(request,  node,  items)
        
        
    resp = simplejson.dumps({'success': True, 'errors': []})
        
    return HttpResponse(resp)
    


def get_metadataschema_keyword_target(request):
    node_id = request.POST.getlist('node_id')
    logger.debug('node_id %s'%node_id)
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
        
@login_required    
def get_item_nodes(request):
    items = request.POST.getlist('items')
    resp = {'nodes': []}
    item_ids = ','.join([ i for i in items])
    query = 'select count(*) from node_items where node_items.node_id = node.id and item_id in (%s)'%item_ids
    logger.debug(query)
    nodes = Node.objects.filter(items__pk__in = items).extra({'count': query})
    
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
    logger.debug('-------request.POST %s'%request.POST)
    logger.debug('smart_folder_id %s'%smart_folder_id)
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
            logger.debug('asfd--------')
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
    
    
