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

from django.core.management import setup_environ
import settings
setup_environ(settings)

from twisted.internet.task import LoopingCall
from twisted.internet import reactor, threads, defer 
#import logger
import datetime 
import os.path
import urllib
import os
import shutil
import uuid
import time

from django.db.models import Q
from django.db import reset_queries
from django.contrib.contenttypes.models import ContentType

from dam.batch_processor.models import MDTask, Machine, MachineState, Action
from dam.repository.models import Item, Component
from dam.variants.models import ImagePreferences,  VideoPreferences,  AudioPreferences

from dam.metadata.models import MetadataProperty, Namespace, MetadataValue
from dam.metadata.views import save_variants_rights
from dam.xmp_embedding import synchronize_metadata, reset_modified_flag

from settings import INSTALLATIONPATH,  MEDIADART_CONF
THUMBS_DIR = os.path.join(INSTALLATIONPATH,  'thumbs')

import logging
logger = logging.getLogger('batch_processor')
logger.addHandler(logging.FileHandler(os.path.join(INSTALLATIONPATH,  'log/batch_processor.log')))
logger.setLevel(logging.DEBUG)

from mediadart.storage import Storage
from mediadart.storage import new_id
from mediadart.mqueue.mqclient_twisted import Proxy

def cb_error(result, component, machine):
    current_state = machine.current_state
    new_action = current_state.action
    failed_state = MachineState.objects.create(name='failed', action=new_action)
    machine.current_state = failed_state
    machine.save()

def machine_to_next_state(machine):
    current_state = machine.current_state
    if current_state.next_state:
        machine.current_state = current_state.next_state
        machine.save()
        execute_state(machine)

def add(component, machine):
#     res_id = new_id(component.file_name)
#     print res_id
#     shutil.copy2(component._id, os.path.join('/tmp/prova/', res_id))
#     print 'copied!'
#     component._id = res_id
#     component.save()
    machine_to_next_state(machine)

def embed_xmp(component, machine):

    def embedding_cb(result, component, machine):
        if result:
            reset_modified_flag(component)
            machine_to_next_state(machine)    
    
    xmp_embedder_proxy = Proxy('XMPEmbedder') 

    metadata_dict = synchronize_metadata(component)

    d = xmp_embedder_proxy.metadata_synch(component.ID, metadata_dict)

    d.addCallbacks(embedding_cb, cb_error, callbackArgs=[component, machine], errbackArgs=[component, machine])

def adapt_resource(component, machine):

    def save_and_extract_features(result, component, machine):
        if result:
            dir, name = os.path.split(result)
            component._id = name
            component.save()
#            extract_features(component)
            machine_to_next_state(machine)

    logger.debug("[Adaptation.execute] component %s" % component.ID)

    adapter_proxy = Proxy('Adapter') 

    item = component.item
    workspace = component.workspace.all()[0] 

    variant = component.variant
    
    source_variant = variant.get_source(workspace,  item)

#    vp = variant.get_preferences(workspace)
    vp = component.get_parameters()
    orig = source_variant.get_component(workspace = workspace,  item = item) 

    dest_res_id = new_id()
        
    if item.type == 'image':
 
        transcoding_format = vp.get('codec','jpg') #change to original format
        max_dim = vp.get('max_dim', -1) 
        cropping = vp.get('cropping', False)
        watermark_enabled = vp.get('watermarking', False)

#         if cropping:
# 
#             extractors = {'image': 'image_basic', 'movie': 'video_basic', 'audio': 'audio_basic', 'doc': ''}
# 
#             my_media_type = orig.media_type.name
#             my_extractor = extractors[my_media_type]
# 
#             f = t.get_features(orig.ID, [my_extractor])
#             features = yield f.parse()
#             width = int(features[my_extractor]['width'])
#             height = int(features[my_extractor]['height'])
#             if width > 0 and height > 0:
#                 delta = int((width - height) / 2)
#                 if delta > 0:
#                     src_x = delta
#                     src_y = 0
#                     src_height = src_width = height
#                 else:
#                     src_x = 0
#                     src_y = -delta
#                     src_height = src_width = width
#             if max_dim > src_width:
#                 crop_dim = src_width
#             else:
#                 crop_dim = max_dim
# 
#             if watermark_enabled:
#                 (res_id, job_id) = yield m.adapt_image(transcoding_format, src_x = src_x, src_y = src_y, src_width = src_width, src_height = src_height, dest_width = crop_dim, dest_height = crop_dim, watermark='/opt/mediadart/share/logo-s.png', output_res_id=component.ID)
#             else:
#                 (res_id, job_id) = yield m.adapt_image(transcoding_format, src_x = src_x, src_y = src_y, src_width = src_width, src_height = src_height, dest_width = crop_dim, dest_height = crop_dim, output_res_id=component.ID)
#                 

