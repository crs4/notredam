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

from twisted.internet import reactor, threads, defer 
#import logger
import datetime 
import os.path
import urllib
import os

os.environ['USE_TWISTED'] = '1'

from django.db.models import Q
from django.db import reset_queries
from django.contrib.contenttypes.models import ContentType

from dam.batch_processor.models import MDTask
from dam.repository.models import Item, Component
from dam.variants.models import ImagePreferences,  VideoPreferences,  AudioPreferences

from dam.metadata.models import MetadataProperty, Namespace, MetadataValue
from dam.metadata.views import save_variants_rights

from mediadart import toolkit

from settings import INSTALLATIONPATH,  MEDIADART_CONF
THUMBS_DIR = os.path.join(INSTALLATIONPATH,  'thumbs')

import logging
logger = logging.getLogger('batch_processor')
logger.addHandler(logging.FileHandler(os.path.join(INSTALLATIONPATH,  'log/batch_processor.log')))
logger.setLevel(logging.DEBUG)

@defer.inlineCallbacks
def perform_adaptation_task(task):

    t = toolkit.Toolkit(settings.MEDIADART_CONF)
    utils = t.get_utils()

    if task.wait_for is not None: 
        if task.wait_for.job_id is None:
            defer.returnValue( (task, 'None') )
        elif task.wait_for.job_id == '':
            pass
        else:
            try:
                stat = yield utils.wait_for_job(task.wait_for.job_id, 5)
#                stat = utils.get_job_status(task.wait_for.job_id)
#                if stat != 1:
#                    return (task, 'None') 
            except:
                defer.returnValue( (task, 'None') )
 
    logger.debug("[Adaptation.execute] task %d" % task.id)
 
    component = task.component
    item = Item.objects.get(component = component)
#    print 'component %s'%component
    workspace = component.workspace.all()[0] 
#    TODO: temporary...

#    print 'workspace  %s'%workspace
    variant = component.variant
    
    source_variant = variant.get_source(workspace,  item)
#    logger.debug('variant %s'%variant)
    vp = variant.get_preferences(workspace)
#    orig = variant.source.get_component( workspace,  item)
    orig = source_variant.get_component(workspace = workspace,  item = item) 
    
    yield utils.wait_for_resource(orig.ID, 5)
    
    if item.type == 'image':
#        print 'image'
 
        transcoding_format = vp.codec
        max_dim = vp.max_dim 
        cropping = vp.cropping
        watermark_enabled = vp.watermarking

        m = t.get_media(orig.ID)
#        logger.debug('orig.ID %s'%orig.ID)

#        logger.debug(cropping)

        if cropping:

            extractors = {'image': 'image_basic', 'movie': 'video_basic', 'audio': 'audio_basic', 'doc': ''}

            my_media_type = orig.media_type.name
            my_extractor = extractors[my_media_type]

            f = t.get_features(orig.ID, [my_extractor])
            features = yield f.parse()
            width = int(features[my_extractor]['width'])
            height = int(features[my_extractor]['height'])
            if width > 0 and height > 0:
                delta = int((width - height) / 2)
                if delta > 0:
                    src_x = delta
                    src_y = 0
                    src_height = src_width = height
                else:
                    src_x = 0
                    src_y = -delta
                    src_height = src_width = width
#                print width, height, src_width, max_dim
            if max_dim > src_width:
                crop_dim = src_width
            else:
                crop_dim = max_dim

#            print src_x, src_y, src_width, src_height, crop_dim, crop_dim
#            logger.debug('--------watermark_enabled %s'%watermark_enabled)
            if watermark_enabled:
                (res_id, job_id) = yield m.adapt_image(transcoding_format, src_x = src_x, src_y = src_y, src_width = src_width, src_height = src_height, dest_width = crop_dim, dest_height = crop_dim, watermark='/opt/mediadart/share/logo-s.png', output_res_id=component.ID)
            else:
                (res_id, job_id) = yield m.adapt_image(transcoding_format, src_x = src_x, src_y = src_y, src_width = src_width, src_height = src_height, dest_width = crop_dim, dest_height = crop_dim, output_res_id=component.ID)
                

        else:
