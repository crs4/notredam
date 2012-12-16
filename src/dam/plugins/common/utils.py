import mimetypes
from struct import unpack
from mprocessor import log
from dam.metadata.models import MetadataProperty, MetadataValue
from dam.repository.models import Item, Component
from dam.supported_types import mime_types_by_type



def save_type(ctype, component):
    "Extract and save the format of the component as the value of dc:format"
    mime_type = mimetypes.guess_type(component.uri)[0]
    component.format = mime_type.split('/')[1]
    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=component, value=mime_type)

def get_ext_by_type(type_name):
    if type_name in mime_types_by_type:
        return [[x[1][0], x[0]] for x in mime_types_by_type[type_name].items()]
    else:
        return None

def get_variants(workspace, media_type = None, auto_generated = None, exclude = []):
    from django.db.models import Q
    from dam.variants.models import Variant
    tmp_variants = Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False)
    if media_type:
        tmp_variants = tmp_variants.filter(media_type__name = media_type)
    
    if auto_generated is not None:
        tmp_variants= tmp_variants.filter(auto_generated = auto_generated)
     
    
    if exclude:
        if not isinstance(exclude, list):
            exclude = [exclude]
        print '---------exclude ' , exclude
        tmp_variants = tmp_variants.exclude(name__in = exclude)
    
    print 'tmp_variants ', tmp_variants
    return [[variant.name] for variant in tmp_variants.distinct()]

def get_source_rendition(item_id, variant_name, workspace):
    """
        Returns the (item, component) objects that represents the given rendition_id
    """
    if hasattr(item_id, 'create_variant'):
        item = item_id
    else:
        item = Item.objects.get(pk = item_id)

    resource = None
    if hasattr(variant_name, 'upper'):   # it looks like a string
        resource = Component.objects.get(workspace=workspace, variant__name=variant_name, item=item)
    elif hasattr(variant_name, 'append'):  # looks like a list
        for name in variant_name:
            try:
                resource = Component.objects.get(workspace=workspace, variant__name=name, item=item)
                break
            except  Component.DoesNotExist:
                pass
    else:
        raise ValueError("invalid value for variant_name = %s" % str(variant_name))

    if not resource:
        raise  Component.DoesNotExist('No resource matching item_id=%s, variant name = %s' % (item_id, variant_name))

    return item, resource

def parse_rendition_url(rendition_id):
    try: 
        item_id, variant_name = rendition_id.split('/')
        return item_id, variant_name
    except ValueError:
        raise ValueError('invalid rendition_id = %s' % rendition_id)

def get_rendition_by_url(rendition_id, workspace):
    "Returns the component corresponding to rendition_id"
    return get_rendition(parse_rendition_url(rendition_id), workspace)

# Utility functions
def resize_image(width, height, max_w, max_h):
    w, h, max_w, max_h = float(width), float(height), float(max_w), float(max_h)
    alfa = min(max_w/w, max_h/h)
    if 0 < alfa < 1:
        return int((w * alfa)/2)*2, int((h * alfa)/2)*2
    else:
        return int(w), int(h)


#
# FLV parsing
#
#def read_tag(f):
#    "read timestamp from FLV file"
#    v = f.read(4)
#    taglen = unpack('!L', v)[0]
#    if taglen == 0:
#        return None, None              # start of file
#    f.seek(-(taglen+4), 1)             # start of tag
#    v = f.read(7)
#    tagtype = unpack('B', v[0])[0]
#    timestamp = unpack('!L', '\x00' + v[4:])[0]
#    f.seek(-(4+7), 1)
#    return tagtype, timestamp
#
#
#def get_flv_duration(filename, stream_type='video'):
#    """return the duration in seconds of an flv file
#
#    FLV records independent timestamps for audio and video. The difference
#    is usually a few tens of seconds. The defaults is the right choice 
#    unless the file contains only audio.
#    """
#    f = open(filename, 'r')
#    v = f.read(5)
#    header = unpack('!B', v[4])[0]
#    if stream_type == 'video':
#        if not header & 0x1:
#            raise Exception('FLV does not contain video')
#        else:
#            target_type = 9
#    elif stream_type == 'audio':
#        if not header & 0x3:
#            raise Exception('FLV does not contain audio')
#        else:
#            target_type = 8
#    else:
#        raise Exception('Unrecognized stream type (must be "audio" or "video")')
#    f.seek(-4, 2)
#    duration = 0
#    # reads flv tags backwards. When the right one (video or audio) is found, return
#    # its timestamp
#    while 1:
#        tagtype, tagtime = read_tag(f)
#        if tagtype in (target_type, None):
#            break
#    if tagtime is None:
#        return 0
#    else:
#        return tagtime/1000.
#
