import mimetypes
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.core.mail import EmailMessage
from mediadart.mqueue.mqclient_async import Proxy
from mediadart.storage import Storage
from dam.xmp_embedding import synchronize_metadata, reset_modified_flag
from dam.metadata.models import MetadataProperty, MetadataValue
from dam.repository.models import Item, Component
from dam.preferences.views import get_metadata_default_language

import logging
logger = logging.getLogger('batch_processor')
logger.addHandler(logging.FileHandler(os.path.join(INSTALLATIONPATH,  'log/batch_processor.log')))
logger.setLevel(logging.DEBUG)

#
# This is the views that receives responses and pushes on the chain of calls
#
def dispatch(request, job_id):
    """General dispatcher for incoming responses"""
    try:
        result = loads(request.raw_post_data)
        action = Action(job_id)
    except Exception, e:
        logger.ERROR('Invalid body in post: %s' % str(e))
        return HttpResponseServerError('invalid data');
    next_step = action.execute(result)
    if next_step not in ('wait', 'done'):
        logger.ERROR('Invalid return value from action')
    if next_step == 'done':    # functions that don't invoke mediadart should be terminal
        action.retire()        # and return done
    elif next_step == 'wait':  # function that invoded mediadart should return wait
        pass
    else:
        logger.ERROR('Invalid return value from action')
    return HttpResponse('ok')

#
# Embed XMP chain
#
def embed_xmp(action, result):
    logger.debug('STARTING embed_xmp')
    component = action.component
    xmp_embedder_proxy = Proxy('XMPEmbedder', callback='http://%s:%s/mprocessor/%s' % (host, port, action.job_id)) 
    metadata_dict = synchronize_metadata(component)
    xmp_embedder_proxy.metadata_synch(component.ID, metadata_dict)
    action.push('embed_xmp_2')
    return 'wait'

def embed_xmb_2(action, result):
    if result:
        reset_modified_flag(action.component)
    else:
        pass  # NOTHING HERE?
    return 'done'

#
# Extract features chain
#
def extract_features(action, result):
    extractors = {'image': 'image_basic', 'video': 'media_basic', 'audio': 'media_basic', 'doc': 'doc_basic'}
    extractor_proxy = Proxy('FeatureExtractor', callback='http://%s:%s/mprocessor/%s' % (host, port, job_id))

    my_media_type = action.component.media_type.name
    my_extractor = extractors[my_media_type]

    if component.variant.auto_generated:
        action.push('save_features', my_extractor)
    else:
        action.push('extract_xmp', my_extractor)
    extractor_proxy.extract(action.component.ID, my_extractor)
    return 'wait'

def extract_xmp(action, result, extractor):
    extractor_proxy = Proxy('FeatureExtractor', callback='http://%s:%s/mprocessor/%s' % (host, port, job_id))
    _save_component_features(action.component, result, extractor)
    extractor_proxy.extract(component.ID, 'xmp_extractor')
    action.push('save_features', 'xmp_extractor')
    return 'wait'

def save_features(action, result, extractor):
    _save_component_features(action.component, result, extractor)
    return 'done'
        

#
# Send Mail
#
def send_mail(action, result):
    logger.debug("[SendMail.execute] component %s" % component.ID)
    logger.debug('component.get_parameters() %s'%component.get_parameters())
    mail = action.component.get_parameters()['mail']
    
    email = EmailMessage('OpenDam Rendition', 'Hi, an OpenDam rendition has been attached.  ', EMAIL_SENDER,
            [mail])
    storage = Storage()
    email.attach_file(storage.abspath(component.ID))
#    reactor.callInThread(email.send)
    email.send()
    logger.debug("[SendMail.end] component %s" % component.ID)
    return 'done'


#
#  Adapt
# 
def adapt_resource(action, result):
    from scripts.models import Script

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

#    variant = component.variant
    
#    source_variant = variant.get_source(workspace,  item)

