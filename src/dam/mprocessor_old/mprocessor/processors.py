import mimetypes
import os
from json import loads
from uuid import uuid4
from twisted.internet import reactor, defer
from django.core.mail import EmailMessage
from django.contrib.contenttypes.models import ContentType
from mediadart import log
from mediadart.mqueue.mqserver import MQServer
from mediadart.storage import Storage, new_id
from mediadart.mqueue.mqclient_twisted import Proxy
from mediadart.utils import default_start_mqueue

from dam.xmp_embedding import synchronize_metadata, reset_modified_flag
from dam.metadata.models import MetadataProperty, MetadataValue
from dam.repository.models import Item, Component
from dam.eventmanager.models import EventRegistration
from dam.workspace.models import DAMWorkspace as Workspace
from dam.mprocessor.models import MAction
from dam.scripts.models import PRESETS, Script
from dam.core.dam_metadata.models import XMPNamespace
from dam.preferences.views import get_metadata_default_language
from dam.geo_features.models import GeoInfo


def new_id():
    "Create your models here."
    return uuid4().hex

class MProcessor(MQServer):
    def mq_activate(self, json_data):
        d = defer.Deferred()
        engine = Engine(d)
        data = loads(json_data)
        reactor.callLater(0, engine.init, data)
        return d

class Engine:
    "Executes a task"
    def __init__(self, d):
        self.maction = None
        self.d = d
        
    def init(self, data):
        log.debug('MProcessor.Engine.init: reading component %s' % (data['component_id']))
        try:
            component = Component.objects.get(pk=data['component_id'])
        except Exception, e:
            log.error('######## db error: unable to read component from db: %s' % str(e))
            self.d.errback('######## unable to read component from db: %s' % str(e))
        else: 
            log.debug('Initializing MAction %s, params=%s' % (data['action_id'], data['params']))
            self.maction = MAction(component, data['action_id'], data['params'])
            self.run('')

    def run(self, result):
        "run the next step in task or return silently"
        fname, fparams = self.maction.pop()
        if fname:
            f = getattr(self, fname, None)
            if f:
                log.debug('######>>> executing %s(result, %s)' % (fname, fparams))
                try: 
                    d = f(result, *fparams)
                    if d:
                        d.addCallbacks(self.run, self.run_on_error)
                    else:
                        reactor.callLater(0, self.run, '')
                except Exception, e:
                    log.error('Exception executing task %s: %s' % (fname, str(e)))
                    self.run_on_error('')
            else:
                self.run_on_error('Unrecognized method name: %s' % fname)
        else:
            log.debug('END OF RUN')
            self.d.callback('ok')   # we are done


    def run_on_error(self, failure):
        log.debug('######### run_on_error %s' % failure)
        self.maction.failed()
        return self.run('')

    def cb_error(self, result):
        log.debug('######### cb_error %s' % result)
        self.maction.failed()
        return result

    def start_upload_event_handlers(self, result, workspace_id):
        workspace = Workspace.objects.get(pk=workspace_id)
        item = self.maction.component.item
        for ws in item.workspaces.all():
            EventRegistration.objects.notify('upload', workspace,  **{'items':[item]})
        return result

    def embed_xmp(self, result):
        def cb_embed_reset_xmp(result):
            if result:
                reset_modified_flag(self.maction.component)
            return result

        log.debug('STARTING embed_xmp')
        component = self.maction.component
        xmp_embedder_proxy = Proxy('XMPEmbedder') 
        metadata_dict = synchronize_metadata(component)
        d = xmp_embedder_proxy.metadata_synch(component.ID, metadata_dict)
        d.addCallback(cb_embed_reset_xmp)
        d.addErrback(self.cb_error)
        return d


#
# Extract features chain
#
    def extract_features(self, result):
        component = self.maction.component
        def cb_save_features(result, extractor):
            log.debug('@@@@@@@@@@ extractor.cb_save_features')
            _save_component_features(component, result, extractor)
            log.debug('@@@@@@@@@@ extractor.cb_save_features: DONE')
            return result

#        def log_error(*params, **kwargs):
#            log.error('###@@@@@@@@@@ LOG_ERROR: %s --- %s' % (params, kwargs))
#            if len(params) == 2:
#                return cb_save_features(*params)

        log.debug("[extract_features] component %s" % component.ID)
        extractor = component.get_extractor()
        extractor_proxy = Proxy('FeatureExtractor')
        log.debug("-########## calling extract_features(%s, (%s), %s)" % (component.ID, component.pk, component.get_extractor()))
        d = extractor_proxy.extract(self.maction.component.ID, extractor)
        #d.addCallbacks(cb_save_features, self.cb_error, [extractor])
        d.addCallbacks(cb_save_features, self.cb_error, [extractor])
        return d


    def extract_xmp(self, result, extractor):
        def cb_save_features(result, extractor):
            _save_component_features(self.maction.component, result, extractor)

        def log_error(*params, **kwargs):
