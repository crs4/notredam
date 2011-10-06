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

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from dam.mprocessor.models import ProcessTarget
from dam.core.dam_repository.models import AbstractItem, AbstractComponent
from dam.settings import SERVER_PUBLIC_ADDRESS, STORAGE_SERVER_URL, MEDIADART_STORAGE
from dam.metadata.models import *



import os, datetime, urlparse, time, re, settings, logging
from json import loads
from django.utils import simplejson
from django.utils.encoding import smart_str

logger = logging.getLogger('dam')

from mediadart.storage import Storage

from uuid import uuid4


def new_id():
    return uuid4().hex



def _get_resource_url(id):
    """
    Returns resource path
    """

    storage = Storage()

    if not id:
        return None

    try:
        
        if storage.exists(id):
            url = '/storage/' + id
        else:
            url = None
    except:
        url = None
    return url

class ItemManager(models.Manager):
    def create(self, workspace, **kwargs):
        from workspace.models import WorkspaceItem
        item = super(ItemManager, self).create(**kwargs)
        WorkspaceItem.objects.create(item = item, workspace = workspace)
        item.add_to_uploaded_inbox(workspace)       
        return item
        
class Item(AbstractItem):

    """
    Concrete class that inherits from the abstract class AbstractItem found in core/dam_repository/models.py     
    Base model describing items. They can contain components only.
    """
    _id = models.CharField(max_length=40,  db_column = 'md_id')
    metadata = generic.GenericRelation('metadata.MetadataValue')
    source_file_path = models.TextField() #path from whom the item was imported(/tmp/somedir/somefile in case of upload)
    objects = ItemManager()
    
    def get_last_update(self, ws):
        ws_item = self.workspaceitem_set.get(item = self, workspace = ws)
        return ws_item.last_update
    
    def update_last_modified(self, time = datetime.datetime.now(), workspaces = []):
        from dam.workspace.models import WorkspaceItem
        logger.debug('workspaces %s'%workspaces)
        
        if not workspaces:
            ws_items = WorkspaceItem.objects.filter(item = self)
        else:
            ws_items = WorkspaceItem.objects.filter(item = self, workspace__in = workspaces)
        
        logger.debug('ws_items %s'%ws_items)
        for ws_item in ws_items:
            ws_item.last_update = time
            ws_item.save()
    
    def _get_id(self):
        return self._id
    
    ID = property(fget=_get_id)   
    
#    def save(self, *args, **kwargs):
#        if not self.pk and not self._id:
#            self._id = new_id()
#        super(Item, self).save(*args, **kwargs)

    class Meta:
        db_table = 'item'

    def __unicode__(self):
        return self.get_file_name()
	
    def save(self, *args, **kwargs):
        super(Item, self).save(*args, **kwargs)
        self.update_last_modified()

        
    def set_metadata(self,property_namespace, property_name, value):
        property = MetadataProperty.objects.get(field_name = property_name, namespace__name = property_namespace)
    
        new_metadata = {}

        if property.type == 'lang':
            if not isinstance(value,  dict):
                raise Exception('format of metadata %s is invalid; it must be a dictionary (ex: {"en-US":"value"})')
            
            new_metadata[str(property.pk)]  = []
            for lang in value.keys():
                
                if lang not in MetadataLanguage.objects.all().values_list('code',  flat = True):
                    raise Exception('invalid language %s for metadata %s' % (lang, data))
                
                new_metadata[str(property.pk)] .append([value[lang],  lang])
            
#                dict

        elif property.type in XMPStructure.objects.all().values_list('name',  flat = True):
#                list of dict
            
            if not isinstance(value,  list):
                raise Exception('format of metadata %s is invalid; it must be a list of dictionaries' % data)
            
            structure = XMPStructure.objects.get(name = property.type)
            structure_list = []
            
            for _structure in value:
                if not isinstance(_structure ,  dict):
                    raise Exception('format of metadata %s is invalid; it must be a list of dictionaries' % data)
                
                tmp_dict = {}
                for el in _structure.keys():
                    property_namespace,   property_field_name = el.split('_')
                    try:
                        el_property = MetadataProperty.objects.get(namespace__prefix = property_namespace,  field_name = property_field_name)
                    except MetadataProperty.DoesNotExist:
                        raise Exception('metadata schema %s unknown' % el)
                    logger.debug('structure %s'%structure)
                    if el_property not in structure.properties.all():
                        raise Exception('unexpected property %s' % el)
                    
                    tmp_dict[str(el_property.pk)] = _structure[el]
                
                structure_list.append(tmp_dict)                    
                    
            new_metadata[str(property.pk)] = structure_list

        elif property.is_array != 'not_array':                