#            logger.debug('component.ID %s'%component.ID)
#            logger.debug('transcoding_format %s'%transcoding_format)
#            logger.debug('max_dim %s'%max_dim)

            if watermark_enabled:
                (res_id, job_id) = yield m.adapt_image(transcoding_format, max_size=max_dim, watermark='/opt/mediadart/share/logo-s.png', output_res_id=component.ID)
            else:
                (res_id, job_id) = yield m.adapt_image(transcoding_format, max_size=max_dim, output_res_id=component.ID)

    elif item.type == 'movie':
#        print 'movie'

        m = t.get_media(orig.ID)
#        logger.debug('orig.ID %s'%orig.ID)

        if vp.media_type.name == "image":

            dim_x = vp.max_dim
            dim_y = vp.max_dim
            thumbnail_position = vp.video_position

            (res_id, job_id) = yield m.extract_video_thumbnail(dim_x, dim_y, thumbnail_position, output_res_id=component.ID)

        else:

            preset_name = vp.preset.name
            param_dict = {}
#            logger.debug('vp.pk %s'%vp.pk)
            for val in vp.values.all():
#                logger.debug('val.value %s'%val.value)
                if val.parameter.name == 'max_size':
                    param_dict[val.parameter.name] = int(val.value)
                else:
                    param_dict[val.parameter.name] = val.value
                
#            logger.debug('preset_name %s'%preset_name)
#            logger.debug('param_dict %s'%param_dict)
#            logger.debug('output_res_id %s'%component.ID)
            if  vp.watermarking:
                param_dict['watermark_uri'] = 'mediadart://' + vp.watermark_uri
                param_dict.update(vp.get_watermarking_params())
                #param_dict['watermark_top'] = 10
                #param_dict['watermark_left'] = 10
                yield utils.wait_for_resource(vp.watermark_uri, 5)
                
#                TODO
            
            
            (res_id, job_id) = yield m.adapt_video2(preset_name,  param_dict,  output_res_id=component.ID)
            

    elif item.type == 'audio':

        preset_name = vp.preset.name
        param_dict = {}
        
        for val in vp.values.all():
                param_dict[val.parameter.name] = val.value
            
#        logger.debug('preset_name %s'%preset_name)
#        logger.debug('param_dict %s'%param_dict)
#        logger.debug('output_res_id %s'%component.ID)

        m = t.get_media(orig.ID)
    
        (res_id, job_id) = yield m.adapt_audio2(preset_name,  param_dict,  output_res_id=component.ID)
        
    
    
    if item.type == 'doc':
 
        transcoding_format = vp.codec
        max_size = vp.max_dim
        
        m = t.get_media(orig.ID)
#        logger.debug('orig.ID %s'%orig.ID)

        (res_id, job_id) = yield m.adapt_doc(transcoding_format,  max_size = max_size,  output_res_id=component.ID)

    logger.debug("[Adaptation.end] task %d" % task.id)

    defer.returnValue( (task, job_id) )

@defer.inlineCallbacks
def perform_feature_extraction_task(task):
#    print 'perform_feature_extraction_task'
    t = toolkit.Toolkit(settings.MEDIADART_CONF)
    utils = t.get_utils()

    if task.wait_for is not None: 
        if task.wait_for.job_id is None:
            defer.returnValue( (task, 'None') )
        elif task.wait_for.job_id == '':
            pass
        else:
            try:
                stat = yield utils.wait_for_job(task.wait_for.job_id, 5)
#                stat = utils.get_job_status(task.wait_for.job_id)
#                if stat != 1:
#                    return (task, 'None') 
            except:
                defer.returnValue( (task, 'None') )

    logger.debug("[FeatureExtraction.execute] task %d" % task.id)

    component = task.component
    workspace = component.workspace.all()[0] 
#    source_variant = workspace.get_source(component.variant.media_type,  component.item)
#    source_variant = component.variant.get_source(workspace,  component.item)

    yield utils.wait_for_resource(component.ID, 5)

    extractors = {'image': 'image_basic', 'movie': 'video_basic', 'audio': 'audio_basic', 'doc': 'doc_basic'}

    my_media_type = component.media_type.name    
    my_extractor = extractors[my_media_type]

#    print my_extractor, my_media_type

    if component.variant.auto_generated:        
        f = t.get_features(component.ID,  [my_extractor])
    else:
        f = t.get_features(component.ID,  [my_extractor, 'xmp_extractor'])
                    
    try:
        job_id = yield f.extract(True)
    except:
        job_id = None

    logger.debug("[FeatureExtraction.end] task %d" % task.id)

    defer.returnValue( (task, job_id) )

