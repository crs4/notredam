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

from django.utils.encoding import smart_str
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import simplejson
from dam.basket.models import Basket
from dam.repository.models import Item, Component
from dam.core.dam_workspace.decorators import permission_required, membership_required
from dam.treeview import views as treeview
from dam.treeview.models import Node,  Category,  SmartFolder
from dam.workspace.models import DAMWorkspace as Workspace
from dam.core.dam_workspace.models import WorkspacePermission, WorkspacePermissionsGroup, WorkspacePermissionAssociation
from dam.variants.models import Variant      
from dam.workspace.forms import AdminWorkspaceForm
from dam.core.dam_repository.models import Type
#from dam.geo_features.models import GeoInfo
#from dam.mprocessor.models import Task
from dam.settings import GOOGLE_KEY, DATABASES
from dam.application.views import NOTAVAILABLE
from dam.preferences.models import DAMComponentSetting
from dam.metadata.models import MetadataProperty
from dam.preferences.views import get_metadata_default_language
from dam.mprocessor.models import Pipeline, Process, ProcessTarget
from dam.eventmanager.models import Event, EventRegistration
from dam.appearance.models import Theme
from dam.upload.views import _run_pipelines

from django.utils.datastructures import SortedDict

from dam.logger import logger
import time
from mx.DateTime.Parser import DateTimeFromString

import operator
import re

@login_required 
@permission_required('admin', False)
def admin_workspace(request,  ws_id):
    """
    Edits information for the given workspace (name, description)
    """
    ws = Workspace.objects.get(pk = ws_id)
    return _admin_workspace(request,  ws)

@login_required 
def create_workspace(request):
    """
    Creates a new workspace
    """
    
    #if not request.user.has_perm('dam_workspace.add_workspace'):
        #
        #return HttpResponseServerError('Permission Denied')
    #else: 
    	#return _admin_workspace(request,  None)
    return _admin_workspace(request,  None)

def _admin_workspace(request,  ws):
    from django.db import IntegrityError
    
    user = User.objects.get(pk=request.session['_auth_user_id'])
    if ws == None:
        ws = Workspace()
    
    form = AdminWorkspaceForm(ws, request.POST)
    if form.is_valid():
        name = form.cleaned_data['name']
        description = form.cleaned_data['description']
        ws.name = name
        ws.description = description
        try:
            if ws.pk == None:
    #                orig = Variant.objects.get(name = 'original',  is_global = True)
    #                ws.default_source_variant = orig
                ws = Workspace.objects.create_workspace(name, description, user)
            else:
                ws.save()
            resp = simplejson.dumps({'success': True,  'ws_id':ws.pk})
        except IntegrityError:
            resp = simplejson.dumps({'success': False,  'errors': [{'name':'field_name', 'msg':'You have already created a workspace named %s'%name}]})
        
       
    else:
        resp = simplejson.dumps({'success': False})

    return HttpResponse(resp)

def _add_items_to_ws(item, ws, current_ws, remove = 'false' ):
    if ws not in item.workspaces.all():
        item.workspaces.add(ws)
        orig_variant = Variant.objects.get(name = 'original')
        original = item.get_variant(current_ws, orig_variant)
        original.workspace.add(ws)
        return True
    return False
        
@permission_required('remove_item')
def _remove_items(request, ws, items):

    for item in items:
        ws.remove_item(item)
        
@login_required
@permission_required('add_item', False)
def add_items_to_ws(request):
    try:
        item_ids = request.POST.getlist('item_id')
        ws_id = request.POST.get('ws_id')
        
        ws = Workspace.objects.get(pk = ws_id)
        user = request.user
        current_ws = request.session['workspace']
        remove = request.POST.get('remove')
        move_public = request.POST.get('move_public', 'false')
        items = Item.objects.filter(pk__in = item_ids)
        
        
        item_imported = []
        run_items = []
        
        for item in items:
            if _add_items_to_ws(item, ws, current_ws, remove):
                run_items.append(item)

        _run_pipelines(run_items, 'upload', user, ws)

        if remove == 'true':
            _remove_items(request, current_ws, items)
                
        if len(item_imported) > 0:
            imported = Node.objects.get(depth = 1,  label = 'Imported',  type = 'inbox',  workspace = ws)
            time_imported = time.strftime("%Y-%m-%d", time.gmtime())
            node = Node.objects.get_or_create(label = time_imported,  type = 'inbox',  parent = imported,  workspace = ws,  depth = 2)[0]
            node.items.add(*item_imported)
        
        resp = simplejson.dumps({'success': True, 'errors': []})

        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