#                list of str
            
            if not isinstance(value,  list):
                raise Exception('format of metadata %s is invalid; it must be a list of strings' % data)
            for el in value:
                if not isinstance(el,  basestring):
                    raise Exception('format of metadata %s is invalid; it must be a list of strings' % data)
            
            new_metadata[str(property.pk)] = value
        else:
#                str
            if not isinstance(value,  basestring) and not isinstance(value,  int) and not isinstance(value,  float):
#                    logger.debug('value %s'%value)
#                    logger.debug('-------------------------------------value.__class__ %s'%value.__class__)
                raise Exception('format of metadata %s is invalid; it must be a string' % data)
            
            new_metadata[str(property.pk)] = value
        
        logger.debug('new_metadata %s' %new_metadata)
        MetadataValue.objects.save_metadata_value([self], new_metadata,  'original', self.workspaces.all()[0]) #workspace for variant metadata, not supported yet



    def get_workspaces_count(self):
        """
        Number of workspaces where the current item has been added
        """
        return self.workspaceitem_set.all().count()
        
    def create_variant(self, variant, ws,  media_type):  # no default for media_type
        """
        Create a new component for this item, using the given variant/media_type 
        and add it to the given workspace
        @param variant an instance of variants.Variant
        @param ws an instance of workspace.DAMWorkspace
        @param media_type an instance of dam_repository.Type
        """
#        if not media_type:
#            media_type = self.default_type
        
        try:
            logger.debug('variant %s'%variant)
            if variant.shared:
                comp = Component.objects.get(item = self, variant= variant)
                comp.workspace.add(ws)
                comp.workspace.add(*self.workspaces.all())
            else:
                #logger.debug('item %s'%self)
                #logger.debug('variant %s'%variant)
                #logger.debug('worskapce %s'%ws)
                #logger.debug('media_type %s'%media_type)
                comp = Component.objects.get(item = self, variant= variant,  workspace = ws)
                
#                comp = Component.objects.get(pk = 1)
                logger.debug('comp %s'%comp)
                
