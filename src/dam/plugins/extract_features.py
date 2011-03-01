import mimetypes
from time import strptime
import re

from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy

from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models
from django.db.models import Q
get_models()

from dam.repository.models import Component
from dam.metadata.models import MetadataProperty, MetadataValue
from dam.variants.models import Variant
from dam.repository.models import Item    
from dam.workspace.models import DAMWorkspace
from dam.plugins.common.utils import get_variants
from uuid import uuid4

def new_id():
    return uuid4().hex

def inspect(workspace):
    variants = get_variants(workspace)
    return {
        'name': __name__,
        'params':[
            {   
                'name': 'source_variant',
                'fieldLabel': 'Source Rendition',
                'xtype': 'select',
                'values': variants,
                'value': variants[0],
                'description': 'input-variant',                
                'help': ''
            }]
         
        } 

class ExtractError(Exception):
    pass

# Entry point
def run(item_id, workspace, source_variant, extractor='basic'):
    deferred = defer.Deferred()
    worker = ExtractFeatures(deferred, itme_id, workspace, source_variant, extractors)
    method = getattr(worker, 'extract_%s' % extractor, None)
    if method is None:
        raise ExtractError('invalid extractor specification; %s' % extractor)
    reactor.callLater(0, method, item_id, workspace, source_variant)
    return deferred


##
## This class executes a series of extract operations, accumulating the results and saving them all.
## In case of the partial failure of a single extractor, # the results from successful operations 
## are saved, and an error is returned.
##
class ExtractFeatures:
    def __init__(self, deferred, item_id, workspace, variant_name, extractor):
        self.deferred = deferred
        self.proxy = Proxy('FeatureExtractor')
        self.workspace = workspace
        self.item = Item.objects.get(pk = item_id)
        self.variant_name = variant_name
        self.source_variant = Variant.objects.get(name = variant_name)
        self.component = self.item.get_variant(workspace, source_variant)
        self.extractor = extractor
        self.extract_method = getattr(self, 'extract_%s' % extractor, None)
        self.ctype = None
        self.result = []

    # the basic extractor is taken from the component using the component type
    def extract_basic(self):
        extractor_type = self.component.get_extractor()    # one of image_basic, media_basic etc.
        d = self.proxy.extract(self.component.ID, self.extractor_type)
        d.addCallbacks(self._cb_basic_ok, self._cb_error, callbackArgs=[extractor_type], errbackArgs=[extractor_type])

    def _save_type(self, ctype):
        try:
            mime_type = mimetypes.guess_type(self.component._id)[0]
            ext = mime_type.split('/')[1]
            self.component.format = ext
            self.component.save()
            metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
            MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=self.component, value=mime_type)
        except Exception, ex:
            log.error(ex)

    def _cb_basic_ok(self, features, extractor_type):
        "save results of basic extractions"
        ctype = ContentType.objects.get_for_model(self.component)
        self._save_type(ctype)
        if extractor_type == 'media_basic':
            for stream in features['streams']:
                if isinstance(features['streams'][stream], dict):  # e se no?
                    m_list, d_list = self._save_features(features['streams'][stream])
                    metadata_list.extend(m_list)
                    delete_list.extend(d_list)
        else: 
            metadata_list, delete_list = _save_features(c, features)    

        MetadataValue.objects.filter(schema__in=delete_list, object_id=c.pk, content_type=ctype).delete()
        for x in metadata_list:
            x.save()
        self.deferred.callback('ok')

    def _save_features(self, features, ctype):
        c = self.component
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
        i = self.item
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


    def _cb_error(self, failure, extractor):
        self.deferred.errback(failure)

    def _cb_xmp_ok(self, result, extractor_type):
        ctype_component = ContentType.objects.get_for_model(self.component)
        ctype = ContentType.objects.get_for_model(self.item)
        self._save_type(ctype_component)

        xpath = re.compile(r'(?P<prefix>\w+):(?P<property>\w+)(?P<array_index>\[\d+\]){,1}')

        user = self.item.uploaded_by()
        metadata_default_language = get_metadata_default_language(user)

        metadata_dict = {}
        metadata_list = []
        delete_list = []

        if not isinstance(features, dict):
            self.item.state = 1  
            self.item.save()
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
                            x = MetadataValue(schema=found_property[0], object_id=self.component.pk, content_type=ctype_component, value=property_value, xpath=property_xpath)
                        else:
                            x = MetadataValue(schema=found_property[0], object_id=self.item.pk, content_type=ctype, value=property_value, xpath=property_xpath)
                        metadata_dict[namespace_obj][property_xpath] = x
                        metadata_list.append(x)

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
                GeoInfo.objects.save_geo_coords(self.component.item, latitude,longitude)
            except Exception, ex:
                logger.debug( 'ex while saving latitude and longitude in dam db: %s'% ex)
        self.deferred.callback('ok')

    def extract_xmp(self):
        extractor_type = 'xmp_extractor'
        extractor_proxy = Proxy('FeatureExtractor')
        d = extractor_proxy.extract(self.component.ID,  extractor_type)
        d.addCallbacks(self._cb_xmp_ok, self._cb_error, callbackArgs=[extractor_type], errbackArgs=[extractor_type])
        return d
        