@login_required
@permission_required('admin')
def delete_ws(request,  ws_id):
    ws = Workspace.objects.get(pk = ws_id)
    if request.user.workspaces.all().count() > 1:
        ws.delete()
        return HttpResponse(simplejson.dumps({'success': True}))
    else:
        return HttpResponseServerError('You must have at least one workspace.')
    
@login_required
def get_workspaces(request):
    try:
        user = request.user
        wss = user.workspaces.all().order_by('name').distinct()
        
        resp = {'workspaces': []}
        for ws in wss:
                        
            root = Node.objects.get_root(ws = ws, type = 'keyword')
            collection_root = Node.objects.get_root(ws = ws, type = 'collection')
            inbox_root = Node.objects.get_root(ws = ws, type = 'inbox')
            name = ws.get_name(user)
            
            tmp = {
                'pk': ws.pk,
                'name': name,
                'description': ws.description,
                'root_id': root.pk,
                'collections_root_id': collection_root.pk,
                'inbox_root_id':inbox_root.pk
            }
            
            default_media_types_selected = ['image', 'video', 'audio', 'doc']
           
            if request.session.__contains__('media_type'):  
                              
                if not request.session['media_type'].__contains__(ws.pk):
                    request.session['media_type'][ws.pk] = default_media_types_selected  
                                                  
            else:                
                request.session['media_type'] = {ws.pk: default_media_types_selected}  
            
            request.session.modified = True
            media_types_selected = request.session['media_type'][ws.pk]                  
            
            tmp['media_type'] = media_types_selected
            
            resp['workspaces'].append(tmp)
            
        resp = simplejson.dumps(resp)
        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

def _search_complex_query(complex_query,  items):
    
    if complex_query['condition'] == 'and':
        for node_id in complex_query['nodes']:
            node = Node.objects.get(pk = node_id['id'])
            if node_id['negated']:
                items = items.exclude(node = node)
                
            else:
                items = items.filter(node__in = node.get_branch())
            
    else:
        
        q = None
        for node_id in complex_query['nodes']:
            node = Node.objects.get(pk = node_id['id'])
            
            if node_id['negated']:
                if q == None:
                    q = ~Q(node = node)
                else:
                    q = q.__or__(~Q(node = node))
            else:
                if q == None:
                    q = Q(node = node)
                else:
                    q = q.__or__(Q(node = node))
            
        items = items.filter(q)                

    return items


def _search(request,  items, workspace = None):
    
    def search_node(node, sub_branch):        
        if show_associated_items:
            return items.filter(node = node)
        else:
            return items.filter(node__in = node.get_branch())
        
    def search_smart_folder(smart_folder_node, items):
                
        complex_query = smart_folder_node.get_complex_query()
        items = _search_complex_query(complex_query,  items)
        return items
        
    query = request.POST.get('query')
    order_by = request.POST.get('order_by',  'creation_time')
    order_mode = request.POST.get('order_mode',  'decrescent')
    
    show_associated_items = request.POST.get('show_associated_items')
    nodes_query = []
    
    nodes_query.extend(request.POST.getlist('keyword'))
    nodes_query.extend(request.POST.getlist('collection'))
    
    smart_folders_query = request.POST.getlist('smart_folder')

    queries = []
    
    complex_query = request.POST.get('complex_query')
    logger.debug('complex_query %s'%complex_query)
    if not workspace:
        workspace = request.session['workspace']
    if complex_query:
        logger.debug('complex_query %s'%complex_query)
        complex_query = simplejson.loads(complex_query)
        
        items = _search_complex_query(complex_query,  items)
        
    else:
        logger.debug('nodes_query %s'%nodes_query)
        if nodes_query:            
            for node_id  in nodes_query:
                node = Node.objects.filter(pk = node_id)                
                if node.count() > 0:
                    node = node[0] 
                    queries.append(search_node(node, not show_associated_items))
                else:
#                    return Item.objects.none()
                    queries.append(Item.objects.none())
                    
        if smart_folders_query:
            for smart_folder_id in smart_folders_query:                
                smart_folder_node = SmartFolder.objects.get(pk = smart_folder_id)
                queries.append(search_smart_folder(smart_folder_node, items))
            
            
#            items = reduce(and_,  queries)
            