#                comp.metadata.all().delete()
            
            
        except Component.DoesNotExist:
            #logger.debug('variant does not exist yet')
            #logger.debug('variant %s'%variant)
            #logger.debug('type %s'%media_type)
                    
            comp = Component.objects.create(variant = variant, item = self, type = media_type)
            comp.workspace.add(ws)
            
            if variant.shared:
                comp.workspace.add(*self.workspaces.all())
        
        #logger.debug('variant %s, comp %s' % (variant, comp))
        #logger.debug('comp.pk %s'%comp.pk)
        
        
        logger.debug('======== COMPONENT_VARIANT  ======= %s %s' % (comp.variant, comp.pk))
        return comp

    def add_to_uploaded_inbox(self, workspace):
        """
        Add the item to the uploaded inbox of the given workspace
        @param ws an instance of workspace.DAMWorkspace
        """
        
        uploaded = workspace.tree_nodes.get(depth = 1, label = 'Uploaded', type = 'inbox')
        time_uploaded = time.strftime("%Y-%m-%d", time.gmtime())
        node = workspace.tree_nodes.get_or_create(label = time_uploaded,  type = 'inbox',  parent = uploaded,  depth = 2)[0]
        node.items.add(self)
        return node

    def delete_from_ws(self, user, workspaces=None):
        """
        Delete the item from the given workspaces 
        If workspaces is not specified, remove the item from the user's workspaces
        @param user an instance of auth.User
        @param workspaces a querySet of workspace.DAMWorkspace (optional)
        """
        from dam.workspace.models import DAMWorkspace as Workspace 
        from operator import or_
        if not workspaces:
            q1 = Workspace.objects.filter( Q(ws_permissions__permission__codename = 'admin') | Q(ws_permissions__permission__codename = 'remove_item'), members = user,ws_permissions__users = user)
            q2 =  Workspace.objects.filter(Q(workspacepermissionsgroup__permissions__codename = 'admin') | Q(workspacepermissionsgroup__permissions__codename = 'remove_item'), members = user, workspacepermissionsgroup__users = user)
            workspaces = reduce(or_, [q1,q2])

        
        for c in self.component_set.filter(workspace__in = workspaces).exclude(variant__name = 'original'):                
            try:
                os.remove(c.get_file_path())
            except:
                pass # maybe file does not exist
            c.delete()
              
        self.workspaceitem_set.filter(workspace__in = workspaces).delete()
            
        if self.get_workspaces_count() == 0:
            #REMOVING ORIGINAL FILE
            orig = self.component_set.get(variant__name = 'original')
            try:
                os.remove(orig.get_file_path())
            except:
                pass #file maybe does not exist
            orig.delete()
            self.delete()
            
           
        else:
            inboxes = self.node_set.filter(type = 'inbox',  workspace__in= workspaces)
            for inbox in inboxes:
                inbox.items.remove(self)
            
    def get_metadata_values(self, metadataschema=None):
        """
        Returns item's metadata for the given XMP Property 
        If the XMP Property is not specified, all the metadata will be returned
        @param metadataschema an instance of metadata.MetadataProperty
        """
        from dam.metadata.models import MetadataValue, MetadataProperty
    
        values = []
        original_component = Component.objects.get(item=self, variant__name='original', workspace=self.workspaces.all()[0])
        if metadataschema:
            schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.pk], metadataschema, set([self.type.name]), set([original_component.media_type.name]), [original_component.pk])
            if delete:
                return None
            if schema_value:
                if schema_value[self.pk]:
                    values = schema_value[self.pk]
                else:
                    values = None
            else:
                values = None
        else:
            for m in self.metadata.all().distinct('schema').values('schema'):
                prop = MetadataProperty.objects.get(pk=m['schema'])
                schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.pk], prop, set([self.type.name]), set([original_component.media_type.name]), [original_component.pk])
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.pk]})

        return values

    def get_formatted_descriptors(self, user, workspace):
        """
        Retrieves all the values for the descriptors for the current item
        and returns them in the format required by the Metadata GUI
        @param user an instance of auth.User
        @param workspace an instance of workspace.DAMWorkspace
        """
        from dam.metadata.models import MetadataDescriptor, MetadataProperty
        from dam.preferences.views import get_metadata_default_language
        
        descriptors = self.get_descriptors(workspace)
        default_language = get_metadata_default_language(user, workspace)
        values = []
        for d, v in descriptors.iteritems():
            desc = MetadataDescriptor.objects.get(pk=d)
            desc_dict = {'caption': '%s' % desc.name}
            desc_value = v
            if isinstance(v, dict):
                if v.has_key(default_language):
                    desc_value = v.get(default_language)
                else:
                    continue
            elif isinstance(v, list):
                for value in v:
                    if isinstance(value, dict):
                        if not isinstance(desc_value, dict):
                            desc_value = {'properties': []}
                        for key, v_value  in value.iteritems():
                            p = MetadataProperty.objects.get(pk=key)
                            desc_value['properties'].append({'caption': p.caption, 'value': v_value})
            desc_dict['value'] = desc_value
            values.append(desc_dict)
        
        logger.debug("values : %s" %values)

        return values

    def get_descriptors(self, workspace=None):  
        """
        Retrieve descriptor values of the current item for the 
        given workspace
        @param workspace an instance of workspace.DAMWorkspace
        """
        from dam.metadata.models import MetadataDescriptorGroup

        if workspace:
            basic = MetadataDescriptorGroup.objects.filter(basic_summary=True, workspace=workspace)
            if basic.count() == 0:
                basic = MetadataDescriptorGroup.objects.filter(basic_summary=True)[0]
            else:
                basic = basic[0]
        else:
            basic = MetadataDescriptorGroup.objects.filter(basic_summary=True)[0]
        
        descriptors = {}
        for d in basic.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors

    def get_file_name(self):
        """
        Returns the file name found in the original variant
        """
        from dam.variants.models import Variant
        try:
            orig = self.component_set.get(variant__name = 'original')
            name = orig.file_name 
        except Component.DoesNotExist:
            name = ''
        return name

    def get_file_size(self):
        """
        Returns the file size found in the original variant
        """
