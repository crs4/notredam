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

def get_variants(workspace, media_type = None, auto_generated = None):
    from django.db.models import Q
    from dam.variants.models import Variant
    tmp_variants = Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False)
    if media_type:
        tmp_variants = tmp_variants.filter(media_type__name = media_type)
    
    if auto_generated is not None:
        tmp_variants= tmp_variants.filter(auto_generated = auto_generated)
     
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
        print 'a', variant_name, item.pk
        resource = Component.objects.get(workspace=workspace, variant__name=variant_name, item=item)
        print 'b'
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