#Text query        
        logger.debug('queries %s'%queries)
        if query:
            processes =  re.findall('\s*process:(\w+):(\w+)\s*', query,  re.U)
            
            metadata_query = re.findall('\s*(\w+:\w+=\w+[.\w]*)\s*', query,  re.U)
            
            inbox = re.findall('\s*Inbox:/(\w+[/\w\-]*)/\s*', query,  re.U)
            
            smart_folder = re.findall('\s*SmartFolders:"(.+)"\s*', query,  re.U)
            
            keywords = re.findall('\s*Keywords:/(.+)/\s*', query,  re.U)
#            spaced_keywords = re.findall('\s*Keywords:"([\w\s/]*)"\s*', query,  re.U)
#            keywords.extend(spaced_keywords)
    #        
            collections= re.findall('\s*Collections:/(.+)/\s*', query,  re.U)
#            spaced_collections = re.findall('\s*Collections:"([\w\s/]*)"\s*', query,  re.U)
#            collections.extend(spaced_collections)
            
            geo = re.findall('\s*geo:\(([\d.-]*),([\d.-]*)\),\(([\d.-]*),([\d.-]*)\)\s*', query,  re.U)
            
    #            just put out  keywords and collections....
    #        simple_query = re.sub('(\w+:\w+)', '', query,)
            simple_query = re.compile('(\w+:/.+/)',  re.U).sub('', query)
            
            simple_query = re.sub('(\w+:".+")', '', simple_query)
            logger.debug('simple_query %s' %simple_query,  )
            
            simple_query = re.sub('\s*SmartFolders:"(.+)"\s*', '', simple_query)
            simple_query = re.sub('\s*Inbox:/(\w+[/\w\-]*)/\s*', '', simple_query)
            simple_query = re.sub('\s*process:(\w+):(\w+)\s*', '', simple_query)
            
#            removing metadata query
            simple_query = re.sub('\s*(\w+:\w+=\w+[.\w]*)\s*', '', simple_query)
            
            logger.debug('----%s'%simple_query)
            
            
    #       remove geo too...
            simple_query = re.sub('(\w+:\(([\d.-]*),([\d.-]*)\),\(([\d.-]*),([\d.-]*)\))', '', simple_query)

            multi_words = re.findall('"(.+?)"', simple_query,  re.U)
            single_word_query = re.compile('"(.+)"',  re.U).sub( '', simple_query)
            
            words = re.findall( '\s*(.+)\s*', single_word_query ,  re.U)
            