#        logger.debug('######## ITEM=%s' % self.pk)
        try:
            orig = self.component_set.get(variant__name = 'original')
            return float(orig.size)
        except Exception,ex:
            logger.debug("Exception: %s" %ex)
            return float(0)

    def get_states(self, workspace=None):
        from dam.workflow.models import StateItemAssociation

        if workspace is None:
            return StateItemAssociation.objects.filter(item = self)
        else:
            return StateItemAssociation.get(item=self, workspace=workspace)

    def get_variant(self, workspace, variant):
        """
        Retrieve the component for the given variant and workspace
        @param workspace an instance of workspace.DAMWorkspace
        @param variant an instance of variants.Variant
        """
        from dam.variants.models import Variant
        try:
            return self.component_set.get(variant = variant, workspace = workspace)
        except Component.DoesNotExist:
            return self.create_variant(variant, workspace)

    def get_variants(self, workspace):
        """
        Retrieve all the item's components
        """
        from dam.variants.models import Variant
        return self.component_set.filter(variant__in = Variant.objects.filter(Q(workspace__isnull = True) | Q(workspace__pk = workspace.pk), hidden = False,  media_type = self.type),  workspace = workspace)

    def keywords(self):    
        """
        Retrieve all the keywords (taxonomy nodes)
        """
        
        return self.node_set.filter(type = 'keyword').values('id','label')

    def collections(self):    
        """
        Retrieve all the keywords (taxonomy nodes)
        """
        
        return self.node_set.filter(type = 'collection').values('id','label')


    def uploaded_by(self):
        """
        Return the uploader user object
        """
        return self.uploader
        
    def get_variant_url(self, variant_name, workspace):
        url = None       
        try:
            variant = workspace.get_variants().distinct().get(media_type =  self.type, name = variant_name)
            url = self.get_variant(workspace, variant).get_url()
                
        except Exception, ex:
            logger.error(ex)
            
        return url

    def _replace_groups(self, group, default_language):
        namespace = group.group('namespace')
        field = group.group('field')
        try:
            schema = MetadataProperty.objects.get(namespace__prefix=namespace, field_name=field)
            values = self.get_metadata_values(schema)
            if isinstance(values, list):
                value = values[0]
            elif isinstance(values, dict):
                value = values.get(default_language, '')
            else:
                value = values
            if not value:
                value = ''
    
            return value
        except:
            raise
            return ''
    

    def _get_caption(self, template_string, language):
        caption = ''
        try:
            pattern = re.compile('%(?P<namespace>\w+):(?P<field>\w+)%')
            groups = re.finditer(pattern, template_string)
            values_dict = {}
            for g in groups:
                values_dict[g.group(0)] = self._replace_groups(g, language)
    
            caption = template_string
    
            for schema in values_dict.keys():
                caption = caption.replace(schema, values_dict[schema])
    
            if not len(caption):
                #caption = str(self.get_file_name())
                caption = unicode(self.get_file_name())
        except Exception, ex:
            logger.exception(ex)
    
        return caption
        
    def get_info(self, workspace,  caption = None, default_language = None):        
        from dam.geo_features.models import GeoInfo
        if caption and default_language: 
           caption = self._get_caption(caption, default_language)
        else:
            caption = ''


#        now = '?t=' + str(time.time());
        t = time.mktime(self.get_last_update(workspace).utctimetuple())
        thumb_url = '/item/%s/%s/?t=%s'%(self.ID, 'thumbnail', t);
        preview_url = '/item/%s/%s/?t=%s'%(self.ID, 'preview', t);
        fullscreen_url = '/item/%s/%s/?t=%s'%(self.ID, 'fullscreen', t);
        in_progress = ProcessTarget.objects.filter(target_id = str(self.pk),actions_todo__gt = 0, process__workspace = workspace).count() > 0;
        
        if in_progress:
            status = 'in_progress';