#    vp = variant.get_preferences(workspace)
    vp = component.get_parameters()
    logger.debug('vp %s'%vp)
    orig = component.source 

    dest_res_id = new_id()
    watermark_filename = vp.get('watermark_filename', False)
    
    if item.type.name == 'image':
        
        args ={}
        argv = [] #for calling imagemagick
        height = int(vp.get('max_height', -1))        
        width = int(vp.get('max_width', -1))
        
        
        script = Script.objects.get(component = component)
        logger.debug('script %s'%script)
        acts = script.actionlist_set.get(media_type__name  = 'image')
        actions = simplejson.loads(acts.actions)['actions']
        logger.debug('actions %s'%actions)
        orig_width = component.source.width
        orig_height = component.source.height
        logger.debug('orig_width %s'%orig_width)
        logger.debug('orig_height %s'%orig_height)
        for action in actions:
            if action['type'] == 'resize':
                
                action['parameters']['max_width'] = min(action['parameters']['max_width'],  orig_width)
                action['parameters']['max_height'] = min(action['parameters']['max_height'],  orig_height)
                argv +=  ['-resize', '%dx%d' % (action['parameters']['max_width'], action['parameters']['max_height'])]
                logger.debug('argv %s'%argv)
                aspect_ratio = orig_height/orig_width 
                
                alfa = min(action['parameters']['max_width']/orig_width, action['parameters']['max_height']/orig_height)
                orig_width = alfa*orig_width
                orig_height = alfa*orig_height
                
                        
                
#                if orig_width > orig_height:
#                    
#                    
#                    orig_width = action['parameters']['max_width']
#                    orig_height = aspect_ratio*orig_width 
#                else:
#                    
#                    orig_height = action['parameters']['max_height']
#                    orig_width = orig_height/aspect_ratio 
#                    logger.debug('elsesssssss orig_height %s'%orig_height)
                
            elif action['type'] == 'crop':
#                action['parameters']['ratio'] = '2:3'
                
                if action['parameters'].get('ratio'):
                    x_ratio, y_ratio = action['parameters']['ratio'].split(':')
                    y_ratio = int(y_ratio)
                    x_ratio = int(x_ratio)
                    logger.debug('x_ratio %s'%x_ratio)
                    logger.debug('y_ratio %s'%y_ratio)
                    final_width = min(orig_width, orig_height*x_ratio/y_ratio)
                    final_height = final_width*y_ratio/x_ratio
   
                        
                    logger.debug('final_height %s'%final_height)
                    logger.debug('final_width %s'%final_width)
                    logger.debug('orig_height %s'%orig_height)
                    logger.debug('orig_width %s'%orig_width)
                    
                    ul_y = (orig_height - final_height)/2
                    ul_x = 0
                    
                    lr_y = ul_y + final_height
                    lr_x = final_width 
                
                     
                    
                else:
                    
                    lr_x = int(int(action['parameters']['lowerright_x'])*component.source.width/100)
                    ul_x = int(int(action['parameters']['upperleft_x'])*component.source.width/100)
                    lr_y = int(int(action['parameters']['lowerright_y'])*component.source.height/100)
                    ul_y = int(int(action['parameters']['upperleft_y'])*component.source.height/100)
                
                orig_width = lr_x -ul_x 
                orig_height = lr_y - ul_y
                
                logger.debug('orig_height %s'%orig_height)
                logger.debug('orig_width %s'%orig_width)
                
                
                argv +=  ['-crop', '%dx%d+%d+%d' % (orig_width, orig_height,  ul_x, ul_y)]
                
                logger.debug('argv %s'%argv)
            elif action['type'] == 'watermark':
                pos_x = int(int(action['parameters']['pos_x_percent'])*orig_width/100)
                pos_y = int(int(action['parameters']['pos_y_percent'])*orig_height/100)
                argv += ['cache://' + watermark_filename, '-geometry', '+%s+%s' % (pos_x,pos_y), '-composite']
 
        transcoding_format = vp.get('codec', orig.format) #change to original format
        dest_res_id = dest_res_id + '.' + transcoding_format
        
        
        
        d = adapter_proxy.adapt_image_magick(orig.ID, dest_res_id, argv)