#            words = re.findall( '\s*([\w+\.*])\s*', single_word_query ,  re.U)
    #            words.extend(multi_words)
            
    #        logger.debug('keywords %s'%keywords )
    #        logger.debug('collections %s'%collections)        
            logger.debug('words %s'%words )
            logger.debug('multi_words %s'%multi_words)
            logger.debug('geo %s'%geo)
            
            
            
            logger.debug('metadata_query %s'%metadata_query)
            logger.debug('queries %s'%queries)
            for metadata_q in metadata_query:
                
                key, value = metadata_q.split('=')
                
                property_namespace,   property_field_name = key.split(':')
                
                try:
                    property = MetadataProperty.objects.get(namespace__prefix = property_namespace,  field_name = property_field_name)
                    logger.debug('items %s'%items)
                    logger.debug('items.filter(metadata__value = value, metadata__schema = property) %s'%items.filter(metadata__value = value, metadata__schema = property))
                    queries.append(items.filter(metadata__value = value, metadata__schema = property))
                
                except MetadataProperty.DoesNotExist:
                    logger.debug(' MetadataProperty.DoesNotExist %s'%metadata_q)
                    queries.append(Item.objects.none())
            
            logger.debug('processes %s'%processes)
            logger.debug('queries %s'%queries)
            for process in processes:
                process_id = process[0]
                type = process[1]
                logger.debug('process_id %s, type %s'%(process_id, type))
                if type == 'total':
                    q = items.filter(pk__in = [p.target_id for p in ProcessTarget.objects.filter(process__pk = process_id)])
                elif type == 'failed':
                    q = items.filter(pk__in = [p.target_id for p in ProcessTarget.objects.filter(process__pk = process_id, actions_failed__gt = 0)])
                elif type == 'completed':
                    q = items.filter(pk__in = [p.target_id for p in ProcessTarget.objects.filter(process__pk = process_id, actions_todo = 0)])
                queries.append(q)
                
            logger.debug('inbox %s'%inbox)
            logger.debug('queries %s'%queries)
            for inbox_el in inbox:
                logger.debug('path %s'%inbox_el)
                node = Node.objects.get_from_path(inbox_el, workspace,   'inbox')
                logger.debug('node found in inbox %s'%node.pk)
                queries.append(items.filter(node = node))
                
            logger.debug('keywords %s'%keywords)
            logger.debug('queries %s'%queries)
            for keyword in keywords:
                if keyword: 
                    logger.debug('keyword: %s'%keyword)
                    node = Node.objects.get_from_path(keyword, workspace,  'keyword')
                    logger.debug('node found %s'%node)
                    
                    queries.append(search_node(node, not show_associated_items))
                    
                else:
                    logger.debug('without keywords')
    #                    searching for items without keyword
                    queries.append(items.exclude(node__in = Node.objects.filter(type = 'keyword')))
                    break
                
            
            logger.debug('collections %s'%collections)
            logger.debug('queries %s'%queries)
            for coll  in collections:
                
    #                q = Q(node__label__iexact = collection.strip(),  node__type = 'collection')
    #                queries.append(items.filter(q))
                logger.debug('path %s'%coll)
                node = Node.objects.get_from_path(coll, workspace,  'collection')
                logger.debug('node found %s'%node)
                queries.append(items.filter(node = node))
                
            logger.debug('smart_folder %s'%smart_folder )
            logger.debug('queries %s'%queries)
            if smart_folder:               
                
                smart_folder_node = SmartFolder.objects.get(workspace = workspace,  label = smart_folder[0])
                queries.append(search_smart_folder(smart_folder_node, items))

            logger.debug('geo %s'%geo)
            logger.debug('queries %s'%queries)
            for coords in geo:
                ne_lat = coords[0]
                ne_lng = coords[1]
                sw_lat = coords[2]
                sw_lng = coords[3]
                if(float(ne_lng)>float(sw_lng)):
                    queries.append(items.filter(geoinfo__latitude__lte=ne_lat, geoinfo__latitude__gte=sw_lat, geoinfo__longitude__lt=ne_lng, geoinfo__longitude__gt=sw_lng))
                else:
                    queries.append(items.filter(Q(geoinfo__longitude__gte=sw_lng) | Q(geoinfo__longitude__lte=ne_lng), geoinfo__latitude__lte=ne_lat, geoinfo__latitude__gte=sw_lat))
            
            logger.debug('words %s'%words)
            logger.debug('queries %s'%queries)
            for word in words:
                logger.debug('word %s'%word)
                if DATABASES['default']['ENGINE'] == 'sqlite3':
                    q = Q(metadata__value__iregex = u'(?:^|(?:[\w\s]*\s))(%s)(?:$|(?:\s+\w*))'%word.strip())                
                    queries.append(items.filter(q))
                    logger.debug('items.filter(q) %s'%items.filter(q))
                elif DATABASES['default']['ENGINE'] == 'mysql':
                    q = Q(metadata__value__iregex = '[[:<:]]%s[[:>:]]'%word.strip())
                    queries.append(items.filter(q))
                
            logger.debug('multi_words %s'%multi_words)
            logger.debug('queries %s'%queries)
            for words in multi_words:
                tmp = re.findall('\s*(.+)\s*', words,  re.U)
                logger.debug('multi words %s'%tmp)
                logger.debug('queries %s'%queries)
                if DATABASES['default']['ENGINE'] == 'sqlite3':
                    words_joined = '\s+'.join(tmp)
                    words_joined = words_joined.strip() 
#                    q = Q(metadata__value__iregex = '(?:^|(?:[\w\s]*\s))(%s)(?:$|(?:\s+\w*))'%words_joined)
                    q = Q(metadata__value__iregex = '%s'%words_joined)
                    

                    queries.append(items.filter(q))
                
                elif DATABASES['default']['ENGINE'] == 'mysql':
                    words_joined = '[[:blank:]]+'.join(tmp)
                    q = Q(metadata__value__iregex = '[[:<:]]%s[[:>:]]'%words_joined)
                    queries.append(items.filter(q))
                    
        
#        logger.debug('queries %s'%queries)
        if queries:
            logger.debug('queries %s'%queries)
            if len(queries) == 1:
                items = queries[0]
                
            else:
                
                items = reduce(operator.and_,  queries)
    
    items.distinct()       
    property = None
    
    if order_by:
        
        if order_by == 'creation_time':
            pass
        
        elif order_by == 'size':            
            items = items.extra(select={order_by: 'select size from component, variants_variant where item_id = item.id and variants_variant.name == "original" '})
        
        else:
            property_namespace, property_field_name = order_by.split('_')
                
            try:
                property = MetadataProperty.objects.get(namespace__prefix__iexact = property_namespace,  field_name__iexact = property_field_name)
            except MetadataProperty.DoesNotExist:
                property = None
        
            if property:
                language_settings = DAMComponentSetting.objects.get(name='supported_languages')