#         else:

        dest_res_id = dest_res_id + '.' + transcoding_format

        if watermark_enabled:
            d = adapter_proxy.adapt_image(orig.ID, dest_res_id, dest_size=(max_dim, max_dim), watermark='/opt/mediadart/share/logo-s.png')
        else:
            d = adapter_proxy.adapt_image(orig.ID, dest_res_id, dest_size=(max_dim, max_dim))

    elif item.type == 'movie':

        if component.variant.media_type.name == "image":

            dim_x = vp['max_dim']
            dim_y = vp['max_dim']
            

            d = adapter_proxy.extract_video_thumbnail(orig.ID, dest_res_id, thumb_size=(dim_x, dim_y))

        else:

            preset_name = vp['preset_name']

            param_dict = vp

            dest_res_id = dest_res_id + '.' + preset_name
            
            for key, val in vp.items():
                if key == 'preset_name':
                    continue
                
                if key == 'max_size':
                    param_dict[key] = int(val)
                else:
                    param_dict[key] = val
                
#             if  vp.watermarking:
#                 param_dict['watermark_uri'] = 'mediadart://' + vp.watermark_uri
#                 param_dict.update(vp.get_watermarking_params())
#                 #param_dict['watermark_top'] = 10
#                 #param_dict['watermark_left'] = 10
#                 yield utils.wait_for_resource(vp.watermark_uri, 5)
                
            d = adapter_proxy.adapt_video(orig.ID, dest_res_id, preset_name,  param_dict)
            

    elif item.type == 'audio':

        
        preset_name = vp['preset_name']        
        param_dict = dict(vp)        

        dest_res_id = dest_res_id + '.' + preset_name
        
        
        d = adapter_proxy.adapt_audio(orig.ID, dest_res_id, preset_name, param_dict)
    
    if item.type == 'doc':
 
        transcoding_format = vp['codec']
        max_size = vp['max_dim']
        
        dest_res_id = dest_res_id + '.' + transcoding_format
        
        d = adapter_proxy.adapt_doc(orig.ID, dest_res_id, max_size)

    d.addCallbacks(save_and_extract_features, cb_error, callbackArgs=[component, machine], errbackArgs=[component, machine])

    logger.debug("[Adaptation.end] component %s" % component.ID)

#    defer.returnValue( (task, job_id) )

def extract_features(component, machine):

    def save_features(result, component, machine):
        save_component_features (component, result)
        machine_to_next_state(machine)

    logger.debug("[FeatureExtraction.execute] component %s" % component.ID)

    extractors = {'image': 'image_basic', 'movie': 'video_basic', 'audio': 'audio_basic', 'doc': 'doc_basic'}

    extractor_proxy = Proxy('FeatureExtractor')

    workspace = component.workspace.all()[0] 

    my_media_type = component.media_type.name
    my_extractor = extractors[my_media_type]

    if component.variant.auto_generated:
        extractor_list = [my_extractor]
    else:
        extractor_list = [my_extractor, 'xmp_extractor']

    d = extractor_proxy.extract_features(component.ID, extractor_list)
    d.addCallbacks(save_features, cb_error, callbackArgs=[component, machine], errbackArgs=[component, machine])

    logger.debug("[FeatureExtraction.end] component %s" % component.ID)

def save_rights(component, machine):

    logger.debug("[SetRights.execute] component %s" % component.ID)
    
    workspace = component.workspace.all()[0] 
    item = component.item
    variant = component.variant

    save_variants_rights(item, workspace, variant)

    machine_to_next_state(machine)

    logger.debug("[SetRights.end] component %s" % component.ID)