#        d = adapter_proxy.adapt_image(orig.ID, dest_res_id, **args)

    elif item.type.name == 'video':
        logger.debug('---------vp %s'%vp)
        
        logger.debug('component.media_type.name %s'%component.media_type.name)
        if component.media_type.name == "image":
            
            dim_x = vp['max_width']
            dim_y = vp['max_height']
            
            transcoding_format = vp.get('codec', orig.format) #change to original format
            dest_res_id = dest_res_id + '.' + transcoding_format
            d = adapter_proxy.extract_video_thumbnail(orig.ID, dest_res_id, thumb_size=(dim_x, dim_y))

        else:
            
            preset_name = PRESETS['video'][vp['preset_name']]['preset']
            logger.debug('preset_name %s'%preset_name)

            param_dict = vp

            dest_res_id = dest_res_id + '.' + PRESETS['video'][vp['preset_name']]['extension']
            
            for key, val in vp.items():
#                if key == 'preset_name':
#                    param_dict[key] = preset_name
#                
                if key == 'max_size' or key == 'watermark_top_percent' or key == 'watermark_left_percent':
                    param_dict[key] = int(val)
                else:
                    param_dict[key] = val
            
            param_dict['preset_name'] = preset_name
            logger.debug('param_dict %s'%param_dict)
#            if watermark_filename:
#                tmp = vp.get('watermark_top')
#                if tmp:
#                    param_dictwatermark_top = tmp
#                    watermark_left = vp.get('watermark_left')
#                else:
#                    watermark_top_percent = vp.get('watermark_top_percent')
#                    watermark_left_percent = vp.get('watermark_left_percent')
#                
#            
#            if  vp.watermarking:
#             param_dict['watermark_uri'] = 'mediadart://' + vp.watermark_uri
#             param_dict.update(vp.get_watermarking_params())
             #param_dict['watermark_top'] = 10
             #param_dict['watermark_left'] = 10
#             yield utils.wait_for_resource(vp.watermark_uri, 5)
                
            d = adapter_proxy.adapt_video(orig.ID, dest_res_id, preset_name,  param_dict)
            

    elif item.type.name == 'audio':
        preset_name = PRESETS['audio'][vp['preset_name']]['preset']
        ext = PRESETS['audio'][vp['preset_name']]['extension']
        vp['preset_name'] = preset_name        
        param_dict = dict(vp)        
        logger.debug("[Adaptation] param_dict %s" % param_dict)
        dest_res_id = dest_res_id + '.' + ext
        
        
        d = adapter_proxy.adapt_audio(orig.ID, dest_res_id, preset_name, param_dict)
    
    if item.type.name == 'doc':
 
        transcoding_format = vp['codec']
#        TODO: add width, to mediadart, see adapt_doc
        max_size = vp['max_height']
        
        dest_res_id = dest_res_id + '.' + transcoding_format
        
        d = adapter_proxy.adapt_doc(orig.ID, dest_res_id, max_size)

    d.addCallbacks(save_and_extract_features, cb_error, callbackArgs=[component, machine], errbackArgs=[component, machine])

    logger.debug("[Adaptation.end] component %s" % component.ID)

#    defer.returnValue( (task, job_id) )










#
#  Utility functions
#
def _save_component_features(component, features, extractor):

    logger.debug("[ExtractMetadata.execute] component %s %s" % (component.ID, features))

    c = component

    metadata_list = []
    delete_list = []
    xmp_metadata_list = []
    xmp_delete_list = []
    workspace = c.workspace.all()[0]

#    source_variant = c.variant.get_source(workspace,  c.item)

    ctype = ContentType.objects.get_for_model(c)

    try:
        logger.debug('*****************************c._id %s'%c._id)
        mime_type = mimetypes.guess_type(c._id)[0]
        ext = mime_type.split('/')[1]
        c.format = ext
        c.save()
        metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
        MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=c, value=mime_type)
    except Exception, ex:
        logger.exception(ex)
        pass

    if extractor == 'xmp_extractor':
        item = Item.objects.get(component = c)
        xmp_metadata_list, xmp_delete_list = _read_xmp_features(item, features, c)
    elif extractor == 'media_basic':
        
        for stream in features['streams']:
            if isinstance(features['streams'][stream], dict):
                m_list, d_list = _save_features(c, features['streams'][stream])
                metadata_list.extend(m_list)
                delete_list.extend(d_list)
    else: 
        metadata_list, delete_list = _save_features(c, features)    

    MetadataValue.objects.filter(schema__in=delete_list, object_id=c.pk, content_type=ctype).delete()

    for x in metadata_list:
        x.save()

    MetadataValue.objects.filter(schema__in=xmp_delete_list, object_id=c.pk, content_type=ctype).delete()

    for x in xmp_metadata_list:
        x.save()
    logger.debug("[ExtractMetadata.end] component %s" % component.ID)