#                language_selected = get_user_setting_by_level(language_settings,workspace)
#                TODO: change when gui multilanguage ready
                language_selected = 'en-US' 
                logger.debug('------------- items.query %s'%items.query)
                items = items.extra(select=SortedDict([(order_by, 'select distinct value from metadata_metadatavalue where object_id = item.id and schema_id = %s  and language=%s')]),  select_params = (str(property.id),  language_selected))
                logger.debug('------------- items.query %s'%items.query)
                
        if order_mode == 'decrescent':
            items = items.order_by('-%s'%order_by)
        else:
            items = items.order_by('%s'%order_by)

    logger.debug('items %s'%items)
    return items

def _search_items(request, workspace, media_type, start=0, limit=30, unlimited=False):
    user = User.objects.get(pk=request.session['_auth_user_id'])
    logger.debug('************** searching items for user %s' % user.pk)

    only_basket = simplejson.loads(request.POST.get('only_basket', 'false'))    
    logger.debug('************** searching only_basket %s' % only_basket)
    
    items = workspace.items.filter(type__name__in = media_type).distinct().order_by('-creation_time')
    logger.debug('******************8 found %d items' % len(items))

    user_basket = Basket.get_basket(user, workspace)
    basket_items = user_basket.items.all().values_list('pk', flat=True)
    logger.debug('******************8 found %d basket items' % len(basket_items))

    if only_basket:
        items = items.filter(pk__in=basket_items)

    items = _search(request,  items)

    total_count = items.count()

    if not unlimited:
        items = items[start:start+limit]

    return (items, total_count)


#def _get_thumb_url(item, workspace):
#
#    thumb_url = NOTAVAILABLE
#    thumb_ready = 0
#
#    try:
#        variant = workspace.get_variants().distinct().get(media_type =  item.type, name = 'thumbnail')
#        url = item.get_variant(workspace, variant).get_component_url()
#        if url:
#            thumb_ready = 1
#            thumb_url = url
#    except:
#        pass
#        
#    return thumb_url, thumb_ready

@login_required
def load_items(request, view_type=None, unlimited=False):
    logger.debug('******************** load_items')
    from datetime import datetime
    try:
        user = request.user
        workspace_id = request.POST.get('workspace_id')

#        if  workspace_id:
#            workspace = Workspace.objects.get(pk = workspace_id)
#        else:
        workspace = request.session['workspace']        

        media_type = request.POST.getlist('media_type')
        
#        save media type on session

        if request.session.__contains__('media_type'):
            request.session['media_type'][workspace.pk] = list(media_type)
        else:
            request.session['media_type']= {workspace.pk: list(media_type)}
            
        request.session.modified = True
        
        start = int(request.POST.get('start', 0))
        limit = int(request.POST.get('limit', 30))
		
        if limit == 0:
            unlimited = True
            
        
        items, total_count = _search_items(request, workspace, media_type, start, limit, unlimited)                    
        item_dict = []
        now = time.time()

        items_pks = [item.pk for item in items]
        
        tasks_pending_obj = []
        tasks_pending = []
                
        thumb_caption_setting = DAMComponentSetting.objects.get(name='thumbnail_caption')
        thumb_caption = thumb_caption_setting.get_user_setting(user, workspace)

        default_language = get_metadata_default_language(user, workspace)

        user_basket = Basket.get_basket(user, workspace)
        basket_items = user_basket.items.all().values_list('pk', flat=True)
        
        items_info = []
        thumb_caption_setting = DAMComponentSetting.objects.get(name='thumbnail_caption')
        thumb_caption = thumb_caption_setting.get_user_setting(user, workspace)
        default_language = get_metadata_default_language(user, workspace)    
        
        for item in items:
            tmp = item.get_info(workspace, thumb_caption, default_language)
            if item.pk in basket_items:
                tmp['item_in_basket'] = 1
            else:
                tmp['item_in_basket'] = 0
                
            items_info.append(tmp)
        
        
