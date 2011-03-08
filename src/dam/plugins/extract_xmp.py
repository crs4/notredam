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
from dam.core.dam_metadata.models import XMPNamespace
from dam.preferences.views import get_metadata_default_language
from dam.variants.models import Variant
from dam.repository.models import Item    
from dam.workspace.models import DAMWorkspace
from dam.plugins.common.utils import save_type
from dam.plugins.extract_xmp_idl import inspect

from uuid import uuid4

def new_id():
    return uuid4().hex

class ExtractError(Exception):
    pass

# Entry point
def run(item_id, workspace, source_variant):
    deferred = defer.Deferred()
    worker = ExtractXMP(deferred, item_id, workspace, source_variant)
    reactor.callLater(0, worker.extract_xmp)
    return deferred


##
## This class executes a series of extract operations, accumulating the results and saving them all.
## In case of the partial failure of a single extractor, # the results from successful operations 
## are saved, and an error is returned.
##
class ExtractXMP:
    def __init__(self, deferred, item_id, workspace, variant_name):
        self.deferred = deferred
        self.proxy = Proxy('FeatureExtractor')
        self.workspace = workspace
        self.item = Item.objects.get(pk = item_id)
        self.variant_name = variant_name
        self.source_variant = Variant.objects.get(name = variant_name)
        self.component = self.item.get_variant(workspace, self.source_variant)
        self.ctype = None
        self.result = []

    def _read_xmp_features(self, features):
        xpath = re.compile(r'(?P<prefix>\w+):(?P<property>\w+)(?P<array_index>\[\d+\]){,1}')
        ctype = ContentType.objects.get_for_model(self.item)
        ctype_component = ContentType.objects.get_for_model(self.component)

        user = self.item.uploaded_by()
        metadata_default_language = get_metadata_default_language(user)

        metadata_dict = {}
        metadata_list = []
        delete_list = []

        log.debug('READ XMP FEATURES')

        if not isinstance(features, dict):
            item.state = 1  
            item.save()
            return [], []

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
                        log.debug('############# setting throw away IS_QUALIFIER option')
                        find_xpath = property_xpath.replace('/?xml:lang', '')
                        if metadata_dict[namespace_obj].has_key(find_xpath):
                            if property_value == 'x-default':
                                property_value = metadata_default_language
                            metadata_dict[namespace_obj][find_xpath].language = property_value
                        else:
                            log.debug('metadata property not found: ' + find_xpath)
                        log.debug('###@@@@ %s: (%s)' % (find_xpath, property_value))
                    else:
                        if found_property[0].is_variant:
                            x = MetadataValue(schema=found_property[0], object_id=self.component.pk, content_type=ctype_component, value=property_value, xpath=property_xpath)
                        else:
                            x = MetadataValue(schema=found_property[0], object_id=self.item.pk, content_type=ctype, value=property_value, xpath=property_xpath)
                        metadata_dict[namespace_obj][property_xpath] = x
                        metadata_list.append(x)
        return metadata_list, delete_list

    def _cb_error(self, failure):
        self.deferred.errback(failure)

    def _cb_xmp_ok(self, features):
        ctype_component = ContentType.objects.get_for_model(self.component)
        ctype = ContentType.objects.get_for_model(self.item)
        xpath = re.compile(r'(?P<prefix>\w+):(?P<property>\w+)(?P<array_index>\[\d+\]){,1}')
        user = self.item.uploaded_by()
        metadata_default_language = get_metadata_default_language(user)
        try:
            save_type(ctype, self.component)
        except Exception, e:
            log.error("Failed to save component format as DC:Format: %s" % (str(e)))

        xmp_metadata_list, xmp_delete_list = self._read_xmp_features(features)

        MetadataValue.objects.filter(schema__in=xmp_delete_list, object_id=self.component.pk, content_type=ctype_component).delete()

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
        extractor_proxy = Proxy('FeatureExtractor')
        d = extractor_proxy.extract(self.component.uri,  'xmp_extractor')
        d.addCallbacks(self._cb_xmp_ok, self._cb_error)
        return d
        

def test():
    print 'test'
    item = Item.objects.get(pk=1)
    workspace = DAMWorkspace.objects.get(pk = 1)
    
    d = run(4,
            workspace,
            source_variant = 'original',
            )
    print 'addBoth'
    d.addBoth(print_result)
    print 'dopo addBoth'
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    