#            now = '?t=' + str(time.time());
#            thumb_url += now;
#            preview_url += now;
#            fullscreen_url += now;
           
        else:
            status = 'completed'

        
        if GeoInfo.objects.filter(item=self).count() > 0:
            geotagged = 1
        else:
            geotagged = 0
        
        info = {
            'name': caption,
            'size':self.get_file_size(), 
            'pk': smart_str(self.pk), 
            '_id':self._id,
           
            'status': status,
            #'thumb': thumb_url is not None,
            'url':smart_str(thumb_url), 
            'type': smart_str(self.type.name),
            'url_preview':preview_url,
			'url_fullscreen': fullscreen_url,
#            'preview_available': False,
            'geotagged': geotagged
            }
            
        states = self.stateitemassociation_set.all()
        if states.count():
            state_association = states[0]
        
            info['state'] = state_association.state.pk
    
        return info


def get_storage_file_name(item_id, workspace_id, variant_name, extension):
    logger.debug(' ######## get_storage_file_name item_id=%s, workspace_id=%s, variant_name=%s, extension=%s' % (item_id, workspace_id, variant_name, extension))
    if not extension.startswith('.'):
        extension = '.' + extension
    return item_id +  '_' + str(workspace_id) + '_' + variant_name +  extension
                       
class Component(AbstractComponent):

    """ 
    Concrete class that inherits from the abstract class AbstractComponent found in core/dam_repository/models.py
    Base model describing components. They can be contained by items.
    """

    _id = models.CharField(max_length=70,  db_column = 'md_id')
    metadata = generic.GenericRelation('metadata.MetadataValue')
    
    variant = models.ForeignKey('variants.Variant')
    workspace = models.ManyToManyField('workspace.DAMWorkspace')    
    media_type = models.ForeignKey('core.dam_repository.Type')
    item = models.ForeignKey(Item)
    _previous_source_id = models.CharField(max_length=40,  null = True,  blank = True)
        
    uri = models.URLField(max_length=512, verify_exists = False,  blank = True,  null = True)
    imported = models.BooleanField(default = False) # if true related variant must not be regenarated from the original

    #new
    parameters = models.TextField(null = True,  blank = True)
    source = models.ForeignKey('self', null = True, blank = True)
    modified_metadata = models.BooleanField(default = False) 
    pipeline = models.ForeignKey('mprocessor.Pipeline', null = True, blank  = True, default = None)   

    # a JSON object with results from extract_basic. Syntax is dependent  on media_type
    _features = models.TextField(null=True, blank=True)  # do not use directly
    
    
    class Meta:
        db_table = 'component'

    def __unicode__(self):
        return self.ID
            
    def save(self, *args, **kwargs):
        import datetime
        super(Component, self).save(*args, **kwargs)
        self.item.update_last_modified(workspaces = self.workspace.all())
            
        #self.item.update_time = datetime.datetime.now()
        #self.item.save()

    def get_features(self):
        klass = {'video': AVFeatures,'audio':AVFeatures, 'image': ImageFeatures, 'doc': PdfFeatures, }
        if not hasattr(self, 'decoded_features'):
            if self._features:
                self.decoded_features = klass[self.media_type.name](loads(self._features))
            else:
                raise Exception('no features available')
        return self.decoded_features
         
    def set_source(self, source):
        self.source = source
        self._previous_source_id = source._id
    
    def copy_metadata(self, component):
        from dam.metadata.models import MetadataValue, MetadataProperty
        values = component.metadata.all().values('xpath', 'language', 'schema_id', 'value', 'content_type_id')
        for value in values:
            schema_id = value.pop('schema_id')
            value['schema'] = MetadataProperty.objects.get(pk = schema_id)
            value['object_id'] = self.pk
            MetadataValue.objects.create(**value)
            
    def _get_id(self):
        return self._id

    def _get_media_type(self):
        return self.type            

    def get_extractor(self):
        extractors = {'image': 'image_basic', 'video': 'media_basic', 'audio': 'media_basic', 'doc': 'doc_basic'}
        return extractors[self.media_type.name]

    ID = property(fget=_get_id)     
    media_type = property(fget=_get_media_type)
    
    def get_file_path(self):
        return os.path.join(MEDIADART_STORAGE, self.uri)
    
    def get_url(self, full_address = False):
        """
        Returns the component url (something like /storage/res_id.ext)
        """
        
        storage = Storage()
        url = None
        try:        
            file_name = self.uri
            if  storage.exists(file_name):
                url = os.path.join(STORAGE_SERVER_URL, file_name)
        
                if full_address:
                    url = SERVER_PUBLIC_ADDRESS + url
                
        except Exception, ex:
            logger.exception(ex)
        
        return url

    def save_rights_value(self, license_value, workspace):
    
        """
        Save license to the given component and set xmp 
        values according to right rules (as defined in XMPRightsValue)
        @param license_value an instance of metadata.RightsValue
        @param workspace an instance of workspace.DAMWorkspace
        """
        from metadata.models import RightsValue,  MetadataValue
    
        logger.debug("SAVING RIGHTS")

        try:    
            logger.debug('try')
            logger.debug('license_value %s' % license_value)
            if isinstance(license_value, RightsValue):
                license = license_value
            else:
                license = RightsValue.objects.get(value__iexact = license_value)

            self.comp_rights = []
            logger.debug('license %s'%license)
            self.metadata.filter(schema__rights_target=True).delete()
            license.components.add(self)
            item_list = [self.item]
        
            xmp_values = {}
            for m in license.xmp_values.all():
                logger.debug('m is %s while m.value is %s' % (m,m.value))
                if not isinstance(m.value, unicode):
                    xmp_values[m.xmp_property.id] = m.value.decode('utf-8')
                else:
                    xmp_values[m.xmp_property.id] = m.value
            logger.debug('xmp_values %s'%xmp_values)
            MetadataValue.objects.save_metadata_value(item_list, xmp_values, self.variant.name, workspace)

        except Exception,  ex:
            logger.debug(ex)
            
            logger.debug(self.variant.name)
            self.metadata.filter(schema__rights_target=True).delete()

            original_comp = self.source
            
            self.comp_rights = []
            self.comp_rights.add(*original_comp.comp_rights.all())
            for m in original_comp.metadata.filter(schema__rights_target=True):
                mv = MetadataValue.objects.create(schema = m.schema, xpath=m.xpath, content_object = self,  value = m.value, language=m.language)
                logger.debug('mv %s'%mv)
    
    def set_parameters(self, params):
        """
        Set adaptation parameters (ex. max_size, transcoding format, and so on)
        @param params a dictionary containing the adaptation parameters
        """
        params_str = ''
        logger.debug('params %s'%params)
        logger.debug('params.keys()%s'%params.keys())
        keys = params.keys()
        keys.sort()
        for key in keys:
            params_str += '%s=%s&'%(key,simplejson.dumps(params[key]))
        
        self.parameters = params_str
        self.save()
        
    def get_parameters(self):
        """
        Get adaptation parameters (ex. max_size, transcoding format, and so on)
        """
    
        logger.debug('self.parameters %s'%self.parameters)
        if self.parameters:
            tmp = dict(urlparse.parse_qsl(self.parameters))
            for key in tmp.keys():
                logger.debug('key %s value %s'%(key, tmp[key]))
                try:
                    tmp[key] = simplejson.loads(tmp[key])
                except:
                    pass
            return tmp
        else:
            return {}
                
    def get_formatted_filesize(self):
        """
        Returns the file size (something like 1.4 KB, 2.7 MB, ...)
        """
        from dam.metadata.views import format_filesize
        return format_filesize(self.size)
    
    def get_metadata_values(self, metadataschema=None):
        """
        Returns the metadata values for the current component and the given
        XMP Property
        If the XMP Property is not specified, it retrieves the metadata values
        for all the XMP Properties
        @param metadataschema an instance of metadata.MetadataProperty (optional)
        """
        from dam.metadata.models import MetadataValue
        values = []
        if metadataschema:
            schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.item.pk], metadataschema, set([self.item.type.name]), set([self.media_type.name]), [self.pk], self)
            if delete:
                return None
            if schema_value:
                if schema_value[self.item.pk]:
                    values = schema_value[self.item.pk]
                else:
	                values = None
            else:
                values = None
        else:
            for m in self.metadata.all().distinct('schema').values('schema'):
                prop = MetadataProperty.objects.get(pk=m['schema'])
                schema_value, delete, b = MetadataValue.objects.get_metadata_values([self.item.pk], prop, set([self.item.type.name]), set([self.media_type.name]), [self.pk], self)
                if delete:
                    return None
                if schema_value:
                    if schema_value[self.item.pk]:
                        values.append({'%s' % prop.pk: schema_value[self.item.pk]})

        return values

    def get_formatted_descriptors(self, group, user, workspace):
        """
        Retrieves all the values for the descriptors for the current component
        and returns them in the format required by the Metadata GUI
        @param group an instance of MetadataDescriptorGroup
        @param user an instance of auth.User
        @param workspace an instance of workspace.DAMWorkspace
        """
        from dam.metadata.models import MetadataDescriptor, MetadataProperty
        from dam.preferences.views import get_metadata_default_language
    
        descriptors = self.get_descriptors(group)
        default_language = get_metadata_default_language(user, workspace)
        values = []
        for d, v in descriptors.iteritems():
            desc = MetadataDescriptor.objects.get(pk=d)
            desc_dict = {'caption': '%s' % desc.name}
            desc_value = v
            logger.info("desc_value %s " %desc_value)
            if isinstance(v, dict):
                if v.has_key(default_language):
                    desc_value = v.get(default_language)
                else:
                    continue
            elif isinstance(v, list):
                for value in v:
                    if isinstance(value, dict):
                        if not isinstance(desc_value, dict):
                            desc_value = {'properties': []}
                        for key, v_value  in value.iteritems():
                            p = MetadataProperty.objects.get(pk=key)
                            desc_value['properties'].append({'caption': p.caption, 'value': v_value})
            desc_dict['value'] = desc_value
            values.append(desc_dict)

        return values

    def get_descriptors(self, desc_group):
        """
        Returns the descriptors value for the given descriptor group
        @param desc_group an instance of metadata.MetadataDescriptorGroup
        """
        item_list = [self.item.pk]
        descriptors = {}
        for d in desc_group.descriptors.all():
            for p in d.properties.all():
                schema_value = self.get_metadata_values(p)
                if schema_value:
                    descriptors[d.pk] = schema_value
                    break

        return descriptors
    
    def get_variant(self):
        """
        Returns the component's variant
        """
        return self.variant
                