def read_xmp_features(item, features, component):
    from time import strptime
    import re

    xpath = re.compile(r'(?P<prefix>\w+):(?P<property>\w+)(?P<array_index>\[\d+\]){,1}')

    ctype = ContentType.objects.get_for_model(item)
    ctype_component = ContentType.objects.get_for_model(component)

    metadata_dict = {}

    metadata_list = []
    delete_list = []

    logger.debug('READ XMP FEATURES')

    if not isinstance(features['xmp_extractor'], dict):
        item.state = 1  
        item.save()
        return metadata_list, delete_list
    for feature in features['xmp_extractor'].keys():
        try:
            namespace_obj = Namespace.objects.get(uri=feature)
        except:
            logger.debug('unknown namespace %s' % feature)
            continue

        metadata_dict[namespace_obj] = {}

        namespace_properties = MetadataProperty.objects.filter(namespace=namespace_obj)
        for property_values in features['xmp_extractor'][feature]:
            property_xpath = property_values[0]
            property_value = property_values[1]
            property_options = property_values[2]
            xpath_splitted = xpath.findall(property_xpath)
            metadata_property = xpath_splitted[0][1].strip()
            metadata_index = xpath_splitted[0][2].strip()
            found_property = namespace_properties.filter(field_name__iexact=metadata_property)
            if found_property.count() > 0 and len(property_value.strip()) > 0:
                if found_property[0].is_array == 'not_array':
                    delete_list.append(found_property[0])
                if property_options['IS_QUALIFIER'] and xpath_splitted[-1][1] == 'lang':
                    find_xpath = property_xpath.replace('/?xml:lang', '')
                    if metadata_dict[namespace_obj].has_key(find_xpath):
                        if property_value == 'x-default':
                            property_value = settings.METADATA_DEFAULT_LANGUAGE
                        metadata_dict[namespace_obj][find_xpath].language = property_value
                    else:
                        logger.debug('metadata property not found: ' + find_xpath)
                else:
                    if found_property[0].is_variant:
                        x = MetadataValue(schema=found_property[0], object_id=component.pk, content_type=ctype_component, value=property_value, xpath=property_xpath)
                    else:
                        x = MetadataValue(schema=found_property[0], object_id=item.pk, content_type=ctype, value=property_value, xpath=property_xpath)
                    metadata_dict[namespace_obj][property_xpath] = x
                    metadata_list.append(x)

    return metadata_list, delete_list

def save_component_features(component, features):

    xmp_metadata_commons = {'size':[('notreDAM','FileSize')]}
    xmp_metadata_audio = {'channels':[('xmpDM', 'audioChannelType')], 'sample_rate':[('xmpDM', 'audioSampleRate')], 'duration':[('notreDAM', 'Duration')]}

    xmp_metadata_video = {'height':[('xmpDM', 'videoFrameSize','stDim','h')] , 'width':[('xmpDM', 'videoFrameSize','stDim','w')], 'fps':[('xmpDM','videoFrameRate')], 'bit_rate':[('xmpDM','fileDataRate')], 'duration':[('notreDAM', 'Duration')]}
    xmp_metadata_image = {'height':[('tiff', 'ImageLength')] , 'width':[('tiff', 'ImageWidth')]}
    xmp_metadata_doc = {'pages': [('notreDAM', 'NPages')], 'Copyright': [('dc', 'rights')]}

    xmp_metadata_image.update(xmp_metadata_commons)
    xmp_metadata_audio.update(xmp_metadata_commons)
    xmp_metadata_doc.update(xmp_metadata_commons)

    xmp_metadata_video.update(xmp_metadata_audio)

    xmp_metadata = {'image': xmp_metadata_image, 'movie': xmp_metadata_video, 'audio': xmp_metadata_audio, 'doc': xmp_metadata_doc}

    logger.debug("[ExtractMetadata.execute] component %s" % component.ID)

    c = component
    metadata_list = []
    xmp_metadata_list = []
    delete_list = []
    xmp_delete_list = []
    workspace = c.workspace.all()[0] 

    source_variant = c.variant.get_source(workspace,  c.item)

    extractors = {'image': 'image_basic', 'movie': 'video_basic', 'audio': 'audio_basic', 'doc': 'doc_basic'}

    my_media_type = c.media_type.name    
    my_extractor = extractors[my_media_type]

    ctype = ContentType.objects.get_for_model(c)

    if features.get('xmp_extractor', None):
        item = Item.objects.get(component = c)
        xmp_metadata_list, xmp_delete_list = read_xmp_features(item, features, c)
    if features.get(my_extractor, None) and isinstance(features.get(my_extractor, None), dict):
        lang = settings.METADATA_DEFAULT_LANGUAGE
        for feature in features[my_extractor].keys():
            if features[my_extractor][feature]=='' or features[my_extractor][feature] == '0':
                continue 
            if feature == 'size':
                c.size = features[my_extractor][feature]
            if feature == 'height':
                c.height = features[my_extractor][feature]
            elif feature == 'width':
                c.width = features[my_extractor][feature]

            try:
                xmp_names = xmp_metadata[my_media_type][feature]
            except KeyError:
                continue

            for m in xmp_names:

                try:
                    ms = MetadataProperty.objects.get(namespace__prefix=m[0], field_name= m[1])
                except:
                    logger.debug( 'inside readfeatures, unknown metadata %s:%s ' %  (m[0],m[1]))
                    continue
                if ms.is_variant or c.variant.name == 'original':
                    if len(m) == 4:
                        property_xpath = "%s:%s[1]/%s:%s" % (m[0], m[1], m[2], m[3])
                    else:
                        property_xpath = ''
                    try:
                        if ms.type == 'lang':
                            x = MetadataValue(schema=ms, object_id=c.pk, content_type=ctype, value=features[my_extractor][feature], language=lang, xpath=property_xpath)
                        else:                            
                            x = MetadataValue(schema=ms, object_id=c.pk, content_type=ctype, value=features[my_extractor][feature], xpath=property_xpath)
                        metadata_list.append(x) 
                        delete_list.append(ms) 
                    except:
                        logger.debug('inside readfeatures, could not get %s' %  ms)
                        continue
    
        c.state = 1
        c.save()

    MetadataValue.objects.filter(schema__in=delete_list, object_id=c.pk, content_type=ctype).delete()

    for x in metadata_list:
        x.save()

    MetadataValue.objects.filter(schema__in=xmp_delete_list, object_id=c.pk, content_type=ctype).delete()

    for x in xmp_metadata_list:
        x.save()

    logger.debug("[ExtractMetadata.end] component %s" % component.ID)