#            log.error('###@@@@@@@@@@ LOG_ERROR: %s --- %s' % (params, kwargs))
            if len(params) == 2:
                return cb_save_features(*params)

        log.debug("[extract_xmp] component %s" % self.maction.component.ID)
        d = None
        extractor = 'xmp_extractor'
        extractor_proxy = Proxy('FeatureExtractor')
        d = extractor_proxy.extract(self.maction.component.ID,  extractor)
        #d.addCallbacks(cb_save_features, self.cb_error, extractor)
        d.addCallbacks(log_error, self.cb_error, [extractor])
        return d

#
# Send Mail
#
    def send_mail(self, result):
        log.debug("[SendMail.execute] component %s" % self.maction.component.ID)
        log.debug('component.get_parameters() %s'%self.maction.component.get_parameters())
        mail = self.maction.component.get_parameters()['mail']
        email = EmailMessage('OpenDam Rendition', 'Hi, an OpenDam rendition has been attached.  ', EMAIL_SENDER,
                [mail])
        storage = Storage()
        email.attach_file(storage.abspath(self.maction.component.ID))
        email.send()
        log.debug("[SendMail.end] component %s" % self.maction.component.ID)
        return None


#
#  Adapt
# 
    def adapt_resource(self, result):

        component = self.maction.component
        adapter_proxy = Proxy('Adapter')
        log.debug("[adapt_resource] from original component %s" % component.source.ID)
        item = component.item
        vp = component.get_parameters()
        log.debug('vp %s'%vp)
        orig = component.source 

        dest_res_id = new_id()
        watermark_filename = vp.get('watermark_filename', False)
        
        if item.type.name == 'image':
            args ={}
            argv = [] #for calling imagemagick
            height = int(vp.get('max_height', -1))        
            width = int(vp.get('max_width', -1))
            script = Script.objects.get(component = component)
            log.debug('script %s'%script)
            acts = script.actionlist_set.get(media_type__name  = 'image')
            actions = loads(acts.actions)['actions']
            log.debug('actions %s'%actions)
            orig_width = component.source.width
            orig_height = component.source.height
            #log.debug('orig_width %s'%orig_width)
            #log.debug('orig_height %s'%orig_height)
            for action in actions:
                if action['type'] == 'resize':
                    action['parameters']['max_width'] = min(action['parameters']['max_width'],  orig_width)
                    action['parameters']['max_height'] = min(action['parameters']['max_height'],  orig_height)
                    argv +=  ['-resize', '%dx%d' % (action['parameters']['max_width'], action['parameters']['max_height'])]
                    #log.debug('argv %s'%argv)
                    aspect_ratio = orig_height/orig_width 
                    alfa = min(action['parameters']['max_width']/orig_width, action['parameters']['max_height']/orig_height)
                    orig_width = alfa*orig_width
                    orig_height = alfa*orig_height
                    
                elif action['type'] == 'crop':
                    if action['parameters'].get('ratio'):
                        x_ratio, y_ratio = action['parameters']['ratio'].split(':')
                        y_ratio = int(y_ratio)
                        x_ratio = int(x_ratio)
                        final_width = min(orig_width, orig_height*x_ratio/y_ratio)
                        final_height = final_width*y_ratio/x_ratio
                        log.debug('ratio=(%s,%s), final(h,w)=(%s, %s), original(h,w)=(%s, %s)'%(
                               x_ratio, y_ratio, final_height, final_width, orig_height, orig_width))
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
                    log.debug('orig(h,w)=(%s, %s)' % (orig_height, orig_width))
                    argv +=  ['-crop', '%dx%d+%d+%d' % (orig_width, orig_height,  ul_x, ul_y)]
                    log.debug('argv %s'%argv)
                elif action['type'] == 'watermark':
                    pos_x = int(int(action['parameters']['pos_x_percent'])*orig_width/100)
                    pos_y = int(int(action['parameters']['pos_y_percent'])*orig_height/100)
                    argv += ['cache://' + watermark_filename, '-geometry', '+%s+%s' % (pos_x,pos_y), '-composite']
     
            transcoding_format = vp.get('codec', orig.format) #change to original format
            dest_res_id = dest_res_id + '.' + transcoding_format
            d = adapter_proxy.adapt_image_magick('%s[0]' % orig.ID, dest_res_id, argv)

        elif item.type.name == 'video':
            log.debug('component.media_type.name %s'%component.media_type.name)
            if component.media_type.name == "image":
                dim_x = vp['max_width']
                dim_y = vp['max_height']
                
                transcoding_format = vp.get('codec', orig.format) #change to original format
                dest_res_id = dest_res_id + '.' + transcoding_format
                d = adapter_proxy.extract_video_thumbnail(orig.ID, dest_res_id, thumb_size=(dim_x, dim_y))
            else:
                preset_name = PRESETS['video'][vp['preset_name']]['preset']
                log.debug('preset_name %s'%preset_name)
                param_dict = vp
                dest_res_id = dest_res_id + '.' + PRESETS['video'][vp['preset_name']]['extension']
                for key, val in vp.items():
                    if key == 'max_size' or key == 'watermark_top_percent' or key == 'watermark_left_percent':
                        param_dict[key] = int(val)
                    else:
                        param_dict[key] = val
                
                param_dict['preset_name'] = preset_name
                log.debug('param_dict %s'%param_dict)
                d = adapter_proxy.adapt_video(orig.ID, dest_res_id, preset_name,  param_dict)

        elif item.type.name == 'audio':
            preset_name = PRESETS['audio'][vp['preset_name']]['preset']
            ext = PRESETS['audio'][vp['preset_name']]['extension']
            vp['preset_name'] = preset_name        
            param_dict = dict(vp)        
            log.debug("[Adaptation] param_dict %s" % param_dict)
            dest_res_id = dest_res_id + '.' + ext
            d = adapter_proxy.adapt_audio(orig.ID, dest_res_id, preset_name, param_dict)
        
        if item.type.name == 'doc':
            transcoding_format = vp['codec']
            max_size = vp['max_height']
            dest_res_id = dest_res_id + '.' + transcoding_format
            d = adapter_proxy.adapt_doc(orig.ID, dest_res_id, max_size)
        log.debug("[Adaptation.end] component %s" % component.ID)
        d.addCallbacks(self.save_component, self.cb_error)
        return d

    def save_component(self, result):   # era save_and_extract_features
        log.debug("[save_component] component %s" % self.maction.component.ID)
        component = self.maction.component
        if result:
            dir, name = os.path.split(result)
            component._id = name
            component.save()
        else:
            log.error('Empty result passed to save_and_extract_features')
        return result