class Watermark(AbstractComponent):

    """ 
    Concrete class that inherits from the abstract class AbstractComponent found in core/dam_repository/models.py
    Base model describing watermark images. They can be contained by workspaces only.
    """

    _id = models.CharField(max_length=40,  db_column = 'md_id')
    workspace = models.ForeignKey('workspace.DAMWorkspace')    
    
    class Meta:
        db_table = 'watermark'

    def __unicode__(self):
        return self.ID
    
    def _get_id(self):
        return self._id

    def get_url(self):
        """
        Returns the component url (something like /storage/res_id.ext)
        """
        from dam.application.views import NOTAVAILABLE

        url = NOTAVAILABLE    
       
        try:
            url = _get_resource_url(self.ID)
            logger.debug('url : %s' %url)
        except Exception,ex:
            logger.error(ex)
            url = NOTAVAILABLE    
            
        return url

    ID = property(fget=_get_id)     

    

#
#
# Utility classes for hiding the details of the syntax of the feature dictionary
# in a Component
#
#


class AVFeatures:
    def __init__(self, features):
        self.info = {}
        self.info['video'] = [features[x] for x in features.keys() if x != 'file' and features[x]['codec_type'] == 'video']
        self.info['audio'] = [features[x] for x in features.keys() if x != 'file' and features[x]['codec_type'] == 'audio']

    def __get_attr(self, name, stream_type):
        if self.info[stream_type]:
            return self.info[stream_type][0][name]
        else:
            raise Exception('No video')

    def get_video_width(self):
        return self.__get_attr('width', 'video')

    def get_video_height(self):
        return self.__get_attr('height', 'video')

    def get_video_codec(self):
        return self.__get_attr('codec_name', 'video')

    def get_audio_codec(self):
        return self.__get_attr('codec_name', 'audio')

    def get_video_duration(self):
        return self.__get_attr('duration', 'video')

    def get_video_frame_rate(self):
        return '%s/%s' % (self.__get_attr('r_frame_rate_num', 'video'), self.__get_attr('r_frame_rate_den', 'video'))

    def get_audio_sample_rate(self):
        return self.__get_attr('sample_rate', 'audio')

    def has_audio(self):
        return not not self.info['audio']

    def has_video(self):
        return not not self.info['video']