@defer.inlineCallbacks
def perform_save_thumb_task(task):
#    print 'perform_feature_extraction_task'
    t = toolkit.Toolkit(settings.MEDIADART_CONF)
    utils = t.get_utils()
    storage = t.get_storage()

    if task.wait_for is not None: 
        if task.wait_for.job_id is None:
            defer.returnValue( (task, 'None') )
        elif task.wait_for.job_id == '':
            pass
        else:
            try:
                stat = yield utils.wait_for_job(task.wait_for.job_id, 5)
#                stat = utils.get_job_status(task.wait_for.job_id)
#                if stat != 1:
#                    return (task, 'None') 
            except:
                defer.returnValue( (task, 'None') )

    logger.debug("[SaveThumb.execute] task %d" % task.id)

    component = task.component

    yield utils.wait_for_resource(component.ID, 5)

    try:
        resource_url = yield storage.get_resource_url(component.ID)
        if resource_url:
            ext = os.path.splitext(resource_url[0])[1]
            urllib.urlretrieve(resource_url[0], os.path.join(settings.THUMBS_DIR,  component.ID + ext)) 
            job_id = ''
        else:
            job_id = None
    except Exception, ex:
        job_id = None
#        logger.debug(ex)

    logger.debug("[SaveThumb.end] task %d" % task.id)

    defer.returnValue( (task, job_id) )

@defer.inlineCallbacks
def perform_set_rights(task):
#    print 'perform_feature_extraction_task'
    t = toolkit.Toolkit(settings.MEDIADART_CONF)
    utils = t.get_utils()

    if task.wait_for is not None: 
        if task.wait_for.job_id is None:
            defer.returnValue( (task, 'None') )
        elif task.wait_for.job_id == '':
            pass
        else:
            try:
                stat = yield utils.wait_for_job(task.wait_for.job_id, 5)
#                stat = utils.get_job_status(task.wait_for.job_id)
#                if stat != 1:
#                    return (task, 'None') 
            except:
                defer.returnValue( (task, 'None') )

    logger.debug("[SetRights.execute] task %d" % task.id)
    
    component = task.component
    workspace = component.workspace.all()[0] 
    item = component.item
    variant = component.variant
    

    source_variant = variant.get_source(workspace,  item)

    orig = source_variant.get_component(workspace = workspace,  item = item) 

    orig_metadata = MDTask.objects.filter(component=orig, task_type='extract_metadata')

    job_id = None

    if orig_metadata.count() == 0:
        save_variants_rights(item, workspace, variant)        
        job_id = ''

    for t in orig_metadata:
        if t.job_id == '':
            save_variants_rights(item, workspace, variant)        
            job_id = ''
            
    logger.debug("[SetRights.end] task %d" % task.id)

    defer.returnValue ((task, job_id))

def new_read_xmp_features(item, features, component):
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

#        print features['xmp_extractor'][feature]

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

@defer.inlineCallbacks
def perform_extract_metadata_task(task):
#    print 'perform_feature_extraction_task'

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

    t = toolkit.Toolkit(settings.MEDIADART_CONF)
    utils = t.get_utils()

    if task.wait_for is not None: 
        if task.wait_for.job_id is None:
            defer.returnValue( (task, 'None') )
        elif task.wait_for.job_id == '':
            pass
        else:
            try:
                stat = yield utils.wait_for_job(task.wait_for.job_id, 5)
#                stat = utils.get_job_status(task.wait_for.job_id)
#                if stat != 1:
#                    return (task, 'None') 
            except:
                defer.returnValue( (task, 'None') )

    logger.debug("[ExtractMetadata.execute] task %d" % task.id)

    c = task.component
    metadata_list = []
    xmp_metadata_list = []
    delete_list = []
    xmp_delete_list = []
    workspace = c.workspace.all()[0] 

    source_variant = c.variant.get_source(workspace,  c.item)

    extractors = {'image': 'image_basic', 'movie': 'video_basic', 'audio': 'audio_basic', 'doc': 'doc_basic'}

    my_media_type = c.media_type.name
    
    my_extractor = extractors[my_media_type]

    if c.variant.auto_generated:
        f = t.get_features(c.ID,  [my_extractor])
    else:
        f = t.get_features(c.ID,  [my_extractor, 'xmp_extractor'])

    ctype = ContentType.objects.get_for_model(c)

    f_status = yield f.get_status()

    if f_status != 2:
        job_id = None
    else:
        features = yield f.parse()
        if features.get('xmp_extractor', None):
            item = Item.objects.get(component = c)
            xmp_metadata_list, xmp_delete_list = new_read_xmp_features(item, features, c)
        if features.get(my_extractor, None) and isinstance(features.get(my_extractor, None), dict):
