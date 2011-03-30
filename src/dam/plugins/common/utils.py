import mimetypes
from mediadart import log
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
def resize_image(width, height, max_w, max_h, enlarge=False):
    alfa = min(float(max_w)/width, float(max_h)/height)
    if (alfa > 1 and enlarge) or (0 < alfa < 1):
        return int((width * alfa)/2)*2, int((height * alfa)/2)*2
    else:
        return width, height

class Pushlist(list):
    "A List where we can push back values when iterating"
    def __init__(self, *args):
        list.__init__(self, *args)
        self.stack = []
        self.iterator = None

    def __iter__(self):
        self.iterator = list.__iter__(self)
        return self

    def next(self):
        if self.stack:
            return self.stack.pop()
        else:
            return self.iterator.next()

    def push(self, a):
        self.stack.append(a)
        

def splitstring(s):
    """Tokenizes a string containing command line arguments:

    See test_splitsstring() for examples.
    """
    s = s.replace('\n', ' ')
    sep = ' '
    l = Pushlist(s.split(sep))
    quotes = ['"', "'"]
    inside = False
    ret = []
    for w in l:
        if inside:
            if not w:
                word += sep
            elif w[-1] == quote:
                word += sep + w[:-1]
                inside = False
                quote=None
                ret.append(word)
            else:
                word += sep + w
        else:
            if not w:
                continue
            elif w[0] in quotes:
                if len(w) > 1 and w[-1] in quotes:   # a single word in quotes
                    ret.append(w[1:-1])
                    #if len(w) > 2:
                    #else:
                    #    ret.append('""')
                else:
                    quote = w[0]
                    inside = True
                    word = w[1:]
            elif w.find('=') >= 0:    # further split arguments of the type key=value so that
                i = w.find('=')       # value is a entry in the list
                if i:
                    ret.append(w[:i])
                ret.append('=')
                l.push(w[i+1:])
            else:
                ret.append(w)
    if inside:
        raise Exception("Error: unmatched quote in string")
    return ret

def test_splitstring():
    cases = [
      ( 'a b c', ['a', 'b', 'c'],),
      ( 'a   c', ['a', 'c'],),
      ( 'a ""  c', ['a', '', 'c'],),
      ( 'a "  "\n  c', ['a','  ', 'c'],),
      ( "a 'a b'  c", ['a', 'a b', 'c'],),
      ( 'a "a b" c', ['a', 'a b', 'c'],),
      ( 'a "a=b" c', ['a', 'a=b', 'c'],),
      ( 'a "a=" c', ['a', 'a=', 'c'],),
      ( 'a  a=  c', ['a', 'a', '=', 'c'],),
      ( 'a  =a  c', ['a', '=', 'a', 'c'],),
      ( 'a a="" c', ['a', 'a', '=', '', 'c'],),
      ( 'a z="b" c', ['a', 'z', '=', 'b', 'c'],),
      ( 'a z="b=c" d', ['a', 'z', '=', 'b=c', 'd'],),
      ( 'a z="x y z" c', ['a', 'z', '=', 'x y z', 'c'],),
    ]
    msg = ""
    for c in cases:
        r = splitstring(c[0])
        if r != c[1]:
            msg += "ERROR: <%s> split in %s (expecting %s)" % (c[0], r, c[1])
    print (not msg and 'OK') or msg
test_splitstring()

