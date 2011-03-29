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

import mimetypes
from time import strptime
from json import dumps
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
from dam.plugins.common.utils import save_type
from dam.plugins.extract_basic_idl import inspect

from uuid import uuid4

def new_id():
    return uuid4().hex

class ExtractError(Exception):
    pass

# Entry point
def run(workspace, item_id, source_variant):
    log.debug('extract_basic: run %s %s' % (workspace, source_variant))
    deferred = defer.Deferred()
    worker = ExtractBasicFeatures(deferred, workspace, item_id, source_variant)
    reactor.callLater(0, worker.extract_basic)
    return deferred


##
## This class executes a series of extract operations, accumulating the results and saving them all.
## In case of the partial failure of a single extractor, # the results from successful operations 
## are saved, and an error is returned.
##
class ExtractBasicFeatures:
    def __init__(self, deferred, workspace, item_id, variant_name):
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
        metadata_list, delete_list = [], []
        log.debug('ExtractBasicFeatures._cb_basic_ok: %s' % features)
        ctype = ContentType.objects.get_for_model(self.component)
        try:
            save_type(ctype, self.component)
        except Exception, e:
            log.error("Failed to save component format as DC:Format: %s" % (str(e)))
        try:
            self.component.features = dumps(features)
            self.component.save()
            print 'saved'
        except Exception, e:
            log.error("Failed to save features in component object: %s" % str(e))
        if extractor_type == 'media_basic':
            for stream in features['streams']:
                if isinstance(features['streams'][stream], dict):  # e se no?
                    m_list, d_list = self._save_features(features['streams'][stream], ctype)
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


class AVFeatures:
    def __init__(self, component):
        features = component.get_features()
        self.info = {}
        self.info['video'] = [x for x in features['streams'].values() if x['codec_type'] == 'video']
        self.info['audio'] = [x for x in features['streams'].values() if x['codec_type'] == 'audio']

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
#  video/*    (streams with codec_type = audio may not be present)
#  audio/*    (only streams with codec_type = audio are present)
#
# {'size': 735801344L,
#  'streams': {
#    '0': {
#        'codec_long_name': 'MPEG-4 part 2',
#        'codec_name': 'mpeg4',
#        'codec_type': 'video',
#        'decoder_time_base': '1/25',
#        'display_aspect_ratio': '13/7',
#        'duration': '6668.600000',
#        'gop_size': '12',
#        'has_b_frames': '1',
#        'height': '336',
#        'index': '0',
#        'nb_frames': '0',
#        'pix_fmt': 'yuv420p',
#        'r_frame_rate': '25.000000',
#        'r_frame_rate_den': '1',
#        'r_frame_rate_num': '25',
#        'sample_aspect_ratio': '1/1',
#        'start_time': '0.000000',
#        'time_base': '1/25',
#        'width': '624'},
#    '1': {
#        'bits_per_sample': '0',
#        'channels': '2',
#        'codec_long_name': 'MP3 (MPEG audio layer 3)',
#        'codec_name': 'mp3',
#        'codec_type': 'audio',
#        'decoder_time_base': '0/1',
#        'duration': '6668.064000',
#        'index': '1',
#        'nb_frames': '0',
#        'sample_rate': '48000.000000',
#        'start_time': '0.000000',
#        'time_base': '3/125'}}}
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