#        for item in items:
#            thumb_url,thumb_ready = _get_thumb_url(item, workspace)
#            logger.debug('thumb_url,thumb_ready %s, %s'%(thumb_url,thumb_ready))
#            
#            geotagged = 0
#            inprogress =  int( (not thumb_ready) or (item.pk in tasks_pending)) 
#            
#            
#            if GeoInfo.objects.filter(item=item).count() > 0:
#                geotagged = 1
#            
#            item_in_basket = 0
#
#            if item.pk in basket_items:
#                item_in_basket = 1
#             
#            states = item.stateitemassociation_set.all()
#            try:
#                my_caption = _get_thumb_caption(item, thumb_caption, default_language)
#            except:
#                # problems retrieving thumb, skip this items
#                continue
##                my_caption = ''
#            if inprogress:
#                preview_available = tasks_pending_obj.filter(component__variant__name = 'preview', component__item = item, params__contains = 'adapt_resource').count()
#            else:
#                preview_available = 0
#            item_info = {
#                "name":my_caption,
#                "pk": smart_str(item.pk),
#                "geotagged": geotagged, 
#                "inprogress": inprogress, 
#                'thumb': thumb_ready, 
#                'type': smart_str(item.type.name),
#                'inbasket': item_in_basket,
#                'preview_available': preview_available,
#                "url":smart_str(thumb_url), "url_preview":smart_str("/redirect_to_component/%s/preview/?t=%s" % (item.pk,  now))
#            }
#            
#            if states.count():
#                state_association = states[0]
#                
#                item_info['state'] = state_association.state.pk
#                
#            item_dict.append(item_info)
        
        res_dict = {"items": items_info, "totalCount": str(total_count)}       
        resp = simplejson.dumps(res_dict)

        return HttpResponse(resp)
    except Exception,  ex:
        logger.exception(ex)
        raise ex

@membership_required
def _switch_workspace(request,  workspace_id):
    workspace = Workspace.objects.get(pk = workspace_id)
    request.session['workspace'] = workspace
    return workspace

def _get_theme():
    try:
        theme = Theme.objects.get(SetAsCurrent = 'True')
    except Exception, err:
        theme = Theme.objects.get(IsDefault = 'True')
    return theme

@login_required
def workspace(request, workspace_id = None):

    """
    
    """
    theme = _get_theme()
    
#    logger.debug('In workspace.views method workspace: current theme is %s' % theme)
#    logger.debug('In workspace.views method workspace: current theme css file is %s' % theme.css_file)
    user = request.user
    logger.info('workspace_id %s'%workspace_id)
    if not workspace_id:
        if request.session.__contains__('workspace'):
            logger.debug('workspace in session')
            workspace = Workspace.objects.get(pk = request.session.get('workspace', ).pk ) #ws in session could be outdated (old name)
        else:
            logger.debug('get default workspace')
            workspace = Workspace.objects.get_default_by_user(user)
            
            request.session['workspace'] = workspace
    else:
        
        workspace = _switch_workspace(request,  workspace_id)
    
    logger.info('workspace %s'%workspace)
    # interface language setting (not for metadata editing!)
    language_setting = None
    try:
        language_setting = DAMComponentSetting.objects.get(name__iexact='application_supported_languages')
    except Exception, err:
        logger.debug('no language set by current user')
    if language_setting != None:
        user_language = language_setting.get_user_setting(user)
        request.session['django_language'] = str(user_language[:2])
        logger.debug('user language is %s' % user_language)
        logger.debug( '\n\n********\ninside workspace in workspace/views ... \nuser_language preferred by the current user: %s'% request.session['django_language'])
        # end of interface language setting

    return render_to_response('workspace_gui.html', RequestContext(request,{'ws_id':workspace.pk,  'ws_name': workspace.get_name(user),  'ws_description': workspace.description, 'theme_css':theme.css_file, 'GOOGLE_KEY': GOOGLE_KEY}))
    #return HttpResponse('')

@login_required
def upload_status(request):
    """
    Returns information for the given items, including name, size, url of thumbnail and preview
    Called every 10 seconds by the GUI for refreshing information on pending items
    """
    try:
        workspace = request.session.get('workspace')
        user = request.user
        items_in_progress = request.POST.getlist('items')
        logger.debug('items_in_progress %s'%items_in_progress)
        resp = {'items':[]}
#### Added by orlando
#        process_id = request.POST.get('process_id')
# get completed targets
#        completed_targets = ProcessTarget.objects.filter(process__workspace = workspace, target_id__in=items_in_progress, actions_todo=0).values_list('target_id', flat = true)
#        info = {}

        process_in_progress = Process.objects.filter(end_date__isnull = True)
        if process_in_progress:
            pending_items = ProcessTarget.objects.filter(process__in = process_in_progress, actions_todo__gt = 0)
        else:
            pending_items = ProcessTarget.objects.none()
        
        resp['status_bar'] = {
            'process_in_progress':  process_in_progress.count(),
            'pending_items': pending_items.count()
        }
