import mimetypes
from time import strptime
import re
from twisted.internet import reactor, defer

from mediadart import log
from mediadart.mqueue.mqclient_twisted import Proxy

from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models

get_models()

from django.contrib.contenttypes.models import ContentType
from dam.repository.models import Component
from dam.metadata.models import MetadataProperty, MetadataValue
from dam.preferences.views import get_metadata_default_language
from dam.variants.models import Variant
from dam.repository.models import Item    
from dam.workspace.models import DAMWorkspace
from dam.plugins.common.utils import save_type, get_variants

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
                'description': 'input-variant',
               
                'help': ''
            }]
         
        } 

class ExtractError(Exception):
    pass

# Entry point
def run(item_id, workspace, source_variant):
    log.debug('extract_basic: run %s %s' % (workspace, source_variant))
    deferred = defer.Deferred()
    worker = ExtractBasicFeatures(deferred, item_id, workspace, source_variant)
    reactor.callLater(0, worker.extract_basic)
    return deferred


##
## This class executes a series of extract operations, accumulating the results and saving them all.
## In case of the partial failure of a single extractor, # the results from successful operations 
## are saved, and an error is returned.
##
class ExtractBasicFeatures:
    def __init__(self, deferred, item_id, workspace, variant_name):
        self.deferred = deferred
        self.proxy = Proxy('FeatureExtractor')
        self.workspace = workspace
        self.item = Item.objects.get(pk = item_id)
        self.variant_name = variant_name
        self.source_variant = Variant.objects.get(name = variant_name)
        self.component = self.item.get_variant(workspace, self.source_variant)
        self.extractor = 'basic'
        self.ctype = None

    # the basic extractor is taken from the component using the component type
    def extract_basic(self):
        extractor_type = self.component.get_extractor()    # one of image_basic, media_basic etc.
        d = self.proxy.extract(self.component.uri, extractor_type)
        d.addCallbacks(self._cb_basic_ok, self._cb_error, callbackArgs=[extractor_type], errbackArgs=[extractor_type])

    def _cb_basic_ok(self, features, extractor_type):
        "save results of basic extractions"
        log.debug('ExtractBasicFeatures._cb_basic_ok: %s' % features)
        ctype = ContentType.objects.get_for_model(self.component)
        try:
            save_type(ctype, self.component)
        except Exception, e:
            log.error("Failed to save component format as DC:Format: %s" % (str(e)))
        if extractor_type == 'media_basic':
            for stream in features['streams']:
                if isinstance(features['streams'][stream], dict):  # e se no?
                    m_list, d_list = self._save_features(features['streams'][stream])
                    metadata_list.extend(m_list)
                    delete_list.extend(d_list)
        else: 
            metadata_list, delete_list = self._save_features(features, ctype)    

        MetadataValue.objects.filter(schema__in=delete_list, object_id=self.component.pk, content_type=ctype).delete()
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
        user = self.item.uploaded_by()
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