#class AudioFeatures:
#    def __init__(self, features):
#        self.features = features
#        self.audio = [x for x in self.features['streams'].values() if x['codec_type'] == 'audio']
#        self.has_audio = not (not self.audio)
#
#    def get_codec_name(self):
#        return self.audio[0]['codec_name']
#
#    def get_duration(self):
#        return self.audio[0]['duration']
#
#    def get_sample_rate(self):
#        return '%s/%s' % (self.video[0]['r_frame_rate_num'], self.video[0]['r_frame_rate_den'])
#

class ImageFeatures:
    def __init__(self, features):
        self.features = features

    def get_codec_name(self):
        return self.features['codec']

    def get_depth(self):
        return self.features['depth']

    def has_frame(self):
        "returns True if the images contains more frames"
        return self.features['has_frame']

    def get_size(self):
        return self.features['size']

    def get_width(self):
        return self.features['width']

    def get_height(self):
        return self.features['height']



class PdfFeatures:
    def __init__(self, features):
        self.features = features

    def get_num_pages(self):
        return self.features['Pages']

    def get_size(self):
        return self.features['size']

    def get_title(self):
        return self.features['Title']


########################################################################
# Format of the produced features.
#
#{'0': {'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
#       'codec_name': 'h264',
#       'codec_type': 'video',
#       'decoder_time_base': '125/5994',
#       'display_aspect_ratio': '12/5',
#       'duration': '149.899899',
#       'gop_size': '12',
#       'has_b_frames': '0',
#       'height': '800',
#       'index': '0',
#       'nb_frames': '0',
#       'pix_fmt': 'yuv420p',
#       'r_frame_rate': '23.976024',
#       'r_frame_rate_den': '1001',
#       'r_frame_rate_num': '24000',
#       'sample_aspect_ratio': '1/1',
#       'size': '140175513.000000',
#       'start_time': '0.000000',
#       'time_base': '1/1000',
#       'width': '1920'},
# '1': {'bits_per_sample': '0',
#       'channels': '2',
#       'codec_long_name': 'Advanced Audio Coding',
#       'codec_name': 'aac',
#       'codec_type': 'audio',
#       'decoder_time_base': '0/1',
#       'duration': '149.899899',
#       'index': '1',
#       'nb_frames': '0',
#       'sample_rate': '44100.000000',
#       'size': '140175513.000000',
#       'start_time': '0.023000',
#       'time_base': '1/1000'},
# 'file': {'bit_rate': '0.000000',
#          'demuxer_long_name': 'FLV format',
#          'demuxer_name': 'flv',
#          'duration': '149.899899',
#          'filename': '/home/orlando/Videos/tron.flv',
#          'index': 'file',
#          'nb_streams': '2',
#          'size': '140175513.000000',
#          'start_time': '0.000000'}}
#
#########################################################################
#
# application/pdf features
# {'Author': 'SAngioni',
#  'CreationDate': 'Fri Mar  4 15:36:08 2011',
#  'Creator': 'Microsoft\xc2\xae Office Word 2007',
#  'Encrypted': 'no',
#  'File size': '428472 bytes',
#  'ModDate': 'Fri Mar  4 15:36:08 2011',
#  'Optimized': 'no',
#  'PDF version': '1.5',
#  'Page size': '595.32 x 841.92 pts (A4)',
#  'Pages': '9',
#  'Producer': 'Microsoft\xc2\xae Office Word 2007',
#  'Tagged': 'yes',
#  'Title': 'bollettinobandi',
#  'size': 428472L}
# 
#########################################################################
#
# #image/* features
#
# {'codec': 'jpeg',
#  'depth': '8',
#  'depth_unit': 'bit',
#  'has_frame': False,
#  'has_sound': False,
#  'height': '600',
#  'size': 73728L,
#  'width': '400'}
# 