#            print features[my_extractor], my_extractor, c.ID
            lang = settings.METADATA_DEFAULT_LANGUAGE
            for feature in features[my_extractor].keys():
                if features[my_extractor][feature]=='' or features[my_extractor][feature] == '0':
                    continue 
                if feature == 'size':
                    # TBD: salvarla ma non mappabile direttamente in xmp
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

        job_id = ''

    logger.debug("[ExtractMetadata.end] task %d" % task.id)

    defer.returnValue( (task, job_id) )

def find_a_new_task():
#    print 'find_a_new_task'
    try:
        now=datetime.datetime.now()
        delta=datetime.timedelta(seconds=30)
        delay = now - delta

        tasks = MDTask.objects.filter(Q(last_try_timestamp__isnull=True) | Q(last_try_timestamp__lt = delay), job_id__isnull=True).exclude(task_type='wait_for_upload').exclude(pk__in=running_tasks)
#        tasks = MDTask.objects.filter(Q(last_try_timestamp__isnull=True), job_id__isnull=True).exclude(task_type='wait_for_upload')[:1]

#        print 'tasks found %s'%tasks
        if tasks.count() == 0:
            task = None
        else:
            adaptation_type = tasks.filter(task_type='adaptation')
            save_thumb_type = tasks.filter(task_type='save_thumb')
            feature_extraction_type = tasks.filter(task_type='feature_extraction')
            metadata_type = tasks.filter(task_type='extract_metadata')
            rights_type = tasks.filter(task_type='set_rights')
            if adaptation_type.count() > 0:
                task = adaptation_type[0] 
            elif save_thumb_type.count() > 0:
                task = save_thumb_type[0] 
            elif feature_extraction_type.count() > 0:
                task = feature_extraction_type[0] 
            elif metadata_type.count() > 0:
                task = metadata_type[0] 
            elif rights_type.count() > 0:
                task = rights_type[0] 
#            task = tasks[0]
            task.last_try_timestamp = now
            task.save()
        return(task)
    except Exception, ex:
#        print 'ex %s'%ex
        return(None)

def remove_running_task(task):
    try:
        running_tasks.remove(task)
    except:
        pass

def add_running_task(task):
    try:
        running_tasks.append(task)
    except:
        pass

def remove_item(item):
    try:
        running_items.remove(item)
    except:
        pass

@defer.inlineCallbacks
def perform_task():
#    print 'perform_task'
    task = yield lock.run(find_a_new_task)

#    print "new thread"

#    print "lock run: %s" % d
#    print 'new thread task',  task

    if task is not None:

#        print 'new thread task',  task.task_type, task.wait_for, task.wait_for.task_type, task.wait_for.job_id

        yield lock.run(add_running_task, task.pk)

        try:

            if task.task_type == "adaptation":
                task, job_id = yield perform_adaptation_task(task)
            elif task.task_type == "feature_extraction":
                task, job_id = yield perform_feature_extraction_task(task)
            elif task.task_type == "extract_metadata":
                task, job_id = yield perform_extract_metadata_task(task)
            elif task.task_type == "save_thumb":
                task, job_id = yield perform_save_thumb_task(task)
            elif task.task_type == "set_rights":
                task, job_id = yield perform_set_rights(task)

        except:
            task, job_id = (task, None) 
        
    else:
        task, job_id = (None, None) 

    update_task((task, job_id))

    if task:
        yield lock.run(remove_running_task, task.pk)

    reset_queries()

def update_task(result):
    task, job_id = result

#    print "update", task.pk, job_id

    if task is not None:
        if job_id != 'None':
            task.job_id = job_id
            task.save()
#         else:
#             now=datetime.datetime.now()
#             delta=datetime.timedelta(seconds=25)
#             delay = now - delta
#             task.last_try_timestamp = delay
#            task.save()

        if task.last_try_timestamp is None:
            now=datetime.datetime.now()
            task.last_try_timestamp = now
            task.save()
            