def _save_features(c, features):

    xmp_metadata_commons = {'size':[('notreDAM','FileSize')]}
    xmp_metadata_audio = {'channels':[('xmpDM', 'audioChannelType')], 'sample_rate':[('xmpDM', 'audioSampleRate')], 'duration':[('notreDAM', 'Duration')]}

    xmp_metadata_video = {'height':[('xmpDM', 'videoFrameSize','stDim','h')] , 'width':[('xmpDM', 'videoFrameSize','stDim','w')], 'r_frame_rate':[('xmpDM','videoFrameRate')], 'bit_rate':[('xmpDM','fileDataRate')], 'duration':[('notreDAM', 'Duration')]}
    xmp_metadata_image = {'height':[('tiff', 'ImageLength')] , 'width':[('tiff', 'ImageWidth')]}
    xmp_metadata_doc = {'pages': [('notreDAM', 'NPages')], 'Copyright': [('dc', 'rights')]}

    xmp_metadata_image.update(xmp_metadata_commons)
    xmp_metadata_audio.update(xmp_metadata_commons)
    xmp_metadata_doc.update(xmp_metadata_commons)

    xmp_metadata_video.update(xmp_metadata_audio)

    xmp_metadata = {'image': xmp_metadata_image, 'video': xmp_metadata_video, 'audio': xmp_metadata_audio, 'doc': xmp_metadata_doc}

    metadata_list = []
    delete_list = []

    media_type = c.media_type.name

    ctype = ContentType.objects.get_for_model(c)

    i = c.item
    user = i.uploaded_by()
    metadata_default_language = get_metadata_default_language(user)

    for feature in features.keys():
        if features[feature]=='' or features[feature] == '0':
            continue 
        if feature == 'size':
            c.size = features[feature]
        if feature == 'height':
            c.height = features[feature]
        elif feature == 'width':
            c.width = features[feature]

        try:
            xmp_names = xmp_metadata[media_type][feature]
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
                        x = MetadataValue(schema=ms, object_id=c.pk, content_type=ctype, value=features[feature], language=metadata_default_language, xpath=property_xpath)
                    else:                            
                        x = MetadataValue(schema=ms, object_id=c.pk, content_type=ctype, value=features[feature], xpath=property_xpath)
                    metadata_list.append(x) 
                    delete_list.append(ms) 
                except:
                    logger.debug('inside readfeatures, could not get %s' %  ms)
                    continue

    c.save()

    return (metadata_list, delete_list)

def _read_xmp_features(item, features, component):
    from time import strptime
    import re

    xpath = re.compile(r'(?P<prefix>\w+):(?P<property>\w+)(?P<array_index>\[\d+\]){,1}')

    ctype = ContentType.objects.get_for_model(item)
    ctype_component = ContentType.objects.get_for_model(component)

    user = item.uploaded_by()
    metadata_default_language = get_metadata_default_language(user)

    metadata_dict = {}

    metadata_list = []
    delete_list = []

    logger.debug('READ XMP FEATURES')

    if not isinstance(features, dict):
        item.state = 1  
        item.save()
        return metadata_list, delete_list
    for feature in features.keys():
        try:
            namespace_obj = XMPNamespace.objects.get(uri=feature)
        except:
            logger.debug('unknown namespace %s' % feature)
            continue

        metadata_dict[namespace_obj] = {}

        namespace_properties = MetadataProperty.objects.filter(namespace=namespace_obj)
        for property_values in features[feature]:
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
                            property_value = metadata_default_language
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


