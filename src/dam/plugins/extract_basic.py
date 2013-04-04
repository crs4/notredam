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

import os
import re
from xml.sax import ContentHandler, parseString
from json import dumps
from django.contrib.contenttypes.models import ContentType
from dam.plugins.common.analyzer import Analyzer
from dam.metadata.models import MetadataProperty, MetadataValue
from dam.preferences.views import get_metadata_default_language
from dam.plugins.common.utils import save_type #, get_flv_duration
from dam.plugins.extract_basic_idl import inspect
from twisted.internet import defer, reactor
from mediadart import log



def run(workspace,             # workspace object
        item_id,               # item pk
        source_variant_name):  # name of the source variant (a string)

    deferred = defer.Deferred()
    adapter = ExtractBasic(deferred, workspace, item_id, source_variant_name)
    reactor.callLater(0, adapter.execute)
    return deferred


class ExtractBasic(Analyzer):
    md_server = "LowLoad"
    exe_list = {'image_basic': 'identify', 'media_basic': 'mediainfo', 'doc_basic': 'pdfinfo'}
    cmd_image_basic = '"file://%(infile)s"'
    cmd_media_basic = '-f "--Output=XML" "file://%(infile)s"'
    cmd_doc_basic   = '"file://%(infile)s"'
    regex  = r'(?P<filename>[^ \[]*)(?P<frame>\[\d+\]){0,1}\s(?P<type>[\w._-]+)\s' \
             r'(?P<width>\d+)x(?P<height>\d+)\s' \
             r'(?P<wcrop>\d+)x(?P<hcrop>\d+)[\+-](?P<wcropoff>\d+)[\+-](?P<hcropoff>\d+)\s' \
             r'(?P<depth>\d+)-(?P<depth_unit>\w+)\s'
    RE = None

    def get_cmdline(self):
        extractor_type = self.source.get_extractor()
        log.debug('######333\n########## ExtractBasic: using %s' % extractor_type)
        self.remote_exe = self.exe_list[extractor_type]
        self.cmdline = getattr(self, 'cmd_%s' % extractor_type)
        self.parser = getattr(self, 'parse_%s' % extractor_type)
        self.cmdline = self.cmdline % {'infile': self.source.uri}

    def parse_stdout(self, result):
        return self.parser(result, self.source.uri)

    def parse_image_basic(self, result, filename):
        features = {}
        if not self.RE:
            self.RE = re.compile(self.regex)
        fullpath = str(self._fc.abspath(filename))
        #log.debug('image_basic_extractor: entering')
        m = self.RE.match(result)
        if not m:
            raise Exception('Unable to parse script output')
        d = m.groupdict()
        size = os.stat(fullpath).st_size
        features['size'] = size
        features['width'] = d['width']
        features['height'] = d['height']
        features['codec'] = d['type'].lower()
        features['has_frame'] = d['frame'] is not None
        features['has_sound'] = False
        features['depth'] = d['depth']            # depth in bits
        features['depth_unit'] = d['depth_unit']  # depth in bits
        self._save_features(features, 'image_basic')
        return 'ok'

    def parse_media_basic(self, result, filename):
        log.debug('parse_media_basic: entering "%s"' % type(result))
        fullpath = str(self._fc.abspath(filename))
        parser = Parser()
        parseString(result.encode('utf-8'), parser)
        features = parser.parsed
        self._save_features(features, 'media_basic')
        return 'ok'

    def parse_doc_basic(self, result, filename):
        log.debug('parse_doc_basic: entering')
        features = {}
        lines = result.split('\n')
        for line in lines:
            sep = line.find(':')
            if sep < 0:
                continue
            key = line[:sep].strip()
            value  = line[sep+1:].strip()
            features[key] = value
        features['size'] = long(features.get('File size', '-1').split()[0])
        features['pages'] = features['Pages']
        self._save_features(features, 'doc_basic')
        return 'ok'

    def _save_features(self, features, extractor_type):
        "save results of basic extractions"
        metadata_list, delete_list = [], []
        #log.debug('ExtractBasicFeatures._save_features: %s' % features)
        ctype = ContentType.objects.get_for_model(self.source)
        try:
            save_type(ctype, self.source)
        except Exception, e:
            log.error("Failed to save component format as DC:Format: %s" % (str(e)))
        try:
            self.source._features = dumps(features)
            self.source.save()
            print 'saved'
        except Exception, e:
            log.error("Failed to save features in component object: %s" % str(e))
        if extractor_type == 'media_basic':
            for stream in features.keys():
                if stream not in ['video', 'audio']:   # skip "general" "menu" or other stream
                    continue
                m_list, d_list = self._save_metadata(features[stream], ctype)
                metadata_list.extend(m_list)
                delete_list.extend(d_list)
        else: 
            metadata_list, delete_list = self._save_metadata(features, ctype)    

        MetadataValue.objects.filter(schema__in=delete_list, object_id=self.source.pk, content_type=ctype).delete()
        for x in metadata_list:
            x.save()

    def _save_metadata(self, features, ctype):
        c = self.source
        #log.debug('######## _save_metadata %s %s' % (c, features))

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
            if feature == 'file_size':
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


class Parser(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.current_track = None   # holds data for the current track
        self.parsed = {}      # holds all tracks
        self.content = ""     # accumulator for character data
        self.numeric = re.compile('\d+\.?\d*$')   
        self.float_required = ['file_size', 'duration', 'overall_bit_rate', 'stream_size', 
                               'ID',  'file_size', 'bit_rate', 'width', 'height', 
                               'frame_rate', 'resolution', 'bit_depth', 'delay',]
        # duration is in milliseconds, we want seconds
        self.conversions = { 'duration': lambda x: str(float(x)/1000.) }  

    def startElement(self, name, attrs):
        if name == 'track':
            t = attrs.getValue('type').lower()
            if t not in self.parsed:    # only one track of a given type is parsed
                self.current_track = {}
                self.parsed[t] = self.current_track

    def endElement(self, name):
        "Put a value in the active dictionary, checking that is a numeric value"
        if name == 'track':
            self.current_track == None
        elif self.current_track is not None:
            name = name.lower()
            value = self.content.strip()
            if name not in self.current_track:
                if name not in self.float_required or self.numeric.match(value):
                    value = self.conversions.get(name, lambda x: x)(value)
                    self.current_track[name] = value
        self.content = ""

    def characters(self, content):
        self.content += content


#def is_flv(streams):
#    for k in streams.keys():
#        if streams[k].get('codec_name', 'no_codec_name') == 'flv':
#            return True
#    return False
#
#def set_flv_duration(streams, filename):
#    if not is_flv(streams):
#        return
#    try:
#        duration = get_flv_duration(filename)
#        log.debug('##########>>>>>>>>> duration' % duration)
#        for s in streams:
#            if 'duration' in streams[s]:
#                streams[s]['duration'] = str(duration)
#    except Exception, e:
#        log.error('<<<<<<<<<<<<< Error while computing flv duration: %s' % e)
#        duration = 0
#


####################################################################
#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from dam.repository.models import Item
from twisted.internet import defer, reactor
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=6)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant_name = 'original',
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
        