def remove_sm(sm):
    try:
        running_sm.remove(sm)
    except:
        pass

def find_sm():
    try:

        available_sm = Machine.objects.filter(wait_for__current_state__name='finished') | Machine.objects.filter(wait_for__isnull=True)
        available_sm = available_sm.exclude(pk__in=running_sm).exclude(current_state__name='finished').exclude(current_state__name='failed').exclude(current_state__name='fake')

        if available_sm.count() > 0:
            sm = available_sm[0].pk
        else:
            sm = None
            
        if sm:
            running_sm.append(sm)
                
        return sm

    except Exception, ex:
#        print 'ex %s'%ex
        return(None)

@defer.inlineCallbacks
def find_statemachine():
    logger.debug('finding tasks...')
    machine = yield lock.run(find_sm)

    if machine is not None:

        execute_machine(machine)
        
#    time.sleep(1)
    
#    reactor.callInThread(find_statemachine)
 
    reactor.callLater(1, find_statemachine)
 
def execute_state(machine):

    state = machine.current_state

    if state.action:
        my_func = globals()[state.action.function]
        my_func(state.action.component, machine)
                    
def execute_machine(sm):
    try:

        machine = Machine.objects.get(pk=sm)            
        execute_state(machine)

    except Exception, ex:
        raise
        print ex

def recursive_delete(state):
    try:
        if state.next_state:
            recursive_delete(state.next_state)
        if state.action:
            state.action.delete()
        state.delete()
    except Exception, ex:
        print ex
        pass
                                                                                          
def cleanup():

    finished = Machine.objects.filter(current_state__name='finished')

    for m in finished:
        if m.machine_set.all().count() == m.machine_set.filter(current_state__name='finished').count():
            try:
                recursive_delete(m.initial_state)
                remove_sm(m.pk)
            except:
                continue
            finally:
                m.delete()
            
@defer.inlineCallbacks
def clean_task():

#    tasks_wait_for = MDTask.objects.filter(wait_for__isnull=False).values_list('wait_for', flat=True)
#    tasks_to_check = MDTask.objects.filter(wait_for__isnull=True, job_id__isnull=False, status__isnull=True).exclude(id__in=tasks_wait_for)

    logger.debug("[CleanTask.execute]")

    yield lock.run(cleanup)
    
    logger.debug("[CleanTask.end]")

    reset_queries()

#    time.sleep(2)

#    reactor.callInThread(clean_task)

    reactor.callLater(2, clean_task)

global lock
global running_sm
running_sm = []
lock = defer.DeferredLock()

#reactor.callInThread(find_statemachine)
#reactor.callInThread(clean_task)

reactor.callLater(3, find_statemachine)
reactor.callLater(2, clean_task)


reactor.run()