#
#  Utility functions
#
def _save_component_features(component, features, extractor):

    log.debug("[_save_component_features] component %s" % component.ID)

    c = component

    metadata_list = []
    delete_list = []
    xmp_metadata_list = []
    xmp_delete_list = []
    workspace = c.workspace.all()[0]

    ctype = ContentType.objects.get_for_model(c)

    try:
        log.debug('*****************************c._id %s'%c._id)
        mime_type = mimetypes.guess_type(c._id)[0]
        ext = mime_type.split('/')[1]
        c.format = ext
        c.save()
        metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
        MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=c, value=mime_type)
    except Exception, ex:
        log.error(ex)

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
    latitude = None
    longitude = None
    for x in xmp_metadata_list:
        if x.xpath == 'exif:GPSLatitude':
            latitude = x.value
        elif x.xpath == 'exif:GPSLongitude':
            longitude = x.value
        x.save()
    if latitude != None and longitude != None:
        try:
            GeoInfo.objects.save_geo_coords(component.item,latitude,longitude)
        except Exception, ex:
            logger.debug( 'ex while saving latitude and longitude in dam db: %s'% ex)
#    log.debug("[ExtractMetadata.end] component %s" % component.ID)
    log.debug("[ExtractMetadata.end]" )


def _save_features(c, features):
    log.debug('######## _save_features %s %s' % (c, features))

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
                log.debug( 'inside readfeatures, unknown metadata %s:%s ' %  (m[0],m[1]))
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
                    log.debug('inside readfeatures, could not get %s' %  ms)
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

    log.debug('READ XMP FEATURES')

    if not isinstance(features, dict):
        item.state = 1  
        item.save()
        return metadata_list, delete_list
    for feature in features.keys():
        try:
            namespace_obj = XMPNamespace.objects.get(uri=feature)
        except Exception, e:
            log.error('#######  Error: unknown namespace %s: %s' % (feature, str(e)))
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
                        log.debug('metadata property not found: ' + find_xpath)
                else:
                    if found_property[0].is_variant:
                        x = MetadataValue(schema=found_property[0], object_id=component.pk, content_type=ctype_component, value=property_value, xpath=property_xpath)
                    else:
                        x = MetadataValue(schema=found_property[0], object_id=item.pk, content_type=ctype, value=property_value, xpath=property_xpath)
                    metadata_dict[namespace_obj][property_xpath] = x
                    metadata_list.append(x)

    return metadata_list, delete_list


def start_server():
    default_start_mqueue(MProcessor)