#    reactor.callLater(1, perform_task)

def find_a_new_item():
#    print 'find_a_new_task'
    try:

        new_item = None

        now=datetime.datetime.now()
        delta=datetime.timedelta(seconds=300)
        delay = now - delta
        
        for i in MDTask.objects.exclude(component__item__pk__in=running_items).values_list('component__item', flat=True).distinct():
            item_tasks = MDTask.objects.filter(component__item=i)
            timeout_tasks = item_tasks.filter(last_try_timestamp__isnull=False, last_try_timestamp__lt=delay).count()
            not_finished = item_tasks.filter(job_id__isnull=True).count()
            failed = item_tasks.filter(status=-1).count()
#            print failed

            if not_finished > 0 and failed == 0 and timeout_tasks == 0:
#                print failed, not_finished
                new_item = i
                break

        if new_item:
            running_items.append(new_item)
        
        return new_item

    except Exception, ex:
#        print 'ex %s'%ex
        return(None)

@defer.inlineCallbacks
def perform_tasks_by_item():
#    print 'perform_task'
    item = yield lock.run(find_a_new_item)

    if item is not None:

#        print 'new item found', item

        yield perform_all_item_tasks(item)

        item = yield lock.run(remove_item, item)

    reactor.callLater(1, perform_tasks_by_item)
                    
@defer.inlineCallbacks
def perform_all_item_tasks(item):
#    print 'find_a_new_task'
    try:

        tasks = MDTask.objects.filter(job_id__isnull=True, component__item=item).exclude(task_type='wait_for_upload')

        if tasks.count() > 0:
            adaptation_type = tasks.filter(task_type='adaptation')
            
            for x in adaptation_type:
                task, job_id = yield perform_adaptation_task(x)            
                update_task((task, job_id))
            
            save_thumb_type = tasks.filter(task_type='save_thumb')

            for x in save_thumb_type:
                task, job_id = yield perform_save_thumb_task(x)                
                update_task((task, job_id))

            feature_extraction_type = tasks.filter(task_type='feature_extraction')

            for x in feature_extraction_type:
                task, job_id = yield perform_feature_extraction_task(x)                
                update_task((task, job_id))

            metadata_type = tasks.filter(task_type='extract_metadata')

            for x in metadata_type:
                task, job_id = yield perform_extract_metadata_task(x)                
                update_task((task, job_id))

            rights_type = tasks.filter(task_type='set_rights')

            for x in rights_type:
                task, job_id = yield perform_set_rights(x)                
                update_task((task, job_id))

    except Exception, ex:
        print ex
        
@defer.inlineCallbacks
def clean_task():

#    tasks_wait_for = MDTask.objects.filter(wait_for__isnull=False).values_list('wait_for', flat=True)
#    tasks_to_check = MDTask.objects.filter(wait_for__isnull=True, job_id__isnull=False, status__isnull=True).exclude(id__in=tasks_wait_for)

    t = toolkit.Toolkit(settings.MEDIADART_CONF)
    utils = t.get_utils()

    tasks_to_check = MDTask.objects.filter(Q(status__isnull=True) | Q(status = 0), job_id__isnull=False)

    logger.debug("[CleanTask.execute]")

    for t in tasks_to_check:
        if t.job_id != '':
            stat = yield utils.get_job_status(t.job_id)
            if stat == -2:
                t.status = None
                t.save()
            else:
                t.status = stat
                t.save()
        else:
            t.status = 1
            t.save()
 
    for i in Item.objects.filter(component__mdtask__in=MDTask.objects.all()).distinct():
        item_tasks = MDTask.objects.filter(component__item=i)
        not_finished = item_tasks.filter(Q(status__isnull=True) | Q(status = 0)).count()
        if not_finished == 0:
            item_tasks.delete()
 
    logger.debug("[CleanTask.end]")

    reset_queries()
 
    reactor.callLater(2, clean_task)

global lock
global running_tasks
running_tasks = []
running_items = []
lock = defer.DeferredLock()

for i in xrange(10):
    reactor.callLater(3, perform_tasks_by_item)    

#for i in xrange(60):
#    reactor.callLater(3, perform_task)

reactor.callLater(2, clean_task)

reactor.run()