####
        if request.POST.get('update_script_monitor'):
            from dam.scripts.views import _script_monitor
            processes_info = _script_monitor(workspace)
            resp['scripts'] = processes_info 
            
        for item_id in items_in_progress:
            try:

        
                item = Item.objects.get(pk = int(item_id)) 
                tmp = item.get_info(workspace, user)
#                if item_id not in completed_targets:
#                    tmp['status'] = 'in_progress'
#                else:
#                    tmp['status'] = 'completed'
                
                resp['items'].append(tmp)
                
            except ProcessTarget.DoesNotExist:
                logger.debug('process target not found for item %s'%item)
                continue


       
        resp = simplejson.dumps(resp)
        return HttpResponse(resp)
    except Exception,ex:
        logger.exception(ex)
        raise ex
    
@login_required
def get_status(request):
    """
    Returns information for the given items, including name, size, url of thumbnail and preview
    Called every 10 seconds by the GUI for refreshing information on pending items
    """
    try:
        workspace = request.session.get('workspace')
        user = request.user
        items_in_progress = request.POST.getlist('items')
        logger.debug('items_in_progress %s'%items_in_progress)
        resp = {'items':[]}
#### Added by orlando
#        process_id = request.POST.get('process_id')
# get completed targets
#        completed_targets = ProcessTarget.objects.filter(process__workspace = workspace, target_id__in=items_in_progress, actions_todo=0).values_list('target_id', flat = true)
#        info = {}

        process_in_progress = Process.objects.filter(end_date__isnull = True)
        if process_in_progress:
            pending_items = ProcessTarget.objects.filter(process__in = process_in_progress, actions_todo__gt = 0)
        else:
            pending_items = ProcessTarget.objects.none()
        
        resp['status_bar'] = {
            'process_in_progress':  process_in_progress.count(),
            'pending_items': pending_items.count()
        }
####
        if request.POST.get('update_script_monitor'):
            from dam.scripts.views import _script_monitor
            processes_info = _script_monitor(workspace)
            resp['scripts'] = processes_info 
            
        for item_id in items_in_progress:
            try:

        
                item = Item.objects.get(pk = int(item_id)) 
                tmp = item.get_info(workspace, user)
#                if item_id not in completed_targets:
#                    tmp['status'] = 'in_progress'
#                else:
#                    tmp['status'] = 'completed'
                
                resp['items'].append(tmp)
                
            except ProcessTarget.DoesNotExist:
                logger.debug('process target not found for item %s'%item)
                continue


       
        resp = simplejson.dumps(resp)
        return HttpResponse(resp)
    except Exception,ex:
        logger.exception(ex)
        raise ex
    
@login_required
def get_n_items(request):
    """
    Returns the number of the items of the given workspace
    Used to avoid deletion of non-empty workspace
    """
    workspace = request.session.get('workspace')
    n_items = workspace.items.all().count()
    resp = {'success': True,  'n_items': n_items}
    return HttpResponse(simplejson.dumps(resp))

@login_required
def get_permissions(request):
    """
    Returns the list of permissions for the current user
    """
    workspace = request.session.get('workspace')
    user = User.objects.get(pk=request.session['_auth_user_id'])
    permissions = workspace.get_permissions(user)
    resp = {'permissions':[]}
    if user.has_perm('dam_workspace.add_workspace'):
        resp['permissions'].append({'name': 'add_ws'})
    for perm in permissions:
        resp['permissions'].append({'name': perm.codename})
    return HttpResponse(simplejson.dumps(resp))
    
@login_required
@permission_required('admin',  False)
def get_ws_members(request):
    """
    Returns the list of members for the current workspace 
    (for workspace admins only)
    Called by the GUI for workspace/members configuration
    """
    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    admin_user = User.objects.get(pk=request.session['_auth_user_id'])

    ws = Workspace.objects.get(pk = ws_id)

    members = ws.get_members()
    
    available_permissions = WorkspacePermission.objects.all()    
    permissions_list = [{'pk': str(p.pk), 'name': str(p.name)} for p in available_permissions]
    
    
    data = {'elements':[]}
    for u in members:
        permissions = ws.get_permissions(u)
        perm_list = [p.pk for p in permissions]
        user_dict = {'id':u.id, 'name':u.username}
        # the following 5 rows of code have been added by clem 
        # to have all the permissions of admin set to true,
        # as it actually is.
        # start
        all_true = False
        for p in available_permissions:
            if admin_user == u:
                all_true = True
                break
        # end
        for p in available_permissions:
            if p.pk in perm_list or all_true == True:
                user_dict[p.codename] = 1
            else:
                user_dict[p.codename] = 0
        if admin_user == u:
            user_dict['editable'] = False
        else:
            user_dict['editable'] = True        
        data['elements'].append(user_dict)
    return HttpResponse(simplejson.dumps(data))

@login_required
@permission_required('admin',  False)
def get_available_users(request):
    """
    Returns the list of available users for the current workspace 
    (for workspace admins only)
    Called by the GUI for workspace/members configuration
    """

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    ws = Workspace.objects.get(pk = ws_id)
    
    users = User.objects.exclude(workspaces=ws)
    
    users_list = [{'id': u.pk, 'name': str(u.username)} for u in users]
    
    data = {'users': users_list}
    
    return HttpResponse(simplejson.dumps(data))

@login_required
@permission_required('admin',  False)
def get_available_permissions(request):
    """
    Returns the list of available permissions for the current workspace 
    (for workspace admins only)
    Called by the GUI for workspace/members configuration    
    """

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    ws = Workspace.objects.get(pk = ws_id)
    
    available_permissions = WorkspacePermission.objects.all()    
    permissions_list = [{'pk': str(p.pk), 'name': str(p.name)} for p in available_permissions]
    
    data = {'available_permissions': permissions_list}
    
    return HttpResponse(simplejson.dumps(data))    
    
@login_required
@permission_required('admin',  False)
def save_members(request):
    """
    Saves the members and their permissions for the current workspace 
    (for workspace admins only)
    Called by the GUI for workspace/members configuration    
    """

    ws_id = request.POST.get('ws_id', request.session.get('workspace').pk)

    ws = Workspace.objects.get(pk = ws_id)

    permissions = request.POST.get('permissions', None)
    
    if permissions:
        permissions_list = simplejson.loads(permissions)
    else:
        permissions_list = []
    
    current_users = []

    for p in permissions_list:
        try:
            user = User.objects.get(pk=p['id'])
            user_perms = []
            current_users.append(user.pk)
            for k, v in p.iteritems():
                if k not in ['id', 'name', 'editable'] and v == 1:
                    try:
                        ws_permission = WorkspacePermission.objects.get(codename=k)
                        user_perms.append(ws_permission)
                    except:
                        pass

            ws.add_member(user, user_perms)

        except:
            continue

    removed_users = ws.members.exclude(pk__in=current_users)
        
    for u in removed_users:
        ws.remove_member(u)
            
    data = {'success': True}
    
    return HttpResponse(simplejson.dumps(data))
    
@login_required
def switch_ws(request):
    workspace_id = request.POST['workspace_id']
    _switch_workspace(request,  workspace_id)
    return HttpResponse(simplejson.dumps({'success': True}))
    
@login_required
def download_renditions(request):
    import  os, settings, tempfile
    items = request.POST.getlist('items')
    renditions = request.POST.getlist('renditions')
    
    compression_type = request.POST.get('compression_type', 'zip')    
    
    if renditions and items:
        suffix = '.' + compression_type
        tmp = tempfile.mkstemp(prefix='archive-', suffix= suffix, dir= settings.MEDIADART_STORAGE)[1]
        
        if compression_type == 'zip':            
            import zipfile
            archive = zipfile.ZipFile(tmp,  'w')
            
        else:
            from tarfile import TarFileCompat as ArchiveFile
            import tarfile
            archive = tarfile.TarFileCompat(tmp, 'w', compression = tarfile.TAR_GZIPPED)
                
        for item in items:    
            
            for rendition in renditions:
                try:
                    c = Component.objects.get(item__pk = item,  variant__pk = rendition)
                    file = os.path.join(settings.MEDIADART_STORAGE, c.uri)
                    #try:
                        #ext = c._id.split('.')[1]                       
                        #file_name =  item + '_' +  c.variant.name +  '.' + ext 
                    #except:
                        #file_name = item + '_' +  c.variant.name
                    file_name = c.uri 

                    
                    archive.write(file, file_name)

                except Component.DoesNotExist:
                    continue
        archive.close()
    
    return HttpResponse(simplejson.dumps({'success': True,  'url':'/storage/' + os.path.basename(tmp) }))
